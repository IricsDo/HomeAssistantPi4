from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from indoor_detection.dataset import DatasetValidationError
from indoor_detection.joint_dataset import class_mapping, prepare_joint_dataset


def _write_joint_source(root: Path, names: str = "[fire, human, smoke]") -> Path:
    for split, color in (("train", "red"), ("val", "green"), ("test", "blue")):
        image_dir = root / split / "images"
        label_dir = root / split / "labels"
        image_dir.mkdir(parents=True)
        label_dir.mkdir(parents=True)
        Image.new("RGB", (16, 16), color).save(image_dir / f"{split}.jpg")
        (label_dir / f"{split}.txt").write_text(
            "0 0.5 0.5 0.2 0.2\n1 0.5 0.5 0.3 0.3\n2 0.5 0.5 0.4 0.4\n"
        )
    dataset_yaml = root / "data.yaml"
    dataset_yaml.write_text(
        f"path: {root.as_posix()}\ntrain: train/images\nval: val/images\n"
        f"test: test/images\nnames: {names}\n"
    )
    return dataset_yaml


def test_prepare_joint_dataset_remaps_all_classes(tmp_path: Path) -> None:
    dataset_yaml = _write_joint_source(tmp_path / "source")

    manifest = prepare_joint_dataset(
        dataset_yaml=dataset_yaml,
        output_dir=tmp_path / "output",
        source_url="https://example.test/dataset",
        source_version="v1",
        source_license="CC BY 4.0",
    )

    assert manifest["source"]["class_mapping"] == {"0": 1, "1": 2, "2": 0}
    assert manifest["output"]["annotation_scope"] == ["smoke", "fire", "person"]
    assert manifest["output"]["manual_box_annotation_required"] is False
    assert manifest["output"]["splits"]["train"] == {
        "images": 1,
        "smoke_boxes": 1,
        "fire_boxes": 1,
        "person_boxes": 1,
        "positive_images": 1,
    }
    label = next((tmp_path / "output" / "labels" / "train").glob("*.txt"))
    assert [line.split()[0] for line in label.read_text().splitlines()] == ["1", "2", "0"]


def test_joint_dataset_rejects_incomplete_class_scope(tmp_path: Path) -> None:
    dataset_yaml = _write_joint_source(tmp_path / "source", "[fire, smoke]")

    with pytest.raises(DatasetValidationError, match="exactly smoke, fire and person"):
        class_mapping(dataset_yaml)


def test_joint_dataset_requires_label_for_every_image(tmp_path: Path) -> None:
    dataset_yaml = _write_joint_source(tmp_path / "source")
    (tmp_path / "source" / "val" / "labels" / "val.txt").unlink()
    output_dir = tmp_path / "output"

    with pytest.raises(DatasetValidationError, match="Missing label"):
        prepare_joint_dataset(
            dataset_yaml=dataset_yaml,
            output_dir=output_dir,
            source_url="https://example.test/dataset",
            source_version="v1",
            source_license="CC BY 4.0",
        )

    assert not output_dir.exists()
