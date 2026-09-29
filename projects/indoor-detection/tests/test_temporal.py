import pytest

from indoor_detection.domain import BoundingBox, Detection, DetectionClass
from indoor_detection.temporal import MultiClassTemporalFilter, TemporalPolicy


def detection(
    frame_index: int,
    target_class: DetectionClass,
    confidence: float = 0.8,
) -> Detection:
    return Detection(
        box=BoundingBox(10, 20, 30, 60),
        confidence=confidence,
        frame_index=frame_index,
        class_id=list(DetectionClass).index(target_class),
        target_class=target_class,
    )


def test_smoke_fire_and_person_use_independent_windows() -> None:
    temporal_filter = MultiClassTemporalFilter()

    first = temporal_filter.update(
        frame_index=0,
        detections=[
            detection(0, DetectionClass.SMOKE),
            detection(0, DetectionClass.FIRE),
            detection(0, DetectionClass.PERSON),
        ],
    )
    assert not first.for_class(DetectionClass.SMOKE).confirmed
    assert not first.for_class(DetectionClass.FIRE).confirmed
    assert first.person_present

    second = temporal_filter.update(
        frame_index=1,
        detections=[
            detection(1, DetectionClass.SMOKE),
            detection(1, DetectionClass.FIRE),
            detection(1, DetectionClass.PERSON),
        ],
    )
    assert not second.for_class(DetectionClass.SMOKE).confirmed
    assert second.for_class(DetectionClass.FIRE).confirmed
    assert second.occupied_hazard

    third = temporal_filter.update(
        frame_index=2,
        detections=[detection(2, DetectionClass.SMOKE)],
        low_image_quality=True,
    )
    assert third.for_class(DetectionClass.SMOKE).confirmed
    assert third.low_image_quality
    assert not third.person_present


def test_class_threshold_does_not_leak_between_tasks() -> None:
    temporal_filter = MultiClassTemporalFilter(
        {
            DetectionClass.SMOKE: TemporalPolicy(1, 1, 0.2),
            DetectionClass.FIRE: TemporalPolicy(1, 1, 0.6),
            DetectionClass.PERSON: TemporalPolicy(1, 1, 0.4),
        }
    )

    decision = temporal_filter.update(
        frame_index=0,
        detections=[
            detection(0, DetectionClass.SMOKE, 0.3),
            detection(0, DetectionClass.FIRE, 0.3),
            detection(0, DetectionClass.PERSON, 0.3),
        ],
    )

    assert decision.active_classes == {DetectionClass.SMOKE}


@pytest.mark.parametrize(
    ("window_size", "minimum_positive_frames"),
    [(0, 1), (3, 0), (3, 4)],
)
def test_rejects_invalid_policy(
    window_size: int,
    minimum_positive_frames: int,
) -> None:
    with pytest.raises(ValueError):
        TemporalPolicy(window_size, minimum_positive_frames, 0.2)
