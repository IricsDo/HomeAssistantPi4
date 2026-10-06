"""Annotation geometry diagnostics; these counts never change labels or gates."""

from collections.abc import Sequence

from indoor_detection.error_analysis import Detection, box_iou


def fire_box_geometry(
    boxes: Sequence[Detection], width: int, height: int, imgsz: int = 768
) -> dict[str, int]:
    if min(width, height, imgsz) <= 0:
        raise ValueError("Image/input dimensions must be positive")
    scale = imgsz / max(width, height)
    areas = [(b.xyxy[2] - b.xyxy[0]) * (b.xyxy[3] - b.xyxy[1]) for b in boxes]
    if any(area <= 0 for area in areas):
        raise ValueError("Ground truth boxes must have positive area")
    result = {
        "boxes": len(boxes), "small_lt_1pct": 0, "short_side_le_12": 0,
        "overlap_iou_ge_50_pairs": 0, "containment_ge_90_pairs": 0,
    }
    for box, area in zip(boxes, areas, strict=True):
        result["small_lt_1pct"] += area / (width * height) < .01
        result["short_side_le_12"] += min(
            box.xyxy[2] - box.xyxy[0], box.xyxy[3] - box.xyxy[1]) * scale <= 12
    for i, left in enumerate(boxes):
        for j in range(i + 1, len(boxes)):
            right = boxes[j]
            result["overlap_iou_ge_50_pairs"] += box_iou(left, right) >= .5
            intersection = (max(0, min(left.xyxy[2], right.xyxy[2])
                                - max(left.xyxy[0], right.xyxy[0]))
                            * max(0, min(left.xyxy[3], right.xyxy[3])
                                  - max(left.xyxy[1], right.xyxy[1])))
            result["containment_ge_90_pairs"] += intersection / min(areas[i], areas[j]) >= .9
    return result
