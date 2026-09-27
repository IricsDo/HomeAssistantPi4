"""Indoor smoke detection package."""

from smoke_detection.domain import BoundingBox, SmokeDetection
from smoke_detection.temporal import TemporalDecision, TemporalSmokeFilter

__all__ = [
    "BoundingBox",
    "SmokeDetection",
    "TemporalDecision",
    "TemporalSmokeFilter",
]

__version__ = "0.1.0"
