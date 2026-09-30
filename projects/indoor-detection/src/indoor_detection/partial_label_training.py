"""Ultralytics dataset and trainer integration for partial-label class scopes."""

from __future__ import annotations

import json
import os
from copy import copy
from pathlib import Path
from typing import Any

import torch
from ultralytics.cfg import DEFAULT_CFG
from ultralytics.data.build import get_split_fraction
from ultralytics.data.dataset import YOLODataset
from ultralytics.models.yolo.detect.train import DetectionTrainer
from ultralytics.models.yolo.detect.val import DetectionValidator
from ultralytics.nn.tasks import DetectionModel
from ultralytics.utils import RANK
from ultralytics.utils.torch_utils import unwrap_model

from indoor_detection.joint_dataset import TARGET_NAMES
from indoor_detection.partial_label_loss import ClassMaskedDetectionLoss

SCOPE_MANIFEST_KEY = "class_scope_manifest"
UNSAFE_MIX_AUGMENTATIONS = ("mosaic", "mixup", "cutmix", "copy_paste")


def _canonical_path(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def resolve_scope_manifest(data: dict[str, Any]) -> Path:
    """Resolve the class-scope manifest declared by a checked YOLO data mapping."""
    raw_path = data.get(SCOPE_MANIFEST_KEY)
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"Dataset YAML must declare a non-empty '{SCOPE_MANIFEST_KEY}'")
    path = Path(raw_path)
    if not path.is_absolute():
        yaml_file = data.get("yaml_file")
        base = Path(str(yaml_file)).parent if yaml_file else Path(str(data["path"]))
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Class-scope manifest not found: {path}")
    return path


def load_class_scopes(manifest_path: Path) -> dict[str, torch.Tensor]:
    """Load and validate an image-to-known-class mapping."""
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("Class-scope manifest must use schema_version 1")
    if document.get("classes") != list(TARGET_NAMES):
        raise ValueError(f"Class-scope manifest classes must be {list(TARGET_NAMES)}")
    images = document.get("images")
    if not isinstance(images, dict) or not images:
        raise ValueError("Class-scope manifest must contain a non-empty images mapping")

    scopes: dict[str, torch.Tensor] = {}
    for raw_image, raw_scope in images.items():
        if not isinstance(raw_image, str) or not isinstance(raw_scope, list):
            raise ValueError("Each class-scope entry must map an image path to a class-name list")
        scope = set(raw_scope)
        if not scope or len(scope) != len(raw_scope) or not scope <= set(TARGET_NAMES):
            raise ValueError(f"Invalid annotation scope for {raw_image}: {raw_scope}")
        image_path = Path(raw_image)
        if not image_path.is_absolute():
            image_path = manifest_path.parent / image_path
        key = _canonical_path(image_path)
        if key in scopes:
            raise ValueError(f"Duplicate canonical image path in class-scope manifest: {raw_image}")
        scopes[key] = torch.tensor([name in scope for name in TARGET_NAMES], dtype=torch.bool)
    return scopes


def _validate_dataset_names(data: dict[str, Any]) -> None:
    names = data.get("names")
    if isinstance(names, dict):
        ordered = [names.get(index, names.get(str(index))) for index in range(len(names))]
    elif isinstance(names, list):
        ordered = names
    else:
        raise ValueError("Dataset must declare canonical class names")
    if ordered != list(TARGET_NAMES):
        raise ValueError(f"Class-scoped dataset names must be {list(TARGET_NAMES)}")


