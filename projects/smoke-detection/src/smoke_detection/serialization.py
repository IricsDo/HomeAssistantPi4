"""Stable JSON representation for smoke events."""

from __future__ import annotations

from typing import Any

from smoke_detection.temporal import TemporalDecision


def decision_to_dict(decision: TemporalDecision, *, frame_index: int) -> dict[str, Any]:
    selected = decision.selected_detection
    return {
        "frame_index": frame_index,
        "smoke_confirmed": decision.confirmed,
        "positive_frames": decision.positive_frames,
        "observed_frames": decision.observed_frames,
        "confidence": round(decision.confidence, 6),
        "low_image_quality": decision.low_image_quality,
        "bounding_box": (
            [round(value, 2) for value in selected.box.as_xyxy()]
            if selected is not None
            else None
        ),
        "estimated_origin": (
            [round(value, 2) for value in decision.estimated_origin]
            if decision.estimated_origin is not None
            else None
        ),
    }
