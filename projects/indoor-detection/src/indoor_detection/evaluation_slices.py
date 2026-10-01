"""Build source-specific evaluation indexes from a scoped joint dataset."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build source-specific evaluation slices")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _source_name(image_path: Path) -> str:
    image_indices = [
        index for index, part in enumerate(image_path.parts) if part.lower() == "images"
    ]
    if not image_indices or image_indices[-1] == 0:
        raise ValueError(f"Image path has no source directory before 'images': {image_path}")
    return image_path.parts[image_indices[-1] - 1]


def _split_images(dataset_root: Path, split_value: Any) -> list[Path]:
    items = [split_value] if isinstance(split_value, str) else split_value
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise ValueError("Evaluation split must be a path or list of paths")
    images: list[Path] = []
    for item in items:
        source = _resolve(dataset_root, item)
        if not source.is_file() or source.suffix.lower() != ".txt":
            raise ValueError(f"Evaluation split must reference a text index: {source}")
        for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if line:
                images.append(_resolve(dataset_root, line).resolve())
    return images


def build_evaluation_slices(
    dataset_yaml: Path, output_dir: Path, *, overwrite: bool = False
) -> dict[str, Any]:
    dataset_yaml = dataset_yaml.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Output directory must be empty: {output_dir}")
    if not dataset_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_yaml}")

    config = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    names = config.get("names")
    if not isinstance(names, (dict, list)):
        raise ValueError("Dataset YAML must define class names")
    scope_value = config.get("class_scope_manifest")
    if not isinstance(scope_value, str) or not scope_value.strip():
        raise ValueError("Dataset YAML must define class_scope_manifest")

    dataset_root = _resolve(dataset_yaml.parent, str(config.get("path", dataset_yaml.parent)))
    scope_manifest = _resolve(dataset_root, scope_value).resolve()
    if not scope_manifest.is_file():
        raise FileNotFoundError(f"Class scope manifest not found: {scope_manifest}")

    grouped: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for split in ("val", "test"):
        if split not in config:
            raise ValueError(f"Dataset YAML is missing '{split}'")
        for image_path in _split_images(dataset_root, config[split]):
            grouped[_source_name(image_path)][split].append(image_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"schema_version": 1, "sources": {}}
    for source_name in sorted(grouped):
        source_dir = output_dir / source_name
        source_dir.mkdir(parents=True, exist_ok=overwrite)
        counts: dict[str, int] = {}
        for split in ("val", "test"):
            paths = sorted(grouped[source_name].get(split, []))
            (source_dir / f"{split}.txt").write_text(
                "".join(f"{path.as_posix()}\n" for path in paths), encoding="utf-8"
            )
            counts[split] = len(paths)
        slice_config = {
            "path": source_dir.as_posix(),
            "train": "val.txt",
            "val": "val.txt",
            "test": "test.txt",
            "class_scope_manifest": scope_manifest.as_posix(),
            "names": names,
        }
        (source_dir / "dataset.yaml").write_text(
            yaml.safe_dump(slice_config, sort_keys=False), encoding="utf-8"
        )
        summary["sources"][source_name] = counts

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_evaluation_slices(args.data, args.output, overwrite=args.overwrite)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
