from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from indoor_detection.scoped_dataset_audit import audit_scoped_dataset


def _write_dataset(root: Path, val_class: int = 1) -> Path:
    scopes: dict[str, list[str]] = {}
    for split, class_id in (("train", 1), ("val", val_class), ("test", 2)):
        image_dir = root / "images" / split
        label_dir = root / "labels" / split
        image_dir.mkdir(parents=True)
        label_dir.mkdir(parents=True)
        image = image_dir / f"{split}.png"
        color = "red" if split in {"train", "val"} else "blue"
        Image.new("RGB", (16, 16), color).save(image)
        (label_dir / f"{split}.txt").write_text(
            f"{class_id} 0.5 0.5 0.25 0.25\n", encoding="utf-8"
        )
        scopes[image.resolve().as_posix()] = ["smoke", "fire", "person"]
    (root / "class_scope_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classes": ["smoke", "fire", "person"],
                "images": scopes,
            }
        ),
        encoding="utf-8",
    )
    dataset_yaml = root / "dataset.yaml"
    dataset_yaml.write_text(
        f"path: {root.as_posix()}\n"
        "train: images/train\nval: images/val\ntest: images/test\n"
        "class_scope_manifest: class_scope_manifest.json\n"
        "names:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )
    return dataset_yaml


def test_audit_reports_cross_split_duplicate(tmp_path: Path) -> None:
    report = audit_scoped_dataset(
        _write_dataset(tmp_path), tmp_path / "report.json", workers=2
    )

    assert report["structure"]["valid"]
    assert report["duplicates"]["exact_groups"] == 1
    assert report["duplicates"]["cross_split_groups"] == 1
    assert report["duplicates"]["annotation_conflict_groups"] == 0
    assert not report["automated_gates_passed"]
    assert not report["training_allowed"]


def test_audit_reports_duplicate_annotation_conflict(tmp_path: Path) -> None:
    report = audit_scoped_dataset(
        _write_dataset(tmp_path, val_class=0), tmp_path / "report.json", workers=1
    )

    assert report["duplicates"]["annotation_conflict_groups"] == 1
