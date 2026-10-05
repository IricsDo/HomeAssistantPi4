"""Extend a frozen scoped corpus with hash-verified train-only CrowdHuman derivatives."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

import yaml

from indoor_detection.compose_dataset import SPLITS, TARGET_NAMES, _resolve_split
from indoor_detection.dataset import DatasetValidationError, parse_yolo_label, sha256_file
from indoor_detection.joint_dataset import _label_for_image
from indoor_detection.partial_label_training import load_class_scopes, resolve_scope_manifest


def extend_scoped_dataset(
    base_yaml: Path, derivative_manifests: list[Path], output: Path
) -> dict[str, Any]:
    """Preserve all base rows/scopes and byte-identical holdout indexes; never approve training."""
    if output.exists():
        raise FileExistsError(output)
    if not derivative_manifests:
        raise ValueError("At least one reviewed derivative is required")
    base_yaml = base_yaml.resolve()
    config = yaml.safe_load(base_yaml.read_text(encoding="utf-8"))
    if config.get("names") != dict(enumerate(TARGET_NAMES)):
        raise DatasetValidationError("Base class names are not canonical")
    config["yaml_file"] = str(base_yaml)
    scope_path = resolve_scope_manifest(config)
    base_scopes = load_class_scopes(scope_path)
    splits = {split: _resolve_split(base_yaml, split) for split in SPLITS}
    indexed = [path for paths in splits.values() for path in paths]
    if len(indexed) != len(set(indexed)):
        raise DatasetValidationError("Base contains duplicate index paths or split overlap")
    scopes = {}
    for path in indexed:
        scope = base_scopes.get(os.path.normcase(str(path.resolve())))
        if scope is None:
            raise DatasetValidationError("Base index has a missing scope")
        scopes[path.as_posix()] = [name for name, known in zip(TARGET_NAMES, scope, strict=True)
                                 if known]
    root = Path(config.get("path", base_yaml.parent))
    if not root.is_absolute():
        root = base_yaml.parent / root
    indexes = {}
    for split in SPLITS:
        raw = config.get(split)
        if not isinstance(raw, str) or Path(raw).suffix != ".txt":
            raise DatasetValidationError("Frozen base must use text split indexes")
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        # Relative image rows would resolve differently under the new dataset root.
        if any(not Path(line.strip()).is_absolute()
               for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()):
            raise DatasetValidationError("Frozen indexes must contain absolute image paths")
        indexes[split] = path.resolve()
    seen = set(indexed)
    added = []
    sources = []
    for manifest_path in derivative_manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (manifest.get("class_id") != 2
                or manifest.get("box_convention") != "vbox clipped to image"
                or not manifest.get("review_sha256")):
            raise DatasetValidationError("Expected reviewed visible-body person derivative")
        records = manifest.get("records", [])
        if not records:
            raise DatasetValidationError("Empty person derivative")
        for row in records:
            image = Path(row["image_path"]).resolve()
            label = Path(row["label_path"]).resolve()
            if image in seen:
                raise DatasetValidationError("Added image repeats base or another derivative path")
            if (row.get("known_classes") != ["person"]
                    or sha256_file(image) != row["image_sha256"]
                    or row["image_sha256"] != row["source_sha256"]
                    or sha256_file(label) != row["label_sha256"]):
                raise DatasetValidationError("Derivative scope or artifact hash changed")
            expected_label = _label_for_image(image)
            if label != expected_label:
                raise DatasetValidationError("Derivative label does not match image layout")
            parsed = parse_yolo_label(label.read_text(encoding="utf-8"), {2})
            if not parsed or len(parsed) != row["boxes"]:
                raise DatasetValidationError("Derivative box count changed")
            seen.add(image)
            added.append(image)
            scopes[image.as_posix()] = ["person"]
        sources.append({"manifest": str(manifest_path.resolve()),
                        "sha256": sha256_file(manifest_path), "images": len(records)})
    output.mkdir(parents=True, exist_ok=False)
    base_train = indexes["train"].read_bytes()
    separator = b"" if not base_train or base_train.endswith(b"\n") else b"\n"
    (output / "train.txt").write_bytes(base_train + separator + "".join(
        f"{path.as_posix()}\n" for path in added).encode("utf-8"))
    for split in ("val", "test"):
        shutil.copyfile(indexes[split], output / f"{split}.txt")
    (output / "dataset.yaml").write_text(yaml.safe_dump({
        "path": output.resolve().as_posix(), "train": "train.txt", "val": "val.txt",
        "test": "test.txt", "class_scope_manifest": "class_scope_manifest.json",
        "names": dict(enumerate(TARGET_NAMES)),
    }, sort_keys=False), encoding="utf-8")
    (output / "class_scope_manifest.json").write_text(json.dumps({
        "schema_version": 1, "classes": list(TARGET_NAMES), "images": scopes,
    }, indent=2) + "\n", encoding="utf-8")
    report = {"training_allowed": False, "status": "AWAITING_JOINT_GATE",
              "base_yaml": str(base_yaml), "base_yaml_sha256": sha256_file(base_yaml),
              "base_scope_sha256": sha256_file(scope_path), "sources": sources,
              "added_train_images": len(added),
              "splits": {s: len(paths) + (len(added) if s == "train" else 0)
                         for s, paths in splits.items()},
              "base_index_sha256": {s: sha256_file(p) for s, p in indexes.items()},
              "output_index_sha256": {s: sha256_file(output / f"{s}.txt") for s in SPLITS}}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def verify_training_readiness(readiness_path: Path) -> dict[str, Any]:
    """Read-only verification of the frozen preparation snapshot; never start training."""
    ready = json.loads(readiness_path.read_text(encoding="utf-8"))
    bindings = [(ready["config"], ready["config_sha256"]),
                (ready["checkpoint"], ready["checkpoint_sha256"]),
                (ready["data_gate"], ready["data_gate_sha256"])]
    for path, digest in bindings:
        if sha256_file(Path(path)) != digest:
            raise DatasetValidationError("Training preparation artifact changed")
    gate = json.loads(Path(ready["data_gate"]).read_text(encoding="utf-8"))
    if not gate.get("training_allowed") or not gate.get("automated_gates_passed"):
        raise DatasetValidationError("Data gate does not approve training")
    if not gate.get("files"):
        raise DatasetValidationError("Data gate has no artifact bindings")
    for path, digest in gate["files"].items():
        if sha256_file(Path(path)) != digest:
            raise DatasetValidationError("Data gate artifact changed")
    config = yaml.safe_load(Path(ready["config"]).read_text(encoding="utf-8"))
    if (Path(config["data"]).resolve() != Path(gate["dataset_yaml"]).resolve()
            or Path(config["model"]).resolve() != Path(ready["checkpoint"]).resolve()
            or Path(config["project"]) / config["name"] != Path(ready["target_run"])
            or config.get("exist_ok") is not False
            or any(config.get(name, 0) != 0
                   for name in ("mosaic", "mixup", "cutmix", "copy_paste"))):
        raise DatasetValidationError("Training configuration violates frozen preparation")
    if Path(ready["target_run"]).exists():
        raise DatasetValidationError("Target run already exists; do not overwrite")
    return {"verification_passed": True, "training_started": False,
            "execution_authorized": False, "target_run": ready["target_run"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify preparation only; no training execution")
    parser.add_argument("--readiness", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(verify_training_readiness(args.readiness), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
