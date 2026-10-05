import io
import json
import zipfile

import pytest
from PIL import Image

from indoor_detection.crowdhuman_pilot import (
    MAX_READ,
    RangeReader,
    acquire,
    audit_exact_overlap,
    audit_near_overlap,
    convert_reviewed_pilot,
    freeze_expansion_plan,
    load_pilot,
    render_review,
)
from indoor_detection.dataset import DatasetValidationError, sha256_file


class Response(io.BytesIO):
    def __init__(self, data, status=206, content_range="bytes 0-0/10"):
        super().__init__(data)
        self.status = status
        self.headers = {"Content-Range": content_range}

    def geturl(self):
        return "https://example.org/archive.zip"


def test_range_seek_and_eof(monkeypatch):
    responses = iter([Response(b"a"), Response(b"hi", content_range="bytes 8-9/10")])
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: next(responses))
    reader = RangeReader("https://example.org/archive.zip")
    assert reader.seek(-2, io.SEEK_END) == 8
    assert reader.read(5) == b"hi"
    assert reader.read() == b""
    assert reader.downloaded == 3
    with pytest.raises(ValueError):
        reader.seek(-1)
    reader.size = MAX_READ + 1
    reader.seek(0)
    with pytest.raises(DatasetValidationError, match="bound"):
        reader.read()


@pytest.mark.parametrize("response", [
    Response(b"a", status=200),
    Response(b"a", content_range="bytes 1-1/10"),
    Response(b""), Response(b"ab"),
])
def test_reject_bad_range(monkeypatch, response):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: response)
    with pytest.raises(DatasetValidationError):
        RangeReader("https://example.org/archive.zip")


def test_changed_size(monkeypatch):
    responses = iter([Response(b"a"), Response(b"b", content_range="bytes 1-1/11")])
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: next(responses))
    reader = RangeReader("https://example.org/archive.zip")
    reader.seek(1)
    with pytest.raises(DatasetValidationError, match="size changed"):
        reader.read(1)


def test_plan_hash_and_ignore(tmp_path):
    annotations = tmp_path / "annotation.odgt"
    annotations.write_text(json.dumps({"ID": "abc", "gtboxes": [{"tag": "mask"}]}))
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"image_ids": ["abc"], "sample_size": 1,
                                "annotation_sha256": "wrong"}))
    with pytest.raises(DatasetValidationError, match="frozen pilot"):
        load_pilot(plan, annotations)
    data = json.loads(plan.read_text())
    data["annotation_sha256"] = sha256_file(annotations)
    plan.write_text(json.dumps(data))
    with pytest.raises(DatasetValidationError, match="body-ignore"):
        load_pilot(plan, annotations)
    data["image_ids"] = ["../abc"]
    plan.write_text(json.dumps(data))
    with pytest.raises(DatasetValidationError, match="IDs"):
        load_pilot(plan, annotations)


