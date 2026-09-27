import pytest

from smoke_detection.benchmark import percentile


def test_percentile_uses_sorted_nearest_rank() -> None:
    assert percentile([10.0, 2.0, 6.0, 4.0, 8.0], 0.5) == 6.0
    assert percentile([10.0, 2.0, 6.0, 4.0, 8.0], 0.95) == 10.0


def test_percentile_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        percentile([], 0.5)
