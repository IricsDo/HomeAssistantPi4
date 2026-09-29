"""Unified indoor smoke, fire and person detection package."""

from indoor_detection.domain import BoundingBox, Detection, DetectionClass
from indoor_detection.temporal import (
    ClassDecision,
    IndoorDecision,
    MultiClassTemporalFilter,
    TemporalPolicy,
)

__all__ = [
    "BoundingBox",
    "ClassDecision",
    "Detection",
    "DetectionClass",
    "IndoorDecision",
    "MultiClassTemporalFilter",
    "TemporalPolicy",
]

__version__ = "0.2.0"
