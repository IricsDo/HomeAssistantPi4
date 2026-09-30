"""Render person candidates into deterministic contact sheets for review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

TILE_SIZE = (320, 260)
IMAGE_AREA = (320, 220)
GRID = (4, 4)


def _load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        record = json.loads(raw_line)
        if not isinstance(record, dict) or not isinstance(record.get("image"), str):
            raise ValueError(f"Invalid candidate record on line {line_number}")
        records.append(record)
    return records


def _review_id(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def _render_tile(record: dict[str, Any], review_id: str) -> Image.Image:
    image_path = Path(record["image"])
    with Image.open(image_path) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        source.thumbnail(IMAGE_AREA, Image.Resampling.LANCZOS)
        tile = Image.new("RGB", TILE_SIZE, "white")
        left = (IMAGE_AREA[0] - source.width) // 2
        top = (IMAGE_AREA[1] - source.height) // 2
        tile.paste(source, (left, top))

    draw = ImageDraw.Draw(tile)
    candidates = record.get("person_candidates", [])
    for candidate in candidates:
        x_center, y_center, width, height = candidate["xywhn"]
        x1 = left + (x_center - width / 2) * source.width
        y1 = top + (y_center - height / 2) * source.height
        x2 = left + (x_center + width / 2) * source.width
        y2 = top + (y_center + height / 2) * source.height
        color = "#2563eb" if candidate["confidence"] >= 0.65 else "#dc2626"
        draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
        draw.text((x1 + 2, max(0, y1 - 12)), f"{candidate['confidence']:.2f}", fill=color)
    max_confidence = max((candidate["confidence"] for candidate in candidates), default=0.0)
    footer = (
        f"{review_id} | {record.get('split', '?')} | "
        f"{record.get('status', '?')} | max={max_confidence:.2f}"
    )
    draw.text((5, IMAGE_AREA[1] + 5), footer, fill="black")
    draw.text((5, IMAGE_AREA[1] + 20), image_path.name[:48], fill="#374151")
    return tile


def create_review_bundle(
    *,
    candidates_path: Path,
    output_dir: Path,
    quality: int = 88,
) -> dict[str, Any]:
    if not candidates_path.is_file():
        raise FileNotFoundError(f"Candidate JSONL not found: {candidates_path}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    if not 1 <= quality <= 100:
        raise ValueError("quality must be in [1, 100]")

    records = _load_records(candidates_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    decision_rows: list[dict[str, str]] = []
    for record in records:
        review_id = _review_id(record)
        status = str(record.get("status", "unknown"))
        grouped[status].append((review_id, record))
        confidences = [
            float(candidate["confidence"]) for candidate in record.get("person_candidates", [])
        ]
        decision_rows.append(
            {
                "review_id": review_id,
                "split": str(record.get("split", "")),
                "status": status,
                "candidate_boxes": str(len(confidences)),
                "min_confidence": f"{min(confidences):.6f}" if confidences else "",
                "max_confidence": f"{max(confidences):.6f}" if confidences else "",
                "decision": "",
                "notes": "",
                "image": record["image"],
            }
        )

    page_capacity = GRID[0] * GRID[1]
    page_counts: dict[str, int] = {}
    for status, items in sorted(grouped.items()):
        status_dir = output_dir / status
        status_dir.mkdir(parents=True, exist_ok=True)
        page_counts[status] = math.ceil(len(items) / page_capacity)
        for page_index, start in enumerate(range(0, len(items), page_capacity), start=1):
            page = Image.new("RGB", (TILE_SIZE[0] * GRID[0], TILE_SIZE[1] * GRID[1]), "#e5e7eb")
            for offset, (review_id, record) in enumerate(items[start : start + page_capacity]):
                x = (offset % GRID[0]) * TILE_SIZE[0]
                y = (offset // GRID[0]) * TILE_SIZE[1]
                page.paste(_render_tile(record, review_id), (x, y))
            page.save(status_dir / f"page-{page_index:04d}.jpg", quality=quality)

    fields = [
        "review_id",
        "split",
        "status",
        "candidate_boxes",
        "min_confidence",
        "max_confidence",
        "decision",
        "notes",
        "image",
    ]
    with (output_dir / "decisions.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(decision_rows)

    report = {
        "schema_version": 1,
        "candidates": candidates_path.resolve().as_posix(),
        "records": len(records),
        "grid": {"columns": GRID[0], "rows": GRID[1]},
        "pages": page_counts,
        "workflow": "Set decision to accept or reject for every row; keep review_id unchanged",
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render person annotation review bundle")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--quality", type=int, default=88)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = create_review_bundle(
        candidates_path=args.candidates,
        output_dir=args.output_dir,
        quality=args.quality,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
