from __future__ import annotations

import io
import zipfile
from pathlib import Path

from PIL import Image

from smoke_detection.indoor_fs_dataset import (
    convert_indoor_fs_label,
    prepare_indoor_fs,
)


def test_convert_indoor_fs_keeps_only_smoke() -> None:
    converted, counts = convert_indoor_fs_label(
        "0 0.2 0.2 0.1 0.1\n1 0.5 0.5 0.2 0.2\n"
    )

    assert converted == "0 0.5 0.5 0.2 0.2\n"
    assert counts == {0: 1, 1: 1}


def test_prepare_indoor_fs_preserves_author_splits(tmp_path: Path) -> None:
    image_buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "gray").save(image_buffer, format="JPEG")
    archive_path = tmp_path / "Indoor-FS.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for source_split in ("train", "valid", "test"):
            archive.writestr(
                f"Indoor FS/{source_split}/images/{source_split}_a.jpg",
                image_buffer.getvalue(),
            )
            archive.writestr(
                f"Indoor FS/{source_split}/labels/{source_split}_a.txt",
                "0 0.2 0.2 0.1 0.1\n1 0.5 0.5 0.2 0.2\n",
            )

    output_dir = tmp_path / "processed"
    manifest = prepare_indoor_fs(archive_path, output_dir, tmp_path / "manifest.json")

    assert (output_dir / "labels" / "val" / "valid_a.txt").read_text() == (
        "0 0.5 0.5 0.2 0.2\n"
    )
    assert manifest["source"]["license"] == "CC-BY-4.0"
    assert manifest["output"]["splits"]["test"]["source_fire_boxes"] == 1
