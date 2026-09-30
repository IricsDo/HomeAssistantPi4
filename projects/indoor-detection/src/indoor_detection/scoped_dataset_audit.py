"""Audit a multi-source YOLO index with per-image annotation scopes."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import DatasetValidationError, parse_yolo_label, sha256_file
from indoor_detection.joint_dataset import TARGET_NAMES, _label_for_image
from indoor_detection.partial_label_training import load_class_scopes, resolve_scope_manifest


def _audit_image(image_path: Path, split: str, known_classes: tuple[bool, ...]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        with Image.open(image_path) as image:
            image.verify()
    except Exception as exc:  # Pillow exposes format-specific exception types.
        errors.append(f"corrupt image: {exc}")

    image_sha256: str | None = None
    try:
        image_sha256 = sha256_file(image_path)
    except OSError as exc:
        errors.append(f"image hash failed: {exc}")

    label_path = _label_for_image(image_path)
    rows: list[list[str]] = []
    if not label_path.is_file():
        errors.append(f"missing label: {label_path}")
    else:
        try:
            rows = parse_yolo_label(label_path.read_text(encoding="utf-8-sig"), {0, 1, 2})
        except (OSError, UnicodeError, DatasetValidationError) as exc:
            errors.append(f"invalid label: {exc}")

    class_counts = Counter(int(row[0]) for row in rows)
    out_of_scope = [class_id for class_id in class_counts if not known_classes[class_id]]
    if out_of_scope:
        errors.append(f"label classes outside annotation scope: {sorted(out_of_scope)}")
    normalized_rows = sorted(" ".join(row) for row in rows)
    return {
        "split": split,
        "image": image_path.resolve().as_posix(),
        "label": label_path.resolve().as_posix(),
        "image_sha256": image_sha256,
        "label_signature": "\n".join(normalized_rows),
        "known_classes": known_classes,
        "class_counts": dict(class_counts),
        "empty_label": not rows,
        "errors": errors,
    }


def audit_scoped_dataset(
    dataset_yaml: Path, report_path: Path, workers: int = 8
) -> dict[str, Any]:
    """Audit structure, scopes, class distribution, and exact duplicates."""
    dataset_yaml = dataset_yaml.resolve()
    if not dataset_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_yaml}")
    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    config["yaml_file"] = str(dataset_yaml)
    scope_manifest = resolve_scope_manifest(config)
    class_scopes = load_class_scopes(scope_manifest)

    split_images = {split: _resolve_split(dataset_yaml, split) for split in SPLITS}
    path_splits: defaultdict[Path, list[str]] = defaultdict(list)
    jobs: list[tuple[Path, str, tuple[bool, ...]]] = []
    errors: list[str] = []
    for split, images in split_images.items():
        for image_path in images:
            resolved = image_path.resolve()
            path_splits[resolved].append(split)
            scope = class_scopes.get(os.path.normcase(str(resolved)))
            if scope is None:
                errors.append(f"{split}: class scope missing for {resolved}")
                continue
            jobs.append((resolved, split, tuple(bool(value) for value in scope.tolist())))

    path_overlap = {
        path.as_posix(): splits for path, splits in path_splits.items() if len(set(splits)) > 1
    }
    if path_overlap:
        errors.append(f"{len(path_overlap)} image paths occur in multiple splits")

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        records = list(executor.map(lambda job: _audit_image(*job), jobs))

    split_reports: dict[str, Any] = {}
    for split in SPLITS:
        selected = [record for record in records if record["split"] == split]
        boxes = Counter()
        scope_counts = Counter()
        positive_images = Counter()
        for record in selected:
            boxes.update(record["class_counts"])
            scope = tuple(
                TARGET_NAMES[index]
                for index, is_known in enumerate(record["known_classes"])
                if is_known
            )
            scope_counts[",".join(scope)] += 1
            for class_id, count in record["class_counts"].items():
                if count:
                    positive_images[TARGET_NAMES[int(class_id)]] += 1
        split_reports[split] = {
            "images": len(selected),
            "labels": sum(Path(record["label"]).is_file() for record in selected),
            "boxes": {
                TARGET_NAMES[class_id]: boxes[class_id] for class_id in range(len(TARGET_NAMES))
            },
            "positive_images": dict(positive_images),
            "empty_labels": sum(record["empty_label"] for record in selected),
            "scope_counts": dict(scope_counts),
            "errors": sum(bool(record["errors"]) for record in selected),
        }

    hashes: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["errors"]:
            errors.extend(
                f"{record['split']}:{record['image']}: {error}"
                for error in record["errors"]
            )
        if record["image_sha256"]:
            hashes[record["image_sha256"]].append(record)
    duplicate_records = [members for members in hashes.values() if len(members) > 1]
    duplicate_groups = []
    for members in duplicate_records:
        duplicate_groups.append(
            {
                "sha256": members[0]["image_sha256"],
                "cross_split": len({member["split"] for member in members}) > 1,
                "annotation_conflict": len({member["label_signature"] for member in members}) > 1,
                "scope_conflict": len({member["known_classes"] for member in members}) > 1,
                "members": [
                    {
                        "split": member["split"],
                        "image": member["image"],
                        "label": member["label"],
                    }
                    for member in members
                ],
            }
        )

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_yaml": dataset_yaml.as_posix(),
        "class_scope_manifest": {
            "path": scope_manifest.as_posix(),
            "sha256": sha256_file(scope_manifest),
            "entries": len(class_scopes),
        },
        "splits": split_reports,
        "structure": {
            "indexed_images": sum(len(images) for images in split_images.values()),
            "audited_images": len(records),
            "path_overlap_count": len(path_overlap),
            "path_overlap_examples": dict(list(path_overlap.items())[:100]),
            "valid": not errors,
            "errors": errors[:500],
            "error_count": len(errors),
        },
        "duplicates": {
            "exact_groups": len(duplicate_groups),
            "cross_split_groups": sum(group["cross_split"] for group in duplicate_groups),
            "annotation_conflict_groups": sum(
                group["annotation_conflict"] for group in duplicate_groups
            ),
            "scope_conflict_groups": sum(group["scope_conflict"] for group in duplicate_groups),
            "examples": duplicate_groups[:100],
            "gate_passed": not duplicate_groups,
        },
        "automated_gates_passed": not errors and not duplicate_groups,
        "visual_annotation_gate": "PENDING",
        "training_allowed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a class-scoped YOLO dataset index")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_scoped_dataset(args.data, args.report, workers=args.workers)
    print(
        json.dumps(
            {
                "structure": report["structure"],
                "duplicates": {
                    key: value
                    for key, value in report["duplicates"].items()
                    if key != "examples"
                },
                "automated_gates_passed": report["automated_gates_passed"],
                "visual_annotation_gate": report["visual_annotation_gate"],
                "training_allowed": report["training_allowed"],
            },
            indent=2,
        )
    )
    return 0 if report["structure"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
