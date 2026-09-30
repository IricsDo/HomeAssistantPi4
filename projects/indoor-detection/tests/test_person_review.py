from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from indoor_detection.person_review import _load_records, create_review_bundle


def test_review_bundle_creates_contact_sheet_and_decision_template(tmp_path: Path) -> None:
    image_path = tmp_path / "source.jpg"
    Image.new("RGB", (200, 100), "gray").save(image_path)
    candidates = tmp_path / "candidates.jsonl"
    record = {
        "image": image_path.as_posix(),
        "split": "train",
        "status": "manual_review",
        "person_candidates": [{"confidence": 0.4, "xywhn": [0.5, 0.5, 0.25, 0.5]}],
    }
    candidates.write_text(json.dumps(record) + "\n", encoding="utf-8")

    report = create_review_bundle(candidates_path=candidates, output_dir=tmp_path / "review")

    assert report["records"] == 1
    assert report["decision_rows"] == 1
    assert report["pages"] == {"manual_review": 1}
    assert (tmp_path / "review/manual_review/page-0001.jpg").is_file()
    with (tmp_path / "review/decisions.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert rows[0]["decision"] == ""
    assert rows[0]["source"] == "primary"
    assert len(rows[0]["candidate_id"]) == 12
    assert rows[0]["image"] == image_path.as_posix()


def test_load_records_rejects_invalid_candidate(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text("[]\n", encoding="utf-8")

    try:
        _load_records(path)
    except ValueError as error:
        assert "line 1" in str(error)
    else:
        raise AssertionError("Expected invalid record to fail")
