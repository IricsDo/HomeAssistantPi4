"""Freeze reviewed training candidates without changing labels or approving training."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import yaml

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import sha256_file
from indoor_detection.partial_label_training import load_class_scopes, resolve_scope_manifest
from indoor_detection.scoped_dataset_audit import _audit_image

POSITIVE_DECISIONS = {"ACCEPT_POSITIVE", "EXCLUDE_TINY_OR_AMBIGUOUS"}
NEGATIVE_DECISIONS = {"ACCEPT_NEGATIVE", "EXCLUDE_AMBIGUOUS"}
ACCEPTED = {"ACCEPT_POSITIVE", "ACCEPT_NEGATIVE"}


def freeze_training_review(dataset: Path, queue: Path, review: Path) -> dict[str, Any]:
    """Fail closed on incomplete review, changed images, invalid labels or holdout leakage.

    Holdout pixels are hashed only for exact-duplicate detection; no predictions,
    annotations or quality metrics are read from held-out images.
    """
    queued = json.loads(queue.read_text(encoding="utf-8"))
    reviewed = json.loads(review.read_text(encoding="utf-8"))
    if queued.get("split") != "train" or reviewed.get("split") != "train":
        raise ValueError("Review must use training images only")
    if reviewed.get("queue_sha256", "").lower() != sha256_file(queue).lower():
        raise ValueError("Review queue hash mismatch")
    if reviewed.get("source_labels_unchanged") is not True:
        raise ValueError("Review must preserve source labels")
    candidates: dict[Path, set[str]] = {}
    for key, decisions in (
        ("small_person_candidates", POSITIVE_DECISIONS),
        ("negative_candidates", NEGATIVE_DECISIONS),
    ):
        for row in queued[key]:
            path = Path(row["image_path"]).resolve()
            if path in candidates:
                raise ValueError("Duplicate queue image")
            candidates[path] = decisions
    records = reviewed["records"]
    paths = [Path(row["image_path"]).resolve() for row in records]
    if len(paths) != len(set(paths)) or set(paths) != set(candidates):
        raise ValueError("Review must cover every queue image exactly once")

    splits = {split: _resolve_split(dataset, split) for split in SPLITS}
    train = set(splits["train"])
    holdout = set(splits["val"]) | set(splits["test"])
    if not set(paths) <= train or set(paths) & holdout:
        raise ValueError("Review contains non-training or holdout paths")
    config = yaml.safe_load(dataset.read_text(encoding="utf-8"))
    config["yaml_file"] = str(dataset.resolve())
    scopes = load_class_scopes(resolve_scope_manifest(config))
    # Read bytes for leakage protection only, including aliases with different paths.
    with ThreadPoolExecutor(max_workers=8) as executor:
        holdout_hashes = set(executor.map(sha256_file, sorted(holdout)))
    holdout_hashes = {value.lower() for value in holdout_hashes}
    accepted: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for path, row in zip(paths, records, strict=True):
        decision = row.get("decision")
        if decision not in candidates[path]:
            raise ValueError(f"Invalid review decision: {path}")
        if not row.get("observation") or not row.get("reviewer"):
            raise ValueError(f"Missing review evidence: {path}")
        if row.get("eligible_for_replay") is not (decision in ACCEPTED):
            raise ValueError(f"Replay eligibility conflicts with decision: {path}")
        scope = scopes.get(os.path.normcase(str(path)))
        if scope is None or tuple(scope.tolist()) != (False, False, True):
            raise ValueError(f"Expected person-only annotation scope: {path}")
        audit = _audit_image(path, "train", (False, False, True))
        if audit["errors"]:
            raise ValueError(f"Source annotation/image audit failed: {path}: {audit['errors']}")
        image_hash = audit["image_sha256"].lower()
        if image_hash != row.get("image_sha256", "").lower():
            raise ValueError(f"Reviewed image hash mismatch: {path}")
        if image_hash in holdout_hashes or image_hash in seen_hashes:
            raise ValueError(f"Exact duplicate in review or holdout: {path}")
        seen_hashes.add(image_hash)
        positive = candidates[path] == POSITIVE_DECISIONS
        if positive == audit["empty_label"]:
            raise ValueError(f"Queue category conflicts with source labels: {path}")
        if decision in ACCEPTED:
            accepted.append({
                "image_path": path.as_posix(),
                "image_sha256": image_hash,
                "label_path": audit["label"],
                "label_sha256": sha256_file(Path(audit["label"])),
                "known_classes": ["person"],
                "decision": decision,
                "boxes": audit["class_counts"].get(2, 0),
            })
    return {
        "schema_version": 1,
        "dataset_yaml": dataset.resolve().as_posix(),
        "dataset_sha256": sha256_file(dataset),
        "queue_sha256": sha256_file(queue),
        "review_sha256": sha256_file(review),
        "split_membership": {
            split: {
                "images": len(images),
                "paths_sha256": hashlib.sha256(
                    "\n".join(path.as_posix() for path in images).encode()
                ).hexdigest(),
            } for split, images in splits.items()
        },
        "decisions": dict(Counter(row["decision"] for row in records)),
        "automated_review_checks_passed": True,
        "accepted_images": accepted,
        "training_allowed": False,
        "pending_gates": [
            "Box-level review of accepted positive annotations",
            "Bounded sampling plan and implementation with full hazard rehearsal",
            "Derivative data audit and frozen validation/test verification",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite review manifest: {args.output}")
    result = freeze_training_review(args.data, args.queue, args.review)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create preserves an existing audit even if another writer races us.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"decisions": result["decisions"], "training_allowed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
