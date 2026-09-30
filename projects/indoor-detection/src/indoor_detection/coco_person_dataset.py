"""Build a reproducible COCO 2017 person subset using unified class id 2."""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from indoor_detection.dataset import _write_json, sha256_file

PERSON_CLASS_ID = 2


def _load_coco(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"COCO annotation file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("COCO annotations must be a JSON object")
    return payload


def _person_category_id(payload: dict[str, Any]) -> int:
    matches = [
        int(category["id"])
        for category in payload.get("categories", [])
        if str(category.get("name", "")).strip().lower() == "person"
    ]
    if len(matches) != 1:
        raise ValueError("COCO annotations must define category 'person' exactly once")
    return matches[0]


def _index_payload(
    payload: dict[str, Any],
) -> tuple[dict[int, dict[str, Any]], dict[int, list[dict[str, Any]]], set[int]]:
    images = {int(image["id"]): image for image in payload.get("images", [])}
    person_category_id = _person_category_id(payload)
    boxes: dict[int, list[dict[str, Any]]] = defaultdict(list)
    crowd_images: set[int] = set()
    for annotation in payload.get("annotations", []):
        if int(annotation.get("category_id", -1)) != person_category_id:
            continue
        image_id = int(annotation["image_id"])
        if image_id not in images:
            raise ValueError(f"Annotation references unknown image id {image_id}")
        if int(annotation.get("iscrowd", 0)):
            crowd_images.add(image_id)
            continue
        bbox = annotation.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError(f"Invalid person bbox for image id {image_id}")
        x, y, width, height = (float(value) for value in bbox)
        if width <= 0 or height <= 0:
            continue
        boxes[image_id].append({"bbox": (x, y, width, height)})
    return images, dict(boxes), crowd_images


def _select_ids(
    images: dict[int, dict[str, Any]],
    boxes: dict[int, list[dict[str, Any]]],
    crowd_images: set[int],
    *,
    positive_limit: int | None,
    negative_limit: int,
    seed: int,
) -> list[int]:
    if positive_limit is not None and positive_limit < 1:
        raise ValueError("positive_limit must be positive or None")
    if negative_limit < 0:
        raise ValueError("negative_limit cannot be negative")
    positives = sorted(boxes)
    negatives = sorted(set(images) - set(boxes) - crowd_images)
    rng = random.Random(seed)
    rng.shuffle(positives)
    rng.shuffle(negatives)
    if positive_limit is not None:
        positives = positives[:positive_limit]
    return sorted([*positives, *negatives[:negative_limit]])


def _split_val_ids(
    images: dict[int, dict[str, Any]],
    boxes: dict[int, list[dict[str, Any]]],
    crowd_images: set[int],
    *,
    seed: int,
) -> tuple[list[int], list[int]]:
    positives = sorted(boxes)
    negatives = sorted(set(images) - set(boxes) - crowd_images)
    rng = random.Random(seed)
    rng.shuffle(positives)
    rng.shuffle(negatives)
    val = positives[::2] + negatives[::2]
    test = positives[1::2] + negatives[1::2]
    return sorted(val), sorted(test)


def _yolo_rows(image: dict[str, Any], annotations: list[dict[str, Any]]) -> str:
    image_width = float(image["width"])
    image_height = float(image["height"])
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"Invalid image dimensions for {image.get('file_name')}")
    rows: list[str] = []
    for annotation in annotations:
        x, y, width, height = annotation["bbox"]
        x1 = max(0.0, min(image_width, x))
        y1 = max(0.0, min(image_height, y))
        x2 = max(0.0, min(image_width, x + width))
        y2 = max(0.0, min(image_height, y + height))
        clipped_width = x2 - x1
        clipped_height = y2 - y1
        if clipped_width <= 0 or clipped_height <= 0:
            continue
        x_center = (x1 + x2) / 2 / image_width
        y_center = (y1 + y2) / 2 / image_height
        rows.append(
            f"{PERSON_CLASS_ID} {x_center:.8f} {y_center:.8f} "
            f"{clipped_width / image_width:.8f} {clipped_height / image_height:.8f}"
        )
    return "".join(f"{row}\n" for row in rows)


def _materialize_split(
    *,
    image_ids: list[int],
    images: dict[int, dict[str, Any]],
    boxes: dict[int, list[dict[str, Any]]],
    source_images: Path,
    output_dir: Path,
    split: str,
) -> dict[str, int]:
    image_output = output_dir / "images" / split
    label_output = output_dir / "labels" / split
    image_output.mkdir(parents=True)
    label_output.mkdir(parents=True)
    stats = {"images": 0, "positive_images": 0, "negative_images": 0, "person_boxes": 0}
    for image_id in image_ids:
        image = images[image_id]
        file_name = str(image["file_name"])
        source = source_images / file_name
        if not source.is_file():
            raise FileNotFoundError(f"COCO image not found: {source}")
        destination = image_output / file_name
        try:
            os.link(source, destination)
        except OSError:
            shutil.copy2(source, destination)
        annotations = boxes.get(image_id, [])
        label = _yolo_rows(image, annotations)
        (label_output / Path(file_name).with_suffix(".txt")).write_text(label, encoding="utf-8")
        stats["images"] += 1
        stats["person_boxes"] += len(annotations)
        stats["positive_images" if annotations else "negative_images"] += 1
    return stats


