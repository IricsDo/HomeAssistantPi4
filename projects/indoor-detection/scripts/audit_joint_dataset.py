"""Audit a prepared joint dataset and render deterministic annotation samples."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

from indoor_detection.compose_dataset import find_roboflow_cross_split_exclusions
from indoor_detection.dataset import IMAGE_SUFFIXES, audit_dataset, parse_yolo_label

NAMES = {0: "smoke", 1: "fire", 2: "person"}
SPLITS = ("train", "val", "test")
SAMPLE_LIMIT = 16
TILE_SIZE = (320, 260)


def _records(dataset_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    counts: dict[str, Any] = {}
    for split in SPLITS:
        image_dir = dataset_root / "images" / split
        label_dir = dataset_root / "labels" / split
        images = sorted(
            path for path in image_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        split_counts: Counter[str] = Counter()
        split_counts.update({f"{name}_positive_images": 0 for name in NAMES.values()})
        for image_path in images:
            label_path = label_dir / f"{image_path.stem}.txt"
            text = label_path.read_text(encoding="utf-8-sig")
            rows = parse_yolo_label(text, set(NAMES))
            classes: Counter[int] = Counter()
            boxes: list[dict[str, Any]] = []
            for fields in rows:
                class_id = int(fields[0])
                coords = [float(value) for value in fields[1:]]
                classes[class_id] += 1
                split_counts[f"{NAMES[class_id]}_boxes"] += 1
                boxes.append({"class_id": class_id, "xywhn": coords})
                x, y, width, height = coords
                outside = (
                    x - width / 2 < 0
                    or y - height / 2 < 0
                    or x + width / 2 > 1
                    or y + height / 2 > 1
                )
                if outside:
                    split_counts["boxes_outside_image"] += 1
                if width * height <= 0.01:
                    split_counts["small_boxes"] += 1
                if width * height >= 0.25:
                    split_counts["large_boxes"] += 1
            present = sorted(classes)
            for class_id in present:
                split_counts[f"{NAMES[class_id]}_positive_images"] += 1
            if not rows:
                group = "negative"
                split_counts["negative_images"] += 1
            elif len(present) > 1:
                group = "multi_class"
                split_counts["multi_class_images"] += 1
            else:
                group = NAMES[present[0]]
            records.append({
                "split": split,
                "image": image_path,
                "boxes": boxes,
                "group": group,
            })
        split_counts["images"] = len(images)
        counts[split] = dict(split_counts)
    return records, counts


def _sample_groups(records: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[f"{record['split']}_{record['group']}"].append(record)
        if record["group"] != "negative":
            for box in record["boxes"]:
                groups[f"{record['split']}_{NAMES[box['class_id']]}_boxes"].append(record)
            if any(box["xywhn"][2] * box["xywhn"][3] <= .01 for box in record["boxes"]):
                groups[f"{record['split']}_small_box"].append(record)
            if any(box["xywhn"][2] * box["xywhn"][3] >= .25 for box in record["boxes"]):
                groups[f"{record['split']}_large_box"].append(record)
    return {
        name: rng.sample(
            list({item["image"]: item for item in items}.values()),
            min(SAMPLE_LIMIT, len(items)),
        )
        for name, items in sorted(groups.items())
    }


def _label_signature(path: Path) -> tuple[tuple[float, ...], ...]:
    rows = parse_yolo_label(path.read_text(encoding="utf-8-sig"), set(NAMES))
    return tuple(
        sorted((float(fields[0]), *(float(value) for value in fields[1:])) for fields in rows)
    )


def _render_group(items: list[dict[str, Any]], destination: Path) -> None:
    columns = 4
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * TILE_SIZE[0], rows * TILE_SIZE[1]), "#e5e7eb")
    for index, item in enumerate(items):
        with Image.open(item["image"]) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((TILE_SIZE[0], TILE_SIZE[1] - 40), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", TILE_SIZE, "white")
        left = (TILE_SIZE[0] - image.width) // 2
        top = 0
        tile.paste(image, (left, top))
        tile_draw = ImageDraw.Draw(tile)
        for box in item["boxes"]:
            x, y, width, height = box["xywhn"]
            x1 = left + (x - width / 2) * image.width
            y1 = top + (y - height / 2) * image.height
            x2 = left + (x + width / 2) * image.width
            y2 = top + (y + height / 2) * image.height
            name = NAMES[box["class_id"]]
            tile_draw.rectangle((x1, y1, x2, y2), outline="#ef4444", width=2)
            tile_draw.text((x1, max(0, y1 - 12)), name, fill="#ef4444")
        caption = f"{item['split']} | {item['image'].name[:42]}"
        tile_draw.text((5, TILE_SIZE[1] - 35), caption, fill="black")
        sheet.paste(tile, ((index % columns) * TILE_SIZE[0], (index // columns) * TILE_SIZE[1]))
    sheet.save(destination, quality=90)


def _render_duplicate_conflicts(
    dataset_root: Path,
    groups: list[list[dict[str, str]]],
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Render every annotation variant side by side for manual adjudication."""
    output_dir.mkdir(parents=True, exist_ok=True)
    review_rows: list[dict[str, Any]] = []
    for group_number, group in enumerate(groups, start=1):
        items: list[dict[str, Any]] = []
        for member in group:
            image_path = dataset_root / "images" / member["split"] / member["file"]
            label_path = dataset_root / "labels" / member["split"] / f"{image_path.stem}.txt"
            rows = parse_yolo_label(label_path.read_text(encoding="utf-8-sig"), set(NAMES))
            items.append({
                "split": member["split"],
                "image": image_path,
                "boxes": [
                    {"class_id": int(row[0]), "xywhn": [float(value) for value in row[1:]]}
                    for row in rows
                ],
            })
            review_rows.append({
                "group": f"duplicate-{group_number:03d}",
                "split": member["split"],
                "image": member["file"],
                "label_file": label_path.name,
                "label_rows": len(rows),
                "classes": ",".join(sorted({NAMES[int(row[0])] for row in rows})),
                "decision": "",
                "review_notes": "",
            })
        _render_group(items, output_dir / f"duplicate-{group_number:03d}.jpg")
    return review_rows