def test_acquisition_and_review(tmp_path, monkeypatch):
    image = io.BytesIO()
    Image.new("RGB", (20, 30), "white").save(image, format="JPEG")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as stream:
        stream.writestr("Images/abc.jpg", image.getvalue())
        stream.writestr("../not-selected.jpg", image.getvalue())
    empty = io.BytesIO()
    with zipfile.ZipFile(empty, "w"):
        pass

    class LocalReader(io.BytesIO):
        def __init__(self, url):
            content = archive.getvalue() if "train01" in url else empty.getvalue()
            super().__init__(content)
            self.size = len(content)
            self.downloaded = 0

    monkeypatch.setattr("indoor_detection.crowdhuman_pilot.RangeReader", LocalReader)
    annotations = tmp_path / "train.odgt"
    annotations.write_text(json.dumps({"ID": "abc", "gtboxes": [
        {"tag": "person", "vbox": [-2, -1, 12, 21], "fbox": [-2, 0, 15, 40]}]}))
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"image_ids": ["abc"], "sample_size": 1,
                                "annotation_sha256": sha256_file(annotations)}))
    output = tmp_path / "acquired"
    result = acquire(plan, annotations, output)
    assert result["training_allowed"] is False
    assert len(result["records"]) == 1
    assert not (tmp_path / "not-selected.jpg").exists()
    with pytest.raises(FileExistsError):
        acquire(plan, annotations, output)
    review = render_review(output, tmp_path / "review")
    assert review["training_allowed"] is False
    assert review["records"][0]["geometry"]["fbox"]["outside_image"] == 1
    assert review["records"][0]["geometry"]["fbox"]["empty_after_clipping"] == 0
    registry = tmp_path / "hashes.json"
    registry.write_text(json.dumps({"records": [{"sha256": result["records"][0]["sha256"],
                                                "split": "val", "path": "existing.jpg"}]}))
    overlap = audit_exact_overlap(output, registry, tmp_path / "overlap.json")
    assert not overlap["exact_duplicate_gate_passed"]
    assert overlap["corpus_overlap"][0]["corpus_matches"][0]["split"] == "val"
    with pytest.raises(FileExistsError):
        audit_exact_overlap(output, registry, tmp_path / "overlap.json")
    registry.write_text(json.dumps({"records": [{"sha256": result["records"][0]["sha256"],
                                                "split": "val",
                                                "path": str(output / "images/abc.jpg")}]}))
    near = audit_near_overlap(output, registry, tmp_path / "near.json")
    assert len(near["corpus_candidates"]) == 1
    assert near["corpus_candidates"][0]["distance"] == 0
    assert near["training_allowed"] is False
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({
        "reviewer": "OpenAI Codex", "box_convention": "vbox",
        "acquisition_sha256": sha256_file(output / "acquisition.json"),
        "annotations_sha256": sha256_file(output / "pilot-annotations.json"),
        "records": [{"image_id": "abc", "decision": "ACCEPT"}],
    }))
    converted = convert_reviewed_pilot(output, review_file, tmp_path / "converted")
    assert converted["images"] == 1 and converted["boxes"] == 1
    assert converted["training_allowed"] is False
    assert (tmp_path / "converted/labels/train/abc.txt").read_text() == (
        "2 0.25000000 0.33333333 0.50000000 0.66666667\n")
    data = json.loads(review_file.read_text())
    data["acquisition_sha256"] = "changed"
    review_file.write_text(json.dumps(data))
    with pytest.raises(DatasetValidationError, match="does not match"):
        convert_reviewed_pilot(output, review_file, tmp_path / "converted-mismatch")
    (output / "images/abc.jpg").write_bytes(b"changed")
    with pytest.raises(DatasetValidationError, match="hash changed"):
        render_review(output, tmp_path / "review-changed")


def test_near_invalid_distance(tmp_path):
    with pytest.raises(ValueError, match="Hamming"):
        audit_near_overlap(tmp_path, tmp_path / "registry.json", tmp_path / "out.json",
                           max_distance=65)


def test_expansion_filter_and_seed(tmp_path):
    annotations = tmp_path / "train.odgt"
    rows = [
        {"ID": "pilot", "gtboxes": [{"hbox": [0, 0, 10, 10]}]},
        {"ID": "good", "gtboxes": [{"hbox": [0, 0, 10, 10]}, {"hbox": [20, 0, 10, 10]}]},
        {"ID": "overlap", "gtboxes": [{"hbox": [0, 0, 10, 10]}, {"hbox": [2, 0, 10, 10]}]},
        {"ID": "invalid", "gtboxes": [{"hbox": [0, 0, 0, 10]}]},
    ]
    annotations.write_text("\n".join(json.dumps(row) for row in rows))
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps({"annotation_sha256": sha256_file(annotations),
                                 "records": [{"image_id": row["ID"],
                                              "provisionally_eligible": True} for row in rows]}))
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"records": [{"image_id": "pilot"}]}))
    plan = freeze_expansion_plan(annotations, audit, review, tmp_path / "plan.json", sample_size=1)
    assert plan["image_ids"] == ["good"] and plan["population_size"] == 1
    assert plan["head_overlap_excluded"] == 1 and plan["invalid_head_excluded"] == 1
    assert plan["training_allowed"] is False
    with pytest.raises(DatasetValidationError, match="sample size"):
        freeze_expansion_plan(annotations, audit, review, tmp_path / "too-large.json",
                              sample_size=2)
