"""Dependency-free domain objects used by inference and tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Axis-aligned bounding box in source-image pixels."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        if self.x2 < self.x1 or self.y2 < self.y1:
            raise ValueError("Bounding box maximums must not be smaller than minimums")

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def estimated_origin(self) -> tuple[float, float]:
        """Return the bottom-center smoke-origin heuristic."""

        return ((self.x1 + self.x2) / 2.0, self.y2)

    def as_xyxy(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass(frozen=True, slots=True)
class SmokeDetection:
    """One smoke detection produced for a video frame or image."""

    box: BoundingBox
    confidence: float
    frame_index: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Detection confidence must be between 0 and 1")
        if self.frame_index < 0:
            raise ValueError("Frame index must be non-negative")

    @property
    def estimated_origin(self) -> tuple[float, float]:
        return self.box.estimated_origin
