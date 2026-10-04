"""Inspect detector errors without using the test split for model selection."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps

from indoor_detection.dataset import IMAGE_SUFFIXES, parse_yolo_label


@dataclass(frozen=True)
class Detection:
    """One absolute-coordinate bounding box."""

    xyxy: tuple[float, float, float, float]
    confidence: float = 1.0
    class_id: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze one indoor detector class")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "val", "test"), default="val")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--confidence", type=float, default=0.20)
    parser.add_argument(
        "--class-name", choices=("smoke", "fire", "person"), default="smoke"
    )
    parser.add_argument("--candidate-confidence", type=float, default=0.001)
    parser.add_argument("--iou", type=float, default=0.50)
    parser.add_argument("--max-det", type=int, default=100)
    parser.add_argument("--gallery-size", type=int, default=48)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def box_iou(left: Detection, right: Detection) -> float:
    ax1, ay1, ax2, ay2 = left.xyxy
    bx1, by1, bx2, by2 = right.xyxy
    intersection_width = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    intersection_height = max(0.0, min(ay2, by2) - max(ay1, by1))
    intersection = intersection_width * intersection_height
    left_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    right_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def match_detections(
    ground_truth: Sequence[Detection],
    predictions: Sequence[Detection],
    iou_threshold: float,
) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    """Greedily match high-confidence predictions to one ground-truth box each."""
    candidates: list[tuple[float, float, int, int]] = []
    for prediction_index, prediction in enumerate(predictions):
        for ground_truth_index, target in enumerate(ground_truth):
            iou = box_iou(prediction, target)
            if iou >= iou_threshold:
                candidates.append(
                    (prediction.confidence, iou, prediction_index, ground_truth_index)
                )
    candidates.sort(reverse=True)
    used_predictions: set[int] = set()
    used_targets: set[int] = set()
    matches: list[tuple[int, int, float]] = []
    for _, iou, prediction_index, ground_truth_index in candidates:
        if prediction_index in used_predictions or ground_truth_index in used_targets:
            continue
        used_predictions.add(prediction_index)
        used_targets.add(ground_truth_index)
        matches.append((prediction_index, ground_truth_index, iou))
    false_positives = [index for index in range(len(predictions)) if index not in used_predictions]
    false_negatives = [index for index in range(len(ground_truth)) if index not in used_targets]
    return matches, false_positives, false_negatives


def _resolve_dataset_split(dataset_yaml: Path, split: str) -> list[Path]:
    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    dataset_root = Path(str(config.get("path", dataset_yaml.parent)))
    if not dataset_root.is_absolute():
        dataset_root = (dataset_yaml.parent / dataset_root).resolve()
    split_value = config.get(split)
    if not isinstance(split_value, (str, list)):
        raise ValueError(f"Dataset YAML has no usable '{split}' split")
    split_items = [split_value] if isinstance(split_value, str) else split_value
    images: list[Path] = []
    for item in split_items:
        source = Path(str(item))
        if not source.is_absolute():
            source = dataset_root / source
        if source.is_dir():
            images.extend(
                path
                for path in source.rglob("*")
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
        elif source.is_file() and source.suffix.lower() == ".txt":
            for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
                line = raw_line.strip()
                if line:
                    path = Path(line)
                    images.append(path if path.is_absolute() else dataset_root / path)
        else:
            raise FileNotFoundError(f"Dataset split source not found: {source}")
    return sorted(images)


def _dataset_class_id(dataset_yaml: Path, class_name: str) -> int:
    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8"))
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


def _filter_images_for_class_scope(
    dataset_yaml: Path, image_paths: Sequence[Path], class_id: int
) -> tuple[list[Path], int, bool]:
    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    if not config.get("class_scope_manifest"):
        return list(image_paths), 0, False

    from indoor_detection.partial_label_training import (
        load_class_scopes,
        resolve_scope_manifest,
    )

    config["yaml_file"] = str(dataset_yaml.resolve())
    scopes = load_class_scopes(resolve_scope_manifest(config))
    selected: list[Path] = []
    for image_path in image_paths:
        key = os.path.normcase(str(image_path.resolve()))
        known_classes = scopes.get(key)
        if known_classes is None:
            raise ValueError(f"Image is missing from class-scope manifest: {image_path}")
        if class_id >= len(known_classes):
            raise ValueError(f"Class id {class_id} is outside the scope manifest")
        if bool(known_classes[class_id]):
            selected.append(image_path)
    return selected, len(image_paths) - len(selected), True


def _label_path(image_path: Path) -> Path:
    parts = list(image_path.parts)
    image_indices = [index for index, part in enumerate(parts) if part.lower() == "images"]
    if not image_indices:
        raise ValueError(f"Image path has no 'images' directory: {image_path}")
    parts[image_indices[-1]] = "labels"
    return Path(*parts).with_suffix(".txt")


def _load_ground_truth(
    image_path: Path,
    width: int,
    height: int,
    class_id: int,
) -> list[Detection]:
    label_path = _label_path(image_path)
    if not label_path.is_file():
        raise FileNotFoundError(f"Label not found: {label_path}")
    detections: list[Detection] = []
    rows = parse_yolo_label(label_path.read_text(encoding="utf-8-sig"), {0, 1, 2})
    for fields in rows:
        if int(fields[0]) != class_id:
            continue
        x_center, y_center, box_width, box_height = (float(value) for value in fields[1:])
        x1 = (x_center - box_width / 2) * width
        y1 = (y_center - box_height / 2) * height
        x2 = (x_center + box_width / 2) * width
        y2 = (y_center + box_height / 2) * height
        detections.append(Detection((x1, y1, x2, y2), class_id=class_id))
    return detections


def _image_stats(image_path: Path) -> dict[str, float | int | str]:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"OpenCV could not read image: {image_path}")
    brightness = float(image.mean())
    contrast = float(image.std())
    laplacian_variance = float(cv2.Laplacian(image, cv2.CV_64F).var())
    if brightness < 64:
        brightness_bucket = "dark"
    elif brightness > 192:
        brightness_bucket = "bright"
    else:
        brightness_bucket = "normal"
    if laplacian_variance < 50:
        sharpness_bucket = "blurred"
    elif laplacian_variance < 150:
        sharpness_bucket = "soft"
    else:
        sharpness_bucket = "sharp"
    return {
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "brightness": brightness,
        "contrast": contrast,
        "laplacian_variance": laplacian_variance,
        "brightness_bucket": brightness_bucket,
        "sharpness_bucket": sharpness_bucket,
    }


def _size_bucket(box: Detection, image_width: int, image_height: int) -> str:
    x1, y1, x2, y2 = box.xyxy
    relative_area = ((x2 - x1) * (y2 - y1)) / (image_width * image_height)
    if relative_area < 0.01:
        return "small_lt_1pct"
    if relative_area < 0.05:
        return "medium_1_to_5pct"
    return "large_ge_5pct"


def _miss_reason(
    target: Detection,
    candidates: Sequence[Detection],
    operating_confidence: float,
    iou_threshold: float,
) -> tuple[str, float, float]:
    if not candidates:
        return "no_candidate", 0.0, 0.0
    scored = [(box_iou(target, candidate), candidate.confidence) for candidate in candidates]
    best_iou, confidence_at_best_iou = max(scored)
    max_overlapping_confidence = max(
        (confidence for iou, confidence in scored if iou >= iou_threshold), default=0.0
    )
    if max_overlapping_confidence and max_overlapping_confidence < operating_confidence:
        return "below_confidence", best_iou, max_overlapping_confidence
    if best_iou < iou_threshold:
        return "localization_or_no_overlap", best_iou, confidence_at_best_iou
    return "duplicate_or_assignment", best_iou, confidence_at_best_iou


def _metric_row(counter: Counter[str]) -> dict[str, float | int]:
    true_positives = counter["tp"]
    false_positives = counter["fp"]
    false_negatives = counter["fn"]
    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives
    precision = true_positives / precision_denominator if precision_denominator else 0.0
    recall = true_positives / recall_denominator if recall_denominator else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _draw_example(record: dict[str, Any], destination: Path, title: str) -> Path:
    image = Image.open(record["image_path"]).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for box in record["ground_truth"]:
        color = "#e53935" if box["missed"] else "#43a047"
        draw.rectangle(box["xyxy"], outline=color, width=4)
    for box in record["predictions"]:
        color = "#fb8c00" if box["false_positive"] else "#1e88e5"
        draw.rectangle(box["xyxy"], outline=color, width=3)
        draw.text(
            (box["xyxy"][0] + 2, box["xyxy"][1] + 2),
            f"{box['confidence']:.2f}",
            fill=color,
            font=font,
            stroke_width=1,
            stroke_fill="black",
        )
    canvas = Image.new("RGB", (image.width, image.height + 28), "#111111")
    canvas.paste(image, (0, 28))
    ImageDraw.Draw(canvas).text((6, 7), title, fill="white", font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=90)
    return destination


def _contact_sheet(images: Iterable[Path], destination: Path, columns: int = 4) -> None:
    paths = list(images)
    if not paths:
        return
    cell_width, cell_height = 320, 240
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#202020")
    for index, path in enumerate(paths):
        with Image.open(path) as image:
            thumbnail = ImageOps.contain(image.convert("RGB"), (cell_width - 8, cell_height - 8))
        x = index % columns * cell_width + (cell_width - thumbnail.width) // 2
        y = index // columns * cell_height + (cell_height - thumbnail.height) // 2
        sheet.paste(thumbnail, (x, y))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=88)


def _write_records_csv(records: Sequence[dict[str, Any]], path: Path) -> None:
    fields = [
        "image",
        "ground_truth_count",
        "prediction_count",
        "true_positives",
        "false_positives",
        "false_negatives",
        "brightness",
        "contrast",
        "laplacian_variance",
        "brightness_bucket",
        "sharpness_bucket",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record[field] for field in fields})


def _summarize(
    records: Sequence[dict[str, Any]], size_counts: dict[str, Counter[str]]
) -> dict[str, Any]:
    overall: Counter[str] = Counter()
    miss_reasons: Counter[str] = Counter()
    image_buckets: dict[str, dict[str, Counter[str]]] = {
        "brightness": defaultdict(Counter),
        "sharpness": defaultdict(Counter),
    }
    for record in records:
        overall.update(
            {
                "tp": record["true_positives"],
                "fp": record["false_positives"],
                "fn": record["false_negatives"],
            }
        )
        for target in record["ground_truth"]:
            if target["missed"]:
                miss_reasons[target["miss_reason"]] += 1
        for dimension, key in (
            ("brightness", "brightness_bucket"),
            ("sharpness", "sharpness_bucket"),
        ):
            image_buckets[dimension][record[key]].update(
                {
                    "tp": record["true_positives"],
                    "fp": record["false_positives"],
                    "fn": record["false_negatives"],
                }
            )
    negative_records = [record for record in records if not record["ground_truth_count"]]
    negative_alarms = [record for record in negative_records if record["prediction_count"]]
    positive_records = [record for record in records if record["ground_truth_count"]]
    return {
        "overall": _metric_row(overall),
        "images": {
            "total": len(records),
            "with_ground_truth": sum(bool(record["ground_truth_count"]) for record in records),
            "with_false_positives": sum(bool(record["false_positives"]) for record in records),
            "with_false_negatives": sum(bool(record["false_negatives"]) for record in records),
        },
        "false_alarm_breakdown": {
            "negative_images": len(negative_records),
            "negative_images_with_predictions": len(negative_alarms),
            "negative_image_false_alarm_rate": (
                len(negative_alarms) / len(negative_records) if negative_records else 0.0
            ),
            "prediction_boxes_on_negative_images": sum(
                record["prediction_count"] for record in negative_alarms
            ),
            "extra_prediction_boxes_on_positive_images": sum(
                record["false_positives"] for record in positive_records
            ),
        },
        "miss_reasons": dict(sorted(miss_reasons.items())),
        "ground_truth_size_buckets": {
            bucket: _metric_row(counter) for bucket, counter in sorted(size_counts.items())
        },
        "image_condition_buckets": {
            dimension: {
                bucket: _metric_row(counter) for bucket, counter in sorted(counters.items())
            }
            for dimension, counters in image_buckets.items()
        },
    }


def _predict_in_bounded_batches(
    model: Any,
    image_paths: Sequence[Path],
    *,
    imgsz: int,
    device: str,
    batch: int,
    confidence: float,
    max_det: int,
) -> Iterable[Any]:
    """Avoid Ultralytics retaining a very large path list in one predictor call."""
    for start in range(0, len(image_paths), batch):
        chunk = image_paths[start : start + batch]
        batch_results = model.predict(
            source=[str(path) for path in chunk],
            imgsz=imgsz,
            rect=False,
            conf=confidence,
            device=device,
            batch=len(chunk),
            max_det=max_det,
            stream=False,
            verbose=False,
        )
        yield from batch_results
        del batch_results
        if str(device).lower() != "cpu":
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        completed = min(start + len(chunk), len(image_paths))
        print(f"analyzed {completed}/{len(image_paths)} images", flush=True)


def analyze_errors(
    *,
    model_path: Path,
    data_path: Path,
    split: str,
    imgsz: int,
    device: str,
    batch: int,
    operating_confidence: float,
    class_name: str,
    candidate_confidence: float,
    iou_threshold: float,
    max_det: int,
    gallery_size: int,
    output_dir: Path,
) -> dict[str, Any]:
    if not 0 <= candidate_confidence <= operating_confidence <= 1:
        raise ValueError("Expected 0 <= candidate confidence <= operating confidence <= 1")
    if not 0 < iou_threshold <= 1:
        raise ValueError("IoU threshold must be in (0, 1]")
    if gallery_size < 0:
        raise ValueError("Gallery size cannot be negative")
    if batch < 1:
        raise ValueError("Batch size must be positive")
    if max_det < 1:
        raise ValueError("Maximum detections must be positive")
    if not model_path.is_file():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {data_path}")

    from ultralytics import YOLO

    image_paths = _resolve_dataset_split(data_path.resolve(), split)
    if not image_paths:
        raise ValueError(f"No images found in split: {split}")
    output_dir.mkdir(parents=True, exist_ok=True)
    class_id = _dataset_class_id(data_path.resolve(), class_name)
    image_paths, excluded_out_of_scope, class_scoped_analysis = _filter_images_for_class_scope(
        data_path.resolve(), image_paths, class_id
    )
    if not image_paths:
        raise ValueError(f"No images have annotation scope for class: {class_name}")
    model = YOLO(str(model_path.resolve()))
    # Initialize lazy CUDA/NMS operations before scoring a batch: a cold NMS
    # timeout can otherwise leave later images in that batch unprocessed.
    model.predict(
        source=str(image_paths[0]),
        imgsz=imgsz,
        rect=False,
        conf=candidate_confidence,
        device=device,
        max_det=max_det,
        verbose=False,
    )
    results = _predict_in_bounded_batches(
        model,
        image_paths,
        imgsz=imgsz,
        device=device,
        batch=batch,
        confidence=candidate_confidence,
        max_det=max_det,
    )

    records: list[dict[str, Any]] = []
    size_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for result in results:
        image_path = Path(result.path).resolve()
        stats = _image_stats(image_path)
        width = int(stats["width"])
        height = int(stats["height"])
        ground_truth = _load_ground_truth(image_path, width, height, class_id)
        all_candidates = [
            Detection(
                tuple(float(value) for value in xyxy),
                float(confidence),
                int(predicted_class),
            )
            for xyxy, confidence, predicted_class in zip(
                result.boxes.xyxy.cpu().tolist(),
                result.boxes.conf.cpu().tolist(),
                result.boxes.cls.cpu().tolist(),
                strict=True,
            )
            if int(predicted_class) == class_id
        ]
        predictions = [
            prediction
            for prediction in all_candidates
            if prediction.confidence >= operating_confidence
        ]
        matches, false_positive_indices, false_negative_indices = match_detections(
            ground_truth, predictions, iou_threshold
        )
        matched_predictions = {prediction_index for prediction_index, _, _ in matches}
        matched_targets = {target_index for _, target_index, _ in matches}

        target_rows: list[dict[str, Any]] = []
        for index, target in enumerate(ground_truth):
            size_bucket = _size_bucket(target, width, height)
            missed = index not in matched_targets
            size_counts[size_bucket]["fn" if missed else "tp"] += 1
            reason, best_iou, candidate_confidence_value = (
                _miss_reason(
                    target, all_candidates, operating_confidence, iou_threshold
                )
                if missed
                else ("matched", 1.0, 1.0)
            )
            target_rows.append(
                {
                    "xyxy": list(target.xyxy),
                    "size_bucket": size_bucket,
                    "missed": missed,
                    "miss_reason": reason,
                    "best_candidate_iou": best_iou,
                    "best_candidate_confidence": candidate_confidence_value,
                }
            )
        prediction_rows = [
            {
                "xyxy": list(prediction.xyxy),
                "confidence": prediction.confidence,
                "false_positive": index not in matched_predictions,
            }
            for index, prediction in enumerate(predictions)
        ]
        records.append(
            {
                "image": image_path.name,
                "image_path": image_path.as_posix(),
                "ground_truth_count": len(ground_truth),
                "prediction_count": len(predictions),
                "true_positives": len(matches),
                "false_positives": len(false_positive_indices),
                "false_negatives": len(false_negative_indices),
                **stats,
                "ground_truth": target_rows,
                "predictions": prediction_rows,
            }
        )

    summary = _summarize(records, size_counts)
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "model": model_path.resolve().as_posix(),
        "dataset_yaml": data_path.resolve().as_posix(),
        "split": split,
        "class_name": class_name,
        "class_id": class_id,
        "class_scoped_analysis": class_scoped_analysis,
        "excluded_out_of_scope_images": excluded_out_of_scope,
        "settings": {
            "imgsz": imgsz,
            "rect": False,
            "warmup_images": 1,
            "operating_confidence": operating_confidence,
            "candidate_confidence": candidate_confidence,
            "iou_threshold": iou_threshold,
            "max_det": max_det,
        },
        "summary": summary,
        "records": records,
    }
    (output_dir / "error-analysis.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_records_csv(records, output_dir / "per-image.csv")

    false_negative_records = sorted(
        (record for record in records if record["false_negatives"]),
        key=lambda record: (record["false_negatives"], -record["laplacian_variance"]),
        reverse=True,
    )[:gallery_size]
    false_positive_records = sorted(
        (record for record in records if record["false_positives"]),
        key=lambda record: (
            not bool(record["ground_truth_count"]),
            max(
                (
                    prediction["confidence"]
                    for prediction in record["predictions"]
                    if prediction["false_positive"]
                ),
                default=0.0,
            ),
            record["false_positives"],
        ),
        reverse=True,
    )[:gallery_size]
    negative_false_alarm_records = sorted(
        (
            record
            for record in records
            if not record["ground_truth_count"] and record["prediction_count"]
        ),
        key=lambda record: max(
            (prediction["confidence"] for prediction in record["predictions"]), default=0.0
        ),
        reverse=True,
    )[:gallery_size]
    fn_paths = [
        _draw_example(
            record,
            output_dir / "false-negatives" / f"{index:03d}_{record['image']}.jpg",
            f"FN={record['false_negatives']} TP={record['true_positives']} {record['image']}",
        )
        for index, record in enumerate(false_negative_records, start=1)
    ]
    fp_paths = [
        _draw_example(
            record,
            output_dir / "false-positives" / f"{index:03d}_{record['image']}.jpg",
            f"FP={record['false_positives']} TP={record['true_positives']} {record['image']}",
        )
        for index, record in enumerate(false_positive_records, start=1)
    ]
    negative_alarm_paths = [
        _draw_example(
            record,
            output_dir / "negative-false-alarms" / f"{index:03d}_{record['image']}.jpg",
            f"NEGATIVE FP={record['prediction_count']} {record['image']}",
        )
        for index, record in enumerate(negative_false_alarm_records, start=1)
    ]
    _contact_sheet(fn_paths, output_dir / "false-negatives-contact-sheet.jpg")
    _contact_sheet(fp_paths, output_dir / "false-positives-contact-sheet.jpg")
    _contact_sheet(
        negative_alarm_paths, output_dir / "negative-false-alarms-contact-sheet.jpg"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = analyze_errors(
        model_path=args.model,
        data_path=args.data,
        split=args.split,
        imgsz=args.imgsz,
        device=args.device,
        batch=args.batch,
        operating_confidence=args.confidence,
        class_name=args.class_name,
        candidate_confidence=args.candidate_confidence,
        iou_threshold=args.iou,
        max_det=args.max_det,
        gallery_size=args.gallery_size,
        output_dir=args.output,
    )
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
