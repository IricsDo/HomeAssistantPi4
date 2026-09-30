from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch
from PIL import Image
from ultralytics.cfg import get_cfg

from indoor_detection.partial_label_training import (
    ClassScopedDetectionTrainer,
    ClassScopedYOLODataset,
    filter_predictions_to_known_classes,
    load_class_scopes,
)


def _write_scoped_dataset(root: Path) -> tuple[Path, Path]:
    image_dir = root / "images" / "train"
    label_dir = root / "labels" / "train"
    image_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    scopes: dict[str, list[str]] = {}
    for name, scope, class_id in (
        ("fire.jpg", ["smoke", "fire"], 1),
        ("person.jpg", ["person"], 2),
    ):
        image = image_dir / name
        Image.new("RGB", (64, 64), "gray").save(image)
        (label_dir / Path(name).with_suffix(".txt")).write_text(
            f"{class_id} 0.5 0.5 0.25 0.25\n", encoding="utf-8"
        )
        scopes[image.resolve().as_posix()] = scope
    manifest = root / "class_scope_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classes": ["smoke", "fire", "person"],
                "images": scopes,
            }
        ),
        encoding="utf-8",
    )
    return image_dir, manifest


def test_dataset_attaches_and_collates_known_classes(tmp_path: Path) -> None:
    image_dir, manifest = _write_scoped_dataset(tmp_path)
    hyp = get_cfg(overrides={"imgsz": 64, "mosaic": 0.0, "mixup": 0.0, "cutmix": 0.0})
    dataset = ClassScopedYOLODataset(
        img_path=str(image_dir),
        imgsz=64,
        batch_size=2,
        augment=False,
        hyp=hyp,
        rect=False,
        cache=False,
        single_cls=False,
        stride=32,
        pad=0.0,
        prefix="test: ",
        task="detect",
        classes=None,
        data={
            "names": {0: "smoke", 1: "fire", 2: "person"},
            "nc": 3,
            "path": str(tmp_path),
            "class_scope_manifest": str(manifest),
        },
        fraction=1.0,
    )

    batch = ClassScopedYOLODataset.collate_fn([dataset[0], dataset[1]])

    assert batch["known_classes"].shape == (2, 3)
    assert {tuple(row.tolist()) for row in batch["known_classes"]} == {
        (True, True, False),
        (False, False, True),
    }


def test_dataset_rejects_label_outside_declared_scope(tmp_path: Path) -> None:
    image_dir, manifest = _write_scoped_dataset(tmp_path)
    fire_scope = json.loads(manifest.read_text(encoding="utf-8"))
    person_image = (image_dir / "person.jpg").resolve().as_posix()
    fire_scope["images"][person_image] = ["smoke", "fire"]
    manifest.write_text(json.dumps(fire_scope), encoding="utf-8")

    with pytest.raises(ValueError, match="outside its declared scope"):
        ClassScopedYOLODataset(
            img_path=str(image_dir),
            imgsz=64,
            batch_size=2,
            augment=False,
            hyp=get_cfg(overrides={"imgsz": 64}),
            rect=False,
            cache=False,
            single_cls=False,
            stride=32,
            pad=0.0,
            prefix="test: ",
            task="detect",
            classes=None,
            data={
                "names": {0: "smoke", 1: "fire", 2: "person"},
                "nc": 3,
                "path": str(tmp_path),
                "class_scope_manifest": str(manifest),
            },
            fraction=1.0,
        )


def test_dataset_rejects_multi_image_augmentation(tmp_path: Path) -> None:
    image_dir, manifest = _write_scoped_dataset(tmp_path)

    with pytest.raises(ValueError, match="require mosaic"):
        ClassScopedYOLODataset(
            img_path=str(image_dir),
            imgsz=64,
            batch_size=2,
            augment=True,
            hyp=get_cfg(overrides={"imgsz": 64, "mosaic": 1.0}),
            rect=False,
            cache=False,
            single_cls=False,
            stride=32,
            pad=0.0,
            prefix="test: ",
            task="detect",
            classes=None,
            data={
                "names": {0: "smoke", 1: "fire", 2: "person"},
                "nc": 3,
                "path": str(tmp_path),
                "class_scope_manifest": str(manifest),
            },
            fraction=1.0,
        )


def test_validation_predictions_are_filtered_by_image_scope() -> None:
    predictions = [
        {
            "boxes": torch.zeros((3, 4)),
            "conf": torch.tensor([0.9, 0.8, 0.7]),
            "cls": torch.tensor([0.0, 1.0, 2.0]),
        },
        {
            "boxes": torch.zeros((2, 4)),
            "conf": torch.tensor([0.6, 0.5]),
            "cls": torch.tensor([1.0, 2.0]),
        },
    ]

    filtered = filter_predictions_to_known_classes(
        predictions,
        torch.tensor([[True, True, False], [False, False, True]]),
    )

    assert filtered[0]["cls"].tolist() == [0.0, 1.0]
    assert filtered[1]["cls"].tolist() == [2.0]


def test_scope_manifest_rejects_unknown_class(tmp_path: Path) -> None:
    manifest = tmp_path / "scope.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classes": ["smoke", "fire", "person"],
                "images": {"image.jpg": ["smoke", "cat"]},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid annotation scope"):
        load_class_scopes(manifest)


def test_class_scoped_trainer_runs_one_synthetic_epoch(tmp_path: Path) -> None:
    from ultralytics import YOLO

    scopes: dict[str, list[str]] = {}
    for split in ("train", "val"):
        image_dir = tmp_path / "images" / split
        label_dir = tmp_path / "labels" / split
        image_dir.mkdir(parents=True)
        label_dir.mkdir(parents=True)
        for index, (scope, class_id) in enumerate(
            ((["smoke", "fire"], 1), (["person"], 2))
        ):
            image = image_dir / f"{split}-{index}.jpg"
            Image.new("RGB", (64, 64), "gray").save(image)
            (label_dir / f"{split}-{index}.txt").write_text(
                f"{class_id} 0.5 0.5 0.25 0.25\n", encoding="utf-8"
            )
            scopes[image.resolve().as_posix()] = scope
    (tmp_path / "class_scope_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classes": ["smoke", "fire", "person"],
                "images": scopes,
            }
        ),
        encoding="utf-8",
    )
    data_yaml = tmp_path / "dataset.yaml"
    data_yaml.write_text(
        f"path: {tmp_path.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "class_scope_manifest: class_scope_manifest.json\n"
        "names:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )

    result = YOLO("yolo26n.yaml").train(
        trainer=ClassScopedDetectionTrainer,
        data=str(data_yaml),
        epochs=1,
        batch=2,
        imgsz=64,
        device="cpu",
        workers=0,
        amp=False,
        mosaic=1.0,
        project=str(tmp_path / "runs"),
        name="synthetic-scope-smoke",
        exist_ok=True,
        save=False,
        plots=False,
        verbose=False,
    )

    assert result is not None
