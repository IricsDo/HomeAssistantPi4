"""Frame annotation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from smoke_detection.domain import SmokeDetection
from smoke_detection.temporal import TemporalDecision


def annotate_frame(
    frame: Any,
    detections: Sequence[SmokeDetection],
    decision: TemporalDecision,
    *,
    blur_score: float,
) -> Any:
    import cv2

    annotated = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection.box.as_xyxy())
        color = (0, 0, 255) if decision.confirmed else (0, 165, 255)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            f"smoke {detection.confidence:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    status = "SMOKE CONFIRMED" if decision.confirmed else "monitoring"
    cv2.putText(
        annotated,
        status,
        (16, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 0, 255) if decision.confirmed else (255, 255, 255),
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
