"""Experimental class-masked classification loss for partial-label YOLO data.

This module only supplies the loss criterion. A training dataset must also
provide a per-image ``known_classes`` boolean tensor in the batch; the regular
YOLO dataset/trainer does not do that yet.
"""

from __future__ import annotations

from typing import Any

import torch
from torch import nn
from ultralytics.utils.loss import E2ELoss, v8DetectionLoss


class PerImageMaskedBCE(nn.Module):
    """Elementwise BCE that ignores unknown classes separately per image."""

    def __init__(self, num_classes: int) -> None:
        super().__init__()
        self.num_classes = num_classes
        self._known_classes: torch.Tensor | None = None
        self._bce = nn.BCEWithLogitsLoss(reduction="none")

    def set_known_classes(self, known_classes: torch.Tensor) -> None:
        if known_classes.ndim != 2 or known_classes.shape[1] != self.num_classes:
            raise ValueError(
                "known_classes must have shape (batch_size, num_classes); "
                f"got {tuple(known_classes.shape)} for {self.num_classes} classes"
            )
        if known_classes.shape[0] == 0 or not torch.all(known_classes.any(dim=1)):
            raise ValueError("Every image must have at least one known class")
        self._known_classes = known_classes.to(dtype=torch.bool)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        known_classes = self._known_classes
        if known_classes is None:
            raise RuntimeError("known_classes must be set for every partial-label batch")
        if logits.ndim != 3 or logits.shape[0] != known_classes.shape[0]:
            raise ValueError("Classification logits must have shape (batch, anchors, classes)")
        if logits.shape[-1] != self.num_classes or targets.shape != logits.shape:
            raise ValueError("Logits and targets must share the configured class dimension")

        class_mask = known_classes.to(device=logits.device).unsqueeze(1)
        return self._bce(logits, targets) * class_mask


def validate_known_class_targets(
    known_classes: torch.Tensor, batch_idx: torch.Tensor, classes: torch.Tensor
) -> None:
    """Reject GT boxes whose class is outside the image's declared annotation scope."""
    if batch_idx.numel() != classes.numel():
        raise ValueError("batch_idx and cls must contain the same number of ground-truth boxes")
    if batch_idx.numel() == 0:
        return

    image_indices = batch_idx.reshape(-1).long().to(known_classes.device)
    class_indices = classes.reshape(-1).long().to(known_classes.device)
    if image_indices.min() < 0 or image_indices.max() >= known_classes.shape[0]:
        raise ValueError("Ground-truth batch_idx is outside the known_classes batch")
    if class_indices.min() < 0 or class_indices.max() >= known_classes.shape[1]:
        raise ValueError("Ground-truth class id is outside the known_classes dimension")
    if not known_classes[image_indices, class_indices].all():
        raise ValueError("Ground-truth class is not marked as known for its image")


class ClassMaskedDetectionLoss(v8DetectionLoss):
    """Apply per-image known-class masks to Ultralytics detection BCE loss."""

    def __init__(self, model: nn.Module, *args: Any, **kwargs: Any) -> None:
        super().__init__(model, *args, **kwargs)
        self.bce = PerImageMaskedBCE(self.nc)

    def loss(
        self, preds: Any, batch: dict[str, torch.Tensor]
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        known_classes = batch.get("known_classes")
        if not isinstance(known_classes, torch.Tensor):
            raise ValueError("Partial-label batches require a known_classes tensor")
        batch_idx = batch.get("batch_idx")
        classes = batch.get("cls")
        if not isinstance(batch_idx, torch.Tensor) or not isinstance(classes, torch.Tensor):
            raise ValueError("Partial-label batches require batch_idx and cls tensors")
        self.bce.set_known_classes(known_classes)
        try:
            validate_known_class_targets(known_classes, batch_idx, classes)
            return super().loss(preds, batch)
        finally:
            self.bce._known_classes = None


def install_class_masked_criterion(model: nn.Module) -> None:
    """Install the partial-label criterion on an Ultralytics detection model."""
    head = model.model[-1]  # type: ignore[attr-defined]
    if getattr(head, "one2one_cv2", None) is not None:
        model.criterion = E2ELoss(model, ClassMaskedDetectionLoss)  # type: ignore[attr-defined]
    else:
        model.criterion = ClassMaskedDetectionLoss(model)  # type: ignore[attr-defined]
