"""Find person annotations missing from smoke/fire datasets without mutating labels."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import sha256_file


def _person_class_id(names: dict[int, str] | list[str]) -> int:
    normalized = dict(enumerate(names)) if isinstance(names, list) else names
    matches = [
        int(class_id)
        for class_id, name in normalized.items()
        if str(name).strip().lower() == "person"
    ]
    if len(matches) != 1:
        raise ValueError("Pretrained model must expose exactly one 'person' class")
    return matches[0]


def _candidate_rows(result: Any, person_class_id: int) -> list[dict[str, Any]]:
    boxes = result.boxes
    if boxes is None:
        return []
    rows: list[dict[str, Any]] = []
    for class_id, confidence, xywhn in zip(
        boxes.cls.tolist(), boxes.conf.tolist(), boxes.xywhn.tolist(), strict=True
    ):
        if int(class_id) != person_class_id:
            continue
        rows.append(
            {
                "confidence": round(float(confidence), 6),
                "xywhn": [round(float(value), 6) for value in xywhn],
            }
        )
    return rows


def _result_records(
    results: Iterable[Any],
    *,
    split_by_path: dict[Path, str],
    person_class_id: int,
    auto_accept_confidence: float,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for result in results:
        image_path = Path(result.path).resolve()
        candidates = _candidate_rows(result, person_class_id)
        if not candidates:
            continue
        records.append(
            {
                "image": image_path.as_posix(),
                "split": split_by_path[image_path],
                "status": (
                    "auto_accept_candidate"
                    if all(row["confidence"] >= auto_accept_confidence for row in candidates)
                    else "manual_review"
                ),
                "person_candidates": candidates,
            }
        )
    return records


def _chunks(values: list[Path], size: int) -> Iterable[list[Path]]:
    if size <= 0:
        raise ValueError("batch must be greater than zero")
    for start in range(0, len(values), size):
        yield values[start : start + size]


def audit_person_annotations(
    *,
    dataset_yaml: Path,
    model_path: Path,
    output_dir: Path,
    candidate_confidence: float = 0.20,
    auto_accept_confidence: float = 0.65,
    imgsz: int = 640,
    device: str = "0",
    batch: int = 16,
) -> dict[str, Any]:
    if not dataset_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_yaml}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Pretrained model not found: {model_path}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    if not 0 <= candidate_confidence <= auto_accept_confidence <= 1:
        raise ValueError("Expected 0 <= candidate_confidence <= auto_accept_confidence <= 1")

    split_images = {split: _resolve_split(dataset_yaml, split) for split in SPLITS}
    split_by_path = {
        image.resolve(): split for split, images in split_images.items() for image in images
    }
    images = sorted(split_by_path)

    from ultralytics import YOLO

    model = YOLO(str(model_path.resolve()))
    person_class_id = _person_class_id(model.names)
    records: list[dict[str, Any]] = []
    for image_batch in _chunks(images, batch):
        results = model.predict(
            source=[str(path) for path in image_batch],
            classes=[person_class_id],
            conf=candidate_confidence,
            imgsz=imgsz,
            device=device,
            batch=len(image_batch),
            stream=True,
            verbose=False,
        )
        records.extend(
            _result_records(
                results,
                split_by_path=split_by_path,
                person_class_id=person_class_id,
                auto_accept_confidence=auto_accept_confidence,
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    status_counts = Counter(record["status"] for record in records)
    split_counts = Counter(record["split"] for record in records)
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "Person annotation candidates; source labels were not modified",
        "dataset_yaml": dataset_yaml.resolve().as_posix(),
        "model": {
            "path": model_path.resolve().as_posix(),
            "sha256": sha256_file(model_path),
        },
        "settings": {
            "candidate_confidence": candidate_confidence,
            "auto_accept_confidence": auto_accept_confidence,
            "imgsz": imgsz,
            "device": device,
            "batch": batch,
        },
        "images_scanned": len(images),
        "images_with_candidates": len(records),
        "candidate_boxes": sum(len(record["person_candidates"]) for record in records),
        "by_status": dict(sorted(status_counts.items())),
        "by_split": dict(sorted(split_counts.items())),
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate person annotation candidates for a YOLO dataset"
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--candidate-confidence", type=float, default=0.20)
    parser.add_argument("--auto-accept-confidence", type=float, default=0.65)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--batch", type=int, default=16)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_person_annotations(
        dataset_yaml=args.data,
        model_path=args.model,
        output_dir=args.output_dir,
        candidate_confidence=args.candidate_confidence,
        auto_accept_confidence=args.auto_accept_confidence,
        imgsz=args.imgsz,
        device=args.device,
        batch=args.batch,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
