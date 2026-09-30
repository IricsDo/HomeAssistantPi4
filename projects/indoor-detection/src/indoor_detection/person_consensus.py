"""Cross-check person annotation candidates with a stronger COCO detector."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from indoor_detection.dataset import sha256_file
from indoor_detection.person_audit import (
    _candidate_rows,
    _chunks,
    _person_class_id,
)
from indoor_detection.person_review import _load_records


def _xywhn_to_xyxy(box: list[float]) -> tuple[float, float, float, float]:
    x_center, y_center, width, height = box
    return (
        x_center - width / 2,
        y_center - height / 2,
        x_center + width / 2,
        y_center + height / 2,
    )


def _box_iou(left: list[float], right: list[float]) -> float:
    left_x1, left_y1, left_x2, left_y2 = _xywhn_to_xyxy(left)
    right_x1, right_y1, right_x2, right_y2 = _xywhn_to_xyxy(right)
    intersection_width = max(0.0, min(left_x2, right_x2) - max(left_x1, right_x1))
    intersection_height = max(0.0, min(left_y2, right_y2) - max(left_y1, right_y1))
    intersection = intersection_width * intersection_height
    left_area = max(0.0, left_x2 - left_x1) * max(0.0, left_y2 - left_y1)
    right_area = max(0.0, right_x2 - right_x1) * max(0.0, right_y2 - right_y1)
    union = left_area + right_area - intersection
    return intersection / union if union > 0 else 0.0


def _match_candidates(
    primary: list[dict[str, Any]], verifier: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    unused = set(range(len(verifier)))
    matched: list[dict[str, Any]] = []
    for candidate in primary:
        best_index = max(
            unused,
            key=lambda index: _box_iou(candidate["xywhn"], verifier[index]["xywhn"]),
            default=None,
        )
        best_iou = (
            _box_iou(candidate["xywhn"], verifier[best_index]["xywhn"])
            if best_index is not None
            else 0.0
        )
        verifier_candidate = (
            verifier[best_index] if best_index is not None and best_iou > 0 else None
        )
        if verifier_candidate is not None:
            unused.remove(best_index)
        matched.append(
            {
                **candidate,
                "verifier_iou": round(best_iou, 6),
                "verifier_confidence": (
                    verifier_candidate["confidence"] if verifier_candidate is not None else None
                ),
                "verifier_xywhn": (
                    verifier_candidate["xywhn"] if verifier_candidate is not None else None
                ),
            }
        )
    return matched, [verifier[index] for index in sorted(unused)]


def _review_status(
    matched: list[dict[str, Any]],
    verifier_only: list[dict[str, Any]],
    *,
    strong_iou: float,
    strong_confidence: float,
) -> str:
    strong = [
        candidate
        for candidate in matched
        if candidate["verifier_iou"] >= strong_iou
        and candidate["verifier_confidence"] is not None
        and candidate["verifier_confidence"] >= strong_confidence
    ]
    if matched and len(strong) == len(matched) and not verifier_only:
        return "consensus_high_review"
    if strong:
        return "consensus_mixed_review"
    return "disagreement_review"


def verify_candidates(
    *,
    candidates_path: Path,
    verifier_model_path: Path,
    output_dir: Path,
    verifier_confidence: float = 0.10,
    strong_confidence: float = 0.50,
    strong_iou: float = 0.50,
    imgsz: int = 640,
    device: str = "0",
    batch: int = 16,
) -> dict[str, Any]:
    if not candidates_path.is_file():
        raise FileNotFoundError(f"Candidate JSONL not found: {candidates_path}")
    if not verifier_model_path.is_file():
        raise FileNotFoundError(f"Verifier model not found: {verifier_model_path}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    if not 0 <= verifier_confidence <= strong_confidence <= 1:
        raise ValueError("Expected 0 <= verifier_confidence <= strong_confidence <= 1")
    if not 0 <= strong_iou <= 1:
        raise ValueError("strong_iou must be in [0, 1]")

    records = _load_records(candidates_path)
    record_by_path = {Path(record["image"]).resolve(): record for record in records}
    if len(record_by_path) != len(records):
        raise ValueError("Candidate JSONL contains duplicate image records")

    from ultralytics import YOLO

    model = YOLO(str(verifier_model_path.resolve()))
    person_class_id = _person_class_id(model.names)
    verified_records: list[dict[str, Any]] = []
    paths = sorted(record_by_path)
    for image_batch in _chunks(paths, batch):
        results = model.predict(
            source=[str(path) for path in image_batch],
            classes=[person_class_id],
            conf=verifier_confidence,
            imgsz=imgsz,
            device=device,
            batch=len(image_batch),
            stream=True,
            verbose=False,
        )
        for result in results:
            image_path = Path(result.path).resolve()
            record = record_by_path[image_path]
            verifier = _candidate_rows(result, person_class_id)
            matched, verifier_only = _match_candidates(record["person_candidates"], verifier)
            verified_records.append(
                {
                    **record,
                    "status": _review_status(
                        matched,
                        verifier_only,
                        strong_iou=strong_iou,
                        strong_confidence=strong_confidence,
                    ),
                    "person_candidates": matched,
                    "verifier_only_candidates": verifier_only,
                }
            )

    verified_records.sort(key=lambda record: record["image"])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in verified_records),
        encoding="utf-8",
    )
    status_counts = Counter(record["status"] for record in verified_records)
    verifier_only_boxes = sum(
        len(record["verifier_only_candidates"]) for record in verified_records
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "Review prioritization only; automatic acceptance is disabled",
        "source_candidates": {
            "path": candidates_path.resolve().as_posix(),
            "sha256": sha256_file(candidates_path),
        },
        "verifier_model": {
            "path": verifier_model_path.resolve().as_posix(),
            "sha256": sha256_file(verifier_model_path),
        },
        "settings": {
            "verifier_confidence": verifier_confidence,
            "strong_confidence": strong_confidence,
            "strong_iou": strong_iou,
            "imgsz": imgsz,
            "device": device,
            "batch": batch,
            "automatic_acceptance": False,
        },
        "images": len(verified_records),
        "by_status": dict(sorted(status_counts.items())),
        "verifier_only_boxes": verifier_only_boxes,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-check person candidates with a stronger detector"
    )
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--verifier-model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--verifier-confidence", type=float, default=0.10)
    parser.add_argument("--strong-confidence", type=float, default=0.50)
    parser.add_argument("--strong-iou", type=float, default=0.50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--batch", type=int, default=16)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_candidates(
        candidates_path=args.candidates,
        verifier_model_path=args.verifier_model,
        output_dir=args.output_dir,
        verifier_confidence=args.verifier_confidence,
        strong_confidence=args.strong_confidence,
        strong_iou=args.strong_iou,
        imgsz=args.imgsz,
        device=args.device,
        batch=args.batch,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
