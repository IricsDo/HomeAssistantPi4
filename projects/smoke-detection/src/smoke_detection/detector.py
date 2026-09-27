"""Ultralytics adapter constrained to a smoke-only model contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from smoke_detection.domain import BoundingBox, SmokeDetection


class InvalidSmokeModelError(ValueError):
    """Raised when a model does not expose exactly the smoke class."""


class UltralyticsSmokeDetector:
    """Lazy Ultralytics backend supporting PyTorch, ONNX and NCNN artifacts."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        confidence_threshold: float = 0.20,
        iou_threshold: float = 0.45,
        image_size: int = 416,
        device: str | None = None,
    ) -> None:
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Smoke model not found: {path}")

        from ultralytics import YOLO

        self._model = YOLO(str(path))
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        self.device = device
        self._smoke_class_id = self._validate_model_names(self._model.names)

    @staticmethod
    def _validate_model_names(names: dict[int, str] | list[str]) -> int:
        normalized = dict(enumerate(names)) if isinstance(names, list) else dict(names)
        smoke_classes = [
            int(class_id)
            for class_id, class_name in normalized.items()
            if str(class_name).strip().lower() == "smoke"
        ]
        if len(normalized) != 1 or len(smoke_classes) != 1:
            raise InvalidSmokeModelError(
                "Expected a smoke-only model with exactly one class named 'smoke'; "
                f"received {normalized}"
            )
        return smoke_classes[0]

    def predict(self, frame: Any, *, frame_index: int) -> list[SmokeDetection]:
        predict_options: dict[str, Any] = {
            "source": frame,
            "conf": self.confidence_threshold,
            "iou": self.iou_threshold,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device is not None:
            predict_options["device"] = self.device

        result = self._model.predict(**predict_options)[0]
        boxes = result.boxes
        if boxes is None:
            return []

        xyxy_values = boxes.xyxy.cpu().tolist()
        confidence_values = boxes.conf.cpu().tolist()
        class_values = boxes.cls.cpu().tolist()

        detections: list[SmokeDetection] = []
        for xyxy, confidence, class_id in zip(
            xyxy_values,
            confidence_values,
            class_values,
            strict=True,
        ):
            if int(class_id) != self._smoke_class_id:
                continue
            detections.append(
                SmokeDetection(
                    box=BoundingBox(*map(float, xyxy)),
                    confidence=float(confidence),
                    frame_index=frame_index,
                )
            )
        return detections
