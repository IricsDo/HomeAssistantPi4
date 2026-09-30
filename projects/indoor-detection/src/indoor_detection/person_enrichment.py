"""Apply reviewed person boxes to an immutable smoke/fire dataset derivative."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from indoor_detection.compose_dataset import SPLITS, _resolve_split
from indoor_detection.dataset import sha256_file
from indoor_detection.person_consensus import _box_iou
from indoor_detection.person_review import _candidate_id


def _source_label_path(image_path: Path) -> Path:
    parts = list(image_path.parts)
    try:
        index = len(parts) - 1 - parts[::-1].index("images")
    except ValueError as error:
        raise ValueError(f"Image path has no 'images' component: {image_path}") from error
    parts[index] = "labels"
    return Path(*parts).with_suffix(".txt")


def _load_decisions(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Decisions TSV not found: {path}")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    required = {
        "candidate_id",
        "source",
        "candidate_index",
        "split",
        "decision",
        "image",
        "xywhn",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Decisions TSV must contain columns: {sorted(required)}")

    candidate_ids = [row["candidate_id"] for row in rows]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Decisions TSV contains duplicate candidate_id values")
    pending = [row["candidate_id"] for row in rows if row["decision"] not in {"accept", "reject"}]
    if pending:
        raise ValueError(f"Review is incomplete: {len(pending)} candidate decisions are pending")

    parsed: list[dict[str, Any]] = []
    for row in rows:
        try:
            xywhn = [float(value) for value in json.loads(row["xywhn"])]
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid xywhn for candidate {row['candidate_id']}") from error
        if len(xywhn) != 4 or not all(0 <= value <= 1 for value in xywhn):
            raise ValueError(f"Invalid normalized box for candidate {row['candidate_id']}")
        x_center, y_center, width, height = xywhn
        if (
            width <= 0
            or height <= 0
            or x_center - width / 2 < 0
            or y_center - height / 2 < 0
            or x_center + width / 2 > 1
            or y_center + height / 2 > 1
        ):
            raise ValueError(f"Invalid normalized box for candidate {row['candidate_id']}")
        try:
            candidate_index = int(row["candidate_index"])
        except ValueError as error:
            raise ValueError(
                f"Invalid candidate_index for candidate {row['candidate_id']}"
            ) from error
        expected_id = _candidate_id(row["image"], row["source"], candidate_index, xywhn)
        if row["candidate_id"] != expected_id:
            raise ValueError(f"Candidate integrity check failed for {row['candidate_id']}")
        parsed.append({**row, "xywhn": xywhn})
    return parsed


def _validate_accepted_boxes(rows: list[dict[str, Any]]) -> None:
    accepted: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["decision"] == "accept":
            accepted[row["image"]].append(row)
    for image, image_rows in accepted.items():
        for index, left in enumerate(image_rows):
            for right in image_rows[index + 1 :]:
                if _box_iou(left["xywhn"], right["xywhn"]) >= 0.90:
                    raise ValueError(
                        "Accepted candidates overlap as duplicates for "
                        f"{image}: {left['candidate_id']} and {right['candidate_id']}"
                    )


def _link_or_copy(source: Path, destination: Path) -> str:
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def _output_name(image_path: Path) -> str:
    digest = hashlib.sha256(image_path.resolve().as_posix().encode("utf-8")).hexdigest()[:12]
    return f"{digest}_{image_path.name}"


def apply_person_decisions(
    *, source_dataset_yaml: Path, decisions_path: Path, output_dir: Path
) -> dict[str, Any]:
    if not source_dataset_yaml.is_file():
        raise FileNotFoundError(f"Source dataset YAML not found: {source_dataset_yaml}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")

    decisions = _load_decisions(decisions_path)
    _validate_accepted_boxes(decisions)
    split_images = {split: _resolve_split(source_dataset_yaml, split) for split in SPLITS}
    split_by_image = {
        image.resolve(): split for split, images in split_images.items() for image in images
    }
    accepted_by_image: dict[Path, list[list[float]]] = defaultdict(list)
    for row in decisions:
        image = Path(row["image"]).resolve()
        actual_split = split_by_image.get(image)
        if actual_split is None:
            raise ValueError(f"Decision references image outside source dataset: {image}")
        if row["split"] != actual_split:
            raise ValueError(
                f"Decision split mismatch for {image}: {row['split']} != {actual_split}"
            )
        if row["decision"] == "accept":
            accepted_by_image[image].append(row["xywhn"])

    transfer_counts: Counter[str] = Counter()
    split_stats: dict[str, dict[str, int]] = {}
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        image_output = output_dir / "images" / split
        label_output = output_dir / "labels" / split
        image_output.mkdir(parents=True, exist_ok=True)
        label_output.mkdir(parents=True, exist_ok=True)
        person_boxes = 0
        images_with_person = 0
        for image in split_images[split]:
            image = image.resolve()
            output_name = _output_name(image)
            transfer_counts[_link_or_copy(image, image_output / output_name)] += 1
            source_label = _source_label_path(image)
            existing = (
                source_label.read_text(encoding="utf-8-sig") if source_label.is_file() else ""
            )
            if existing and not existing.endswith("\n"):
                existing += "\n"
            accepted = accepted_by_image.get(image, [])
            appended = "".join(
                "2 " + " ".join(f"{value:.6f}" for value in xywhn) + "\n" for xywhn in accepted
            )
            (label_output / Path(output_name).with_suffix(".txt")).write_text(
                existing + appended, encoding="utf-8"
            )
            person_boxes += len(accepted)
            images_with_person += bool(accepted)
        split_stats[split] = {
            "images": len(split_images[split]),
            "images_with_reviewed_person": images_with_person,
            "reviewed_person_boxes": person_boxes,
        }

    (output_dir / "dataset.yaml").write_text(
        f"path: {output_dir.resolve().as_posix()}\n"
        "train: images/train\nval: images/val\ntest: images/test\n\n"
        "names:\n  0: smoke\n  1: fire\n  2: person\n",
        encoding="utf-8",
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": "Smoke/fire corpus enriched with reviewed person boxes",
        "source_dataset_yaml": source_dataset_yaml.resolve().as_posix(),
        "decisions": {
            "path": decisions_path.resolve().as_posix(),
            "sha256": sha256_file(decisions_path),
            "accepted": sum(row["decision"] == "accept" for row in decisions),
            "rejected": sum(row["decision"] == "reject" for row in decisions),
        },
        "transfer": dict(sorted(transfer_counts.items())),
        "splits": split_stats,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a person-enriched immutable dataset derivative"
    )
    parser.add_argument("--source-data", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = apply_person_decisions(
        source_dataset_yaml=args.source_data,
        decisions_path=args.decisions,
        output_dir=args.output_dir,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
