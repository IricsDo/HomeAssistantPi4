"""Compose unified YOLO datasets with optional Roboflow de-leakage."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from indoor_detection.dataset import IMAGE_SUFFIXES, sha256_file

SPLITS = ("train", "val", "test")
TARGET_NAMES = ("smoke", "fire", "person")
SPLIT_PRIORITY = {"train": 0, "val": 1, "test": 2}


def _parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("source must use NAME=DATASET_YAML")
    name, raw_path = value.split("=", 1)
    if not name.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("source must use non-empty NAME=DATASET_YAML")
    return name.strip(), Path(raw_path.strip())


def _resolve_split(dataset_yaml: Path, split: str) -> list[Path]:
    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"Dataset YAML must be a mapping: {dataset_yaml}")
    root = Path(str(config.get("path", dataset_yaml.parent)))
    if not root.is_absolute():
        root = (dataset_yaml.parent / root).resolve()
    value = config.get(split)
    if not isinstance(value, (str, list)):
        raise ValueError(f"Dataset YAML has no usable '{split}' split: {dataset_yaml}")
    items = [value] if isinstance(value, str) else value
    images: list[Path] = []
    for item in items:
        source = Path(str(item))
        if not source.is_absolute():
            source = root / source
        if source.is_dir():
            images.extend(
                path.resolve()
                for path in source.rglob("*")
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
        elif source.is_file() and source.suffix.lower() == ".txt":
            for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
                line = raw_line.strip()
                if line:
                    path = Path(line)
                    images.append((path if path.is_absolute() else root / path).resolve())
        else:
            raise FileNotFoundError(f"Dataset split source not found: {source}")
    return sorted(images)


def _roboflow_base_id(path: Path) -> str:
    name = path.name
    # Joint intake prefixes a short hash of the full source path to avoid name
    # collisions; strip that prefix before grouping Roboflow augmentation IDs.
    if len(name) > 13 and name[12] == "_" and all(c in "0123456789abcdef" for c in name[:12]):
        name = name[13:]
    return name.split(".rf.", 1)[0]


def _dhash(path: Path) -> int:
    with Image.open(path) as image:
        grayscale = image.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
        pixels = list(grayscale.tobytes())
    value = 0
    for row in range(8):
        offset = row * 9
        for column in range(8):
            value = (value << 1) | (pixels[offset + column + 1] > pixels[offset + column])
    return value


def _hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def find_roboflow_cross_split_exclusions(
    split_images: dict[str, list[Path]], max_hamming_distance: int = 5
) -> tuple[set[Path], list[dict[str, Any]]]:
    """Drop near-identical lower-priority variants while keeping dissimilar name clashes."""
    groups: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for split, images in split_images.items():
        for image in images:
            groups[_roboflow_base_id(image)].append((split, image))

    exclusions: set[Path] = set()
    evidence: list[dict[str, Any]] = []
    for base_id, members in sorted(groups.items()):
        if len({split for split, _ in members}) < 2:
            continue
        hashes = {path: _dhash(path) for _, path in members}
        ordered = sorted(
            members,
            key=lambda item: (SPLIT_PRIORITY[item[0]], item[1].as_posix()),
            reverse=True,
        )
        kept: list[tuple[str, Path]] = []
        for split, path in ordered:
            match = next(
                (
                    (kept_split, kept_path, _hamming_distance(hashes[path], hashes[kept_path]))
                    for kept_split, kept_path in kept
                    if kept_split != split
                    and _hamming_distance(hashes[path], hashes[kept_path])
                    <= max_hamming_distance
                ),
                None,
            )
            if match is None:
                kept.append((split, path))
                continue
            kept_split, kept_path, distance = match
            exclusions.add(path)
            evidence.append(
                {
                    "base_id": base_id,
                    "excluded_split": split,
                    "excluded": path.as_posix(),
                    "kept_split": kept_split,
                    "kept": kept_path.as_posix(),
                    "dhash_hamming_distance": distance,
                }
            )
    return exclusions, evidence


def compose_dataset(
    *,
    sources: list[tuple[str, Path]],
    output_dir: Path,
    roboflow_deduplicate: set[str],
    max_hamming_distance: int = 5,
    emit_class_scopes: bool = False,
    exclude_images: set[Path] | None = None,
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    if not sources:
        raise ValueError("At least one source dataset is required")
    source_names = [name for name, _ in sources]
    if len(source_names) != len(set(source_names)):
        raise ValueError("Source dataset names must be unique")
    unknown = roboflow_deduplicate - set(source_names)
    if unknown:
        raise ValueError(f"Unknown de-duplication sources: {sorted(unknown)}")
    requested_exclusions = {path.resolve() for path in (exclude_images or set())}
    found_exclusions: set[Path] = set()

    output_dir.mkdir(parents=True, exist_ok=True)
    combined: dict[str, list[Path]] = {split: [] for split in SPLITS}
    class_scopes: dict[Path, list[str]] = {}
    source_reports: list[dict[str, Any]] = []
    for name, dataset_yaml in sources:
        dataset_yaml = dataset_yaml.resolve()
        if not dataset_yaml.is_file():
            raise FileNotFoundError(f"Dataset YAML not found: {dataset_yaml}")
        split_images = {split: _resolve_split(dataset_yaml, split) for split in SPLITS}
        exclusions: set[Path] = set()
        evidence: list[dict[str, Any]] = []
        if name in roboflow_deduplicate:
            exclusions, evidence = find_roboflow_cross_split_exclusions(
                split_images, max_hamming_distance
            )
        manual_exclusions = {
            image
            for images in split_images.values()
            for image in images
            if image in requested_exclusions
        }
        found_exclusions.update(manual_exclusions)
        exclusions.update(manual_exclusions)
        kept_counts: dict[str, int] = {}
        for split in SPLITS:
            kept = [path for path in split_images[split] if path not in exclusions]
            combined[split].extend(kept)
            kept_counts[split] = len(kept)
        source_manifest = dataset_yaml.parent / "manifest.json"
        annotation_scope: list[str] | None = None
        if emit_class_scopes:
            if not source_manifest.is_file():
                raise FileNotFoundError(
                    f"Source class scope requires a manifest: {source_manifest}"
                )
            source_metadata = json.loads(source_manifest.read_text(encoding="utf-8"))
            raw_scope = source_metadata.get("output", {}).get("annotation_scope")
            if not isinstance(raw_scope, list):
                raise ValueError(f"Source manifest has no annotation scope: {source_manifest}")
            scope = set(raw_scope)
            if not scope or len(scope) != len(raw_scope) or not scope <= set(TARGET_NAMES):
                raise ValueError(f"Invalid annotation scope in {source_manifest}: {raw_scope}")
            annotation_scope = [target for target in TARGET_NAMES if target in scope]
            for split in SPLITS:
                for image in split_images[split]:
                    if image in exclusions:
                        continue
                    previous = class_scopes.setdefault(image, annotation_scope)
                    if previous != annotation_scope:
                        raise ValueError(f"Conflicting annotation scopes for image: {image}")
        source_reports.append(
            {
                "name": name,
                "dataset_yaml": dataset_yaml.as_posix(),
                "manifest": (
                    {
                        "path": source_manifest.as_posix(),
                        "sha256": sha256_file(source_manifest),
                    }
                    if source_manifest.is_file()
                    else None
                ),
                "input_images": {
                    split: len(split_images[split]) for split in SPLITS
                },
                "kept_images": kept_counts,
                "annotation_scope": annotation_scope,
                "manual_exclusions": sorted(path.as_posix() for path in manual_exclusions),
                "roboflow_cross_split_exclusions": evidence,
            }
        )

    missing_exclusions = requested_exclusions - found_exclusions
    if missing_exclusions:
        raise ValueError(
            "Requested exclusions are outside all source splits: "
            f"{sorted(path.as_posix() for path in missing_exclusions)}"
        )

    for split in SPLITS:
        combined[split] = sorted(set(combined[split]))
        (output_dir / f"{split}.txt").write_text(
            "".join(f"{path.as_posix()}\n" for path in combined[split]), encoding="utf-8"
        )
    class_scope_line = (
        "class_scope_manifest: class_scope_manifest.json\n" if emit_class_scopes else ""
    )
    (output_dir / "dataset.yaml").write_text(
        f"path: {output_dir.resolve().as_posix()}\n"
        f"train: train.txt\nval: val.txt\ntest: test.txt\n{class_scope_line}\n"
        "names:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )
    if emit_class_scopes:
        scope_document = {
            "schema_version": 1,
            "classes": list(TARGET_NAMES),
            "images": {
                path.resolve().as_posix(): class_scopes[path]
                for split in SPLITS
                for path in combined[split]
            },
        }
        (output_dir / "class_scope_manifest.json").write_text(
            json.dumps(scope_document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": "Combined indoor-detection dataset index",
        "settings": {
            "roboflow_deduplicate": sorted(roboflow_deduplicate),
            "max_dhash_hamming_distance": max_hamming_distance,
            "split_priority": ["test", "val", "train"],
            "class_scopes": emit_class_scopes,
            "manual_exclusions": sorted(path.as_posix() for path in requested_exclusions),
        },
        "sources": source_reports,
        "output": {"splits": {split: len(combined[split]) for split in SPLITS}},
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compose indoor-detection dataset indexes")
    parser.add_argument("--source", action="append", type=_parse_source, required=True)
    parser.add_argument("--roboflow-deduplicate", action="append", default=[])
    parser.add_argument("--max-hamming-distance", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--class-scopes",
        action="store_true",
        help="Emit per-image annotation scopes from each source manifest",
    )
    parser.add_argument(
        "--exclude-image",
        action="append",
        type=Path,
        default=[],
        help="Exclude an adjudicated source image while preserving source files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = compose_dataset(
        sources=args.source,
        output_dir=args.output_dir,
        roboflow_deduplicate=set(args.roboflow_deduplicate),
        max_hamming_distance=args.max_hamming_distance,
        emit_class_scopes=args.class_scopes,
        exclude_images=set(args.exclude_image),
    )
    print(json.dumps(report["output"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
