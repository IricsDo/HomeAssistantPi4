from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from indoor_detection.dataset import sha256_file
from indoor_detection.train_data_repair import build_train_derivative, rotate_raw_box_8


def _fixture(root: Path, action: str = "orient_raw") -> tuple[Path, Path, Path]:
    scopes = {}
    for split in ("train", "val", "test"):
        image = root / "images" / split / "sample.jpg"
        image.parent.mkdir(parents=True)
        raster = Image.new("RGB", (80, 120), "red")
        raster.paste("blue", (40, 0, 80, 120))
        exif = raster.getexif()
        exif[274] = 8 if action == "orient_raw" and split == "train" else 1
        raster.save(image, exif=exif)
        label = root / "labels" / split / "sample.txt"
        label.parent.mkdir(parents=True)
        label.write_text("0 0.4 0.5 0.2 0.3\n1 0.2 0.7 0.1 0.04\n")
        (root / f"{split}.txt").write_bytes((image.as_posix() + "\r\n").encode())
        scopes[image.as_posix()] = ["smoke", "fire"]
    scope = root / "class_scope_manifest.json"
    scope.write_text(json.dumps({"schema_version": 1, "classes": ["smoke", "fire", "person"],
                                 "images": scopes}))
    data = root / "dataset.yaml"
    data.write_text(f"path: {root.as_posix()}\ntrain: train.txt\nval: val.txt\ntest: test.txt\n"
                    "class_scope_manifest: class_scope_manifest.json\n"
                    "names: {0: smoke, 1: fire, 2: person}\n")
    image = root / "images" / "train" / "sample.jpg"
    label = root / "labels" / "train" / "sample.txt"
    review = root / "review.json"
    review.write_text(json.dumps({
        "status": "APPROVED_DERIVATIVE_ONLY", "source_yaml_sha256": sha256_file(data),
        "source_scope_sha256": sha256_file(scope), "entries": [{
            "id": "audit-001", "image": image.as_posix(), "label": label.as_posix(),
            "image_sha256": sha256_file(image), "label_sha256": sha256_file(label),
            "review_status": "REVIEWED", "reason": "Native review recorded", "action": action,
            "coordinate_basis": "raw_confirmed", "fire_rows": "1 0.6 0.6 0.2 0.2\n",
        }]}))
    return data, review, root / "derivative"


def test_exif_derivative_transforms_all_classes_and_preserves_benchmarks(tmp_path: Path) -> None:
    data, review, output = _fixture(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = build_train_derivative(data, review, output)
    receipt = result["receipts"][0]
    assert receipt["pixel_parity"]
    assert np.array_equal(cv2.imread(receipt["image"]), cv2.imread(receipt["output_image"]))
    rows = [row.split() for row in receipt["after_rows"].splitlines()]
    assert list(map(float, rows[0][1:])) == pytest.approx([0.5, 0.6, 0.3, 0.2])
    assert list(map(float, rows[1][1:])) == pytest.approx([0.7, 0.8, 0.04, 0.1])
    assert all(path.read_bytes() == content for path, content in before.items())
    for split in ("val", "test"):
        assert (output / f"{split}.txt").read_bytes() == (tmp_path / f"{split}.txt").read_bytes()
    assert not result["training_allowed"]


@pytest.mark.parametrize("action", ["unknown_fire", "replace_fire", "keep"])
def test_review_actions_preserve_smoke(tmp_path: Path, action: str) -> None:
    data, review, output = _fixture(tmp_path, action)
    result = build_train_derivative(data, review, output)
    if action == "keep":
        assert result["changed"] == 0
        assert (output / "train.txt").read_text() == (tmp_path / "train.txt").read_text()
        return
    receipt = result["receipts"][0]
    assert receipt["after_rows"].splitlines()[0] == "0 0.4 0.5 0.2 0.3"
    assert sha256_file(Path(receipt["image"])) == receipt["output_image_sha256"]
    if action == "unknown_fire":
        assert receipt["known_classes"] == ["smoke"]
        assert len(receipt["after_rows"].splitlines()) == 1
    else:
        assert receipt["after_rows"].splitlines()[1] == "1 0.6 0.6 0.2 0.2"


@pytest.mark.parametrize("defect", ["hash", "val", "pending", "basis", "duplicate", "binding"])
def test_rejects_unapproved_or_changed_input_before_writes(tmp_path: Path, defect: str) -> None:
    data, review, output = _fixture(tmp_path)
    document = json.loads(review.read_text())
    entry = document["entries"][0]
    if defect == "hash":
        entry["label_sha256"] = "bad"
    elif defect == "val":
        entry["image"] = entry["image"].replace("/train/", "/val/")
    elif defect == "pending":
        entry["review_status"] = "PENDING"
    elif defect == "basis":
        entry["coordinate_basis"] = "unconfirmed"
    elif defect == "duplicate":
        document["entries"].append(dict(entry))
    else:
        document["source_scope_sha256"] = "bad"
    review.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        build_train_derivative(data, review, output)
    assert not output.exists()


def test_derivative_never_overwrites_output(tmp_path: Path) -> None:
    data, review, output = _fixture(tmp_path)
    output.mkdir()
    with pytest.raises(FileExistsError):
        build_train_derivative(data, review, output)


def test_orientation_8_roundtrip(tmp_path: Path) -> None:
    original = ["2", "0.2", "0.7", "0.08", "0.03"]
    row = original
    for _ in range(4):
        row = rotate_raw_box_8(row)
    assert row[0] == "2"
    assert list(map(float, row[1:])) == pytest.approx(list(map(float, original[1:])))


def test_preserves_unsorted_training_index_order(tmp_path: Path) -> None:
    data, review, output = _fixture(tmp_path, "keep")
    first = tmp_path / "images" / "train" / "sample.jpg"
    second = first.with_name("a-second.jpg")
    second.write_bytes(first.read_bytes())
    (tmp_path / "labels" / "train" / "a-second.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    manifest = tmp_path / "class_scope_manifest.json"
    scopes = json.loads(manifest.read_text())
    scopes["images"][second.as_posix()] = ["smoke", "fire"]
    manifest.write_text(json.dumps(scopes))
    document = json.loads(review.read_text())
    document["source_scope_sha256"] = sha256_file(manifest)
    review.write_text(json.dumps(document))
    (tmp_path / "train.txt").write_text(first.as_posix() + "\n" + second.as_posix() + "\n")
    build_train_derivative(data, review, output)
    assert (output / "train.txt").read_bytes() == (tmp_path / "train.txt").read_bytes()
