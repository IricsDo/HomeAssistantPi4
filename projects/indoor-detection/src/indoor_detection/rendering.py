"""Frame annotation helpers for smoke, fire and person."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from indoor_detection.domain import Detection, DetectionClass
from indoor_detection.temporal import IndoorDecision

COLORS = {
    DetectionClass.SMOKE: (128, 128, 128),
    DetectionClass.FIRE: (0, 0, 255),
    DetectionClass.PERSON: (0, 200, 0),
}


def annotate_frame(
    frame: Any,
    detections: Sequence[Detection],
    decision: IndoorDecision,
    *,
    blur_score: float,
) -> Any:
    import cv2

    annotated = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection.box.as_xyxy())
        color = COLORS[detection.target_class]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            f"{detection.target_class.value} {detection.confidence:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    active = ", ".join(sorted(item.value for item in decision.active_classes))
    status = active.upper() if active else "MONITORING"
    status_color = (0, 0, 255) if decision.hazard_confirmed else (255, 255, 255)
    cv2.putText(
        annotated,
        status,
        (16, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        status_color,
        2,
    )
    if decision.low_image_quality:
        cv2.putText(
            annotated,
            f"LOW IMAGE QUALITY ({blur_score:.1f})",
            (16, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 255),
            2,
        )
    return annotated
