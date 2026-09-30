import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from indoor_detection.partial_label_review import create_partial_label_review


def _write_dataset(root: Path) -> Path:
    for split in ("train", "val", "test"):
        for directory in (root / "images" / split, root / "labels" / split):
            directory.mkdir(parents=True)
        for stem, label in (("positive", "0 0.5 0.5 0.2 0.2\n"), ("negative", "")):
            Image.new("RGB", (32, 24), "white").save(root / "images" / split / f"{stem}.jpg")
            (root / "labels" / split / f"{stem}.txt").write_text(label, encoding="utf-8")
    (root / "dataset.yaml").write_text(
        f"path: {root.as_posix()}\ntrain: images/train\nval: images/val\n"
        "test: images/test\nnames:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps({"output": {"annotation_scope": ["smoke", "fire"]}}),
        encoding="utf-8",
    )
    return root / "dataset.yaml"


def test_partial_label_review_samples_each_split_and_scope_stratum(tmp_path: Path) -> None:
    dataset_yaml = _write_dataset(tmp_path / "dataset")
    output_dir = tmp_path / "review"

    report = create_partial_label_review(
        sources=[("fire_smoke", dataset_yaml)],
        output_dir=output_dir,
        sample_per_stratum=1,
    )

    assert report["review_count"] == 6
    assert report["sources"][0]["unknown_target_classes"] == ["person"]
    assert report["sources"][0]["sample_by_split_and_stratum"]["train"] == {
        "both": 0,
        "fire_only": 0,
        "negative": 1,
        "smoke_only": 1,
    }
    with (output_dir / "review.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 6
    assert {row["unknown_target_classes"] for row in rows} == {"person"}
    assert len(list((output_dir / "contact-sheets").glob("*.jpg"))) == 6


def test_partial_label_review_refuses_nonempty_output(tmp_path: Path) -> None:
    dataset_yaml = _write_dataset(tmp_path / "dataset")
    output_dir = tmp_path / "review"
    output_dir.mkdir()
    (output_dir / "existing.txt").write_text("preserve", encoding="utf-8")

    with pytest.raises(FileExistsError):
        create_partial_label_review(
            sources=[("fire_smoke", dataset_yaml)],
            output_dir=output_dir,
        )

    assert (output_dir / "existing.txt").read_text(encoding="utf-8") == "preserve"
