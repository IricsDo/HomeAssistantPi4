from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from smoke_detection.dataset import (
    DatasetValidationError,
    _safe_member_name,
    audit_dataset,
    convert_home_fire_label,
    parse_yolo_label,
    prepare_home_fire,
)


def test_convert_home_fire_keeps_only_smoke() -> None:
    converted, counts = convert_home_fire_label(
        "0 0.5 0.5 0.2 0.3\n1 0.4 0.3 0.1 0.2\n"
    )

    assert converted == "0 0.4 0.3 0.1 0.2\n"
    assert counts == {0: 1, 1: 1}


@pytest.mark.parametrize("name", ["../escape.txt", "/absolute.txt", "a/../../escape.txt"])
def test_rejects_unsafe_zip_member(name: str) -> None:
    with pytest.raises(DatasetValidationError):
        _safe_member_name(name)


def test_rejects_invalid_yolo_coordinates() -> None:
    with pytest.raises(DatasetValidationError, match="center outside"):
        parse_yolo_label("0 1.2 0.5 0.2 0.2", {0})


def test_audit_detects_cross_split_duplicate(tmp_path: Path) -> None:
    from PIL import Image

    for split in ("train", "val", "test"):
        (tmp_path / "images" / split).mkdir(parents=True)
        (tmp_path / "labels" / split).mkdir(parents=True)

    for split in ("train", "val"):
        Image.new("RGB", (8, 8), "white").save(tmp_path / "images" / split / "same.jpg")
        (tmp_path / "labels" / split / "same.txt").write_text("", encoding="utf-8")
    Image.new("RGB", (8, 8), "black").save(tmp_path / "images" / "test" / "other.jpg")
    (tmp_path / "labels" / "test" / "other.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n", encoding="utf-8"
    )

    report = audit_dataset(tmp_path, tmp_path / "report.json")

    assert report["valid"] is True
    assert len(report["duplicates"]["exact_duplicate_examples"]) == 1
    assert report["duplicates"]["cross_split_groups"] == 1
    assert report["splits"]["test"]["boxes"] == 1


def test_prepare_home_fire_creates_smoke_only_dataset(tmp_path: Path) -> None:
    from PIL import Image

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    image_buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "gray").save(image_buffer, format="JPEG")
    for split in ("train", "val", "test"):
        with zipfile.ZipFile(raw_dir / f"{split}.zip", "w") as archive:
            archive.writestr(f"images/{split}_a.jpg", image_buffer.getvalue())
            archive.writestr(
                f"labels/{split}_a.txt",
                "0 0.2 0.2 0.1 0.1\n1 0.5 0.5 0.2 0.2\n",
            )

    output_dir = tmp_path / "processed"
    manifest = prepare_home_fire(raw_dir, output_dir, tmp_path / "manifest.json")

    assert (output_dir / "labels" / "train" / "train_a.txt").read_text() == (
        "0 0.5 0.5 0.2 0.2\n"
    )
    assert "0: smoke" in (output_dir / "dataset.yaml").read_text()
    assert manifest["output"]["splits"]["train"]["source_fire_boxes"] == 1
