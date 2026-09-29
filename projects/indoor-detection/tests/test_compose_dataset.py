from __future__ import annotations

from pathlib import Path

from PIL import Image

from indoor_detection.compose_dataset import compose_dataset


def _write_source(root: Path) -> Path:
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