def _download_one(image: dict[str, Any], destination: Path) -> bool:
    if destination.is_file():
        return False
    url = str(image.get("coco_url") or image.get("flickr_url") or "")
    if not url:
        raise ValueError(f"Image {image.get('id')} has no download URL")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "HomeAssistantPi4/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                partial.write_bytes(response.read())
            with Image.open(partial) as downloaded:
                downloaded.verify()
            partial.replace(destination)
            return True
        except Exception:
            partial.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    return False


def _download_missing_images(
    *,
    image_ids: list[int],
    images: dict[int, dict[str, Any]],
    destination: Path,
    workers: int,
) -> int:
    if workers < 1:
        raise ValueError("download_workers must be positive")
    selected = [
        (images[image_id], destination / str(images[image_id]["file_name"]))
        for image_id in image_ids
    ]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        downloaded = list(executor.map(lambda item: _download_one(*item), selected))
    return sum(downloaded)


def prepare_coco_person(
    *,
    train_annotations: Path,
    train_images: Path,
    val_annotations: Path,
    val_images: Path,
    output_dir: Path,
    manifest_path: Path,
    train_positive_limit: int = 6000,
    train_negative_limit: int = 1000,
    seed: int = 42,
    download_missing: bool = False,
    download_workers: int = 8,
) -> dict[str, Any]:
    """Create a bounded person subset while preserving raw COCO files."""
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    train_payload = _load_coco(train_annotations)
    val_payload = _load_coco(val_annotations)
    train_index = _index_payload(train_payload)
    val_index = _index_payload(val_payload)
    train_ids = _select_ids(
        *train_index,
        positive_limit=train_positive_limit,
        negative_limit=train_negative_limit,
        seed=seed,
    )
    val_ids, test_ids = _split_val_ids(*val_index, seed=seed)

    downloaded = {"train": 0, "val": 0}
    if download_missing:
        downloaded["train"] = _download_missing_images(
            image_ids=train_ids,
            images=train_index[0],
            destination=train_images,
            workers=download_workers,
        )
        downloaded["val"] = _download_missing_images(
            image_ids=sorted([*val_ids, *test_ids]),
            images=val_index[0],
            destination=val_images,
            workers=download_workers,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        train_stats = _materialize_split(
            image_ids=train_ids,
            images=train_index[0],
            boxes=train_index[1],
            source_images=train_images,
            output_dir=output_dir,
            split="train",
        )
        val_stats = _materialize_split(
            image_ids=val_ids,
            images=val_index[0],
            boxes=val_index[1],
            source_images=val_images,
            output_dir=output_dir,
            split="val",
        )
        test_stats = _materialize_split(
            image_ids=test_ids,
            images=val_index[0],
            boxes=val_index[1],
            source_images=val_images,
            output_dir=output_dir,
            split="test",
        )
        (output_dir / "dataset.yaml").write_text(
            f"path: {output_dir.resolve().as_posix()}\n"
            "train: images/train\nval: images/val\ntest: images/test\n\n"
            "names:\n  0: smoke\n  1: fire\n  2: person\n",
            encoding="utf-8",
        )
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": "COCO 2017 person subset for unified indoor detection",
            "source": {
                "homepage": "https://cocodataset.org/",
                "annotation_license": "CC-BY-4.0",
                "image_license": "Per-image Flickr license recorded by COCO",
                "train_annotations": {
                    "path": train_annotations.resolve().as_posix(),
                    "sha256": sha256_file(train_annotations),
                },
                "val_annotations": {
                    "path": val_annotations.resolve().as_posix(),
                    "sha256": sha256_file(val_annotations),
                },
            },
            "selection": {
                "seed": seed,
                "train_positive_limit": train_positive_limit,
                "train_negative_limit": train_negative_limit,
                "crowd_only_images_excluded": True,
                "val2017_partition": "alternating shuffled positive and negative ids",
                "downloaded_missing_images": downloaded,
                "image_ids": {"train": train_ids, "val": val_ids, "test": test_ids},
            },
            "output": {
                "class_names": ["smoke", "fire", "person"],
                "annotation_scope": ["person"],
                "splits": {"train": train_stats, "val": val_stats, "test": test_stats},
            },
        }
        _write_json(output_dir / "manifest.json", manifest)
        _write_json(manifest_path, manifest)
        return manifest
    except Exception:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a bounded COCO person subset")
    parser.add_argument("--train-annotations", type=Path, required=True)
    parser.add_argument("--train-images", type=Path, required=True)
    parser.add_argument("--val-annotations", type=Path, required=True)
    parser.add_argument("--val-images", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--train-positive-limit", type=int, default=6000)
    parser.add_argument("--train-negative-limit", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--download-workers", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = prepare_coco_person(
        train_annotations=args.train_annotations,
        train_images=args.train_images,
        val_annotations=args.val_annotations,
        val_images=args.val_images,
        output_dir=args.output_dir,
        manifest_path=args.manifest,
        train_positive_limit=args.train_positive_limit,
        train_negative_limit=args.train_negative_limit,
        seed=args.seed,
        download_missing=args.download_missing,
        download_workers=args.download_workers,
    )
    print(json.dumps(manifest["output"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
