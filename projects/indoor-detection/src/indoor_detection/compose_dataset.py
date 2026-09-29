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
    return path.name.split(".rf.", 1)[0]


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

    output_dir.mkdir(parents=True, exist_ok=True)
    combined: dict[str, list[Path]] = {split: [] for split in SPLITS}
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
        kept_counts: dict[str, int] = {}
        for split in SPLITS:
            kept = [path for path in split_images[split] if path not in exclusions]
            combined[split].extend(kept)
            kept_counts[split] = len(kept)
        source_manifest = dataset_yaml.parent / "manifest.json"
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
                "roboflow_cross_split_exclusions": evidence,
            }
        )

    for split in SPLITS:
        combined[split] = sorted(set(combined[split]))
        (output_dir / f"{split}.txt").write_text(
            "".join(f"{path.as_posix()}\n" for path in combined[split]), encoding="utf-8"
        )
    (output_dir / "dataset.yaml").write_text(
        f"path: {output_dir.resolve().as_posix()}\n"
        "train: train.txt\nval: val.txt\ntest: test.txt\n\n"
        "names:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": "Combined indoor-detection dataset index",
        "settings": {
            "roboflow_deduplicate": sorted(roboflow_deduplicate),
            "max_dhash_hamming_distance": max_hamming_distance,
            "split_priority": ["test", "val", "train"],
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = compose_dataset(
        sources=args.source,
        output_dir=args.output_dir,
        roboflow_deduplicate=set(args.roboflow_deduplicate),
        max_hamming_distance=args.max_hamming_distance,
    )
    print(json.dumps(report["output"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
