"""Evaluate a trained detector on a named split and persist machine-readable metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate an indoor detector checkpoint")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", choices=("val", "test"), default="test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--report", type=Path, required=True)
    threshold_group = parser.add_mutually_exclusive_group()
    threshold_group.add_argument(
        "--target-recall",
        type=float,
        help="Select the highest validation confidence meeting recall",
    )
    threshold_group.add_argument(
        "--operating-threshold", type=float, help="Report precision/recall at a frozen confidence"
    )
    return parser


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _select_operating_point(
    curves_results: list[Any],
    *,
    target_recall: float | None = None,
    threshold: float | None = None,
) -> dict[str, Any] | None:
    if target_recall is None and threshold is None:
        return None
    if target_recall is not None and not 0 < target_recall <= 1:
        raise ValueError("target_recall must be in the interval (0, 1]")
    if threshold is not None and not 0 <= threshold <= 1:
        raise ValueError("operating_threshold must be in the interval [0, 1]")

    confidence_curves: dict[str, tuple[list[float], list[float]]] = {}
    for x_values, y_values, x_label, y_label in curves_results:
        if str(x_label).lower() != "confidence":
            continue
        ndim = getattr(y_values, "ndim", None)
        is_nested = ndim > 1 if ndim is not None else bool(y_values) and isinstance(
            y_values[0], (list, tuple)
        )
        class_values = y_values[0] if is_nested else y_values
        confidence_curves[str(y_label).lower()] = (
            [float(value) for value in x_values],
            [float(value) for value in class_values],
        )
    if "precision" not in confidence_curves or "recall" not in confidence_curves:
        raise RuntimeError("Ultralytics did not expose precision/recall confidence curves")

    x_values, recalls = confidence_curves["recall"]
    precision_x, precisions = confidence_curves["precision"]
    if x_values != precision_x:
        raise RuntimeError("Precision and recall confidence grids differ")
    if target_recall is not None:
        eligible = [index for index, recall in enumerate(recalls) if recall >= target_recall]
        index = eligible[-1] if eligible else max(range(len(recalls)), key=recalls.__getitem__)
    else:
        assert threshold is not None
        index = min(
            range(len(x_values)), key=lambda candidate: abs(x_values[candidate] - threshold)
        )
    return {
        "threshold": x_values[index],
        "precision": precisions[index],
        "recall": recalls[index],
        "target_recall": target_recall,
        "target_met": target_recall is None or recalls[index] >= target_recall,
    }


def evaluate(
    *,
    model_path: Path,
    data_path: Path,
    split: str,
    imgsz: int,
    device: str,
    project: Path,
    name: str,
    report_path: Path,
    target_recall: float | None = None,
    operating_threshold: float | None = None,
) -> dict[str, Any]:
    if not model_path.is_file():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {data_path}")

    from ultralytics import YOLO

    model = YOLO(str(model_path.resolve()))
    metrics = model.val(
        data=str(data_path.resolve()),
        split=split,
        imgsz=imgsz,
        device=device,
        project=str(project.resolve()),
        name=name,
        plots=True,
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "model": {
            "path": model_path.resolve().as_posix(),
            "bytes": model_path.stat().st_size,
            "sha256": _sha256(model_path),
        },
        "dataset_yaml": data_path.resolve().as_posix(),
        "split": split,
        "imgsz": imgsz,
        "metrics": _json_value(metrics.results_dict),
        "speed_ms_per_image": _json_value(metrics.speed),
        "operating_point": _select_operating_point(
            metrics.curves_results,
            target_recall=target_recall,
            threshold=operating_threshold,
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate(
        model_path=args.model,
        data_path=args.data,
        split=args.split,
        imgsz=args.imgsz,
        device=args.device,
        project=args.project,
        name=args.name,
        report_path=args.report,
        target_recall=args.target_recall,
        operating_threshold=args.operating_threshold,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
