from __future__ import annotations

from collections import Counter

import pytest

from smoke_detection.error_analysis import (
    Detection,
    _metric_row,
    _miss_reason,
    _size_bucket,
    _summarize,
    box_iou,
    match_detections,
)


def test_box_iou() -> None:
    first = Detection((0, 0, 10, 10))
    second = Detection((5, 5, 15, 15))

    assert box_iou(first, second) == pytest.approx(25 / 175)


def test_match_detections_assigns_each_target_once() -> None:
    targets = [Detection((0, 0, 10, 10)), Detection((20, 20, 30, 30))]
    predictions = [
        Detection((0, 0, 10, 10), 0.9),
        Detection((1, 1, 9, 9), 0.8),
        Detection((20, 20, 30, 30), 0.7),
    ]

    matches, false_positives, false_negatives = match_detections(targets, predictions, 0.5)

    assert {(prediction, target) for prediction, target, _ in matches} == {(0, 0), (2, 1)}
    assert false_positives == [1]
    assert false_negatives == []


def test_miss_reason_distinguishes_low_confidence_and_localization() -> None:
    target = Detection((0, 0, 10, 10))

    low_confidence = _miss_reason(target, [Detection((0, 0, 10, 10), 0.1)], 0.2, 0.5)
    localization = _miss_reason(target, [Detection((8, 8, 18, 18), 0.8)], 0.2, 0.5)

    assert low_confidence[0] == "below_confidence"
    assert localization[0] == "localization_or_no_overlap"


@pytest.mark.parametrize(
    ("box", "expected"),
    [
        (Detection((0, 0, 9, 9)), "small_lt_1pct"),
        (Detection((0, 0, 20, 20)), "medium_1_to_5pct"),
        (Detection((0, 0, 30, 30)), "large_ge_5pct"),
    ],
)
def test_size_bucket_uses_relative_image_area(box: Detection, expected: str) -> None:
    assert _size_bucket(box, 100, 100) == expected


def test_metric_row_handles_object_detection_counts() -> None:
    metrics = _metric_row(Counter(tp=8, fp=2, fn=2))

    assert metrics["precision"] == pytest.approx(0.8)
    assert metrics["recall"] == pytest.approx(0.8)
    assert metrics["f1"] == pytest.approx(0.8)


def test_summary_separates_true_negative_false_alarms() -> None:
    common = {
        "ground_truth": [],
        "brightness_bucket": "normal",
        "sharpness_bucket": "sharp",
        "true_positives": 0,
        "false_negatives": 0,
    }
    records = [
        {
            **common,
            "ground_truth_count": 0,
            "prediction_count": 2,
            "false_positives": 2,
        },
        {
            **common,
            "ground_truth_count": 0,
            "prediction_count": 0,
            "false_positives": 0,
        },
        {
            **common,
            "ground_truth_count": 1,
            "prediction_count": 2,
            "false_positives": 1,
        },
    ]

    breakdown = _summarize(records, {})["false_alarm_breakdown"]

    assert breakdown["negative_images"] == 2
    assert breakdown["negative_images_with_predictions"] == 1
    assert breakdown["negative_image_false_alarm_rate"] == pytest.approx(0.5)
    assert breakdown["prediction_boxes_on_negative_images"] == 2
    assert breakdown["extra_prediction_boxes_on_positive_images"] == 1
