"""Low-cost image-quality signals used alongside smoke inference."""

from __future__ import annotations

from typing import Any


def variance_of_laplacian(frame: Any) -> float:
    """Measure edge sharpness; lower values generally indicate blur."""

    import cv2

    if frame is None:
        raise ValueError("frame must not be None")
    gray = frame if len(frame.shape) == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_low_quality(frame: Any, *, blur_threshold: float) -> tuple[bool, float]:
    if blur_threshold < 0:
        raise ValueError("blur_threshold must be non-negative")
    score = variance_of_laplacian(frame)
    return (score < blur_threshold, score)
