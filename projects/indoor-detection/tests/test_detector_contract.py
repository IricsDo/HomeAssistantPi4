import pytest

from indoor_detection.detector import InvalidDetectionModelError, UltralyticsIndoorDetector
from indoor_detection.domain import DetectionClass


def test_accepts_exactly_smoke_fire_and_person() -> None:
    class_map = UltralyticsIndoorDetector._validate_model_names(
        {0: "smoke", 1: "fire", 2: "person"}
    )

    assert class_map == {
        0: DetectionClass.SMOKE,
        1: DetectionClass.FIRE,
        2: DetectionClass.PERSON,
    }


def test_accepts_class_order_defined_by_model() -> None:
    class_map = UltralyticsIndoorDetector._validate_model_names(
        ["person", "smoke", "fire"]
    )

    assert class_map[0] is DetectionClass.PERSON


@pytest.mark.parametrize(
    "names",
    [
        {0: "smoke"},
        {0: "smoke", 1: "fire"},
        {0: "smoke", 1: "fire", 2: "cat"},
        {0: "smoke", 1: "fire", 2: "person", 3: "cat"},
    ],
)
def test_rejects_models_that_do_not_match_contract(names: dict[int, str]) -> None:
    with pytest.raises(InvalidDetectionModelError):
        UltralyticsIndoorDetector._validate_model_names(names)


def test_class_thresholds_are_independent() -> None:
    thresholds = UltralyticsIndoorDetector._normalize_thresholds({"person": 0.5})

    assert thresholds[DetectionClass.SMOKE] == 0.20
    assert thresholds[DetectionClass.FIRE] == 0.25
    assert thresholds[DetectionClass.PERSON] == 0.5
