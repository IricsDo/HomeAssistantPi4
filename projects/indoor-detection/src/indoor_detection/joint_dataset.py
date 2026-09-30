"""Prepare a fully annotated smoke/fire/person YOLO dataset.

This intake path is intentionally separate from the legacy smoke/fire sources:
every imported image must have an annotation file whose declared class scope
contains all three deployment classes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import DatasetValidationError, parse_yolo_label

TARGET_NAMES = ("smoke", "fire", "person")
CLASS_ALIASES = {
    "smoke": "smoke",
    "fire": "fire",
    "person": "person",
    "human": "person",
    "people": "person",
}


def _normalize_class_name(value: object) -> str:
    normalized = "".join(character for character in str(value).casefold() if character.isalnum())
    try:
        return CLASS_ALIASES[normalized]
    except KeyError as exc:
        raise DatasetValidationError(f"Unsupported source class name: {value!r}") from exc


def class_mapping(dataset_yaml: Path) -> dict[int, int]:
    """Return source-to-target IDs after validating an exact three-class contract."""
    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise DatasetValidationError("Dataset YAML must be a mapping")
    names = config.get("names")
    if isinstance(names, list):
        indexed_names = dict(enumerate(names))
    elif isinstance(names, dict):
        try:
            indexed_names = {int(key): value for key, value in names.items()}
        except (TypeError, ValueError) as exc:
            raise DatasetValidationError("Dataset class IDs must be integers") from exc
    else:
        raise DatasetValidationError("Dataset YAML must declare names as a list or mapping")

    normalized = {
        source_id: _normalize_class_name(name) for source_id, name in indexed_names.items()
    }
    if len(normalized) != 3 or set(normalized.values()) != set(TARGET_NAMES):
        raise DatasetValidationError(
            "Joint dataset must declare exactly smoke, fire and person/human classes"
        )
    return {source_id: TARGET_NAMES.index(name) for source_id, name in normalized.items()}


def _label_for_image(image_path: Path) -> Path:
    parts = list(image_path.parts)
    positions = [index for index, part in enumerate(parts) if part.casefold() == "images"]
    if not positions:
        raise DatasetValidationError(f"Image path has no 'images' directory: {image_path}")
    parts[positions[-1]] = "labels"
    return Path(*parts).with_suffix(".txt")


def _output_stem(image_path: Path) -> str:
    digest = hashlib.sha256(image_path.resolve().as_posix().encode()).hexdigest()[:12]
    return f"{digest}_{image_path.stem}"


def _link_or_copy(source: Path, destination: Path) -> str:
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def _convert_label(
    label_path: Path, mapping: dict[int, int]
) -> tuple[str, Counter[int], int]:
    counts: Counter[int] = Counter()
    converted: list[str] = []
    polygon_count = 0
    for line_number, raw_line in enumerate(
        label_path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) == 5:
            rows = parse_yolo_label(line, set(mapping))
            fields = rows[0]
        else:
            # Roboflow can export an occasional segmentation polygon in an
            # otherwise detection dataset. Convert it to its enclosing box so
            # the object remains supervised in the bbox-only training pipeline.
            try:
                source_id = int(fields[0])
                coordinates = [float(value) for value in fields[1:]]
            except (ValueError, IndexError) as exc:
                raise DatasetValidationError(
                    f"{label_path}: line {line_number}: invalid polygon values"
                ) from exc
            if source_id not in mapping:
                raise DatasetValidationError(
                    f"{label_path}: line {line_number}: unexpected class {source_id}"
                )
            if len(coordinates) < 6 or len(coordinates) % 2:
                raise DatasetValidationError(
                    f"{label_path}: line {line_number}: polygon needs at least 3 xy points"
                )
            if not all(0 <= value <= 1 for value in coordinates):
                raise DatasetValidationError(
                    f"{label_path}: line {line_number}: polygon coordinate outside [0, 1]"
                )
            xs, ys = coordinates[::2], coordinates[1::2]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            if x_min == x_max or y_min == y_max:
                raise DatasetValidationError(
                    f"{label_path}: line {line_number}: polygon has zero area"
                )
            fields = [
                str(source_id),
                str((x_min + x_max) / 2),
                str((y_min + y_max) / 2),
                str(x_max - x_min),
                str(y_max - y_min),
            ]
            polygon_count += 1
        target_id = mapping[int(fields[0])]
        counts[target_id] += 1
        converted.append(" ".join([str(target_id), *fields[1:]]))
    return ("\n".join(converted) + ("\n" if converted else ""), counts, polygon_count)


def prepare_joint_dataset(
    *,
    dataset_yaml: Path,
    output_dir: Path,
    source_url: str,
    source_version: str,
    source_license: str,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    """Create an immutable unified-class derivative from a complete joint dataset."""
    dataset_yaml = dataset_yaml.resolve()
    if not dataset_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_yaml}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")

    mapping = class_mapping(dataset_yaml)
    output_dir.mkdir(parents=True, exist_ok=True)
    split_reports: dict[str, Any] = {}
    transfer_counts: Counter[str] = Counter()
    source_paths: set[Path] = set()
    try:
        for split in SPLITS:
            images = _resolve_split(dataset_yaml, split)
            images_out = output_dir / "images" / split
            labels_out = output_dir / "labels" / split
            images_out.mkdir(parents=True)
            labels_out.mkdir(parents=True)
            stats: Counter[str] = Counter()
            for image_path in images:
                if image_path in source_paths:
                    raise DatasetValidationError(
                        f"Source image appears in multiple splits: {image_path}"
                    )
                source_paths.add(image_path)
                label_path = _label_for_image(image_path)
                if not label_path.is_file():
                    raise DatasetValidationError(f"Missing label for {image_path}: {label_path}")

                label_text, class_counts, polygon_count = _convert_label(label_path, mapping)
                output_stem = _output_stem(image_path)
                image_destination = images_out / f"{output_stem}{image_path.suffix.lower()}"
                transfer_counts[_link_or_copy(image_path, image_destination)] += 1
                (labels_out / f"{output_stem}.txt").write_text(label_text, encoding="utf-8")

                stats["images"] += 1
                stats["smoke_boxes"] += class_counts[0]
                stats["fire_boxes"] += class_counts[1]
                stats["person_boxes"] += class_counts[2]
                stats["polygons_converted_to_boxes"] += polygon_count
                if class_counts:
                    stats["positive_images"] += 1
                else:
                    stats["negative_images"] += 1
            split_reports[split] = dict(stats)

        (output_dir / "dataset.yaml").write_text(
            f"path: {output_dir.resolve().as_posix()}\n"
            "train: images/train\nval: images/val\ntest: images/test\n\n"
            "names:\n  0: smoke\n  1: fire\n  2: person\n",
            encoding="utf-8",
        )
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "Fully annotated smoke/fire/person unified derivative",
            "source": {
                "dataset_yaml": dataset_yaml.as_posix(),
                "url": source_url,
                "version": source_version,
                "license": source_license,
                "archive_sha256": source_sha256,
                "class_mapping": {str(key): value for key, value in sorted(mapping.items())},
            },
            "output": {
                "class_names": list(TARGET_NAMES),
                "annotation_scope": list(TARGET_NAMES),
                "manual_box_annotation_required": False,
                "splits": split_reports,
                "image_transfer": dict(transfer_counts),
                "annotation_conversion": {
                    "segmentation_polygons": "Converted to enclosing YOLO bounding boxes",
                    "polygon_rows_converted": sum(
                        split_reports[split].get("polygons_converted_to_boxes", 0)
                        for split in SPLITS
                    ),
                },
            },
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return manifest
    except Exception:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a complete joint YOLO dataset")
    parser.add_argument("--dataset-yaml", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--source-license", required=True)
    parser.add_argument("--source-sha256")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = prepare_joint_dataset(
        dataset_yaml=args.dataset_yaml,
        output_dir=args.output_dir,
        source_url=args.source_url,
        source_version=args.source_version,
        source_license=args.source_license,
        source_sha256=args.source_sha256,
    )
    print(json.dumps(manifest["output"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
