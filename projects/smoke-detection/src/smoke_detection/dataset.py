"""Prepare and audit smoke-only YOLO datasets without modifying source archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image

SPLITS = ("train", "val", "test")
IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
ARCHIVES = {split: f"{split}.zip" for split in SPLITS}


class DatasetValidationError(ValueError):
    """Raised when a source archive or YOLO annotation is unsafe or invalid."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member_name(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    member = PurePosixPath(normalized)
    if member.is_absolute() or ".." in member.parts:
        raise DatasetValidationError(f"Unsafe ZIP member: {name}")
    return member


def parse_yolo_label(text: str, allowed_classes: set[int] | None = None) -> list[list[str]]:
    """Parse and validate YOLO rows while retaining the source coordinate strings."""
    rows: list[list[str]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 5:
            raise DatasetValidationError(f"Line {line_number}: expected 5 fields")
        try:
            class_id = int(fields[0])
            coords = [float(value) for value in fields[1:]]
        except ValueError as exc:
            raise DatasetValidationError(f"Line {line_number}: non-numeric value") from exc
        if allowed_classes is not None and class_id not in allowed_classes:
            raise DatasetValidationError(f"Line {line_number}: unexpected class {class_id}")
        if not all(math.isfinite(value) for value in coords):
            raise DatasetValidationError(f"Line {line_number}: non-finite coordinate")
        x_center, y_center, width, height = coords
        if not (0 <= x_center <= 1 and 0 <= y_center <= 1):
            raise DatasetValidationError(f"Line {line_number}: center outside [0, 1]")
        if not (0 < width <= 1 and 0 < height <= 1):
            raise DatasetValidationError(f"Line {line_number}: invalid width or height")
        rows.append(fields)
    return rows


def convert_home_fire_label(text: str) -> tuple[str, Counter[int]]:
    """Convert Home-fire classes (0 fire, 1 smoke) to smoke-only class 0."""
    source_counts: Counter[int] = Counter()
    converted: list[str] = []
    for fields in parse_yolo_label(text, {0, 1}):
        source_class = int(fields[0])
        source_counts[source_class] += 1
        if source_class == 1:
            converted.append(" ".join(["0", *fields[1:]]))
    output = "\n".join(converted)
    if output:
        output += "\n"
    return output, source_counts


def _zip_entries(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    entries: dict[str, zipfile.ZipInfo] = {}
    for info in archive.infolist():
        member = _safe_member_name(info.filename)
        if info.is_dir():
            continue
        key = member.as_posix()
        if key in entries:
            raise DatasetValidationError(f"Duplicate ZIP member: {key}")
        entries[key] = info
    return entries


def _find_entries(
    entries: dict[str, zipfile.ZipInfo], directory: str, suffixes: set[str]
) -> dict[str, tuple[str, zipfile.ZipInfo]]:
    found: dict[str, tuple[str, zipfile.ZipInfo]] = {}
    for name, info in entries.items():
        member = PurePosixPath(name)
        if directory not in member.parts or member.suffix.lower() not in suffixes:
            continue
        stem = member.stem
        if stem in found:
            raise DatasetValidationError(f"Duplicate stem in {directory}: {stem}")
        found[stem] = (member.name, info)
    return found


def _prepare_split(archive_path: Path, output_root: Path, split: str) -> dict[str, int]:
    images_out = output_root / "images" / split
    labels_out = output_root / "labels" / split
    images_out.mkdir(parents=True)
    labels_out.mkdir(parents=True)

    stats = Counter[str]()
    with zipfile.ZipFile(archive_path) as archive:
        entries = _zip_entries(archive)
        images = _find_entries(entries, "images", IMAGE_SUFFIXES)
        labels = _find_entries(entries, "labels", {".txt"})
        if images.keys() != labels.keys():
            missing_labels = sorted(images.keys() - labels.keys())[:10]
            missing_images = sorted(labels.keys() - images.keys())[:10]
            raise DatasetValidationError(
                f"{split}: image/label mismatch; missing labels={missing_labels}, "
                f"missing images={missing_images}"
            )

        for stem in sorted(images):
            image_name, image_info = images[stem]
            _, label_info = labels[stem]
            label_text = archive.read(label_info).decode("utf-8-sig")
            converted, source_counts = convert_home_fire_label(label_text)
            image_bytes = archive.read(image_info)
            (images_out / image_name).write_bytes(image_bytes)
            (labels_out / f"{stem}.txt").write_text(converted, encoding="utf-8")

            stats["images"] += 1
            stats["source_fire_boxes"] += source_counts[0]
            stats["source_smoke_boxes"] += source_counts[1]
            stats["smoke_boxes"] += source_counts[1]
            if source_counts[1]:
                stats["positive_images"] += 1
            else:
                stats["negative_images"] += 1
    return dict(stats)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prepare_home_fire(raw_dir: Path, output_dir: Path, manifest_path: Path) -> dict[str, Any]:
    """Create a smoke-only dataset from the official Home-fire v1.0.0 archives."""
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    archives = {split: raw_dir / filename for split, filename in ARCHIVES.items()}
    missing = [str(path) for path in archives.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source archives: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        split_stats = {
            split: _prepare_split(archive_path, output_dir, split)
            for split, archive_path in archives.items()
        }
        dataset_yaml = (
            f"path: {output_dir.resolve().as_posix()}\n"
            "train: images/train\nval: images/val\ntest: images/test\n\n"
            "names:\n  0: smoke\n"
        )
        (output_dir / "dataset.yaml").write_text(dataset_yaml, encoding="utf-8")
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "Home-fire-dataset smoke-only derivative",
            "source": {
                "repository": "https://github.com/PengBo0/Home-fire-dataset",
                "commit": "889064eaafd87f32ef6b1d7128d4c98cb31fe7a5",
                "release": "v1.0.0",
                "license": "CC-BY-NC-4.0",
                "doi": "10.1109/ACCESS.2025.3566907",
                "class_mapping": {"0": "fire (discarded)", "1": "smoke -> 0"},
            },
            "archives": {
                split: {
                    "filename": archive_path.name,
                    "bytes": archive_path.stat().st_size,
                    "sha256": sha256_file(archive_path),
                }
                for split, archive_path in archives.items()
            },
            "output": {"class_names": ["smoke"], "splits": split_stats},
        }
        _write_json(output_dir / "manifest.json", manifest)
        _write_json(manifest_path, manifest)
        return manifest
    except Exception:
        # Only remove the new, incomplete derivative. Source archives are never touched.
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise


def audit_dataset(dataset_root: Path, report_path: Path) -> dict[str, Any]:
    """Validate image/label pairs and detect exact duplicate images across splits."""
    split_reports: dict[str, Any] = {}
    hashes: dict[str, list[dict[str, str]]] = defaultdict(list)
    errors: list[str] = []

    for split in SPLITS:
        image_dir = dataset_root / "images" / split
        label_dir = dataset_root / "labels" / split
        images = {
            path.stem: path
            for path in image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        }
        labels = {path.stem: path for path in label_dir.glob("*.txt")}
        missing_labels = sorted(images.keys() - labels.keys())
        missing_images = sorted(labels.keys() - images.keys())
        boxes = 0
        empty_labels = 0
        corrupt_images = 0
        invalid_labels = 0

        for stem, image_path in images.items():
            try:
                with Image.open(image_path) as image:
                    image.verify()
            except Exception as exc:  # Pillow exposes format-specific exception types.
                corrupt_images += 1
                errors.append(f"{split}/{image_path.name}: corrupt image: {exc}")
            digest = sha256_file(image_path)
            hashes[digest].append({"split": split, "file": image_path.name})

            label_path = labels.get(stem)
            if label_path is None:
                continue
            try:
                rows = parse_yolo_label(label_path.read_text(encoding="utf-8-sig"), {0})
                boxes += len(rows)
                if not rows:
                    empty_labels += 1
            except (OSError, UnicodeError, DatasetValidationError) as exc:
                invalid_labels += 1
                errors.append(f"{split}/{label_path.name}: invalid label: {exc}")

        split_reports[split] = {
            "images": len(images),
            "labels": len(labels),
            "boxes": boxes,
            "empty_labels": empty_labels,
            "missing_labels": len(missing_labels),
            "missing_images": len(missing_images),
            "corrupt_images": corrupt_images,
            "invalid_labels": invalid_labels,
        }
        if missing_labels:
            errors.append(f"{split}: labels missing for {missing_labels[:20]}")
        if missing_images:
            errors.append(f"{split}: images missing for {missing_images[:20]}")

    duplicate_groups = [members for members in hashes.values() if len(members) > 1]
    cross_split = [
        members for members in duplicate_groups if len({member["split"] for member in members}) > 1
    ]
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_root": dataset_root.resolve().as_posix(),
        "splits": split_reports,
        "duplicates": {
            "exact_duplicate_groups": len(duplicate_groups),
            "exact_duplicate_examples": duplicate_groups[:100],
            "cross_split_groups": len(cross_split),
            "cross_split_examples": cross_split[:100],
        },
        "errors": errors,
        "valid": not errors,
    }
    _write_json(report_path, report)
    return report


def _prepare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Home-fire v1.0.0 as smoke-only YOLO")
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser


def prepare_main(argv: list[str] | None = None) -> int:
    args = _prepare_parser().parse_args(argv)
    manifest = prepare_home_fire(args.raw_dir, args.output_dir, args.manifest)
    print(json.dumps(manifest["output"], indent=2))
    return 0


def _audit_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a smoke-only YOLO dataset")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def audit_main(argv: list[str] | None = None) -> int:
    args = _audit_parser().parse_args(argv)
    report = audit_dataset(args.dataset_root, args.report)
    print(json.dumps({"valid": report["valid"], **report["duplicates"]}, indent=2))
    return 0 if report["valid"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or audit smoke-detection datasets")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="Prepare Home-fire as smoke-only")
    prepare_parser.add_argument("--raw-dir", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--manifest", type=Path, required=True)
    audit_parser = subparsers.add_parser("audit", help="Audit a smoke-only dataset")
    audit_parser.add_argument("--dataset-root", type=Path, required=True)
    audit_parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        manifest = prepare_home_fire(args.raw_dir, args.output_dir, args.manifest)
        print(json.dumps(manifest["output"], indent=2))
        return 0
    report = audit_dataset(args.dataset_root, args.report)
    print(json.dumps({"valid": report["valid"], **report["duplicates"]}, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
