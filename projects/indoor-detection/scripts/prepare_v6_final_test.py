"""Freeze v6 test inputs, smoke comparability and execution protocol on E:."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from ultralytics import YOLO

from indoor_detection.dataset import parse_yolo_label
from indoor_detection.error_analysis import (
    _filter_images_for_class_scope,
    _label_path,
    _resolve_dataset_split,
)
from indoor_detection.test_protocol import compare_smoke_membership

ROOT = Path("E:/HomeAssistantPi4/reports/indoor-v6-768-test-preparation-v1")
TEST_ROOT = Path("E:/HomeAssistantPi4/reports/indoor-v6-768-final-test-v1")
DATA = Path("E:/HomeAssistantPi4/processed/indoor-partial-joint-v4/dataset.yaml")
BASE_DATA = Path("E:/HomeAssistantPi4/processed/smoke-combined-v2/dataset.yaml")
BASE_MODEL = Path("E:/HomeAssistantPi4/models/checkpoints/smoke_yolo26n_combined_v2.pt")
CANDIDATE = Path(
    "E:/HomeAssistantPi4/reports/indoor-v6-768-exact-hazard-calibration-v2/"
    "validation-candidate.json"
)
BASE_SHA = "1104f90ee0723e0877a4797c71cd88ebc7b43a5841396d153010f59781ea3d04"


def main() -> None:
    ROOT.mkdir(exist_ok=False)
    hashes: dict[str, str] = {}

    def sha(path: Path) -> str:
        key = path.resolve().as_posix()
        if key not in hashes:
            hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes[key]

    def signature(path: Path) -> tuple[str, tuple[tuple[float, ...], ...]]:
        label = _label_path(path)
        sha(label)
        rows = parse_yolo_label(label.read_text(encoding="utf-8-sig"), {0, 1, 2})
        return sha(path), tuple(
            sorted(tuple(float(v) for v in r[1:]) for r in rows if int(r[0]) == 0)
        )

    for manifest_path in (
        CANDIDATE.parent / "artifact-manifest.json",
        Path("E:/HomeAssistantPi4/reports/indoor-partial-joint-v4-audit/artifact-manifest.json"),
    ):
        manifest = json.loads(manifest_path.read_text())
        for entry in manifest["files"]:
            if sha(Path(entry["path"])) != entry["sha256"]:
                raise ValueError(f"Artifact drift: {entry['path']}")
        sha(manifest_path)
    candidate = json.loads(CANDIDATE.read_text())
    if (
        not candidate["validation_quality_passed"]
        or sha(Path(candidate["model"])) != candidate["model_sha256"]
    ):
        raise ValueError("Candidate checkpoint/validation gate mismatch")
    if sha(BASE_MODEL) != BASE_SHA or YOLO(str(BASE_MODEL)).names != {0: "item"}:
        raise ValueError("Baseline snapshot hash or original class mapping changed")
    if YOLO(candidate["model"]).names != {0: "smoke", 1: "fire", 2: "person"}:
        raise ValueError("Candidate class names changed")
    images = _resolve_dataset_split(DATA, "test")
    smoke, _, _ = _filter_images_for_class_scope(DATA, images, 0)
    current = [signature(p) for p in smoke]
    old_images = _resolve_dataset_split(BASE_DATA, "test")
    old = [signature(p) for p in old_images]
    membership = compare_smoke_membership(current, old)
    current_hashes = {key[0] for key in current}
    overlaps = {}
    for split in ("train", "val"):
        split_images = _resolve_dataset_split(BASE_DATA, split)
        overlaps[split] = [p.as_posix() for p in split_images if sha(p) in current_hashes]
    if any(overlaps.values()):
        raise ValueError("Smoke test overlaps baseline train/validation")
    remaining = Counter(old) - Counter(current)
    excluded = []
    for path, key in zip(old_images, old, strict=True):
        if remaining[key]:
            excluded.append(
                {"path": path.as_posix(), "image_sha256": key[0], "smoke_boxes": len(key[1])}
            )
            remaining[key] -= 1
    counts = {}
    for class_id, name in enumerate(("smoke", "fire", "person")):
        selected, _, scoped = _filter_images_for_class_scope(DATA, images, class_id)
        if not scoped:
            raise ValueError("Test must use annotation scopes")
        targets = 0
        for path in selected:
            sha(path)
            label = _label_path(path)
            sha(label)
            targets += sum(
                int(r[0]) == class_id
                for r in parse_yolo_label(label.read_text(encoding="utf-8-sig"), {0, 1, 2})
            )
        counts[name] = {"images": len(selected), "targets": targets}
    for dataset in (DATA, BASE_DATA):
        for name in ("dataset.yaml", "train.txt", "val.txt", "test.txt"):
            sha(dataset.parent / name)
    sha(DATA.parent / "class_scope_manifest.json")
    for path in (
        CANDIDATE,
        Path(__file__),
        Path("projects/indoor-detection/scripts/run_v6_final_test.py"),
        Path("projects/indoor-detection/src/indoor_detection/test_protocol.py"),
        Path("projects/indoor-detection/src/indoor_detection/error_analysis.py"),
        Path("projects/indoor-detection/src/indoor_detection/partial_label_training.py"),
    ):
        sha(path)
    evidence = {
        "status": "PASS",
        "smoke_membership": membership,
        "baseline_only_images": excluded,
        "baseline_train_val_overlaps": overlaps,
        "test_counts": counts,
        "full_test_images": len(images),
        "baseline_class_projection": (
            "raw0=item -> smoke0; snapshot hash and original single_cls "
            "smoke dataset bind semantics"
        ),
        "prior_test_use": "v2 test results were previously inspected; not an untouched holdout",
    }
    protocol = {
        "owner": "OpenAI Codex",
        "status": "FROZEN_BEFORE_TEST",
        "authorization": "User requested continuing approved project plan on2026-10-06",
        "bindings": hashes,
        "candidate": candidate,
        "data": DATA.as_posix(),
        "baseline_model": BASE_MODEL.as_posix(),
        "baseline_threshold": 0.43043043043043044,
        "matching": {
            "imgsz": 768,
            "rect": False,
            "candidate_confidence": 0.001,
            "batch": 16,
            "max_det": 100,
            "iou": 0.5,
            "warmup": 1,
        },
        "metrics": "Square class-scoped AP atconf.001/maxdet100; no test operating-point selection",
        "decision": (
            "Predeclared test floors smoke/fireR>=.90,personF1>=.65/R>=.60; "
            "smoke delta>=-.03 aggregate and each source"
        ),
        "stop": (
            "One fixed evaluation; no test tuning, retries, training or export. "
            "Failed quality closes candidate for release."
        ),
        "test_root": TEST_ROOT.as_posix(),
        "preparation": evidence,
    }
    for filename, value in (("readiness.json", evidence), ("protocol.json", protocol)):
        (ROOT / filename).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print("ProtocolSHA", sha(ROOT / "protocol.json"), flush=True)


if __name__ == "__main__":
    main()
