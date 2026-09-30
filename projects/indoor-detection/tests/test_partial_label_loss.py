from __future__ import annotations

import pytest
import torch

from indoor_detection.partial_label_loss import (
    PerImageMaskedBCE,
    validate_known_class_targets,
)


def test_unknown_classes_contribute_no_loss_or_gradient() -> None:
    loss = PerImageMaskedBCE(num_classes=3)
    loss.set_known_classes(torch.tensor([[True, True, False], [False, False, True]]))
    logits = torch.zeros((2, 2, 3), requires_grad=True)
    targets = torch.zeros_like(logits)

    loss(logits, targets).sum().backward()

    assert torch.equal(logits.grad[0, :, 2], torch.zeros(2))
    assert torch.equal(logits.grad[1, :, :2], torch.zeros((2, 2)))
    assert torch.all(logits.grad[0, :, :2] != 0)
    assert torch.all(logits.grad[1, :, 2] != 0)


def test_masked_loss_matches_bce_on_known_class_entries() -> None:
    loss = PerImageMaskedBCE(num_classes=3)
    loss.set_known_classes(torch.tensor([[True, False, True]]))
    logits = torch.tensor([[[0.0, 1.0, -1.0]]])
    targets = torch.tensor([[[1.0, 1.0, 0.0]]])

    actual = loss(logits, targets)
    expected = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, targets, reduction="none"
    )

    assert torch.allclose(actual, expected * torch.tensor([[[1, 0, 1]]]))


def test_rejects_images_with_no_known_classes() -> None:
    loss = PerImageMaskedBCE(num_classes=3)

    with pytest.raises(ValueError, match="at least one known class"):
        loss.set_known_classes(torch.tensor([[False, False, False]]))


def test_requires_scope_for_each_loss_call() -> None:
    loss = PerImageMaskedBCE(num_classes=3)

    with pytest.raises(RuntimeError, match="set for every"):
        loss(torch.zeros((1, 1, 3)), torch.zeros((1, 1, 3)))


def test_rejects_ground_truth_class_outside_image_scope() -> None:
    known = torch.tensor([[True, False, False], [False, False, True]])

    with pytest.raises(ValueError, match="not marked as known"):
        validate_known_class_targets(
            known,
            torch.tensor([0]),
            torch.tensor([[1.0]]),
        )


def test_accepts_empty_targets_for_negative_images() -> None:
    validate_known_class_targets(
        torch.tensor([[True, False, False]]),
        torch.empty(0, dtype=torch.long),
        torch.empty((0, 1)),
    )


def test_yolo26n_criterion_runs_masked_forward_and_backward() -> None:
    from ultralytics.cfg import get_cfg
    from ultralytics.nn.tasks import DetectionModel

    from indoor_detection.partial_label_loss import install_class_masked_criterion

    model = DetectionModel("yolo26n.yaml", nc=3, verbose=False)
    model.args = get_cfg()
    install_class_masked_criterion(model)
    model.train()
    batch = {
        "img": torch.rand(2, 3, 64, 64),
        "batch_idx": torch.empty(0, dtype=torch.long),
        "cls": torch.empty((0, 1)),
        "bboxes": torch.empty((0, 4)),
        "known_classes": torch.tensor([[True, True, False], [False, False, True]]),
    }

    loss, components = model(batch)
    loss.sum().backward()

    assert torch.isfinite(loss).all()
    assert set(components) == {"box_loss", "cls_loss", "l1_loss"}
    assert any(parameter.grad is not None for parameter in model.parameters())
