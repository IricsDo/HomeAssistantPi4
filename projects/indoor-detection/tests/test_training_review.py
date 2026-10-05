from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from indoor_detection.dataset import sha256_file
from indoor_detection.training_review import freeze_training_review, main


def _fixture(root: Path) -> tuple[Path, Path, Path]:
    scopes = {}
    images = {}
    for split, names in (("train", ["positive", "negative"]), ("val", ["val"]),
                         ("test", ["test"])):
        (root / "images" / split).mkdir(parents=True)
        (root / "labels" / split).mkdir(parents=True)
        for name in names:
            path = root / "images" / split / f"{name}.png"
            Image.new("RGB", (16, 16), (len(images) * 40, 20, 30)).save(path)
            images[name] = path
            scopes[path.as_posix()] = ["person"]
            (root / "labels" / split / f"{name}.txt").write_text(
                "" if name == "negative" else "2 0.5 0.5 0.25 0.25\n", encoding="utf-8"
            )
    (root / "scopes.json").write_text(json.dumps({
        "schema_version": 1, "classes": ["smoke", "fire", "person"], "images": scopes,
    }), encoding="utf-8")
    data = root / "dataset.yaml"
    data.write_text(
        f"path: {root.as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\n"
        "class_scope_manifest: scopes.json\nnames: [smoke, fire, person]\n", encoding="utf-8"
    )
    queue = root / "queue.json"
    queue.write_text(json.dumps({
        "split": "train", "small_person_candidates": [{"image_path": str(images['positive'])}],
        "negative_candidates": [{"image_path": str(images['negative'])}],
    }), encoding="utf-8")
    review = root / "review.json"
    review.write_text(json.dumps({
        "split": "train", "source_labels_unchanged": True, "queue_sha256": sha256_file(queue),
        "records": [{
            "image_path": str(images[name]), "image_sha256": sha256_file(images[name]),
            "decision": decision, "observation": "original image inspected",
            "reviewer": "OpenAI Codex", "eligible_for_replay": True,
        } for name, decision in (("positive", "ACCEPT_POSITIVE"),
                                 ("negative", "ACCEPT_NEGATIVE"))],
    }), encoding="utf-8")
    return data, queue, review


def test_freeze_keeps_unique_candidates_and_training_closed(tmp_path: Path) -> None:
    result = freeze_training_review(*_fixture(tmp_path))
    assert result["automated_review_checks_passed"]
    assert not result["training_allowed"]
    assert result["decisions"] == {"ACCEPT_POSITIVE": 1, "ACCEPT_NEGATIVE": 1}
    assert [row["boxes"] for row in result["accepted_images"]] == [1, 0]
    assert all(row["label_sha256"] for row in result["accepted_images"])
    assert result["split_membership"]["test"]["images"] == 1


@pytest.mark.parametrize(("field", "value"), [
    ("decision", "REVIEW_REQUIRED"), ("decision", "ACCEPT_NEGATIVE"),
    ("image_sha256", "changed"), ("eligible_for_replay", False), ("observation", ""),
])
def test_invalid_record_fails_closed(tmp_path: Path, field: str, value: object) -> None:
    data, queue, review = _fixture(tmp_path)
    payload = json.loads(review.read_text())
    payload["records"][0][field] = value
    review.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        freeze_training_review(data, queue, review)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "hash", "split"])
def test_invalid_review_fails_closed(tmp_path: Path, mutation: str) -> None:
    data, queue, review = _fixture(tmp_path)
    payload = json.loads(review.read_text())
    if mutation == "missing":
        payload["records"].pop()
    elif mutation == "duplicate":
        payload["records"].append(payload["records"][0])
    elif mutation == "hash":
        payload["queue_sha256"] = "changed"
    else:
        payload["split"] = "val"
    review.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        freeze_training_review(data, queue, review)


def test_holdout_content_alias_fails(tmp_path: Path) -> None:
    args = _fixture(tmp_path)
    (tmp_path / "images/val/val.png").write_bytes(
        (tmp_path / "images/train/positive.png").read_bytes()
    )
    with pytest.raises(ValueError, match="Exact duplicate"):
        freeze_training_review(*args)


def test_changed_annotation_category_fails(tmp_path: Path) -> None:
    args = _fixture(tmp_path)
    (tmp_path / "labels/train/negative.txt").write_text("2 0.5 0.5 0.25 0.25\n")
    with pytest.raises(ValueError, match="category conflicts"):
        freeze_training_review(*args)


def test_cli_preserves_existing_manifest(tmp_path: Path) -> None:
    data, queue, review = _fixture(tmp_path)
    output = tmp_path / "manifest.json"
    output.write_text("preserve me")
    with pytest.raises(FileExistsError):
        main(["--data", str(data), "--queue", str(queue), "--review", str(review),
              "--output", str(output)])
    assert output.read_text() == "preserve me"
