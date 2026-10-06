"""Validate comparable smoke membership before opening a fixed test candidate."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence


def compare_smoke_membership(
    current: Sequence[tuple[str, tuple[tuple[float, ...], ...]]],
    baseline: Sequence[tuple[str, tuple[tuple[float, ...], ...]]],
) -> dict[str, int | bool]:
    """Require every current image and smoke annotation to exist in old test.

    Compare multisets, including negatives and duplicate multiplicity. An old
    test superset is allowed; regression runs both models on the full current
    membership, never just on a favorable selected subset.
    """
    if not current or not baseline:
        raise ValueError("Test memberships must be nonempty")
    current_counts = Counter(current)
    baseline_counts = Counter(baseline)
    missing = current_counts - baseline_counts
    if missing:
        raise ValueError("Current smoke test images/annotations absent from baseline test")
    return {
        "comparable": True,
        "current_images": len(current),
        "baseline_images": len(baseline),
        "baseline_only_images": sum((baseline_counts - current_counts).values()),
    }


def test_quality_decision(
    metrics: dict[str, dict[str, float]], smoke_regression: dict[str, float]
) -> dict[str, bool]:
    """Apply predeclared conservative test floors and same-source regression."""
    return {
        "smoke": metrics["smoke"]["recall"] >= 0.90,
        "fire": metrics["fire"]["recall"] >= 0.90,
        "person": metrics["person"]["f1"] >= 0.65 and metrics["person"]["recall"] >= 0.60,
        "smoke_regression": all(delta >= -0.03 for delta in smoke_regression.values()),
    }
