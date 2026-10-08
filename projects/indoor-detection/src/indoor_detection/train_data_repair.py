"""Build a train-only derivative from explicit, hash-bound review decisions."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml
from PIL import Image

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import parse_yolo_label, sha256_file
from indoor_detection.joint_dataset import TARGET_NAMES, _label_for_image
from indoor_detection.partial_label_training import resolve_scope_manifest


def rotate_raw_box_8(row: list[str]) -> list[str]:
    """EXIF 8: (x, y) -> (y, 1-x), including width/height exchange."""
    x, y, width, height = map(float, row[1:])
    return [row[0], *(f"{value:.12f}" for value in (y, 1 - x, height, width))]


def build_train_derivative(data: Path, review: Path, output: Path) -> dict[str, Any]:
    data, review, output = data.resolve(), review.resolve(), output.resolve()
    config = yaml.safe_load(data.read_text(encoding="utf-8-sig"))
    if config.get("names") not in (TARGET_NAMES, dict(enumerate(TARGET_NAMES))):
        raise ValueError("Canonical smoke/fire/person mapping required")
    config["yaml_file"] = str(data)
    scope_path = resolve_scope_manifest(config)
    scope = json.loads(scope_path.read_text(encoding="utf-8-sig"))
    splits = {split: _resolve_split(data, split) for split in SPLITS}
    train = {path.resolve().as_posix() for path in splits["train"]}
    held = {path.resolve().as_posix() for split in ("val", "test") for path in splits[split]}
    review_document = json.loads(review.read_text(encoding="utf-8"))
    for path, field in ((data, "source_yaml_sha256"), (scope_path, "source_scope_sha256")):
        if sha256_file(path) != review_document[field]:
            raise ValueError(f"Source binding changed: {path}")
    if review_document.get("status") != "APPROVED_DERIVATIVE_ONLY":
        raise ValueError("Final derivative-only approval required")
    decisions = review_document["entries"]
    if not decisions:
        raise ValueError("Empty review")
    seen: set[str] = set()
    seen_ids: set[str] = set()
    benchmark_indexes: dict[str, Path] = {}
    for split in SPLITS:
        index = data.parent / config[split]
        lines = [Path(line) for line in index.read_text(encoding="utf-8-sig").splitlines()
                 if line]
        if not all(path.is_absolute() for path in lines) or (
            sorted(path.resolve() for path in lines) != splits[split]
        ):
            raise ValueError("Absolute unique source indexes required")
        benchmark_indexes[split] = index
        splits[split] = [path.resolve() for path in lines]
    approved: list[tuple[dict[str, Any], Path, Path, list[list[str]], list[str]]] = []
    # Validate every decision before creating any output.
    for decision in decisions:
        stem = decision["id"]
        if Path(stem).name != stem or stem in {".", ".."} or stem in seen_ids:
            raise ValueError("Invalid or duplicate review ID")
        seen_ids.add(stem)
        image = Path(decision["image"]).resolve()
        key = image.as_posix()
        label = _label_for_image(image)
        if key not in train or key in held or key in seen:
            raise ValueError(f"Review must contain unique train-only members: {key}")
        seen.add(key)
        if Path(decision["label"]).resolve() != label:
            raise ValueError("Label path does not match image")
        for path, field in ((image, "image_sha256"), (label, "label_sha256")):
            if sha256_file(path) != decision[field]:
                raise ValueError(f"Source hash changed: {path}")
        if decision.get("review_status") != "REVIEWED" or not decision.get("reason"):
            raise ValueError("Completed review and reason required")
        action = decision["action"]
        if action not in {"keep", "replace_fire", "unknown_fire", "orient_raw"}:
            raise ValueError("Unsupported review action")
        rows = parse_yolo_label(label.read_text(encoding="utf-8-sig"), {0, 1, 2})
        known = list(scope["images"][key])
        with Image.open(image) as raster:
            orientation = raster.getexif().get(274, 1)
        if action == "orient_raw":
            if orientation != 8 or decision.get("coordinate_basis") != "raw_confirmed":
                raise ValueError("Raw-coordinate orientation8 must be individually confirmed")
            rows = [rotate_raw_box_8(row) for row in rows]
        elif orientation != 1:
            raise ValueError("Nontrivial EXIF requires explicit coordinate review")
        if action == "replace_fire":
            replacement = parse_yolo_label(decision["fire_rows"], {1})
            if not replacement or "fire" not in known:
                raise ValueError("Replacement requires fire boxes and known fire scope")
            rows = [row for row in rows if int(row[0]) != 1] + replacement
        if action == "unknown_fire":
            known = [name for name in known if name != "fire"]
            if not known:
                raise ValueError("Cannot remove every known class")
            rows = [row for row in rows if int(row[0]) != 1]
        # Validate transformed rows too; do not clamp or discard small boxes.
        parse_yolo_label("\n".join(" ".join(row) for row in rows), {0, 1, 2})
        if action in {"orient_raw", "replace_fire"}:
            for row in rows:
                x, y, width, height = map(float, row[1:])
                if min(x - width / 2, y - height / 2) < -1e-9 or max(
                    x + width / 2, y + height / 2
                ) > 1 + 1e-9:
                    raise ValueError("Repaired box extends beyond raster")
        approved.append((decision, image, label, rows, known))
    if output.exists():
        raise FileExistsError(f"Derivative already exists: {output}")
    output.mkdir(parents=True)
    remap: dict[str, str] = {}
    receipts: list[dict[str, Any]] = []
    for decision, image, label, rows, known in approved:
        if decision["action"] == "keep":
            continue
        stem = decision["id"]
        destination = output / "images" / "train" / f"{stem}{image.suffix}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        parity: bool | None = None
        if decision["action"] == "orient_raw":
            destination = destination.with_suffix(".png")
            pixels = cv2.imread(str(image))
            if pixels is None or not cv2.imwrite(str(destination), pixels):
                raise ValueError(f"Cannot write oriented image: {image}")
            parity = bool(np.array_equal(pixels, cv2.imread(str(destination))))
            if not parity:
                raise ValueError("Oriented pixel parity failed")
            with Image.open(destination) as raster:
                if raster.getexif().get(274, 1) != 1:
                    raise ValueError("Residual EXIF orientation")
        else:
            shutil.copyfile(image, destination)
        new_label = _label_for_image(destination)
        new_label.parent.mkdir(parents=True, exist_ok=True)
        new_label.write_text("".join(" ".join(row) + "\n" for row in rows), encoding="utf-8")
        remap[image.as_posix()] = destination.as_posix()
        del scope["images"][image.as_posix()]
        scope["images"][destination.as_posix()] = known
        receipts.append({**decision, "output_image": destination.as_posix(),
                         "output_label": new_label.as_posix(), "known_classes": known,
                         "before_rows": label.read_text(encoding="utf-8-sig"),
                         "after_rows": new_label.read_text(encoding="utf-8"),
                         "output_image_sha256": sha256_file(destination),
                         "output_label_sha256": sha256_file(new_label), "pixel_parity": parity})
    for split in SPLITS:
        # The existing joint indexes are absolute; preserve benchmark index bytes.
        if split in {"val", "test"}:
            shutil.copyfile(benchmark_indexes[split], output / f"{split}.txt")
        else:
            (output / "train.txt").write_text("".join(
                remap.get(path.resolve().as_posix(), path.resolve().as_posix()) + "\n"
                for path in splits[split]), encoding="utf-8")
    (output / "class_scope_manifest.json").write_text(json.dumps(scope, indent=2) + "\n")
    new_config = {"path": output.as_posix(), "train": "train.txt", "val": "val.txt",
                  "test": "test.txt", "class_scope_manifest": "class_scope_manifest.json",
                  "names": dict(enumerate(TARGET_NAMES))}
    (output / "dataset.yaml").write_text(yaml.safe_dump(new_config, sort_keys=False))
    result = {"owner": "OpenAI Codex", "training_allowed": False,
              "source_yaml": data.as_posix(), "source_yaml_sha256": sha256_file(data),
              "review": review.as_posix(), "review_sha256": sha256_file(review),
              "reviewed": len(decisions), "changed": len(receipts), "receipts": receipts}
    (output / "repair_receipts.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_train_derivative(args.data, args.review, args.output)
    print(json.dumps({key: value for key, value in result.items() if key != "receipts"}))


if __name__ == "__main__":
    main()