def audit_joint_dataset(
    dataset_root: Path,
    report_dir: Path,
    seed: int = 42,
    visual_review_status: str = "pending",
    visual_review_notes: str = "",
) -> dict[str, Any]:
    if visual_review_status not in {"pending", "passed", "failed"}:
        raise ValueError("visual_review_status must be pending, passed or failed")
    report_dir.mkdir(parents=True, exist_ok=True)
    structure = audit_dataset(dataset_root, report_dir / "structural-audit.json")
    records, distributions = _records(dataset_root)
    manifest = json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))
    duplicate_label_conflicts: list[list[str]] = []
    conflict_groups: list[list[dict[str, str]]] = []
    for group in structure["duplicates"]["exact_duplicate_examples"]:
        signatures = {
            _label_signature(
                dataset_root / "labels" / item["split"] / f"{Path(item['file']).stem}.txt"
            )
            for item in group
        }
        if len(signatures) > 1:
            duplicate_label_conflicts.append([f"{item['split']}/{item['file']}" for item in group])
            conflict_groups.append(group)

    split_images = {
        split: [record["image"] for record in records if record["split"] == split]
        for split in SPLITS
    }
    _, near_duplicate_evidence = find_roboflow_cross_split_exclusions(split_images)

    samples = _sample_groups(records, seed)
    contact_dir = report_dir / "contact-sheets"
    contact_dir.mkdir(exist_ok=True)
    for group, items in samples.items():
        _render_group(items, contact_dir / f"{group}.jpg")
    conflict_dir = report_dir / "duplicate-conflicts"
    conflict_rows = _render_duplicate_conflicts(dataset_root, conflict_groups, conflict_dir)
    review_csv = report_dir / "duplicate-adjudication.csv"
    with review_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "group", "split", "image", "label_file", "label_rows", "classes",
            "decision", "review_notes",
        ])
        writer.writeheader()
        writer.writerows(conflict_rows)
    gate_blockers: list[str] = []
    boxes_outside_image = sum(
        split_counts.get("boxes_outside_image", 0) for split_counts in distributions.values()
    )
    if not structure["valid"]:
        gate_blockers.append("Structural image/label or annotation validation failed")
    if boxes_outside_image:
        gate_blockers.append(f"{boxes_outside_image} bounding boxes extend outside their images")
    if structure["duplicates"]["exact_duplicate_groups"]:
        gate_blockers.append(
            f"{structure['duplicates']['exact_duplicate_groups']} exact duplicate image "
            "groups remain"
        )
    if duplicate_label_conflicts:
        gate_blockers.append(
            f"{len(duplicate_label_conflicts)} duplicate image groups have conflicting labels"
        )
    if near_duplicate_evidence:
        gate_blockers.append("Roboflow near-duplicate candidates cross split boundaries")
    if visual_review_status != "passed":
        gate_blockers.append("Visual annotation and indoor relevance review has not passed")

    report = {
        "dataset_root": dataset_root.resolve().as_posix(),
        "source": manifest.get("source"),
        "data_gate_passed": not gate_blockers,
        "data_gate_blockers": gate_blockers,
        "structural_valid": structure["valid"],
        "structure": structure["splits"],
        "exact_duplicates": structure["duplicates"],
        "duplicate_label_conflict_groups": len(duplicate_label_conflicts),
        "duplicate_label_conflict_examples": duplicate_label_conflicts[:30],
        "duplicate_conflict_contact_sheets": str(conflict_dir.resolve()),
        "duplicate_adjudication_csv": str(review_csv.resolve()),
        "roboflow_near_duplicate_exclusions": len(near_duplicate_evidence),
        "roboflow_near_duplicate_examples": near_duplicate_evidence[:100],
        "class_distribution": distributions,
        "boxes_outside_image": boxes_outside_image,
        "annotation_sample_groups": {name: len(items) for name, items in samples.items()},
        "annotation_sample_seed": seed,
        "contact_sheets": str(contact_dir.resolve()),
        "visual_review": {
            "status": visual_review_status,
            "notes": visual_review_notes,
        },
    }
    (report_dir / "joint-audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--visual-review-status",
        choices=("pending", "passed", "failed"),
        default="pending",
    )
    parser.add_argument("--visual-review-notes", default="")
    args = parser.parse_args(argv)
    report = audit_joint_dataset(
        args.dataset_root,
        args.report_dir,
        args.seed,
        args.visual_review_status,
        args.visual_review_notes,
    )
    print(json.dumps({
        "data_gate_passed": report["data_gate_passed"],
        "data_gate_blockers": report["data_gate_blockers"],
        "structural_valid": report["structural_valid"],
        "duplicate_groups": report["exact_duplicates"]["exact_duplicate_groups"],
        "duplicate_label_conflict_groups": report["duplicate_label_conflict_groups"],
        "cross_split_exact_groups": report["exact_duplicates"]["cross_split_groups"],
        "roboflow_near_duplicate_exclusions": report["roboflow_near_duplicate_exclusions"],
        "boxes_outside_image": report["boxes_outside_image"],
        "visual_review": report["visual_review"],
    }, indent=2))
    return 0 if report["structural_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
