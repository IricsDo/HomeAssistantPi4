"""Audit train-only annotation coverage; image-relative sizes remain unverified."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from indoor_detection.crowdhuman_assessment import _valid_box, assess_annotations
from indoor_detection.crowdhuman_pilot import REVISION
from indoor_detection.dataset import DatasetValidationError, sha256_file


def assess_coverage(annotations: Path, previous_plans: list[Path]) -> dict[str, Any]:
    """Retain the previous conservative whole-image filters and exclude attempted IDs."""
    audit = assess_annotations(annotations)
    eligible = {r["image_id"] for r in audit["records"] if r["provisionally_eligible"]}
    excluded: set[str] = set()
    bindings = []
    for path in previous_plans:
        plan = json.loads(path.read_text(encoding="utf-8"))
        if plan.get("annotation_sha256") != audit["annotation_sha256"]:
            raise DatasetValidationError("Previous plan annotation hash mismatch")
        ids = plan.get("image_ids", [])
        if (not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids)
                or len(ids) != len(set(ids)) or len(ids) != plan.get("sample_size")):
            raise DatasetValidationError("Invalid previous plan IDs")
        excluded.update(ids)
        bindings.append({"path": str(path.resolve()), "sha256": sha256_file(path)})
    known = {r["image_id"] for r in audit["records"]}
    if not excluded <= known:
        raise DatasetValidationError("Previous plan IDs absent from annotations")
    counts: Counter[str] = Counter()
    rows = []
    for line in annotations.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        image_id = row["ID"]
        if image_id not in eligible:
            continue
        if image_id in excluded:
            counts["previously_attempted_eligible_images"] += 1
            continue
        boxes = row["gtboxes"]
        heads = [b.get("hbox") for b in boxes]
        if not all(_valid_box(h) for h in heads):
            counts["invalid_head_excluded"] += 1
            continue
        suspicious = False
        for index, (x, y, w, h) in enumerate(heads):
            for X, Y, W, H in heads[:index]:
                intersection = (max(0, min(x + w, X + W) - max(x, X))
                                * max(0, min(y + h, Y + H) - max(y, Y)))
                if intersection / min(w * h, W * H) >= 0.5:
                    suspicious = True
                    break
            if suspicious:
                break
        if suspicious:
            counts["head_overlap_excluded"] += 1
            continue
        visible = [b["vbox"] for b in boxes]
        span_w = max(x + w for x, y, w, h in visible) - min(b[0] for b in visible)
        span_h = max(y + h for x, y, w, h in visible) - min(b[1] for b in visible)
        # This envelope is NOT the image boundary, and boxes are NOT clipped here.
        ratios = [w * h / (span_w * span_h) for x, y, w, h in visible]
        proxy_small = sum(r < 0.01 for r in ratios)
        share = proxy_small / len(boxes)
        stratum = ("high" if proxy_small >= 3 and share >= 0.30 else
                   "some" if proxy_small >= 1 else "none")
        pixel_small = sum(w * h < 32 ** 2 for x, y, w, h in visible)
        occluded = sum(b.get("extra", {}).get("occ", 0) != 0 for b in boxes)
        counts["remaining_images"] += 1
        counts["person_boxes"] += len(boxes)
        counts["envelope_proxy_small_boxes"] += proxy_small
        counts["raw_area_below_1024_px_boxes"] += pixel_small
        counts["occluded_boxes"] += occluded
        counts[f"stratum_{stratum}_images"] += 1
        rows.append({"image_id": image_id, "person_boxes": len(boxes),
                     "envelope_proxy_small_boxes": proxy_small,
                     "envelope_proxy_small_share": share, "stratum": stratum,
                     "raw_area_below_1024_px_boxes": pixel_small,
                     "occluded_boxes": occluded, "visible_envelope_width": span_w,
                     "visible_envelope_height": span_h})
    return {"schema_version": 1, "training_allowed": False,
            "annotation_sha256": audit["annotation_sha256"],
            "annotation_counts": audit["counts"], "previous_plans": bindings,
            "previous_attempted_ids": sorted(excluded), "counts": dict(counts),
            "records": sorted(rows, key=lambda r: r["image_id"]),
            "image_relative_sizes_verified": False,
            "limitations": ["ODGT has no image dimensions; envelope ratio is a ranking proxy",
                            "Raw pixel area is source-resolution dependent",
                            "No clipping, image decode, completeness or duplicate gate",
                            "Head-overlap filter can exclude valid occluded crowds"]}


def freeze_plan(report_path: Path, quotas: dict[str, int], *, seed: int = 45) -> dict[str, Any]:
    """Freeze a bounded diagnostic pilot, never approve conversion or training."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if set(quotas) != {"high", "some", "none"} or any(
            type(n) is not int or n < 0 for n in quotas.values()) or sum(quotas.values()) < 1:
        raise DatasetValidationError("Invalid stratum quotas")
    rng = random.Random(seed)
    ids = []
    population = {}
    for name in ("high", "some", "none"):
        pool = sorted(r["image_id"] for r in report["records"] if r["stratum"] == name)
        if len(pool) != len(set(pool)) or quotas[name] > len(pool):
            raise DatasetValidationError("Quota exceeds unique stratum population")
        population[name] = len(pool)
        ids.extend(rng.sample(pool, quotas[name]))
    if len(ids) != len(set(ids)) or set(ids) & set(report["previous_attempted_ids"]):
        raise DatasetValidationError("Selected IDs overlap previous intake or each other")
    return {"schema_version": 1, "training_allowed": False, "revision": REVISION,
            "annotation_sha256": report["annotation_sha256"],
            "coverage_sha256": sha256_file(report_path), "seed": seed,
            "sample_size": len(ids), "population_size": len(report["records"]),
            "image_ids": ids, "stratum_quotas": quotas, "stratum_population": population,
            "visual_spotcheck_ids": ids, "visual_review_required": "All pilot images",
            "selection": f"Sorted train IDs, Random({seed}), high/some/none envelope-proxy strata",
            "stop_condition": "Any new systematic completeness/box problem stops conversion; "
                              "no expansion if accepted clipped vboxes have <30% boxes with "
                              "area/image_area <1%; report each stratum separately",
            "actual_size_gate": {"small_area_fraction": 0.01,
                                 "minimum_accepted_small_box_share": 0.30},
            "limitations": report["limitations"],
            "next_steps": ["Acquire pinned train members; decode actual dimensions",
                           "Audit clipped vboxes and actual size distribution",
                           "Review all pilot annotations, exact/near corpus+holdout overlap",
                           "No automatic expansion or training; record go/no-go first"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--previous-plan", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(args.output)
    report = assess_coverage(args.annotations, args.previous_plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
