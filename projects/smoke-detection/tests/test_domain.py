import pytest

from smoke_detection.domain import BoundingBox, SmokeDetection


def test_bounding_box_estimates_origin_at_bottom_center() -> None:
    box = BoundingBox(10, 20, 30, 60)

    assert box.width == 20
    assert box.height == 40
    assert box.estimated_origin == (20, 60)


def test_bounding_box_rejects_inverted_coordinates() -> None:
    with pytest.raises(ValueError):
        BoundingBox(20, 10, 5, 30)


def test_detection_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        SmokeDetection(BoundingBox(0, 0, 10, 10), confidence=1.01, frame_index=0)
