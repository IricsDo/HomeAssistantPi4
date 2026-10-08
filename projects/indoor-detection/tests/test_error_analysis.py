from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from PIL import Image

from indoor_detection.error_analysis import (
    Detection,
    _dataset_class_id,
    _draw_example,
    _filter_images_for_class_scope,
    _metric_row,
    _miss_reason,
    _predict_in_bounded_batches,
    _size_bucket,
    _summarize,
    box_iou,
    match_detections,
)


@pytest.mark.parametrize("orientation", [1, 3, 6, 8])
def test_gallery_uses_exif_oriented_prediction_frame(tmp_path: Path, orientation: int) -> None:
    import cv2
    import numpy as np

    source = Image.new("RGB", (80, 120), "red")
    source.paste("blue", (40, 0, 80, 120))
    metadata = source.getexif()
    metadata[274] = orientation
    path = tmp_path / "source.jpg"
    source.save(path, exif=metadata)
    destination = tmp_path / "gallery.jpg"
    _draw_example(
        {"image_path": str(path), "ground_truth": [], "predictions": []},
        destination,
        "EXIF regression",
    )
    expected = Image.fromarray(cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB))
    with Image.open(destination) as rendered:
        assert rendered.size == (expected.width, expected.height + 28)
        pixels = rendered.crop((0, 28, expected.width, expected.height + 28))
        assert np.abs(np.asarray(pixels).astype(float) - np.asarray(expected)).mean() < 5


@pytest.mark.parametrize("batch", [1, 2])
def test_audit_uses_square_inputs_for_every_chunk(batch: int) -> None:
    class Predictor:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def predict(self, **kwargs: object) -> list[str]:
            self.calls.append(kwargs)
            assert kwargs["rect"] is False
            assert kwargs["imgsz"] == 512
            return list(kwargs["source"])

    model = Predictor()
    paths = [Path("landscape.jpg"), Path("portrait.jpg"), Path("square.jpg")]
    results = list(_predict_in_bounded_batches(
        model, paths, imgsz=512, device="cpu", batch=batch,
        confidence=0.001, max_det=300,
    ))
    assert results == [str(path) for path in paths]
    assert [call["batch"] for call in model.calls] == ([1, 1, 1] if batch == 1 else [2, 1])


def test_dataset_class_id_resolves_unified_mapping(tmp_path: Path) -> None:
    dataset_yaml = tmp_path / "dataset.yaml"
    dataset_yaml.write_text(
        "names:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )

    assert _dataset_class_id(dataset_yaml, "person") == 2


def test_filters_images_outside_requested_class_scope(tmp_path: Path) -> None:
    smoke_image = (tmp_path / "smoke.jpg").resolve()
    person_image = (tmp_path / "person.jpg").resolve()
    manifest = tmp_path / "scopes.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classes": ["smoke", "fire", "person"],
                "images": {
                    smoke_image.as_posix(): ["smoke", "fire"],
                    person_image.as_posix(): ["person"],
                },
            }
        ),
        encoding="utf-8",
    )
    dataset_yaml = tmp_path / "dataset.yaml"
    dataset_yaml.write_text(
        "path: .\nclass_scope_manifest: scopes.json\n"
        "names: [smoke, fire, person]\n",
        encoding="utf-8",
    )

    selected, excluded, scoped = _filter_images_for_class_scope(
        dataset_yaml, [smoke_image, person_image], 2
    )

    assert selected == [person_image]
    assert excluded == 1
    assert scoped


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
