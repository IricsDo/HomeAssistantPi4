from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from indoor_detection.person_audit import (
    _candidate_rows,
    _chunks,
    _person_class_id,
    _result_records,
)


class Values:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def tolist(self) -> list[object]:
        return self.values


def result(path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        path=str(path),
        boxes=SimpleNamespace(
            cls=Values([0.0, 2.0]),
            conf=Values([0.91, 0.40]),
            xywhn=Values([[0.5, 0.5, 0.2, 0.4], [0.1, 0.2, 0.1, 0.1]]),
        ),
    )


def test_person_class_id_is_resolved_by_name() -> None:
    assert _person_class_id({0: "person", 1: "bicycle"}) == 0
    assert _person_class_id(["cat", "person"]) == 1


def test_person_class_id_rejects_missing_person() -> None:
    with pytest.raises(ValueError, match="person"):
        _person_class_id({0: "cat"})


def test_candidate_rows_keep_only_person_class(tmp_path: Path) -> None:
    rows = _candidate_rows(result(tmp_path / "image.jpg"), person_class_id=0)

    assert rows == [{"confidence": 0.91, "xywhn": [0.5, 0.5, 0.2, 0.4]}]


def test_result_records_mark_low_confidence_for_review(tmp_path: Path) -> None:
    image = (tmp_path / "image.jpg").resolve()

    records = _result_records(
        [result(image)],
        split_by_path={image: "train"},
        person_class_id=2,
        high_confidence_threshold=0.65,
    )

    assert records[0]["status"] == "manual_review"
    assert records[0]["split"] == "train"


def test_result_records_do_not_auto_accept_high_confidence(tmp_path: Path) -> None:
    image = (tmp_path / "image.jpg").resolve()

    records = _result_records(
        [result(image)],
        split_by_path={image: "test"},
        person_class_id=0,
        high_confidence_threshold=0.65,
    )

    assert records[0]["status"] == "high_confidence_review"


def test_chunks_limit_the_number_of_images_loaded_together(tmp_path: Path) -> None:
    paths = [tmp_path / f"{index}.jpg" for index in range(5)]

    assert list(_chunks(paths, 2)) == [paths[:2], paths[2:4], paths[4:]]

    with pytest.raises(ValueError, match="batch"):
        list(_chunks(paths, 0))
