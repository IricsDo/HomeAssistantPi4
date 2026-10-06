import pytest

from indoor_detection.test_protocol import compare_smoke_membership
from indoor_detection.test_protocol import test_quality_decision as quality_decision


def test_membership_allows_old_superset_including_negatives():
    positive = ("one", ((0.5, 0.5, 0.1, 0.1),))
    negative = ("two", ())
    assert compare_smoke_membership([positive, negative], [positive, negative, ("extra", ())]) == {
        "comparable": True,
        "current_images": 2,
        "baseline_images": 3,
        "baseline_only_images": 1,
    }


@pytest.mark.parametrize(
    "current,baseline",
    [
        ([], [("one", ())]),
        ([("one", ())], []),
        ([("one", ())], [("other", ())]),
        ([("one", ())], [("one", ((0.5, 0.5, 0.1, 0.1),))]),
        ([("one", ()), ("one", ())], [("one", ())]),
    ],
)
def test_membership_rejects_missing_labels_images_or_multiplicity(current, baseline):
    with pytest.raises(ValueError):
        compare_smoke_membership(current, baseline)


def test_test_floors_and_source_regression_are_not_rounded():
    metrics = {
        "smoke": {"recall": 0.9},
        "fire": {"recall": 0.9},
        "person": {"recall": 0.6, "f1": 0.65},
    }
    assert all(quality_decision(metrics, {"all": -0.03, "source": 0}).values())
    metrics["person"]["recall"] = 0.599999
    result = quality_decision(metrics, {"all": 0, "source": -0.030001})
    assert result["person"] is False
    assert result["smoke_regression"] is False
