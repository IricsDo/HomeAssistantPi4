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
    parser.add_argument("--batch", type=int, default=24)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--class-name", choices=("smoke", "fire", "person"), default="smoke")
    threshold_group = parser.add_mutually_exclusive_group()
    threshold_group.add_argument(
        "--target-recall",
        type=float,
        help="Select the highest validation confidence meeting recall",
    )
    threshold_group.add_argument(
        "--operating-threshold", type=float, help="Report precision/recall at a frozen confidence"
    )
    threshold_group.add_argument(
        "--maximize-f1",
        action="store_true",
        help="Select the validation confidence with the highest class F1",
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
    maximize_f1: bool = False,
    class_index: int = 0,
) -> dict[str, Any] | None:
    if target_recall is None and threshold is None and not maximize_f1:
        return None
    if sum((target_recall is not None, threshold is not None, maximize_f1)) > 1:
        raise ValueError("Choose only one operating-point selection policy")
    if target_recall is not None and not 0 < target_recall <= 1:
        raise ValueError("target_recall must be in the interval (0, 1]")
    if threshold is not None and not 0 <= threshold <= 1:
        raise ValueError("operating_threshold must be in the interval [0, 1]")

    confidence_curves: dict[str, tuple[list[float], list[float]]] = {}
    for x_values, y_values, x_label, y_label in curves_results:
        if str(x_label).lower() != "confidence":
            continue
        ndim = getattr(y_values, "ndim", None)
        is_nested = (
            ndim > 1
            if ndim is not None
            else bool(y_values) and isinstance(y_values[0], (list, tuple))
        )
        class_values = y_values[class_index] if is_nested else y_values
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
    if maximize_f1:
        f1_values = [
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
            for precision, recall in zip(precisions, recalls, strict=True)
        ]
        index = max(
            range(len(f1_values)), key=lambda candidate: (f1_values[candidate], x_values[candidate])
        )
    elif target_recall is not None:
        eligible = [index for index, recall in enumerate(recalls) if recall >= target_recall]
        index = eligible[-1] if eligible else max(range(len(recalls)), key=recalls.__getitem__)
    else:
        assert threshold is not None
        index = min(
            range(len(x_values)), key=lambda candidate: abs(x_values[candidate] - threshold)
        )
    point = {
        "threshold": x_values[index],
        "precision": precisions[index],
        "recall": recalls[index],
        "target_recall": target_recall,
        "target_met": target_recall is None or recalls[index] >= target_recall,
    }
    if maximize_f1:
        point.update({"selection": "max_f1", "f1": f1_values[index]})
    return point


def _dataset_class_id(data_path: Path, class_name: str) -> int:
    import yaml

    config = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    names = config.get("names")
    normalized = dict(enumerate(names)) if isinstance(names, list) else names
    if not isinstance(normalized, dict):
        raise ValueError("Dataset YAML must define class names")
    matches = [
        int(class_id)
        for class_id, name in normalized.items()
        if str(name).strip().lower() == class_name
    ]
    if len(matches) != 1:
        raise ValueError(f"Dataset must define class '{class_name}' exactly once")
    return matches[0]


def _dataset_uses_class_scopes(data_path: Path) -> bool:
    import yaml

    config = yaml.safe_load(data_path.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    return bool(config.get("class_scope_manifest"))


def _per_class_metrics(metrics: Any) -> dict[str, dict[str, float]]:
    names = dict(metrics.names)
    box = metrics.box
    arrays = {
        "precision": list(box.p),
        "recall": list(box.r),
        "map50": list(box.ap50),
        "map50_95": list(box.ap),
    }
    class_ids = list(getattr(box, "ap_class_index", range(len(box.p))))
    if any(len(values) != len(class_ids) for values in arrays.values()):
        raise RuntimeError("Per-class metric arrays do not match ap_class_index")
    return {
        str(names[int(class_id)]): {
            metric_name: float(values[position]) for metric_name, values in arrays.items()
        }
        for position, class_id in enumerate(class_ids)
    }


def evaluate(
    *,
    model_path: Path,
    data_path: Path,
    split: str,
    imgsz: int,
    device: str,
    batch: int,
    workers: int,
    project: Path,
    name: str,
    report_path: Path,
    target_recall: float | None = None,
    operating_threshold: float | None = None,
    maximize_f1: bool = False,
    class_name: str = "smoke",
    pretrained_person: bool = False,
    square: bool = False,
) -> dict[str, Any]:
    if not model_path.is_file():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {data_path}")

    from ultralytics import YOLO

    class_id = _dataset_class_id(data_path, class_name)
    model = YOLO(str(model_path.resolve()))
    validation_options: dict[str, Any] = {}
    uses_class_scopes = _dataset_uses_class_scopes(data_path)
    if uses_class_scopes:
        from indoor_detection.partial_label_training import ClassScopedDetectionValidator

        validation_options["validator"] = ClassScopedDetectionValidator
    if pretrained_person:
        if class_name != "person" or not uses_class_scopes:
            raise ValueError("Pretrained person projection requires scoped person evaluation")
        from indoor_detection.pretrained_person_validation import PretrainedPersonScopedValidator

        validation_options["validator"] = PretrainedPersonScopedValidator
    if square:
        if not uses_class_scopes:
            raise ValueError("Square comparison requires a scoped dataset")
        from indoor_detection.partial_label_training import SquareClassScopedDetectionValidator
        from indoor_detection.pretrained_person_validation import (
            SquarePretrainedPersonScopedValidator,
        )

        validation_options["validator"] = (
            SquarePretrainedPersonScopedValidator
            if pretrained_person else SquareClassScopedDetectionValidator
        )
        validation_options["rect"] = False
    metrics = model.val(
        data=str(data_path.resolve()),
        split=split,
        imgsz=imgsz,
        device=device,
        batch=batch,
        workers=workers,
        project=str(project.resolve()),
        name=name,
        plots=True,
        **validation_options,
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
        "batch": batch,
        "workers": workers,
        "class_scoped_validation": uses_class_scopes,
        "pretrained_person_projection": pretrained_person,
        "square_calibration": square,
        "metrics": _json_value(metrics.results_dict),
        "per_class_metrics": _per_class_metrics(metrics),
        "speed_ms_per_image": _json_value(metrics.speed),
        "operating_point": _select_operating_point(
            metrics.curves_results,
            target_recall=target_recall,
            threshold=operating_threshold,
            maximize_f1=maximize_f1,
            class_index=class_id,
        ),
        "operating_point_class": {"id": class_id, "name": class_name},
    }
    if uses_class_scopes and not pretrained_person:
        report["operating_points"] = {
            name: _select_operating_point(
                metrics.curves_results,
                target_recall=0.90 if name != "person" else None,
                maximize_f1=name == "person",
                class_index=_dataset_class_id(data_path, name),
            )
            for name in ("smoke", "fire", "person")
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
        batch=args.batch,
        workers=args.workers,
        project=args.project,
        name=args.name,
        report_path=args.report,
        target_recall=args.target_recall,
        operating_threshold=args.operating_threshold,
        maximize_f1=args.maximize_f1,
        class_name=args.class_name,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
