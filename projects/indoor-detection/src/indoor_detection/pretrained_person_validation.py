"""Evaluation-only projection of pretrained COCO person into the indoor class space."""

from typing import Any

import torch
from ultralytics.utils.metrics import ConfusionMatrix

from indoor_detection.partial_label_training import ClassScopedDetectionValidator


def validate_pretrained_person_names(names: dict[int, str]) -> None:
    if len(names) != 80 or names.get(0) != "person":
        raise ValueError("Expected an unchanged 80-class COCO checkpoint with person=0")


def project_person_predictions(
    predictions: list[dict[str, torch.Tensor]],
) -> list[dict[str, torch.Tensor]]:
    """Drop non-person outputs and map person=0 to person=2 without mutating inputs."""
    result = []
    for prediction in predictions:
        classes = prediction["cls"]
        if classes.numel() and ((classes < 0).any() or (classes >= 80).any()):
            raise ValueError("Pretrained prediction class is outside COCO class space")
        keep = classes == 0
        projected = {key: value[keep] for key, value in prediction.items()}
        projected["cls"] = torch.full_like(classes[keep], 2)
        result.append(projected)
    return result


class PretrainedPersonScopedValidator(ClassScopedDetectionValidator):
    """Use unchanged indoor labels/scopes with an unchanged pretrained model."""

    def init_metrics(self, model: Any) -> None:
        validate_pretrained_person_names(model.names)
        super().init_metrics(model)
        self.names = {0: "smoke", 1: "fire", 2: "person"}
        self.nc = 3
        self.metrics.names = self.names
        self.confusion_matrix = ConfusionMatrix(names=self.names)

    def postprocess(self, preds: torch.Tensor) -> list[dict[str, torch.Tensor]]:
        # Detect NMS infers the original channel count (nc=0); projection follows NMS.
        return project_person_predictions(super().postprocess(preds))
