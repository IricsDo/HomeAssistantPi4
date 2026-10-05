"""Assess original CrowdHuman training annotations without converting or training."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from indoor_detection.dataset import DatasetValidationError, sha256_file


def _valid_box(value: Any) -> bool:
    return (isinstance(value, list) and len(value) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                    and math.isfinite(v) for v in value)
            and value[2] > 0 and value[3] > 0)


def assess_annotations(path: Path) -> dict[str, Any]:
    """Exclude whole images with body ignore regions; head ignore is separate."""
    counts: Counter[str] = Counter()
    records = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetValidationError(f"Invalid JSON at line {line_number}") from exc
            if not isinstance(row, dict):
                raise DatasetValidationError(f"Expected object at line {line_number}")
            image_id = row.get("ID")
            if (not isinstance(image_id, str) or not image_id or image_id in seen
                    or any(c in image_id for c in ("/", "\\", ":")) or image_id in (".", "..")):
                raise DatasetValidationError(f"Invalid or duplicate image ID at {line_number}")
            seen.add(image_id)
            boxes = row.get("gtboxes")
            if not isinstance(boxes, list):
                raise DatasetValidationError(f"Invalid gtboxes: {image_id}")
            ignored = invalid = people = 0
            for box in boxes:
                if not isinstance(box, dict) or box.get("tag") not in ("person", "mask"):
                    raise DatasetValidationError(f"Unknown annotation tag: {image_id}")
                extra = box.get("extra", {})
                head = box.get("head_attr", {})
                if not isinstance(extra, dict) or not isinstance(head, dict):
                    raise DatasetValidationError(f"Invalid attributes: {image_id}")
                for attrs in (extra, head):
                    flag = attrs.get("ignore", 0)
                    if type(flag) is not int or flag not in (0, 1):
                        raise DatasetValidationError(f"Invalid ignore flag: {image_id}")
                body_ignore = box["tag"] == "mask" or extra.get("ignore", 0) == 1
                ignored += int(body_ignore)
                counts["mask_boxes"] += int(box["tag"] == "mask")
                counts["body_ignored_boxes"] += int(body_ignore)
                counts["head_ignored_boxes"] += int(head.get("ignore", 0) == 1)
                counts["body_ignore_key_absent"] += int("ignore" not in extra)
                if body_ignore:
                    continue
                people += 1
                counts["person_boxes"] += 1
                valid = _valid_box(box.get("vbox")) and _valid_box(box.get("fbox"))
                invalid += int(not valid)
                counts["invalid_person_body_boxes"] += int(not valid)
                counts["different_visible_full_boxes"] += int(box.get("vbox") != box.get("fbox"))
                counts["occluded_person_boxes"] += int(extra.get("occ", 0) != 0)
            eligible = ignored == 0 and invalid == 0 and people > 0
            counts["images"] += 1
            counts["images_with_body_ignore"] += int(ignored > 0)
            counts["images_with_invalid_body_box"] += int(invalid > 0)
            counts["provisionally_eligible_images"] += int(eligible)
            records.append({"image_id": image_id, "person_boxes": people,
                            "body_ignored_boxes": ignored, "invalid_body_boxes": invalid,
                            "provisionally_eligible": eligible})
    if not records:
        raise DatasetValidationError("Empty annotations")
    return {"schema_version": 1, "annotation_path": str(path.resolve()),
            "annotation_sha256": sha256_file(path), "counts": dict(counts), "records": records,
            "training_allowed": False,
            "policy": "Whole-image exclusion for body ignore or invalid body geometry",
            "limitations": ["No images inspected by this annotation audit",
                            "No image bounds, completeness, duplicates or domain gate",
                            "Visible/full box compatibility not approved",
                            "Head ignore is not body ignore; absent optional ignore defaults to 0"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite assessment: {args.output}")
    report = assess_annotations(args.annotations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
