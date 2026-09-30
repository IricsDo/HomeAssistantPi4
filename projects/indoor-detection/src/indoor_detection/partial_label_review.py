"""Create stratified visual review bundles for partial-label datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import IMAGE_SUFFIXES, parse_yolo_label

TARGET_NAMES = ("smoke", "fire", "person")
COLORS = {"smoke": "#06b6d4", "fire": "#ef4444", "person": "#22c55e"}
TILE_SIZE = (400, 300)
IMAGE_AREA = (400, 260)
GRID = (4, 4)


def _parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("source must use NAME=DATASET_YAML")
    name, raw_path = value.split("=", 1)
    if not name or not raw_path:
        raise argparse.ArgumentTypeError("source must use NAME=DATASET_YAML")
    return name, Path(raw_path)


def _class_names(data: dict[str, Any]) -> dict[int, str]:
    names = data.get("names")
    if isinstance(names, list):
        return dict(enumerate(str(value).strip().lower() for value in names))
    if isinstance(names, dict):
        try:
            return {int(key): str(value).strip().lower() for key, value in names.items()}
        except (TypeError, ValueError) as exc:
            raise ValueError("Dataset class IDs must be integers") from exc
    raise ValueError("Dataset YAML must declare names as a list or mapping")


def _label_path(image_path: Path) -> Path:
    parts = list(image_path.parts)
    image_dir = next(
        (index for index in range(len(parts) - 1, -1, -1) if parts[index] == "images"),
        None,
    )
    if image_dir is None:
        raise ValueError(f"Image path does not contain an images directory: {image_path}")
    parts[image_dir] = "labels"
    return Path(*parts).with_suffix(".txt")


def _stratum(class_ids: set[int], name_to_id: dict[str, int], scope: set[str]) -> str:
    if scope == {"smoke", "fire"}:
        smoke = name_to_id["smoke"] in class_ids
        fire = name_to_id["fire"] in class_ids
        if smoke and fire:
            return "both"
        if smoke:
            return "smoke_only"
        if fire:
            return "fire_only"
        return "negative"
    if scope == {"person"}:
        return "person_present" if name_to_id["person"] in class_ids else "negative"
    return "other_scope"


def _draw_page(items: list[dict[str, Any]], destination: Path) -> None:
    columns = GRID[0]
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * TILE_SIZE[0], rows * TILE_SIZE[1]), "#e5e7eb")
    for index, item in enumerate(items):
        with Image.open(item["image"]) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail(IMAGE_AREA, Image.Resampling.LANCZOS)
        tile = Image.new("RGB", TILE_SIZE, "white")
        left = (IMAGE_AREA[0] - image.width) // 2
        top = (IMAGE_AREA[1] - image.height) // 2
        tile.paste(image, (left, top))
        draw = ImageDraw.Draw(tile)
        for box in item["boxes"]:
            x, y, width, height = box["xywhn"]
            x1 = left + (x - width / 2) * image.width
            y1 = top + (y - height / 2) * image.height
            x2 = left + (x + width / 2) * image.width
            y2 = top + (y + height / 2) * image.height
            name = box["name"]
            color = COLORS[name]
            draw.rectangle((x1, y1, x2, y2), outline=color, width=2)
            draw.text((x1 + 2, max(0, y1 - 12)), name, fill=color)
        draw.text((5, TILE_SIZE[1] - 36), f"{item['split']} | {item['stratum']}", fill="black")
        draw.text((5, TILE_SIZE[1] - 20), item["image"].name[:54], fill="#374151")
        sheet.paste(tile, ((index % columns) * TILE_SIZE[0], (index // columns) * TILE_SIZE[1]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=90)


def create_partial_label_review(
    *,
    sources: list[tuple[str, Path]],
    output_dir: Path,
    sample_per_stratum: int = 15,
    seed: int = 42,
) -> dict[str, Any]:
    if sample_per_stratum <= 0:
        raise ValueError("sample_per_stratum must be greater than zero")
    if not sources:
        raise ValueError("At least one source dataset is required")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    if len({name for name, _ in sources}) != len(sources):
        raise ValueError("Source names must be unique")

    all_samples: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []
    for source_name, yaml_path in sources:
        yaml_path = yaml_path.resolve()
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Dataset YAML not found: {yaml_path}")
        import yaml

        config = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError(f"Dataset YAML must be a mapping: {yaml_path}")
        names = _class_names(config)
        name_to_id = {name: class_id for class_id, name in names.items()}
        manifest_path = yaml_path.parent / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        scope = set(manifest.get("output", {}).get("annotation_scope", []))
        if not scope or not scope <= set(TARGET_NAMES) or not scope <= set(name_to_id):
            raise ValueError(f"Invalid annotation scope in {manifest_path}: {sorted(scope)}")
        if scope not in ({"smoke", "fire"}, {"person"}):
            raise ValueError(f"Unsupported partial-label scope for {source_name}: {sorted(scope)}")

        stratum_names = (
            ("both", "smoke_only", "fire_only", "negative")
            if scope == {"smoke", "fire"}
            else ("person_present", "negative")
        )
        population: dict[str, Counter[str]] = {
            split: Counter({stratum: 0 for stratum in stratum_names}) for split in SPLITS
        }
        groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for split in SPLITS:
            for image_path in _resolve_split(yaml_path, split):
                if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                label_path = _label_path(image_path)
                if not label_path.is_file():
                    raise FileNotFoundError(
                        f"Missing label file for review candidate: {label_path}"
                    )
                rows = parse_yolo_label(label_path.read_text(encoding="utf-8-sig"), set(names))
                boxes = [
                    {
                        "class_id": int(row[0]),
                        "name": names[int(row[0])],
                        "xywhn": [float(value) for value in row[1:]],
                    }
                    for row in rows
                ]
                class_ids = {box["class_id"] for box in boxes}
                stratum = _stratum(class_ids, name_to_id, scope)
                population[split][stratum] += 1
                groups[(split, stratum)].append({
                    "source": source_name,
                    "split": split,
                    "stratum": stratum,
                    "image": image_path,
                    "label": label_path,
                    "boxes": boxes,
                    "scope": sorted(scope),
                    "unknown_classes": sorted(set(TARGET_NAMES) - scope),
                })

        selected_counts: dict[str, dict[str, int]] = {
            split: {stratum: 0 for stratum in stratum_names} for split in SPLITS
        }
        for (split, stratum), records in sorted(groups.items()):
            key = f"{source_name}/{split}/{stratum}"
            key_seed = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
            rng = random.Random(seed ^ key_seed)
            selected = rng.sample(records, min(sample_per_stratum, len(records)))
            selected_counts[split][stratum] = len(selected)
            for item in selected:
                payload = f"{source_name}|{split}|{item['image'].as_posix()}".encode()
                item["review_id"] = hashlib.sha256(payload).hexdigest()[:12]
                all_samples.append(item)

        source_reports.append({
            "source": source_name,
            "dataset_yaml": yaml_path.as_posix(),
            "annotation_scope": sorted(scope),
            "unknown_target_classes": sorted(set(TARGET_NAMES) - scope),
            "population_by_split_and_stratum": {
                split: dict(sorted(counts.items())) for split, counts in population.items()
            },
            "sample_by_split_and_stratum": selected_counts,
        })

    grouped_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in all_samples:
        grouped_samples[f"{item['source']}__{item['split']}__{item['stratum']}"].append(item)
    for group_name, items in sorted(grouped_samples.items()):
        for page_index in range(0, len(items), GRID[0] * GRID[1]):
            page = page_index // (GRID[0] * GRID[1]) + 1
            _draw_page(items[page_index : page_index + GRID[0] * GRID[1]],
                       output_dir / "contact-sheets" / f"{group_name}__{page:02d}.jpg")

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = [
            "review_id", "source", "split", "stratum", "annotation_scope",
            "unknown_target_classes", "known_boxes", "image", "label",
            "other_target_visible", "review_status", "review_notes",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in sorted(all_samples, key=lambda record: record["review_id"]):
            counts = Counter(box["name"] for box in item["boxes"])
            writer.writerow({
                "review_id": item["review_id"],
                "source": item["source"],
                "split": item["split"],
                "stratum": item["stratum"],
                "annotation_scope": ",".join(item["scope"]),
                "unknown_target_classes": ",".join(item["unknown_classes"]),
                "known_boxes": json.dumps(dict(sorted(counts.items())), separators=(",", ":")),
                "image": item["image"].as_posix(),
                "label": item["label"].as_posix(),
                "other_target_visible": "",
                "review_status": "pending",
                "review_notes": "",
            })

    report: dict[str, Any] = {
        "schema_version": 1,
        "seed": seed,
        "sample_per_stratum": sample_per_stratum,
        "review_count": len(all_samples),
        "sources": source_reports,
        "review_instructions": (
            "For each image, record whether any unknown_target_classes are visible. "
            "This stratified sample is a screening estimate, not proof of absence."
        ),
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        "# Partial-label cross-class review\n\n"
        "Review every contact sheet and update `review.csv`. For each row, set "
        "`other_target_visible` to `yes`, `no`, or `uncertain`; add notes when needed. "
        "The sample is a screening estimate, not proof that unobserved classes are absent. "
        "Images and source labels are not copied or modified.\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create stratified partial-label review sheets")
    parser.add_argument("--source", action="append", type=_parse_source, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-per-stratum", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = create_partial_label_review(
        sources=args.source,
        output_dir=args.output_dir,
        sample_per_stratum=args.sample_per_stratum,
        seed=args.seed,
    )
    print(json.dumps({"review_count": report["review_count"], "output_dir": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
