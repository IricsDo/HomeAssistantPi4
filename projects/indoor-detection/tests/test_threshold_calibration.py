import random

import pytest

from indoor_detection.threshold_calibration import (
    calibrate_exact_recall,
    exact_threshold_summary,
)


def record(name, targets, predictions):
    return {"image_path": name,
            "ground_truth": [{"xyxy": b} for b in targets],
            "predictions": [{"xyxy": b, "confidence": c} for b, c in predictions]}


def report(records):
    return {"split": "val", "class_scoped_analysis": True,
            "settings": {"rect": False, "candidate_confidence": .001,
                         "operating_confidence": .001, "iou_threshold": .5},
            "records": records}


def test_exact_curve_rematches_ties_duplicates_and_negatives():
    box = (0, 0, 10, 10)
    other = (20, 20, 30, 30)
    rows = [record("a", [box, other], [(box, .9), (box, .8), (other, .4)]),
            record("b", [], [(box, .8), (other, .4)]),
            record("c", [box], [(box, .4)]), record("d", [], [])]
    result = calibrate_exact_recall(report(rows), reference_threshold=.8)
    assert result["selected"]["threshold"] == .4
    assert result["selected"]["true_positives"] == 3
    assert result["selected"]["false_positives"] == 3
    assert result["selected"]["negative_image_false_alarm_rate"] == .5
    assert result["reference"]["true_positives"] == 1
    for row in result["curve"]:
        assert exact_threshold_summary(rows, row["threshold"]) == {
            k: v for k, v in row.items() if k != "threshold"}


def test_unattainable_target_returns_no_selected_point():
    result = calibrate_exact_recall(
        report([record("a", [(0, 0, 10, 10)], [])]), reference_threshold=.5)
    assert result["selected"] is None
    assert result["target_met"] is False


@pytest.mark.parametrize("field,value", [("split", "test"), ("class_scoped_analysis", False)])
def test_rejects_ineligible_report(field, value):
    candidate = report([])
    candidate[field] = value
    with pytest.raises(ValueError):
        calibrate_exact_recall(candidate, reference_threshold=.5)


@pytest.mark.parametrize("key,value", [("rect", True), ("operating_confidence", .5),
                                      ("iou_threshold", 0)])
def test_rejects_bad_settings(key, value):
    candidate = report([])
    candidate["settings"][key] = value
    with pytest.raises(ValueError):
        calibrate_exact_recall(candidate, reference_threshold=.5)


@pytest.mark.parametrize("confidence", [float("nan"), 1.1, -.1])
def test_rejects_invalid_prediction_confidence(confidence):
    box = (0, 0, 10, 10)
    with pytest.raises(ValueError):
        exact_threshold_summary([record("a", [box], [(box, confidence)])], .5)


def test_rejects_duplicate_images_and_zero_targets():
    box = (0, 0, 10, 10)
    row = record("a", [box], [(box, .8)])
    with pytest.raises(ValueError, match="Duplicate"):
        calibrate_exact_recall(report([row, row]), reference_threshold=.5)
    with pytest.raises(ValueError, match="ground truth"):
        calibrate_exact_recall(report([record("a", [], [])]), reference_threshold=.5)


def test_curve_matches_brute_force_with_overlapping_boxes_and_tied_scores():
    rng = random.Random(42)
    for attempt in range(30):
        targets = [(0, 0, 10, 10), (3, 0, 13, 10), (20, 0, 30, 10)]
        predictions = []
        for _ in range(12):
            x = rng.choice([0, 2, 3, 5, 20, 40])
            predictions.append(((x, 0, x + 10, 10), rng.choice([.2, .4, .6, .8])))
        rows = [record(str(attempt), targets, predictions)]
        curve = calibrate_exact_recall(report(rows), reference_threshold=.5)["curve"]
        for row in curve:
            assert exact_threshold_summary(rows, row["threshold"]) == {
                k: v for k, v in row.items() if k != "threshold"}


def test_boundary_clipped_zero_area_predictions_count_as_false_positives():
    rows = [record("a", [(0, 0, 10, 10)],
                   [((10, 0, 10, 10), .8), ((0, 0, 10, 10), .7)])]
    selected = calibrate_exact_recall(report(rows), reference_threshold=.75)["selected"]
    assert selected["true_positives"] == 1
    assert selected["false_positives"] == 1
    assert selected["threshold"] == .7
