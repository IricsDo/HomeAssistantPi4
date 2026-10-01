from pathlib import Path

import pytest
import yaml

from indoor_detection.evaluation_slices import build_evaluation_slices


def test_builds_source_specific_val_and_test_indexes(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    scope = dataset / "class_scope_manifest.json"
    scope.write_text('{"schema_version": 1, "images": {}}\n', encoding="utf-8")
    val_paths = [
        tmp_path / "processed" / "fire-source" / "images" / "val" / "a.jpg",
        tmp_path / "processed" / "person-source" / "images" / "val" / "b.jpg",
    ]
    test_paths = [
        tmp_path / "processed" / "fire-source" / "images" / "test" / "c.jpg",
        tmp_path / "processed" / "person-source" / "images" / "test" / "d.jpg",
    ]
    (dataset / "val.txt").write_text(
        "".join(f"{path.as_posix()}\n" for path in val_paths), encoding="utf-8"
    )
    (dataset / "test.txt").write_text(
        "".join(f"{path.as_posix()}\n" for path in test_paths), encoding="utf-8"
    )
    dataset_yaml = dataset / "dataset.yaml"
    dataset_yaml.write_text(
        "path: .\nval: val.txt\ntest: test.txt\n"
        "class_scope_manifest: class_scope_manifest.json\n"
        "names: [smoke, fire, person]\n",
        encoding="utf-8",
    )

    output = tmp_path / "slices"
    summary = build_evaluation_slices(dataset_yaml, output)

    assert summary["sources"] == {
        "fire-source": {"val": 1, "test": 1},
        "person-source": {"val": 1, "test": 1},
    }
    fire_config = yaml.safe_load((output / "fire-source" / "dataset.yaml").read_text())
    assert fire_config["train"] == "val.txt"
    assert fire_config["class_scope_manifest"] == scope.resolve().as_posix()
    assert (output / "fire-source" / "val.txt").read_text().strip().endswith("a.jpg")


def test_refuses_nonempty_output(tmp_path: Path) -> None:
    output = tmp_path / "slices"
    output.mkdir()
    (output / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="must be empty"):
        build_evaluation_slices(tmp_path / "missing.yaml", output)


def test_overwrites_existing_source_directory(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "class_scope_manifest.json").write_text(
        '{"schema_version": 1, "images": {}}\n', encoding="utf-8"
    )
    image = tmp_path / "processed" / "fire-source" / "images" / "val" / "a.jpg"
    for split in ("val", "test"):
        (dataset / f"{split}.txt").write_text(f"{image.as_posix()}\n", encoding="utf-8")
    dataset_yaml = dataset / "dataset.yaml"
    dataset_yaml.write_text(
        "path: .\nval: val.txt\ntest: test.txt\n"
        "class_scope_manifest: class_scope_manifest.json\n"
        "names: [smoke, fire, person]\n",
        encoding="utf-8",
    )
    output = tmp_path / "slices"
    (output / "fire-source").mkdir(parents=True)

    summary = build_evaluation_slices(dataset_yaml, output, overwrite=True)

    assert summary["sources"]["fire-source"] == {"val": 1, "test": 1}
    assert (output / "fire-source" / "dataset.yaml").is_file()
