"""Prepare the CC BY 4.0 Indoor Fire and Smoke dataset for unified YOLO."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from indoor_detection.dataset import (
    IMAGE_SUFFIXES,
    DatasetValidationError,
    _safe_member_name,
    parse_yolo_label,
    sha256_file,
)

SOURCE_SPLITS = {"train": "train", "valid": "val", "test": "test"}
SOURCE_ROOT = PurePosixPath("Indoor FS")


def convert_indoor_fs_label(text: str) -> tuple[str, Counter[int]]:
    """Map Indoor FS classes to 0 smoke, 1 fire, leaving 2 for person."""
    counts: Counter[int] = Counter()
    converted: list[str] = []
    for fields in parse_yolo_label(text, {0, 1}):
        source_class = int(fields[0])
        counts[source_class] += 1
        target_class = 1 if source_class == 0 else 0
        converted.append(" ".join([str(target_class), *fields[1:]]))
    output = "\n".join(converted)
    return (output + "\n" if output else ""), counts


def _safe_entries(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
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


def _split_members(
    entries: dict[str, zipfile.ZipInfo], source_split: str
) -> tuple[dict[str, tuple[str, zipfile.ZipInfo]], dict[str, zipfile.ZipInfo]]:
    image_prefix = SOURCE_ROOT / source_split / "images"
    label_prefix = SOURCE_ROOT / source_split / "labels"
    images: dict[str, tuple[str, zipfile.ZipInfo]] = {}
    labels: dict[str, zipfile.ZipInfo] = {}
    for name, info in entries.items():
        member = PurePosixPath(name)
        if member.parent == image_prefix and member.suffix.lower() in IMAGE_SUFFIXES:
            if member.stem in images:
                raise DatasetValidationError(
                    f"Duplicate image stem in {source_split}: {member.stem}"
                )
            images[member.stem] = (member.name, info)
        elif member.parent == label_prefix and member.suffix.lower() == ".txt":
            if member.stem in labels:
                raise DatasetValidationError(
                    f"Duplicate label stem in {source_split}: {member.stem}"
                )
            labels[member.stem] = info
    if images.keys() != labels.keys():
        missing_labels = sorted(images.keys() - labels.keys())[:10]
        missing_images = sorted(labels.keys() - images.keys())[:10]
        raise DatasetValidationError(
            f"{source_split}: image/label mismatch; missing labels={missing_labels}, "
            f"missing images={missing_images}"
        )
    return images, labels


def _extract_split(
    archive: zipfile.ZipFile,
    entries: dict[str, zipfile.ZipInfo],
    source_split: str,
    target_split: str,
    output_dir: Path,
) -> dict[str, int]:
    images, labels = _split_members(entries, source_split)
    image_output = output_dir / "images" / target_split
    label_output = output_dir / "labels" / target_split
    image_output.mkdir(parents=True)
    label_output.mkdir(parents=True)
    stats: Counter[str] = Counter()
    for stem in sorted(images):
        image_name, image_info = images[stem]
        label_text = archive.read(labels[stem]).decode("utf-8-sig")
        converted, source_counts = convert_indoor_fs_label(label_text)
        (image_output / image_name).write_bytes(archive.read(image_info))
        (label_output / f"{stem}.txt").write_text(converted, encoding="utf-8")
        stats["images"] += 1
        stats["source_fire_boxes"] += source_counts[0]
        stats["source_smoke_boxes"] += source_counts[1]
        stats["smoke_boxes"] += source_counts[1]
        stats["fire_boxes"] += source_counts[0]
        if source_counts[0] or source_counts[1]:
            stats["positive_images"] += 1
        else:
            stats["negative_images"] += 1
    return dict(stats)


def prepare_indoor_fs(
    archive_path: Path, output_dir: Path, manifest_path: Path
) -> dict[str, Any]:
    """Extract an immutable Indoor FS archive into a unified-class derivative."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"Indoor FS archive not found: {archive_path}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = _safe_entries(archive)
            split_stats = {
                target_split: _extract_split(
                    archive, entries, source_split, target_split, output_dir
                )
                for source_split, target_split in SOURCE_SPLITS.items()
            }
        (output_dir / "dataset.yaml").write_text(
            f"path: {output_dir.resolve().as_posix()}\n"
            "train: images/train\nval: images/val\ntest: images/test\n\n"
            "names:\n  0: smoke\n  1: fire\n  2: person\n",
            encoding="utf-8",
        )
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "Indoor Fire and Smoke Dataset unified-class derivative",
            "source": {
                "repository": "https://huggingface.co/datasets/shahriar-5/IFireSmoke",
                "commit": "22b3c06db783d3e75c74234faa511020912eac64",
                "license": "CC-BY-4.0",
                "paper_doi": "10.1371/journal.pone.0322052",
                "class_mapping": {"0": "fire -> 1", "1": "smoke -> 0"},
            },
            "archive": {
                "filename": archive_path.name,
                "bytes": archive_path.stat().st_size,
                "sha256": sha256_file(archive_path),
            },
            "output": {
                "class_names": ["smoke", "fire", "person"],
                "splits": split_stats,
                "annotation_scope": ["smoke", "fire"],
            },
        }
        payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        (output_dir / "manifest.json").write_text(payload, encoding="utf-8")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(payload, encoding="utf-8")
        return manifest
    except Exception:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Indoor FS for unified YOLO")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = prepare_indoor_fs(args.archive, args.output_dir, args.manifest)
    print(json.dumps(manifest["output"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
