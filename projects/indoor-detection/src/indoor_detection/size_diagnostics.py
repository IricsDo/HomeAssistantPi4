"""Describe existing matches by projected pixel size, without changing eligibility."""

from collections import defaultdict
from typing import Any


def height_bucket(height: float) -> str:
    for limit in (16, 32, 64, 128):
        if height < limit:
            return f"lt_{limit}"
    return "ge_128"


def projected_size_report(records: list[dict[str, Any]], imgsz: int) -> dict[str, Any]:
    if imgsz <= 0:
        raise ValueError("Input size must be positive")
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for record in records:
        longest = max(record["width"], record["height"])
        if min(record["width"], record["height"]) <= 0:
            raise ValueError("Image dimensions must be positive")
        for target in record["ground_truth"]:
            x1, y1, x2, y2 = target["xyxy"]
            if x2 <= x1 or y2 <= y1:
                raise ValueError("Ground truth box must have positive dimensions")
            for size, prefix in ((512, "fixed_512"), (imgsz, "native")):
                width = (x2 - x1) * size / longest
                height = (y2 - y1) * size / longest
                keys = [f"{prefix}/height/{height_bucket(height)}"]
                if width <= 12 and height <= 12:
                    keys.append(f"{prefix}/both_sides_le_12")
                if min(width, height) <= 12:
                    keys.append(f"{prefix}/short_side_le_12")
                for key in keys:
                    counts[key][0] += 1
                    counts[key][1] += not target["missed"]
    return {
        "imgsz": imgsz,
        "projection": "Square letterbox scale before integer rounding; no eligibility filtering",
        "buckets": {
            key: {"targets": total, "recalled": recalled, "recall": recalled / total}
            for key, (total, recalled) in sorted(counts.items())
        },
    }
