"""Stable JSON representation for unified indoor detection events."""

from __future__ import annotations

from typing import Any

from indoor_detection.domain import DetectionClass
from indoor_detection.temporal import ClassDecision, IndoorDecision


def _class_decision_to_dict(decision: ClassDecision) -> dict[str, Any]:
    selected = decision.selected_detection
    return {
        "confirmed": decision.confirmed,
        "positive_frames": decision.positive_frames,
        "observed_frames": decision.observed_frames,
        "confidence": round(decision.confidence, 6),
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


def decision_to_dict(decision: IndoorDecision, *, frame_index: int) -> dict[str, Any]:
    active = sorted(target_class.value for target_class in decision.active_classes)
    return {
        "schema_version": 2,
        "frame_index": frame_index,
        "active_classes": active,
        "hazard_confirmed": decision.hazard_confirmed,
        "person_present": decision.person_present,
        "occupied_hazard": decision.occupied_hazard,
        "low_image_quality": decision.low_image_quality,
        "classes": {
            target_class.value: _class_decision_to_dict(
                decision.for_class(target_class)
            )
            for target_class in DetectionClass
        },
    }
