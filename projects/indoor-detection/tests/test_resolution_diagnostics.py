import pytest
import torch

from indoor_detection.pretrained_person_validation import (
    project_person_predictions,
    validate_pretrained_person_names,
)
from indoor_detection.size_diagnostics import height_bucket, projected_size_report


def test_projection_keeps_person_and_does_not_mutate_original():
    original = {"cls": torch.tensor([0.0, 2.0, 79.0]), "conf": torch.tensor([0.8, 0.7, 0.6])}
    projected = project_person_predictions([original])[0]
    assert projected["cls"].tolist() == [2.0]
    assert projected["conf"].tolist() == pytest.approx([0.8])
    assert original["cls"].tolist() == [0.0, 2.0, 79.0]


def test_projection_handles_empty_and_rejects_unknown_class():
    assert project_person_predictions([{"cls": torch.tensor([])}])[0]["cls"].numel() == 0
    with pytest.raises(ValueError):
        project_person_predictions([{"cls": torch.tensor([80])}])


def test_projection_requires_original_coco_names():
    names = {i: str(i) for i in range(80)}
    names[0] = "person"
    validate_pretrained_person_names(names)
    with pytest.raises(ValueError):
        validate_pretrained_person_names({0: "smoke", 1: "fire", 2: "person"})


def test_fixed_groups_are_stable_when_native_size_changes():
    records = [{"width": 1024, "height": 512, "ground_truth": [
        {"xyxy": [0, 0, 24, 24], "missed": True},
        {"xyxy": [0, 0, 40, 64], "missed": False},
    ]}]
    small = projected_size_report(records, 512)["buckets"]
    large = projected_size_report(records, 768)["buckets"]
    assert {k: v for k, v in small.items() if k.startswith("fixed")} == {
        k: v for k, v in large.items() if k.startswith("fixed")
    }
    assert small["fixed_512/both_sides_le_12"]["targets"] == 1
    assert "native/both_sides_le_12" not in large
    assert height_bucket(32) == "lt_64"


def test_size_diagnostics_rejects_invalid_resolution():
    with pytest.raises(ValueError):
        projected_size_report([], 0)


def test_square_validator_builds_square_dataset_without_changing_default(monkeypatch):
    from types import SimpleNamespace

    import indoor_detection.partial_label_training as scoped

    monkeypatch.setattr(scoped, "ClassScopedYOLODataset", lambda **kwargs: kwargs)
    args = SimpleNamespace(
        fraction=1.0, split="val", imgsz=640, cache=False, single_cls=False,
        task="detect", classes=None,
    )
    for cls, rectangular in (
        (scoped.ClassScopedDetectionValidator, True),
        (scoped.SquareClassScopedDetectionValidator, False),
    ):
        validator = object.__new__(cls)
        validator.args = args
        validator.stride = 32
        validator.data = {}
        dataset = validator.build_dataset("unused", batch=20)
        assert dataset["rect"] is rectangular