class ClassScopedYOLODataset(YOLODataset):
    """YOLO dataset that attaches a validated class-scope vector to every image."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        hyp = kwargs.get("hyp")
        if kwargs.get("augment") and any(
            float(getattr(hyp, name, 0.0)) > 0 for name in UNSAFE_MIX_AUGMENTATIONS
        ):
            raise ValueError(
                "Class-scoped datasets require mosaic, mixup, cutmix and copy_paste to be 0"
            )
        super().__init__(*args, **kwargs)
        _validate_dataset_names(self.data)
        manifest_path = resolve_scope_manifest(self.data)
        self.class_scopes = load_class_scopes(manifest_path)
        missing = [
            path
            for path in self.im_files
            if _canonical_path(Path(path)) not in self.class_scopes
        ]
        if missing:
            raise ValueError(
                "Class-scope manifest has no entry for "
                f"{len(missing)} dataset images; first: {missing[0]}"
            )
        for label in self.labels:
            known = self.class_scopes[_canonical_path(Path(label["im_file"]))]
            classes = torch.as_tensor(label["cls"], dtype=torch.long).reshape(-1)
            if classes.numel() and not known[classes].all():
                raise ValueError(
                    f"Label contains a class outside its declared scope: {label['im_file']}"
                )

    def __getitem__(self, index: int) -> dict[str, Any]:
        sample = super().__getitem__(index)
        sample["known_classes"] = self.class_scopes[
            _canonical_path(Path(sample["im_file"]))
        ].clone()
        return sample

    @staticmethod
    def collate_fn(batch: list[dict[str, Any]]) -> dict[str, Any]:
        collated = YOLODataset.collate_fn(batch)
        collated["known_classes"] = torch.stack(list(collated["known_classes"]))
        return collated


class ClassMaskedDetectionModel(DetectionModel):
    """Detection model whose lazy criterion understands per-image class scopes."""

    def init_criterion(self) -> Any:
        from ultralytics.utils.loss import E2ELoss

        if getattr(self.model[-1], "one2one_cv2", None) is not None:
            return E2ELoss(self, ClassMaskedDetectionLoss)
        return ClassMaskedDetectionLoss(self)


def filter_predictions_to_known_classes(
    predictions: list[dict[str, torch.Tensor]], known_classes: torch.Tensor
) -> list[dict[str, torch.Tensor]]:
    """Remove predictions for classes that are unknown in each validation image."""
    if known_classes.ndim != 2 or len(predictions) != known_classes.shape[0]:
        raise ValueError("Validation predictions and known_classes batch dimensions must match")
    filtered: list[dict[str, torch.Tensor]] = []
    for index, prediction in enumerate(predictions):
        classes = prediction["cls"].long()
        if classes.numel() and (classes.min() < 0 or classes.max() >= known_classes.shape[1]):
            raise ValueError("Validation prediction class is outside the known_classes dimension")
        keep = known_classes[index].to(classes.device)[classes]
        filtered.append(
            {
                key: (
                    value[keep]
                    if isinstance(value, torch.Tensor)
                    and value.ndim
                    and len(value) == len(keep)
                    else value
                )
                for key, value in prediction.items()
            }
        )
    return filtered


class ClassScopedDetectionValidator(DetectionValidator):
    """Detection validator that ignores predictions for unannotated classes."""

    def preprocess(self, batch: dict[str, Any]) -> dict[str, Any]:
        processed = super().preprocess(batch)
        known_classes = processed.get("known_classes")
        if not isinstance(known_classes, torch.Tensor):
            raise ValueError("Partial-label validation batches require known_classes")
        self._batch_known_classes = known_classes
        return processed

    def init_metrics(self, model: torch.nn.Module) -> None:
        super().init_metrics(model)
        native_model = model.model if getattr(model, "format", None) == "pt" else model
        detection_model = getattr(native_model, "model", None)
        self._detection_head = detection_model[-1] if detection_model else None

    def postprocess(self, predictions: Any) -> list[dict[str, torch.Tensor]]:
        raw = predictions[1] if isinstance(predictions, tuple) else None
        head = getattr(self, "_detection_head", None)
        known_classes = getattr(self, "_batch_known_classes", None)
        if (
            head is not None
            and isinstance(raw, dict)
            and isinstance(raw.get("one2one"), dict)
            and isinstance(known_classes, torch.Tensor)
        ):
            decoded = head._inference(raw["one2one"]).permute(0, 2, 1)
            scores = decoded[..., 4 : 4 + self.nc]
            scores.masked_fill_(~known_classes[:, None, :], 0.0)
            predictions = head.postprocess(decoded)
        return super().postprocess(predictions)

    def update_metrics(
        self, predictions: list[dict[str, torch.Tensor]], batch: dict[str, Any]
    ) -> None:
        known_classes = batch.get("known_classes")
        if not isinstance(known_classes, torch.Tensor):
            raise ValueError("Partial-label validation batches require known_classes")
        super().update_metrics(
            filter_predictions_to_known_classes(predictions, known_classes), batch
        )


class ClassScopedDetectionTrainer(DetectionTrainer):
    """YOLO trainer for datasets with explicit per-image annotation scopes."""

    def __init__(
        self,
        cfg: Any = DEFAULT_CFG,
        overrides: dict[str, Any] | None = None,
        _callbacks: Any = None,
    ) -> None:
        safe_overrides = dict(overrides or {})
        for name in UNSAFE_MIX_AUGMENTATIONS:
            safe_overrides[name] = 0.0
        super().__init__(cfg=cfg, overrides=safe_overrides, _callbacks=_callbacks)

    def build_dataset(self, img_path: str, mode: str = "train", batch: int | None = None):
        fraction = (
            1.0
            if self.data.get("complete")
            else get_split_fraction(
                self.args.fraction, "train" if mode == "train" else self.args.split
            )
        )
        return ClassScopedYOLODataset(
            img_path=img_path,
            imgsz=self.args.imgsz,
            batch_size=batch,
            augment=mode == "train",
            hyp=self.args,
            rect=self.args.rect or mode == "val",
            cache=self.args.cache or None,
            single_cls=self.args.single_cls or False,
            stride=max(int(unwrap_model(self.model).stride.max()), 32),
            pad=0.0 if mode == "train" else 0.5,
            prefix=f"{mode}: ",
            task=self.args.task,
            classes=self.args.classes,
            data=self.data,
            fraction=fraction,
        )

    def get_model(self, cfg: str | None = None, weights: str | None = None, verbose: bool = True):
        model = self.set_model_names_for_load(
            ClassMaskedDetectionModel(
                cfg,
                nc=self.data["nc"],
                ch=self.data["channels"],
                verbose=verbose and RANK == -1,
            )
        )
        if weights:
            model.load(weights)
        return model

    def get_validator(self):
        return ClassScopedDetectionValidator(
            self.test_loader,
            save_dir=self.save_dir,
            args=copy(self.args),
            _callbacks=self.callbacks,
        )
