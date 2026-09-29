import pytest

from indoor_detection.domain import BoundingBox, Detection, DetectionClass


def detection(target_class: DetectionClass) -> Detection:
    return Detection(
        box=BoundingBox(10, 20, 30, 60),
        confidence=0.8,
        frame_index=0,
        class_id=0,
        target_class=target_class,
    )


def test_bounding_box_exposes_bottom_center() -> None:
    box = BoundingBox(10, 20, 30, 60)

    assert box.width == 20
    assert box.height == 40
    assert box.bottom_center == (20, 60)


def test_only_hazards_have_estimated_origin() -> None:
    assert detection(DetectionClass.SMOKE).estimated_origin == (20, 60)
    assert detection(DetectionClass.FIRE).estimated_origin == (20, 60)
    assert detection(DetectionClass.PERSON).estimated_origin is None


def test_bounding_box_rejects_inverted_coordinates() -> None:
    with pytest.raises(ValueError):
        BoundingBox(20, 10, 5, 30)


def test_detection_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        Detection(
            BoundingBox(0, 0, 10, 10),
            confidence=1.01,
            frame_index=0,
            class_id=0,
            target_class=DetectionClass.SMOKE,
        )
