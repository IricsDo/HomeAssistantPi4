from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from indoor_detection.coco_person_dataset import prepare_coco_person


def _write_coco(root: Path, prefix: str, image_ids: list[int]) -> tuple[Path, Path]:
    image_dir = root / f"{prefix}2017"
    image_dir.mkdir(parents=True)
    images = []
    for image_id in image_ids:
        file_name = f"{image_id:012d}.jpg"
        Image.new("RGB", (100, 80), "gray").save(image_dir / file_name)
        images.append({"id": image_id, "file_name": file_name, "width": 100, "height": 80})
    annotations = [
        {
            "id": 1,
            "image_id": image_ids[0],
            "category_id": 1,
            "bbox": [10, 20, 30, 40],
            "iscrowd": 0,
        },
        {
            "id": 2,
            "image_id": image_ids[1],
            "category_id": 1,
            "bbox": [0, 0, 20, 20],
            "iscrowd": 0,
        },
        {
            "id": 3,
            "image_id": image_ids[-1],
            "category_id": 1,
            "bbox": [0, 0, 100, 80],
            "iscrowd": 1,
        },
    ]
    annotation_path = root / f"instances_{prefix}2017.json"
    annotation_path.write_text(
        json.dumps(
            {
                "images": images,
                "annotations": annotations,
                "categories": [{"id": 1, "name": "person"}],
            }
        ),
        encoding="utf-8",
    )
    return annotation_path, image_dir


def test_prepare_coco_person_creates_reproducible_unified_subset(tmp_path: Path) -> None:
    train_annotations, train_images = _write_coco(tmp_path, "train", [1, 2, 3, 4])
    val_annotations, val_images = _write_coco(tmp_path, "val", [10, 11, 12, 13])
    output = tmp_path / "output"

    manifest = prepare_coco_person(
        train_annotations=train_annotations,
        train_images=train_images,
        val_annotations=val_annotations,
        val_images=val_images,
        output_dir=output,
        manifest_path=tmp_path / "manifest.json",
        train_positive_limit=1,
        train_negative_limit=1,
        seed=42,
    )

    assert manifest["output"]["splits"]["train"]["images"] == 2
    assert manifest["output"]["splits"]["train"]["positive_images"] == 1
    assert (
        manifest["output"]["splits"]["val"]["images"]
        + manifest["output"]["splits"]["test"]["images"]
        == 3
    )
    labels = list((output / "labels").rglob("*.txt"))
    assert any(path.read_text(encoding="utf-8").startswith("2 ") for path in labels)
    assert all(
        not line or line.startswith("2 ")
        for path in labels
        for line in path.read_text(encoding="utf-8").splitlines()
    )
    dataset_yaml = (output / "dataset.yaml").read_text(encoding="utf-8")
    assert "0: smoke" in dataset_yaml
    assert "1: fire" in dataset_yaml
    assert "2: person" in dataset_yaml
