from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from indoor_detection.compose_dataset import compose_dataset


def _write_source(root: Path, annotation_scope: list[str] | None = None) -> Path:
    colors = {"train": "red", "val": "green", "test": "blue"}
    for split in ("train", "val", "test"):
        (root / "images" / split).mkdir(parents=True)
        (root / "labels" / split).mkdir(parents=True)
        name = f"unique-{split}.rf.{split}.jpg"
        Image.new("RGB", (16, 16), colors[split]).save(root / "images" / split / name)
        (root / "labels" / split / Path(name).with_suffix(".txt")).write_text("")
    duplicate_train = root / "images" / "train" / "shared.rf.train.jpg"
    duplicate_test = root / "images" / "test" / "shared.rf.test.jpg"
    Image.new("RGB", (16, 16), "gray").save(duplicate_train)
    Image.new("RGB", (16, 16), "gray").save(duplicate_test)
    (root / "labels" / "train" / "shared.rf.train.txt").write_text("")
    (root / "labels" / "test" / "shared.rf.test.txt").write_text("")
    dataset_yaml = root / "dataset.yaml"
    dataset_yaml.write_text(
        f"path: {root.as_posix()}\ntrain: images/train\nval: images/val\n"
        "test: images/test\nnames:\n  0: smoke\n  1: fire\n  2: person\n"
    )
    if annotation_scope is not None:
        (root / "manifest.json").write_text(
            json.dumps({"output": {"annotation_scope": annotation_scope}}),
            encoding="utf-8",
        )
    return dataset_yaml


def test_compose_dataset_excludes_lower_priority_roboflow_variant(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dataset_yaml = _write_source(source)

    report = compose_dataset(
        sources=[("indoor", dataset_yaml)],
        output_dir=tmp_path / "combined",
        roboflow_deduplicate={"indoor"},
    )

    assert report["output"]["splits"] == {"train": 1, "val": 1, "test": 2}
    evidence = report["sources"][0]["roboflow_cross_split_exclusions"]
    assert len(evidence) == 1
    assert evidence[0]["excluded_split"] == "train"
    assert evidence[0]["kept_split"] == "test"
    output_yaml = (tmp_path / "combined" / "dataset.yaml").read_text()
    assert "2: person" in output_yaml


def test_compose_dataset_emits_per_image_class_scopes(tmp_path: Path) -> None:
    fire_source = tmp_path / "fire-source"
    person_source = tmp_path / "person-source"

    compose_dataset(
        sources=[
            ("fire", _write_source(fire_source, ["smoke", "fire"])),
            ("person", _write_source(person_source, ["person"])),
        ],
        output_dir=tmp_path / "combined",
        roboflow_deduplicate=set(),
        emit_class_scopes=True,
    )

    dataset_yaml = (tmp_path / "combined" / "dataset.yaml").read_text()
    manifest = json.loads((tmp_path / "combined" / "class_scope_manifest.json").read_text())
    fire_image = (fire_source / "images" / "train" / "unique-train.rf.train.jpg").resolve()
    person_image = (person_source / "images" / "train" / "unique-train.rf.train.jpg").resolve()

    assert "class_scope_manifest: class_scope_manifest.json" in dataset_yaml
    assert manifest["classes"] == ["smoke", "fire", "person"]
    assert manifest["images"][fire_image.as_posix()] == ["smoke", "fire"]
    assert manifest["images"][person_image.as_posix()] == ["person"]
