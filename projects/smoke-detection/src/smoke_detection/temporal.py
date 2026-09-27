"""Temporal confirmation for recall-oriented smoke alerts."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from smoke_detection.domain import SmokeDetection


@dataclass(frozen=True, slots=True)
class FrameObservation:
    frame_index: int
    detections: tuple[SmokeDetection, ...]
    low_image_quality: bool

    @property
    def positive(self) -> bool:
        return bool(self.detections)


@dataclass(frozen=True, slots=True)
class TemporalDecision:
    """Aggregated smoke state over the current temporal window."""

    confirmed: bool
    positive_frames: int
    observed_frames: int
    confidence: float
    selected_detection: SmokeDetection | None
    low_image_quality: bool

    @property
    def estimated_origin(self) -> tuple[float, float] | None:
        if self.selected_detection is None:
            return None
        return self.selected_detection.estimated_origin


class TemporalSmokeFilter:
    """Confirm smoke when enough recent frames contain a qualified detection."""

    def __init__(
        self,
        *,
        window_size: int = 5,
        minimum_positive_frames: int = 3,
        confidence_threshold: float = 0.20,
    ) -> None:
        if window_size < 1:
            raise ValueError("window_size must be at least 1")
        if not 1 <= minimum_positive_frames <= window_size:
            raise ValueError("minimum_positive_frames must be between 1 and window_size")
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1")

        self.window_size = window_size
        self.minimum_positive_frames = minimum_positive_frames
        self.confidence_threshold = confidence_threshold
        self._history: deque[FrameObservation] = deque(maxlen=window_size)

    def reset(self) -> None:
        self._history.clear()

    def update(
        self,
        *,
        frame_index: int,
        detections: Sequence[SmokeDetection],
        low_image_quality: bool = False,
    ) -> TemporalDecision:
        qualified = tuple(
            detection
            for detection in detections
            if detection.confidence >= self.confidence_threshold
        )
        self._history.append(
            FrameObservation(
                frame_index=frame_index,
                detections=qualified,
                low_image_quality=low_image_quality,
            )
        )

        positive_frames = sum(observation.positive for observation in self._history)
        candidates = [
            detection
            for observation in self._history
            for detection in observation.detections
        ]
        selected = max(candidates, key=lambda item: item.confidence, default=None)

        return TemporalDecision(
            confirmed=positive_frames >= self.minimum_positive_frames,
            positive_frames=positive_frames,
            observed_frames=len(self._history),
            confidence=selected.confidence if selected is not None else 0.0,
            selected_detection=selected,
            low_image_quality=any(item.low_image_quality for item in self._history),
        )
