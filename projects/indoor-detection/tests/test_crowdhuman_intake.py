import json

import pytest
import yaml
from PIL import Image

from indoor_detection.crowdhuman_intake import extend_scoped_dataset, verify_training_readiness
from indoor_detection.dataset import DatasetValidationError, sha256_file


def fixture_corpus(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    scopes = {}
    for split, color in [("train", "red"), ("val", "green"), ("test", "blue")]:
        path = base / f"{split}.jpg"
        Image.new("RGB", (20, 20), color).save(path)
        scopes[path.as_posix()] = ["smoke", "fire"]
        (base / f"{split}.txt").write_bytes(f"{path.as_posix()}\r\n".encode())
    (base / "class_scope_manifest.json").write_text(json.dumps({
        "schema_version": 1, "classes": ["smoke", "fire", "person"], "images": scopes,
    }))
    data = base / "dataset.yaml"
    data.write_text(yaml.safe_dump({"path": base.as_posix(), "train": "train.txt",
                                   "val": "val.txt", "test": "test.txt",
                                   "class_scope_manifest": "class_scope_manifest.json",
                                   "names": {0: "smoke", 1: "fire", 2: "person"}}))
    derivative = tmp_path / "derivative"
    images = derivative / "images/train"
    labels = derivative / "labels/train"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    image = images / "new.jpg"
    Image.new("RGB", (20, 20), "yellow").save(image)
    label = labels / "new.txt"
    label.write_text("2 0.5 0.5 0.5 0.5\n")
    manifest = derivative / "manifest.json"
    manifest.write_text(json.dumps({
        "class_id": 2, "box_convention": "vbox clipped to image", "review_sha256": "bound",
        "records": [{"image_path": str(image), "label_path": str(label), "boxes": 1,
                     "known_classes": ["person"], "image_sha256": sha256_file(image),
                     "source_sha256": sha256_file(image), "label_sha256": sha256_file(label)}],
    }))
    return data, manifest


@pytest.mark.parametrize("convention", ["vbox clipped to image", "COCO bbox clipped to image"])
def test_extends_train_preserving_holdout_bytes_and_base_scopes(tmp_path, convention):
    base, manifest = fixture_corpus(tmp_path)
    payload = json.loads(manifest.read_text())
    payload["box_convention"] = convention
    manifest.write_text(json.dumps(payload))
    out = tmp_path / "joint"
    result = extend_scoped_dataset(base, [manifest], out)
    assert result["splits"] == {"train": 2, "val": 1, "test": 1}
    assert not result["training_allowed"]
    assert result["sources"][0]["box_convention"] == convention
    for split in ("val", "test"):
        assert (out / f"{split}.txt").read_bytes() == (base.parent / f"{split}.txt").read_bytes()
    assert (out / "train.txt").read_bytes().startswith((base.parent / "train.txt").read_bytes())
    scopes = json.loads((out / "class_scope_manifest.json").read_text())["images"]
    assert sorted(scopes.values()) == [["person"], ["smoke", "fire"],
                                      ["smoke", "fire"], ["smoke", "fire"]]
    with pytest.raises(FileExistsError):
        extend_scoped_dataset(base, [manifest], out)


def test_combines_reviewed_coco_and_crowdhuman_with_explicit_conventions(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    base, crowd_manifest = fixture_corpus(first)
    _, coco_manifest = fixture_corpus(second)
    payload = json.loads(coco_manifest.read_text())
    payload["box_convention"] = "COCO bbox clipped to image"
    coco_manifest.write_text(json.dumps(payload))
    output = tmp_path / "joint"
    report = extend_scoped_dataset(base, [crowd_manifest, coco_manifest], output)
    assert report["added_train_images"] == 2
    assert report["splits"] == {"train": 3, "val": 1, "test": 1}
    assert [source["box_convention"] for source in report["sources"]] == [
        "vbox clipped to image", "COCO bbox clipped to image",
    ]
    assert not report["training_allowed"]
    for split in ("val", "test"):
        assert (output / f"{split}.txt").read_bytes() == (
            base.parent / f"{split}.txt"
        ).read_bytes()


@pytest.mark.parametrize("failure", ["hash", "scope", "count", "duplicate", "relative_index",
                                     "head_boxes", "unreviewed"])
def test_rejects_unsafe_derivative_before_creating_output(tmp_path, failure):
    base, manifest = fixture_corpus(tmp_path)
    data = json.loads(manifest.read_text())
    if failure == "hash":
        data["records"][0]["label_sha256"] = "changed"
    elif failure == "scope":
        data["records"][0]["known_classes"] = ["smoke"]
    elif failure == "count":
        data["records"][0]["boxes"] = 2
    elif failure == "relative_index":
        (base.parent / "val.txt").write_text("val.jpg\n")
    elif failure == "head_boxes":
        data["box_convention"] = "hbox"
    elif failure == "unreviewed":
        data.pop("review_sha256")
    manifest.write_text(json.dumps(data))
    manifests = [manifest, manifest] if failure == "duplicate" else [manifest]
    out = tmp_path / "joint"
    with pytest.raises(DatasetValidationError):
        extend_scoped_dataset(base, manifests, out)
    assert not out.exists()


@pytest.mark.parametrize("change", [None, "checkpoint", "gate_file", "existing_run", "mixing"])
def test_readiness_is_read_only_and_rejects_drift(tmp_path, change):
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"mock checkpoint")
    data = tmp_path / "data.yaml"
    data.write_text("names: [smoke, fire, person]\n")
    run = tmp_path / "runs/v5"
    cfg = tmp_path / "train.yaml"
    cfg.write_text(yaml.safe_dump({"data": str(data), "model": str(checkpoint),
                                  "project": str(run.parent), "name": run.name,
                                  "exist_ok": False, "mosaic": 1.0 if change == "mixing" else 0}))
    gate = tmp_path / "gate.json"
    gate.write_text(json.dumps({"training_allowed": True, "automated_gates_passed": True,
                                "dataset_yaml": str(data),
                                "files": {str(data): sha256_file(data)}}))
    ready = tmp_path / "ready.json"
    ready.write_text(json.dumps({"config": str(cfg), "config_sha256": sha256_file(cfg),
                                 "checkpoint": str(checkpoint),
                                 "checkpoint_sha256": sha256_file(checkpoint),
                                 "data_gate": str(gate), "data_gate_sha256": sha256_file(gate),
                                 "target_run": str(run)}))
    if change == "checkpoint":
        checkpoint.write_bytes(b"changed")
    elif change == "gate_file":
        data.write_text("changed")
    elif change == "existing_run":
        run.mkdir(parents=True)
    if change is None:
        result = verify_training_readiness(ready)
        assert result["verification_passed"] and not result["training_started"]
        assert not result["execution_authorized"] and not run.exists()
    else:
        with pytest.raises(DatasetValidationError):
            verify_training_readiness(ready)
