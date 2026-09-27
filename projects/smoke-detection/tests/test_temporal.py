import pytest

from smoke_detection.domain import BoundingBox, SmokeDetection
from smoke_detection.temporal import TemporalSmokeFilter


def detection(frame_index: int, confidence: float = 0.8) -> SmokeDetection:
    return SmokeDetection(
        box=BoundingBox(10, 20, 30, 60),
        confidence=confidence,
        frame_index=frame_index,
    )


def test_confirms_three_positive_frames_in_five_frame_window() -> None:
    temporal_filter = TemporalSmokeFilter(window_size=5, minimum_positive_frames=3)

    assert not temporal_filter.update(frame_index=0, detections=[detection(0)]).confirmed
    assert not temporal_filter.update(frame_index=1, detections=[]).confirmed
    assert not temporal_filter.update(frame_index=2, detections=[detection(2)]).confirmed
    decision = temporal_filter.update(frame_index=3, detections=[detection(3)])

    assert decision.confirmed
    assert decision.positive_frames == 3
    assert decision.estimated_origin == (20, 60)


def test_expires_old_positive_frames() -> None:
    temporal_filter = TemporalSmokeFilter(window_size=3, minimum_positive_frames=2)
    temporal_filter.update(frame_index=0, detections=[detection(0)])
    assert temporal_filter.update(frame_index=1, detections=[detection(1)]).confirmed

    temporal_filter.update(frame_index=2, detections=[])
    decision = temporal_filter.update(frame_index=3, detections=[])

    assert not decision.confirmed
    assert decision.positive_frames == 1


def test_ignores_detections_below_threshold() -> None:
    temporal_filter = TemporalSmokeFilter(
        window_size=1,
        minimum_positive_frames=1,
        confidence_threshold=0.2,
    )

    decision = temporal_filter.update(frame_index=0, detections=[detection(0, 0.19)])

    assert not decision.confirmed
    assert decision.selected_detection is None


def test_preserves_low_quality_flag_without_suppressing_alert() -> None:
    temporal_filter = TemporalSmokeFilter(window_size=1, minimum_positive_frames=1)

    decision = temporal_filter.update(
        frame_index=0,
        detections=[detection(0)],
        low_image_quality=True,
    )

    assert decision.confirmed
    assert decision.low_image_quality


@pytest.mark.parametrize(
    ("window_size", "minimum_positive_frames"),
    [(0, 1), (3, 0), (3, 4)],
)
def test_rejects_invalid_window_configuration(
    window_size: int,
    minimum_positive_frames: int,
) -> None:
    with pytest.raises(ValueError):
        TemporalSmokeFilter(
            window_size=window_size,
            minimum_positive_frames=minimum_positive_frames,
        )
