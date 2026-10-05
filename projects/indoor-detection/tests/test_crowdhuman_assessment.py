import json

import pytest

from indoor_detection.crowdhuman_assessment import assess_annotations, main
from indoor_detection.dataset import DatasetValidationError


def annotation(tag="person", **kwargs):
    return {"tag": tag, "vbox": [0, 0, 10, 20], "fbox": [-5, -5, 20, 30], **kwargs}


def write_rows(tmp_path, rows):
    path = tmp_path / "train.odgt"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


def test_whole_image_exclusion_and_separate_head_ignore(tmp_path):
    path = write_rows(tmp_path, [
        {"ID": "clean", "gtboxes": [annotation(head_attr={"ignore": 1})]},
        {"ID": "masked", "gtboxes": [annotation(), annotation("mask")]},
        {"ID": "ignored", "gtboxes": [annotation(extra={"ignore": 1})]},
        {"ID": "invalid", "gtboxes": [annotation(vbox=[0, 0, 0, 1])]},
    ])
    result = assess_annotations(path)
    assert result["counts"]["provisionally_eligible_images"] == 1
    assert result["counts"]["images_with_body_ignore"] == 2
    assert result["counts"]["head_ignored_boxes"] == 1
    assert not result["training_allowed"]
    assert result["records"][0]["provisionally_eligible"]


@pytest.mark.parametrize("rows", [
    [{"ID": "same", "gtboxes": []}, {"ID": "same", "gtboxes": []}],
    [{"ID": "../unsafe", "gtboxes": []}],
    [{"ID": "x", "gtboxes": [annotation("face")]}],
    [{"ID": "x", "gtboxes": [annotation(extra={"ignore": "1"})]}],
    [],
])
def test_reject_invalid_schema(tmp_path, rows):
    with pytest.raises(DatasetValidationError):
        assess_annotations(write_rows(tmp_path, rows))


def test_nonfinite_geometry_is_not_eligible(tmp_path):
    path = write_rows(tmp_path, [{"ID": "x", "gtboxes": [
        annotation(fbox=[0, 0, float("nan"), 20])]}])
    assert not assess_annotations(path)["records"][0]["provisionally_eligible"]


def test_cli_preserves_previous_output(tmp_path):
    path = write_rows(tmp_path, [{"ID": "x", "gtboxes": [annotation()]}])
    output = tmp_path / "report.json"
    args = ["--annotations", str(path), "--output", str(output)]
    assert main(args) == 0
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        main(args)
    assert output.read_bytes() == before
