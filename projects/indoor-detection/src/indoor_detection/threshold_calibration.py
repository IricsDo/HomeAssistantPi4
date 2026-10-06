"""Calibrate validation thresholds using the existing explicit greedy matcher."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from indoor_detection.error_analysis import Detection, match_detections


def _boxes(record: dict[str, Any]) -> tuple[list[Detection], list[Detection]]:
    targets = [Detection(tuple(row["xyxy"])) for row in record["ground_truth"]]
    predictions = [
        Detection(tuple(row["xyxy"]), float(row["confidence"]))
        for row in record["predictions"]
    ]
    for box in targets + predictions:
        if len(box.xyxy) != 4 or not all(math.isfinite(v) for v in box.xyxy):
            raise ValueError("Boxes must have four finite coordinates")
        if box.xyxy[2] < box.xyxy[0] or box.xyxy[3] < box.xyxy[1]:
            raise ValueError("Box coordinates must be ordered")
    if any(b.xyxy[2] == b.xyxy[0] or b.xyxy[3] == b.xyxy[1] for b in targets):
        raise ValueError("Ground truth boxes must have positive area")
    # Predictions clipped to an image boundary can have zero area. Retain them
    # as false positives, consistent with box_iou/match_detections (IoU zero).
    if any(not math.isfinite(p.confidence) or not 0 <= p.confidence <= 1
           for p in predictions):
        raise ValueError("Prediction confidences must be finite and in [0, 1]")
    return targets, predictions


def _metrics(tp: int, fp: int, targets: int, negative: int, alarms: int) -> dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / targets if targets else 0.0
    return {
        "true_positives": tp, "false_positives": fp, "false_negatives": targets - tp,
        "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "negative_images": negative, "negative_images_with_predictions": alarms,
        "negative_image_false_alarm_rate": alarms / negative if negative else 0.0,
    }


def exact_threshold_summary(
    records: Sequence[dict[str, Any]], threshold: float, iou: float = 0.5
) -> dict[str, Any]:
    """Rematch all images after inclusive confidence filtering."""
    if not math.isfinite(threshold) or not 0 <= threshold <= 1 or not 0 < iou <= 1:
        raise ValueError("Invalid threshold or IoU")
    tp = fp = targets_count = negatives = alarms = 0
    for record in records:
        targets, candidates = _boxes(record)
        predictions = [p for p in candidates if p.confidence >= threshold]
        matches, extra, _ = match_detections(targets, predictions, iou)
        tp += len(matches)
        fp += len(extra)
        targets_count += len(targets)
        if not targets:
            negatives += 1
            alarms += bool(predictions)
    return _metrics(tp, fp, targets_count, negatives, alarms)


def calibrate_exact_recall(
    report: dict[str, Any], *, target_recall: float = 0.9, reference_threshold: float
) -> dict[str, Any]:
    """Select the highest observed confidence reaching empirical target recall.

    Matching processes confidence descending. Lower-confidence predictions cannot
    change higher-confidence assignments; equal-confidence groups remain together.
    Build the exact curve once, then independently rematch the selected threshold.
    Candidate extraction/NMS/max_det must stay fixed. This is not a new model.val
    interpolated curve, nor a sweep of different prediction calls.
    """
    if not math.isfinite(target_recall) or not 0 < target_recall <= 1:
        raise ValueError("Target recall must be in (0, 1]")
    settings = report["settings"]
    floor = settings["candidate_confidence"]
    if (report["split"] != "val" or not report["class_scoped_analysis"]
            or settings["rect"] is not False
            or settings["operating_confidence"] != floor):
        raise ValueError("Requires scoped square validation with all candidate predictions")
    if not 0 <= floor <= reference_threshold <= 1:
        raise ValueError("Reference threshold must be inside the candidate range")
    iou = settings["iou_threshold"]
    if not 0 < iou <= 1:
        raise ValueError("Invalid IoU")
    records = report["records"]
    events: dict[float, list[int]] = defaultdict(lambda: [0, 0, 0])
    targets_count = negatives = 0
    seen: set[str] = set()
    for record in records:
        if record["image_path"] in seen:
            raise ValueError("Duplicate image in candidate report")
        seen.add(record["image_path"])
        targets, predictions = _boxes(record)
        if any(p.confidence < floor for p in predictions):
            raise ValueError("Prediction below declared candidate floor")
        matches, _, _ = match_detections(targets, predictions, iou)
        matched = {index for index, _, _ in matches}
        targets_count += len(targets)
        for index, prediction in enumerate(predictions):
            events[prediction.confidence][0 if index in matched else 1] += 1
        if not targets:
            negatives += 1
            if predictions:
                events[max(p.confidence for p in predictions)][2] += 1
    if not targets_count:
        raise ValueError("Calibration requires ground truth targets")
    required_tp = math.ceil(target_recall * targets_count)
    tp = fp = alarms = 0
    curve: list[dict[str, Any]] = []
    selected = None
    for confidence, (add_tp, add_fp, add_alarms) in sorted(events.items(), reverse=True):
        tp += add_tp
        fp += add_fp
        alarms += add_alarms
        row = {"threshold": confidence, **_metrics(tp, fp, targets_count, negatives, alarms)}
        curve.append(row)
        if selected is None and tp >= required_tp:
            selected = row
    if selected is not None:
        verified = exact_threshold_summary(records, selected["threshold"], iou)
        if verified != {k: v for k, v in selected.items() if k != "threshold"}:
            raise ValueError("Curve differs from independent selected-threshold rematching")
    return {
        "selection": "highest_observed_confidence_with_empirical_recall",
        "target_recall": target_recall, "required_true_positives": required_tp,
        "target_met": selected is not None, "selected": selected, "curve": curve,
        "reference": {"threshold": reference_threshold,
                      **exact_threshold_summary(records, reference_threshold, iou)},
        "candidate_floor": floor,
    }
