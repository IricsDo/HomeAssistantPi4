from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from indoor_detection.person_enrichment import apply_person_decisions
from indoor_detection.person_review import _candidate_id

FIELDS = [
    "review_id",
    "candidate_id",
    "source",
    "candidate_index",
    "split",
    "status",
    "confidence",
    "verifier_confidence",
    "verifier_iou",
    "decision",
    "notes",
    "image",
    "xywhn",
]


def _fixture(tmp_path: Path, decision: str) -> tuple[Path, Path]:
    source = tmp_path / "source"
    image_path = source / "images/train/example.jpg"
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (100, 80), "gray").save(image_path)
    label_path = source / "labels/train/example.txt"
    label_path.parent.mkdir(parents=True)
    label_path.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    for split in ("val", "test"):
        (source / f"images/{split}").mkdir(parents=True)
    dataset_yaml = source / "dataset.yaml"
    dataset_yaml.write_text(
        f"path: {source.as_posix()}\n"
        "train: images/train\nval: images/val\ntest: images/test\n"
        "names: [smoke, fire, person]\n",
        encoding="utf-8",
    )
    decisions = tmp_path / "decisions.tsv"
    with decisions.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": _candidate_id(
                    image_path.resolve().as_posix(),
                    "primary",
                    0,
                    [0.4, 0.4, 0.2, 0.4],
                ),
                "source": "primary",
                "candidate_index": "0",
                "split": "train",
                "decision": decision,
                "image": image_path.resolve().as_posix(),
                "xywhn": json.dumps([0.4, 0.4, 0.2, 0.4]),
            }
        )
    return dataset_yaml, decisions


def test_apply_person_decisions_creates_derivative_without_mutating_source(
    tmp_path: Path,
) -> None:
    dataset_yaml, decisions = _fixture(tmp_path, "accept")

    report = apply_person_decisions(
        source_dataset_yaml=dataset_yaml,
        decisions_path=decisions,
        output_dir=tmp_path / "output",
    )

    output_labels = list((tmp_path / "output/labels/train").glob("*.txt"))
    assert len(output_labels) == 1
    assert output_labels[0].read_text(encoding="utf-8").splitlines() == [
        "0 0.5 0.5 0.2 0.2",
        "2 0.400000 0.400000 0.200000 0.400000",
    ]
    assert report["decisions"]["accepted"] == 1
    assert (dataset_yaml.parent / "labels/train/example.txt").read_text(
        encoding="utf-8"
    ) == "0 0.5 0.5 0.2 0.2\n"


def test_apply_person_decisions_blocks_incomplete_review(tmp_path: Path) -> None:
    dataset_yaml, decisions = _fixture(tmp_path, "")

    with pytest.raises(ValueError, match="incomplete"):
        apply_person_decisions(
            source_dataset_yaml=dataset_yaml,
            decisions_path=decisions,
            output_dir=tmp_path / "output",
        )
