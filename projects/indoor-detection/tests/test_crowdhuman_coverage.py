import json

import pytest

from indoor_detection.crowdhuman_coverage import assess_coverage, freeze_plan
from indoor_detection.crowdhuman_pilot import load_pilot
from indoor_detection.dataset import DatasetValidationError, sha256_file


def box(x=0, size=100, ignore=0):
    return {"tag": "person", "vbox": [x, 0, size, size],
            "fbox": [x, 0, size, size], "hbox": [x, 0, 5, 5],
            "extra": {"ignore": ignore, "occ": 1}}


def fixture_files(tmp_path):
    annotations = tmp_path / "train.odgt"
    rows = [
        {"ID": "old", "gtboxes": [box()]},
        {"ID": "high", "gtboxes": [box(), box(200, 5), box(400, 5), box(600, 5)]},
        {"ID": "some", "gtboxes": [box(), box(200, 5)]},
        {"ID": "none", "gtboxes": [box()]},
        {"ID": "ignored", "gtboxes": [box(ignore=1)]},
        {"ID": "overlap", "gtboxes": [box(), box()]},
    ]
    annotations.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"sample_size": 1, "image_ids": ["old"],
                                    "annotation_sha256": sha256_file(annotations)}))
    return annotations, previous


def test_coverage_filters_and_proxy(tmp_path):
    annotations, previous = fixture_files(tmp_path)
    report = assess_coverage(annotations, [previous])
    assert report["counts"]["remaining_images"] == 3
    assert report["counts"]["head_overlap_excluded"] == 1
    assert report["counts"]["person_boxes"] == 7
    assert report["counts"]["envelope_proxy_small_boxes"] == 4
    assert not report["image_relative_sizes_verified"]
    assert not report["training_allowed"]
    assert {r["image_id"]: r["stratum"] for r in report["records"]} == {
        "high": "high", "some": "some", "none": "none"}


def test_frozen_plan_is_deterministic_and_acquisition_compatible(tmp_path):
    annotations, previous = fixture_files(tmp_path)
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(assess_coverage(annotations, [previous])))
    quotas = {"high": 1, "some": 1, "none": 1}
    plan = freeze_plan(report_path, quotas)
    assert plan == freeze_plan(report_path, quotas)
    assert plan["image_ids"] == ["high", "some", "none"]
    assert plan["visual_spotcheck_ids"] == plan["image_ids"]
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    _, rows = load_pilot(plan_path, annotations)
    assert set(rows) == set(plan["image_ids"])
    with pytest.raises(DatasetValidationError, match="Quota"):
        freeze_plan(report_path, {"high": 2, "some": 0, "none": 0})


@pytest.mark.parametrize("bad_ids", [["old", "old"], ["missing"]])
def test_bad_prior_plan_rejected(tmp_path, bad_ids):
    annotations, previous = fixture_files(tmp_path)
    previous.write_text(json.dumps({"sample_size": len(bad_ids), "image_ids": bad_ids,
                                    "annotation_sha256": sha256_file(annotations)}))
    with pytest.raises(DatasetValidationError):
        assess_coverage(annotations, [previous])


def test_annotation_hash_mismatch_rejected(tmp_path):
    annotations, previous = fixture_files(tmp_path)
    annotations.write_text(annotations.read_text() + "\n")
    with pytest.raises(DatasetValidationError, match="hash mismatch"):
        assess_coverage(annotations, [previous])
