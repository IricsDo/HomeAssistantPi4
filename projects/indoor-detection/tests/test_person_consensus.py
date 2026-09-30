from __future__ import annotations

from types import SimpleNamespace

from indoor_detection.person_consensus import (
    _box_iou,
    _match_candidates,
    _review_status,
    _verifier_rows,
)


def candidate(confidence: float, xywhn: list[float]) -> dict[str, object]:
    return {"confidence": confidence, "xywhn": xywhn}


class Values:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def tolist(self) -> list[object]:
        return self.values


def test_box_iou_uses_normalized_xywh_boxes() -> None:
    assert _box_iou([0.5, 0.5, 0.4, 0.4], [0.5, 0.5, 0.4, 0.4]) == 1.0
    assert _box_iou([0.2, 0.2, 0.1, 0.1], [0.8, 0.8, 0.1, 0.1]) == 0.0


def test_verifier_rows_counts_visible_pose_keypoints() -> None:
    result = SimpleNamespace(
        boxes=SimpleNamespace(
            cls=Values([0.0]),
            conf=Values([0.9]),
            xywhn=Values([[0.5, 0.5, 0.2, 0.4]]),
        ),
        keypoints=SimpleNamespace(conf=Values([[0.9, 0.7, 0.4, 0.1]])),
    )

    rows = _verifier_rows(result, person_class_id=0, keypoint_confidence=0.5)

    assert rows[0]["visible_keypoints"] == 2
    assert rows[0]["mean_visible_keypoint_confidence"] == 0.8


def test_match_candidates_is_one_to_one_and_preserves_verifier_only() -> None:
    primary = [
        candidate(0.8, [0.25, 0.25, 0.2, 0.2]),
        candidate(0.7, [0.75, 0.75, 0.2, 0.2]),
    ]
    verifier = [
        candidate(0.9, [0.25, 0.25, 0.2, 0.2]),
        candidate(0.6, [0.5, 0.5, 0.1, 0.1]),
    ]

    matched, verifier_only = _match_candidates(primary, verifier)

    assert matched[0]["verifier_iou"] == 1.0
    assert matched[0]["verifier_confidence"] == 0.9
    assert matched[1]["verifier_iou"] == 0.0
    assert verifier_only == [verifier[1]]


def test_review_status_never_implies_automatic_acceptance() -> None:
    matched = [
        {
            "verifier_iou": 0.8,
            "verifier_confidence": 0.9,
            "verifier_visible_keypoints": 6,
        }
    ]

    status = _review_status(
        matched,
        [],
        strong_iou=0.5,
        strong_confidence=0.5,
        min_visible_keypoints=4,
    )

    assert status == "consensus_high_review"


def test_review_status_rejects_pose_box_without_enough_visible_keypoints() -> None:
    matched = [
        {
            "verifier_iou": 0.8,
            "verifier_confidence": 0.9,
            "verifier_visible_keypoints": 2,
        }
    ]

    assert (
        _review_status(
            matched,
            [],
            strong_iou=0.5,
            strong_confidence=0.5,
            min_visible_keypoints=4,
        )
        == "disagreement_review"
    )
