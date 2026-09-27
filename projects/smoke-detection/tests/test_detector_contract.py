import pytest

from smoke_detection.detector import InvalidSmokeModelError, UltralyticsSmokeDetector


def test_accepts_exactly_one_smoke_class() -> None:
    class_id = UltralyticsSmokeDetector._validate_model_names({0: "smoke"})

    assert class_id == 0


@pytest.mark.parametrize(
    "names",
    [
        {0: "person"},
        {0: "smoke", 1: "fire"},
        {0: "fire", 1: "person"},
    ],
)
def test_rejects_non_smoke_or_multi_class_models(names: dict[int, str]) -> None:
    with pytest.raises(InvalidSmokeModelError):
        UltralyticsSmokeDetector._validate_model_names(names)
