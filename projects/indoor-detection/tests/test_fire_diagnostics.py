import pytest

from indoor_detection.error_analysis import Detection
from indoor_detection.fire_diagnostics import fire_box_geometry


def test_nested_and_disjoint_boxes_are_diagnostics_only():
    boxes = [Detection((0, 0, 100, 100)), Detection((1, 1, 10, 10)),
             Detection((200, 200, 300, 300))]
    row = fire_box_geometry(boxes, 400, 400)
    assert row["boxes"] == 3
    assert row["containment_ge_90_pairs"] == 1
    assert row["overlap_iou_ge_50_pairs"] == 0
    assert row["small_lt_1pct"] == 1
    assert len(boxes) == 3


def test_same_boxes_and_projected_short_side_boundary():
    boxes = [Detection((0, 0, 10, 10)), Detection((0, 0, 10, 10))]
    row = fire_box_geometry(boxes, 640, 640)
    assert row["overlap_iou_ge_50_pairs"] == 1
    assert row["short_side_le_12"] == 2


@pytest.mark.parametrize("width,height", [(0, 10), (10, -1)])
def test_rejects_invalid_dimensions(width, height):
    with pytest.raises(ValueError):
        fire_box_geometry([], width, height)
