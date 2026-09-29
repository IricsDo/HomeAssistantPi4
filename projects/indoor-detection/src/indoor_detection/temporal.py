"""Independent temporal policies for smoke, fire and person detections."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from indoor_detection.domain import SUPPORTED_CLASSES, Detection, DetectionClass


@dataclass(frozen=True, slots=True)
class TemporalPolicy:
    window_size: int
    minimum_positive_frames: int
    confidence_threshold: float

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise ValueError("window_size must be at least 1")
        if not 1 <= self.minimum_positive_frames <= self.window_size:
            raise ValueError("minimum_positive_frames must be between 1 and window_size")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1")


DEFAULT_POLICIES: dict[DetectionClass, TemporalPolicy] = {
    DetectionClass.SMOKE: TemporalPolicy(5, 3, 0.20),
    DetectionClass.FIRE: TemporalPolicy(3, 2, 0.25),
    DetectionClass.PERSON: TemporalPolicy(1, 1, 0.35),
}


@dataclass(frozen=True, slots=True)
class FrameObservation:
    frame_index: int
    detections: tuple[Detection, ...]

    @property
    def positive(self) -> bool:
        return bool(self.detections)


@dataclass(frozen=True, slots=True)
class ClassDecision:
    target_class: DetectionClass
    confirmed: bool
    positive_frames: int
    observed_frames: int
    confidence: float
    selected_detection: Detection | None

    @property
    def estimated_origin(self) -> tuple[float, float] | None:
        if self.selected_detection is None:
            return None
        return self.selected_detection.estimated_origin


@dataclass(frozen=True, slots=True)
class IndoorDecision:
    """One frame's aggregate state after applying class-specific policies."""

    by_class: Mapping[DetectionClass, ClassDecision]
    low_image_quality: bool

    def for_class(self, target_class: DetectionClass) -> ClassDecision:
        return self.by_class[target_class]

    @property
    def active_classes(self) -> frozenset[DetectionClass]:
        return frozenset(
            target_class
            for target_class, decision in self.by_class.items()
            if decision.confirmed
        )

    @property
    def hazard_confirmed(self) -> bool:
        return bool(
            self.active_classes & {DetectionClass.SMOKE, DetectionClass.FIRE}
        )

    @property
    def person_present(self) -> bool:
        return DetectionClass.PERSON in self.active_classes

    @property
    def occupied_hazard(self) -> bool:
        return self.hazard_confirmed and self.person_present


class _ClassTemporalFilter:
    def __init__(self, target_class: DetectionClass, policy: TemporalPolicy) -> None:
        self.target_class = target_class
        self.policy = policy
        self._history: deque[FrameObservation] = deque(maxlen=policy.window_size)

    def reset(self) -> None:
        self._history.clear()

    def update(self, *, frame_index: int, detections: Sequence[Detection]) -> ClassDecision:
        qualified = tuple(
            detection
            for detection in detections
            if detection.target_class is self.target_class
            and detection.confidence >= self.policy.confidence_threshold
        )
        self._history.append(FrameObservation(frame_index, qualified))
        positive_frames = sum(item.positive for item in self._history)
        selected = max(
            (detection for item in self._history for detection in item.detections),
            key=lambda item: item.confidence,
            default=None,
        )
        return ClassDecision(
            target_class=self.target_class,
            confirmed=positive_frames >= self.policy.minimum_positive_frames,
            positive_frames=positive_frames,
            observed_frames=len(self._history),
            confidence=selected.confidence if selected else 0.0,
            selected_detection=selected,
        )


class MultiClassTemporalFilter:
    """Apply independent confirmation windows without coupling the three tasks."""

    def __init__(
        self,
        policies: Mapping[DetectionClass, TemporalPolicy] | None = None,
    ) -> None:
        resolved = dict(DEFAULT_POLICIES)
        if policies:
            resolved.update(policies)
        if set(resolved) != SUPPORTED_CLASSES:
            raise ValueError("Policies must cover smoke, fire and person")
        self.policies = resolved
        self._filters = {
            target_class: _ClassTemporalFilter(target_class, policy)
            for target_class, policy in resolved.items()
        }

    def reset(self) -> None:
        for temporal_filter in self._filters.values():
            temporal_filter.reset()

    def update(
        self,
        *,
        frame_index: int,
        detections: Sequence[Detection],
        low_image_quality: bool = False,
    ) -> IndoorDecision:
        return IndoorDecision(
            by_class={
                target_class: temporal_filter.update(
                    frame_index=frame_index,
                    detections=detections,
                )
                for target_class, temporal_filter in self._filters.items()
            },
            low_image_quality=low_image_quality,
        )
