from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from indoor_detection.dataset import DatasetValidationError
from indoor_detection.joint_dataset import class_mapping, prepare_joint_dataset
from scripts.audit_joint_dataset import audit_joint_dataset


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
        source_sha256="abc123",
    )

    assert manifest["source"]["class_mapping"] == {"0": 1, "1": 2, "2": 0}
    assert manifest["output"]["annotation_scope"] == ["smoke", "fire", "person"]
    assert manifest["output"]["manual_box_annotation_required"] is False
    assert manifest["source"]["archive_sha256"] == "abc123"
    assert manifest["output"]["splits"]["train"] == {
        "images": 1,
        "smoke_boxes": 1,
        "fire_boxes": 1,
        "person_boxes": 1,
        "polygons_converted_to_boxes": 0,
        "positive_images": 1,
    }
    label = next((tmp_path / "output" / "labels" / "train").glob("*.txt"))
    assert [line.split()[0] for line in label.read_text().splitlines()] == ["1", "2", "0"]


def test_prepare_joint_dataset_converts_polygon_to_enclosing_box(tmp_path: Path) -> None:
    dataset_yaml = _write_joint_source(tmp_path / "source")
    train_label = tmp_path / "source" / "train" / "labels" / "train.txt"
    train_label.write_text(train_label.read_text() + "2 0.1 0.2 0.7 0.2 0.7 0.8 0.1 0.8\n")

    manifest = prepare_joint_dataset(
        dataset_yaml=dataset_yaml,
        output_dir=tmp_path / "output",
        source_url="https://example.test/dataset",
        source_version="v1",
        source_license="CC BY 4.0",
    )

    assert manifest["output"]["annotation_conversion"]["polygon_rows_converted"] == 1
    label = next((tmp_path / "output" / "labels" / "train").glob("*.txt"))
    rows = label.read_text().splitlines()
    polygon_box = rows[-1].split()
    assert polygon_box[0] == "0"
    assert [float(value) for value in polygon_box[1:]] == pytest.approx([0.4, 0.5, 0.6, 0.6])


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


def test_audit_renders_side_by_side_duplicate_annotation_conflicts(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    report_dir = tmp_path / "report"
    for split in ("train", "val", "test"):
        (dataset_root / "images" / split).mkdir(parents=True)
        (dataset_root / "labels" / split).mkdir(parents=True)
    for name in ("copy-a.jpg", "copy-b.jpg"):
        Image.new("RGB", (32, 32), "red").save(dataset_root / "images" / "train" / name)
    Image.new("RGB", (32, 32), "blue").save(dataset_root / "images" / "val" / "val.jpg")
    Image.new("RGB", (32, 32), "green").save(dataset_root / "images" / "test" / "test.jpg")
    (dataset_root / "labels" / "train" / "copy-a.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    (dataset_root / "labels" / "train" / "copy-b.txt").write_text("1 0.5 0.5 0.3 0.3\n")
    (dataset_root / "labels" / "val" / "val.txt").write_text("")
    (dataset_root / "labels" / "test" / "test.txt").write_text("")
    (dataset_root / "manifest.json").write_text('{"source": {}}')

    report = audit_joint_dataset(dataset_root, report_dir)

    assert report["duplicate_label_conflict_groups"] == 1
    assert (report_dir / "duplicate-conflicts" / "duplicate-001.jpg").is_file()
    csv_text = (report_dir / "duplicate-adjudication.csv").read_text(encoding="utf-8-sig")
    assert "copy-a.jpg" in csv_text and "copy-b.jpg" in csv_text
