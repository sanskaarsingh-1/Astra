"""
Astra AI — BigEarthNet v2 ResNet-50 Multi-Label Training Pipeline
Production-quality training, validation, and evaluation pipeline for Sentinel-2 scene classification.

Satisfies SIH 2026 requirement:
"at least one remote-sensing visual/VLM component adapted using BigEarthNet"

CRITICAL INVARIANTS & SPECIFICATIONS:
- Multi-label classification (BCEWithLogitsLoss, raw logits, sigmoid for probabilities)
- Complete, unconstrained BigEarthNet v2.0 dataset (480,038 physical samples across 115 tiles)
- Positive loss weighting derived exclusively from the 237,871-sample training split
- ResNet-50 backbone with ImageNet-v2 pretrained weights + fresh 19-class linear head
- Checkpoint isolation (saves to output_dir, never overwrites verified baseline ben_classifier.pth)
- Mixed precision training (torch.amp) optimized for RTX 5060 Blackwell GPU
- Fault-tolerant resume capability (--resume) and per-epoch atomic latest_model.pth saving
- Deterministic Sentinel-2 L2A BOA reflectance scaling (DN / 10000.0) into [0, 1]
- Early stopping based on validation Macro F1
- Safe pre-flight sanity check mode (--sanity_check_only) with guaranteed zero training steps
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Windows Virtual Memory & BLAS thread allocation guard (prevents WinError 1455 & OpenBLAS alloc retries)
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    import numpy as np
    import rasterio
    from sklearn.metrics import precision_recall_fscore_support
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset
    import torchvision.models as models
    import torchvision.transforms as T
    from tqdm import tqdm
    from loguru import logger
except ImportError as err:
    import sys
    sys.stderr.write(
        f"\n[ENVIRONMENT ERROR] Missing dependency: {err}\n"
        f"Active Python interpreter: {sys.executable}\n\n"
        f"This script requires the Astra verified GPU environment containing PyTorch, rasterio, etc.\n"
        f"Please run using the backend virtual environment interpreter directly:\n"
        f"  .\\backend\\.venv\\Scripts\\python.exe -m backend.training.train_ben_classifier ...\n\n"
        f"Or activate the environment first in PowerShell:\n"
        f"  .\\backend\\.venv\\Scripts\\Activate.ps1\n\n"
    )
    sys.exit(1)

# ─── Authoritative 19 BigEarthNet v2.0 Classes (reBEN / Table 1) ─────────────
BEN_CLASSES = [
    "Urban fabric",
    "Industrial or commercial units",
    "Arable land",
    "Permanent crops",
    "Pastures",
    "Complex cultivation patterns",
    "Land occupied by agriculture with natural vegetation",
    "Agro-forestry areas",
    "Broad-leaved forest",
    "Coniferous forest",
    "Mixed forest",
    "Natural grassland and sparsely vegetated areas",
    "Moors, heathland and sclerophyllous vegetation",
    "Transitional woodland, shrub",
    "Beaches, dunes, sands",
    "Inland wetlands",
    "Coastal wetlands",
    "Inland waters",
    "Marine waters",
]

LABEL_TO_IDX: Dict[str, int] = {label: i for i, label in enumerate(BEN_CLASSES)}
IDX_TO_LABEL: Dict[int, str] = {i: label for i, label in enumerate(BEN_CLASSES)}


# ─── Dataset: Manifest-driven GeoTIFF Loader ────────────────────────────────
class BigEarthNetManifestDataset(Dataset):
    """
    BigEarthNet v2 Dataset Loader — reads strictly from authoritative CSV manifests.
    Expects columns: patch_id (or sample_id), image_path, label_indices, split, etc.
    """

    def __init__(self, manifest_csv: Path, repo_root: Path, transform=None):
        self.repo_root = Path(repo_root)
        self.transform = transform
        self.samples: List[Dict[str, Any]] = []

        if not manifest_csv.exists():
            raise FileNotFoundError(f"Manifest CSV not found: {manifest_csv}")

        with open(manifest_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_path = self.repo_root / row["image_path"]
                idx_str = row.get("label_indices", "").strip()
                if idx_str:
                    lbl_indices = [int(x) for x in idx_str.split(";") if x.strip()]
                else:
                    lbl_indices = []
                sample_id = row.get("sample_id") or row.get("patch_id")
                self.samples.append({
                    "sample_id": sample_id,
                    "image_path": img_path,
                    "label_indices": lbl_indices,
                })

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        item = self.samples[idx]
        img_path = item["image_path"]
        label_indices = item["label_indices"]

        # Read 3-band Sentinel-2 GeoTIFF (B04 Red, B03 Green, B02 Blue) — uint16
        with rasterio.open(str(img_path)) as src:
            arr = src.read()  # shape (3, H, W), uint16

        # Deterministic physical reflectance scaling for Sentinel-2 Level-2A (Bottom-Of-Atmosphere):
        # Digital Numbers (DN) = 10,000 * Surface Reflectance
        # Scale to [0.0, 1.0] physical reflectance range without arbitrary contrast distortion:
        arr = np.clip(arr.astype(np.float32) / 10000.0, 0.0, 1.0)
        img = torch.from_numpy(arr)  # float32 tensor (3, H, W)

        if self.transform is not None:
            img = self.transform(img)

        # Multi-hot target vector of shape [19]
        label_vec = torch.zeros(len(BEN_CLASSES), dtype=torch.float32)
        for idx_lbl in label_indices:
            if 0 <= idx_lbl < len(BEN_CLASSES):
                label_vec[idx_lbl] = 1.0

        return img, label_vec


# ─── Model Construction ──────────────────────────────────────────────────────
def build_model(num_classes: int = 19, pretrained: bool = True) -> nn.Module:
    """
    Build ResNet-50 for multi-label classification.
    Classifier head: nn.Linear(2048, num_classes)
    Output shape: [batch_size, num_classes] (raw logits)
    Fully compatible with backend/services/model_service.py checkpoint loading.
    """
    weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
    model = models.resnet50(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


# ─── Class Weight Loader & Mathematical Validator ───────────────────────────
def load_and_validate_class_weights(
    manifest_dir: Path,
    expected_classes: List[str],
    device: torch.device,
) -> torch.Tensor:
    """
    Load precomputed class weights from dataset_statistics.json and mathematically validate them:
    - Confirms file exists (fails loudly if missing)
    - Confirms exactly 19 classes matching authoritative taxonomy order
    - Confirms weights are strictly derived from TRAINING SPLIT only (237,871 samples)
    - Validates pos_weight[c] == (N_train - train_pos[c]) / train_pos[c]
    - Confirms all values are positive and finite
    """
    stats_json_path = manifest_dir / "dataset_statistics.json"
    if not stats_json_path.exists():
        raise FileNotFoundError(
            f"FATAL: Class weighting enabled, but statistics file does not exist: {stats_json_path.resolve()}\n"
            f"Cannot proceed without verified training statistics. Please verify manifest directory."
        )

    with open(stats_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Validate split counts
    train_count = data.get("splits", {}).get("train")
    if train_count is None or train_count != 237871:
        raise ValueError(
            f"FATAL: Unexpected training split count in {stats_json_path}: expected 237,871, found {train_count}"
        )

    class_counts = data.get("class_counts", {})
    if len(class_counts) != len(expected_classes):
        raise ValueError(
            f"FATAL: Class count mismatch in {stats_json_path}: "
            f"expected {len(expected_classes)} classes, found {len(class_counts)}"
        )

    pos_weights: List[float] = []
    for idx, cls_name in enumerate(expected_classes):
        if cls_name not in class_counts:
            raise KeyError(f"FATAL: Missing class '{cls_name}' in {stats_json_path}")
        entry = class_counts[cls_name]

        # Verify class index
        if entry.get("index") != idx:
            raise ValueError(
                f"FATAL: Class index mismatch for '{cls_name}': expected {idx}, found {entry.get('index')}"
            )

        train_pos = entry.get("train_positives")
        if train_pos is None or train_pos <= 0:
            raise ValueError(f"FATAL: Invalid train_positives for '{cls_name}': {train_pos}")

        # Mathematical verification: pos_weight = (N_train - train_pos) / train_pos
        expected_weight = (train_count - train_pos) / train_pos
        recorded_weight = entry.get("pos_weight")

        if recorded_weight is None or not np.isfinite(recorded_weight) or recorded_weight <= 0:
            raise ValueError(f"FATAL: Non-finite or non-positive pos_weight for '{cls_name}': {recorded_weight}")

        # Tolerance check: ensure recorded pos_weight is derived from TRAIN ONLY
        if abs(recorded_weight - expected_weight) / expected_weight > 0.01:
            raise ValueError(
                f"FATAL: Recorded pos_weight ({recorded_weight}) for '{cls_name}' deviates from "
                f"training-split formula (N_train - train_pos) / train_pos = {expected_weight:.4f}"
            )

        pos_weights.append(float(recorded_weight))

    if len(pos_weights) != 19:
        raise ValueError(f"FATAL: Expected exactly 19 weights, got {len(pos_weights)}")

    weight_tensor = torch.tensor(pos_weights, dtype=torch.float32, device=device)
    logger.success(
        f"Loaded and validated 19 positive class weights from {stats_json_path.name} "
        f"(min: {min(pos_weights):.2f} [{expected_classes[int(np.argmin(pos_weights))]}], "
        f"max: {max(pos_weights):.2f} [{expected_classes[int(np.argmax(pos_weights))]}])"
    )
    return weight_tensor


# ─── Atomic Checkpoint Saving ───────────────────────────────────────────────
def save_checkpoint_atomic(state: Dict[str, Any], filepath: Path) -> None:
    """Save checkpoint atomically using a temporary file to prevent corruption on interruption."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
    torch.save(state, str(tmp_path))
    tmp_path.replace(filepath)


# ─── Metrics Computation ────────────────────────────────────────────────────
def compute_multilabel_metrics(
    y_true: np.ndarray,
    y_pred_probs: np.ndarray,
    threshold: float = 0.5,
    class_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute micro, macro, and per-class precision, recall, and F1.
    y_true: binary array of shape (N, num_classes)
    y_pred_probs: probability array of shape (N, num_classes) from sigmoid
    """
    y_pred = (y_pred_probs >= threshold).astype(int)

    # Micro metrics
    p_micro, r_micro, f1_micro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="micro", zero_division=0
    )

    # Macro metrics
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )

    # Per-class metrics
    p_class, r_class, f1_class, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )

    per_class_metrics: Dict[str, Dict[str, Any]] = {}
    if class_names is None:
        class_names = [f"class_{i}" for i in range(y_true.shape[1])]

    for i, name in enumerate(class_names):
        per_class_metrics[name] = {
            "precision": round(float(p_class[i]), 4),
            "recall": round(float(r_class[i]), 4),
            "f1": round(float(f1_class[i]), 4),
            "support": int(support[i]),
        }

    return {
        "micro_precision": round(float(p_micro), 4),
        "micro_recall": round(float(r_micro), 4),
        "micro_f1": round(float(f1_micro), 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "threshold": threshold,
        "per_class": per_class_metrics,
    }


# ─── Dataset Pre-flight Sanity Checks ────────────────────────────────────────
def dataset_sanity_check(manifest_dir: Path, repo_root: Path) -> Dict[str, Any]:
    """
    Perform rigorous dataset sanity validation before training begins:
    - Verifies manifest existence
    - Verifies no sample_id overlap between train, val, test
    - Verifies image files exist and have exactly 3 optical channels
    - Verifies label values and class index bounds [0, 18]
    - Verifies class distribution and positive support counts
    """
    logger.info("Running dataset pre-flight sanity checks...")

    expected_splits = {}
    for sp in ["train", "val", "test"]:
        p_clean = manifest_dir / f"{sp}.csv"
        p_legacy = manifest_dir / f"bigearthnet_{sp}.csv"
        csv_path = p_clean if p_clean.exists() else p_legacy
        expected_splits[sp] = csv_path

    split_sample_ids: Dict[str, set] = {}
    split_counts: Dict[str, int] = {}
    class_counts_train = {cls_name: 0 for cls_name in BEN_CLASSES}

    for split_name, csv_path in expected_splits.items():
        if not csv_path.exists():
            raise FileNotFoundError(
                f"FATAL: Missing required manifest: {csv_path.resolve()}\n"
                f"Please ensure manifests exist in {manifest_dir}"
            )

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            rows = list(reader)

        # Safety Guard: Fail loudly on incompatible dataset routing
        if "im1_path" in fieldnames or ("question" in fieldnames and "answer" in fieldnames):
            raise ValueError(
                f"FATAL DATASET INCOMPATIBILITY: Manifest '{csv_path.name}' contains Change VQA / CDVQA data. "
                f"The BigEarthNet ResNet-50 pipeline requires optical LULC remote-sensing imagery."
            )
        if "path_A" in fieldnames or "path_label" in fieldnames:
            raise ValueError(
                f"FATAL DATASET INCOMPATIBILITY: Manifest '{csv_path.name}' contains LEVIR-CD change detection data. "
                f"The BigEarthNet ResNet-50 pipeline requires single-time optical remote-sensing imagery."
            )
        if "annotation_path" in fieldnames and "vrsbench" in str(csv_path).lower():
            raise ValueError(
                f"FATAL DATASET INCOMPATIBILITY: Manifest '{csv_path.name}' contains VRSBench multimodal data. "
                f"The BigEarthNet ResNet-50 pipeline requires BigEarthNet Sentinel-2 optical imagery."
            )

        count = len(rows)
        split_counts[split_name] = count
        if count == 0:
            raise ValueError(f"FATAL: Manifest {csv_path.name} is empty (0 samples).")

        ids = set()
        for idx, row in enumerate(rows):
            sid = row.get("sample_id") or row.get("patch_id")
            if not sid:
                raise ValueError(f"FATAL: Row {idx} in {csv_path.name} has missing sample_id/patch_id")
            if sid in ids:
                raise ValueError(f"FATAL: Duplicate identifier '{sid}' in {csv_path.name}")
            ids.add(sid)

            # Check for Sentinel-1 SAR modality
            if "_S1A_" in sid or "_S1B_" in sid or sid.startswith("S1"):
                raise ValueError(
                    f"FATAL MODALITY INCOMPATIBILITY: Sample '{sid}' is Sentinel-1 SAR data. "
                    f"The ResNet-50 optical classifier requires 3-band Sentinel-2 optical RGB imagery."
                )

            # Check first sample image existence and band count
            img_rel = row.get("image_path")
            if not img_rel:
                raise ValueError(f"FATAL: Row {idx} in {csv_path.name} missing image_path")
            img_full = repo_root / img_rel
            if not img_full.exists():
                raise FileNotFoundError(
                    f"FATAL: Image file not found: {img_full}\n"
                    f"Referenced in {csv_path.name} row {idx} ({sid})"
                )

            if idx == 0:
                with rasterio.open(str(img_full)) as src_check:
                    if src_check.count != 3:
                        raise ValueError(
                            f"FATAL FORMAT ERROR: Image '{img_full}' has {src_check.count} bands. "
                            f"Expected exactly 3 optical channels (B04, B03, B02)."
                        )

            # Check label indices
            idx_str = row.get("label_indices", "").strip()
            if idx_str:
                indices = [int(x) for x in idx_str.split(";")]
                for i in indices:
                    if not (0 <= i < len(BEN_CLASSES)):
                        raise ValueError(
                            f"FATAL: Invalid label index {i} in {csv_path.name} row {idx}. "
                            f"Must be between 0 and {len(BEN_CLASSES) - 1}."
                        )
                    if split_name == "train":
                        class_counts_train[BEN_CLASSES[i]] += 1

        split_sample_ids[split_name] = ids
        logger.info(f"  ✓ {split_name.capitalize()} manifest verified: {count:,} samples, 100% files present")

    # Verify zero data leakage across splits
    train_val_overlap = split_sample_ids["train"].intersection(split_sample_ids["val"])
    train_test_overlap = split_sample_ids["train"].intersection(split_sample_ids["test"])
    val_test_overlap = split_sample_ids["val"].intersection(split_sample_ids["test"])

    if train_val_overlap or train_test_overlap or val_test_overlap:
        raise ValueError(
            f"FATAL: Data leakage detected across splits! "
            f"Train-Val: {len(train_val_overlap)}, Train-Test: {len(train_test_overlap)}, Val-Test: {len(val_test_overlap)}"
        )

    logger.info("  ✓ Zero data leakage confirmed: Train, Val, and Test sample sets are completely disjoint.")
    logger.info("Dataset pre-flight sanity checks PASSED.")

    return {
        "split_counts": split_counts,
        "class_counts_train": class_counts_train,
    }


# ─── DataLoader Sanity Check ────────────────────────────────────────────────
def dataloader_sanity_check(
    train_loader: DataLoader,
    model: nn.Module,
    criterion: nn.Module,
    device: torch.device,
) -> None:
    """
    Perform a single forward pass sanity check without weight updates.
    Verifies batch loading, tensor shapes, types, CUDA transfer, and loss computation.
    DOES NOT call optimizer.step() or loss.backward().
    """
    logger.info("Running DataLoader & Tensor Shape sanity check...")
    model.eval()

    try:
        sample_batch = next(iter(train_loader))
        images, labels = sample_batch

        # Verify shapes
        batch_size = images.shape[0]
        if images.shape[1:] != torch.Size([3, 224, 224]):
            raise ValueError(f"Unexpected image tensor shape: {images.shape}, expected [B, 3, 224, 224]")
        if labels.shape[1:] != torch.Size([19]):
            raise ValueError(f"Unexpected label tensor shape: {labels.shape}, expected [B, 19]")
        if images.dtype != torch.float32:
            raise TypeError(f"Unexpected image dtype: {images.dtype}, expected torch.float32")
        if labels.dtype != torch.float32:
            raise TypeError(f"Unexpected label dtype: {labels.dtype}, expected torch.float32")

        # Test CUDA transfer
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        # Forward pass in inference mode
        with torch.inference_mode():
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(images)
                loss = criterion(logits, labels)

        if logits.shape != torch.Size([batch_size, 19]):
            raise ValueError(f"Unexpected logits shape: {logits.shape}, expected [{batch_size}, 19]")
        if torch.isnan(loss) or torch.isinf(loss):
            raise ValueError(f"Non-finite loss computed during sanity check: {loss.item()}")

        logger.info(
            f"  ✓ Sanity Batch: {batch_size} samples | Images: {list(images.shape)} | "
            f"Labels: {list(labels.shape)} | Logits: {list(logits.shape)} | Sample Loss: {loss.item():.4f}"
        )
        logger.info("DataLoader & Forward Pass sanity check PASSED.")

    except Exception as e:
        logger.error(f"DataLoader sanity check FAILED: {e}")
        raise


# ─── Training Epoch ─────────────────────────────────────────────────────────
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    scaler: torch.amp.GradScaler,
    device: torch.device,
    epoch: int,
    total_epochs: int,
    threshold: float = 0.5,
) -> Tuple[float, float]:
    """Train for one epoch with batch-level progress bar, mixed precision, and label-wise accuracy."""
    model.train()
    running_loss = 0.0
    correct_label_preds = 0
    total_label_preds = 0
    total_batches = len(loader)

    pbar = tqdm(
        loader,
        desc=f"Epoch {epoch:02d}/{total_epochs:02d} [Train]",
        leave=False,
        dynamic_ncols=True,
        file=sys.stdout,
    )

    for images, labels in pbar:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
            logits = model(images)
            loss = criterion(logits, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        batch_loss = loss.item()
        running_loss += batch_loss

        # Multi-label label-wise binary accuracy accumulation (sigmoid >= threshold == ground truth)
        with torch.no_grad():
            preds = (torch.sigmoid(logits) >= threshold).float()
            correct_label_preds += (preds == labels).sum().item()
            total_label_preds += labels.numel()

        current_lr = optimizer.param_groups[0]["lr"]
        pbar.set_postfix({"loss": f"{batch_loss:.4f}", "lr": f"{current_lr:.2e}"})

    avg_loss = running_loss / max(total_batches, 1)
    train_accuracy = (correct_label_preds / max(total_label_preds, 1)) * 100.0
    return avg_loss, train_accuracy


# ─── Validation Epoch ───────────────────────────────────────────────────────
def validate_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    epoch: int,
    total_epochs: int,
    threshold: float = 0.5,
) -> Tuple[float, Dict[str, Any], float]:
    """Validate for one epoch with inference_mode, multi-label metrics, and label-wise accuracy."""
    model.eval()
    running_loss = 0.0
    correct_label_preds = 0
    total_label_preds = 0
    all_preds = []
    all_labels = []
    total_batches = len(loader)

    pbar = tqdm(
        loader,
        desc=f"Epoch {epoch:02d}/{total_epochs:02d} [Val]  ",
        leave=False,
        dynamic_ncols=True,
        file=sys.stdout,
    )

    with torch.inference_mode():
        for images, labels in pbar:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(images)
                loss = criterion(logits, labels)

            running_loss += loss.item()
            probs = torch.sigmoid(logits)

            preds = (probs >= threshold).float()
            correct_label_preds += (preds == labels).sum().item()
            total_label_preds += labels.numel()

            all_preds.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

    avg_loss = running_loss / max(total_batches, 1)
    val_accuracy = (correct_label_preds / max(total_label_preds, 1)) * 100.0
    y_pred_probs = np.vstack(all_preds)
    y_true = np.vstack(all_labels)

    metrics = compute_multilabel_metrics(
        y_true=y_true,
        y_pred_probs=y_pred_probs,
        threshold=threshold,
        class_names=BEN_CLASSES,
    )

    return avg_loss, metrics, val_accuracy


# ─── Final Test Evaluation ──────────────────────────────────────────────────
def evaluate_test_set(
    model: nn.Module,
    test_loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    threshold: float = 0.5,
) -> Tuple[float, Dict[str, Any]]:
    """Run final evaluation over all test samples using the best checkpoint."""
    model.eval()
    running_loss = 0.0
    correct_label_preds = 0
    total_label_preds = 0
    all_preds = []
    all_labels = []

    pbar = tqdm(
        test_loader,
        desc="Final Test Evaluation",
        leave=False,
        dynamic_ncols=True,
        file=sys.stdout,
    )

    with torch.inference_mode():
        for images, labels in pbar:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(images)
                loss = criterion(logits, labels)

            running_loss += loss.item()
            probs = torch.sigmoid(logits)

            preds = (probs >= threshold).float()
            correct_label_preds += (preds == labels).sum().item()
            total_label_preds += labels.numel()

            all_preds.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

    avg_loss = running_loss / max(len(test_loader), 1)
    test_accuracy = (correct_label_preds / max(total_label_preds, 1)) * 100.0
    y_pred_probs = np.vstack(all_preds)
    y_true = np.vstack(all_labels)

    metrics = compute_multilabel_metrics(
        y_true=y_true,
        y_pred_probs=y_pred_probs,
        threshold=threshold,
        class_names=BEN_CLASSES,
    )
    metrics["test_accuracy"] = round(test_accuracy, 2)
    metrics["accuracy"] = round(test_accuracy, 2)

    return avg_loss, metrics


# ─── Evaluation-Only Pipeline ────────────────────────────────────────────────
def run_evaluation_only(
    args: argparse.Namespace,
    repo_root: Path,
    manifest_dir: Path,
    output_dir: Path,
    original_ckpt: Path,
    device: torch.device,
    gpu_name: str,
) -> None:
    """
    Execute evaluation-only pipeline on the untouched BigEarthNet test set.
    Guarantees:
    - Zero retraining, no optimizer, no gradient updates, no weight changes
    - Preserves existing checkpoints (best_model.pth, final_model.pth, latest_model.pth, training_history.json)
    - Loads specified checkpoint (defaults to best_model.pth from Epoch 19)
    - Evaluates complete 119,825 test samples using single-process DataLoader (num_workers=0) for Windows stability
    - Computes test loss, accuracy, micro/macro/per-class F1, precision, recall
    - Saves test_evaluation.json and metrics.json into output_dir
    """
    logger.info("=" * 70)
    logger.info("ASTRA AI — BIGEARTHNET V2.0 EVALUATION-ONLY MODE")
    logger.info("=" * 70)
    logger.info("Mode: EVALUATION ONLY (All training loops and weight updates bypassed)")

    # 1. Resolve and Validate Checkpoint
    if args.checkpoint:
        ckpt_path = Path(args.checkpoint)
        if not ckpt_path.is_absolute():
            ckpt_path = (repo_root / ckpt_path).resolve()
    else:
        ckpt_path = output_dir / "best_model.pth"

    if not ckpt_path.exists():
        raise FileNotFoundError(f"FATAL: Evaluation checkpoint not found: {ckpt_path}")

    # Explicit safety guard: reject baseline 2019 checkpoint
    if ckpt_path == original_ckpt or (ckpt_path.name == "ben_classifier.pth" and "baseline" in str(ckpt_path)):
        raise ValueError(
            f"FATAL: Incompatible legacy checkpoint rejected: {ckpt_path}\n"
            f"The legacy baseline checkpoint belongs to the 2019 conference taxonomy and is not a valid v2.0 checkpoint."
        )

    logger.info(f"Loading checkpoint: {ckpt_path}")
    checkpoint = torch.load(str(ckpt_path), map_location=device)

    if "model_state_dict" not in checkpoint:
        raise KeyError(f"FATAL: Checkpoint {ckpt_path.name} missing required key: 'model_state_dict'")

    # Extract checkpoint metadata
    ckpt_epoch = checkpoint.get("epoch") or checkpoint.get("best_epoch", "Unknown")
    ckpt_val_macro_f1 = checkpoint.get("best_val_macro_f1")
    if ckpt_val_macro_f1 is None and "val_metrics" in checkpoint:
        ckpt_val_macro_f1 = checkpoint["val_metrics"].get("macro_f1")

    logger.info(f"Checkpoint Metadata: Epoch={ckpt_epoch} | Best Val Macro F1={ckpt_val_macro_f1}")

    # 2. Build Model Architecture and Load Weights (pretrained=False avoids ImageNet download)
    model = build_model(num_classes=len(BEN_CLASSES), pretrained=False).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Verify classification head dimensions
    fc_weights = checkpoint["model_state_dict"].get("fc.weight")
    if fc_weights is not None and fc_weights.shape[0] != len(BEN_CLASSES):
        raise ValueError(
            f"FATAL: Checkpoint output classes ({fc_weights.shape[0]}) does not match BigEarthNet v2.0 ({len(BEN_CLASSES)})"
        )
    logger.info(f"Loaded ResNet-50 backbone with 19-class linear head on {device} ({gpu_name})")

    # 3. Resolve and Validate Test Manifest
    test_manifest = manifest_dir / "test.csv" if (manifest_dir / "test.csv").exists() else manifest_dir / "bigearthnet_test.csv"
    if not test_manifest.exists():
        raise FileNotFoundError(f"FATAL: Test manifest does not exist: {test_manifest}")

    # 4. Construct Loss Function (weighted BCE matching training configuration)
    if args.use_class_weights:
        pos_weight_tensor = load_and_validate_class_weights(manifest_dir, BEN_CLASSES, device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)
        logger.info("Using weighted BCEWithLogitsLoss (class positive weights loaded from dataset_statistics.json)")
    else:
        criterion = nn.BCEWithLogitsLoss()
        logger.info("Using unweighted BCEWithLogitsLoss")

    # 5. Build Dataset and DataLoader
    eval_transform = T.Compose([
        T.Resize((224, 224), antialias=True),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    test_dataset = BigEarthNetManifestDataset(test_manifest, repo_root, transform=eval_transform)
    logger.info(f"Test Dataset: {len(test_dataset):,} samples from {test_manifest.name}")

    if len(test_dataset) != 119825:
        logger.warning(
            f"Note: Test dataset has {len(test_dataset):,} samples (standard BigEarthNet v2.0 test split is 119,825)."
        )

    # Windows stability: num_workers=0 avoids spawning child processes that exhaust Windows commit charge
    eval_num_workers = args.num_workers
    pin_memory = False if eval_num_workers == 0 else (device.type == "cuda")

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=eval_num_workers,
        pin_memory=pin_memory,
        persistent_workers=False,
        drop_last=False,
    )

    # 6. Sanity Check Only option
    if args.sanity_check_only:
        logger.info("Running single-batch forward pass evaluation sanity check...")
        dataloader_sanity_check(test_loader, model, criterion, device)
        logger.success("Evaluation sanity check PASSED. Exiting without full evaluation.")
        return

    # 7. Run Full Test Evaluation
    logger.info("=" * 70)
    logger.info(f"STARTING EVALUATION ON {len(test_dataset):,} TEST SAMPLES")
    logger.info(f"DataLoader Config: num_workers={eval_num_workers}, pin_memory={pin_memory}, batch_size={args.batch_size}")
    logger.info("=" * 70)

    t_start = time.perf_counter()
    test_loss, test_metrics = evaluate_test_set(
        model=model,
        test_loader=test_loader,
        criterion=criterion,
        device=device,
        threshold=args.threshold,
    )
    eval_duration = time.perf_counter() - t_start

    # 8. Structure Results and Save Artifacts
    test_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "checkpoint_path": str(ckpt_path),
        "checkpoint_epoch": ckpt_epoch,
        "best_epoch": ckpt_epoch,
        "val_macro_f1_at_selection": ckpt_val_macro_f1,
        "best_val_macro_f1": ckpt_val_macro_f1,
        "test_sample_count": len(test_dataset),
        "test_loss": round(test_loss, 4),
        "test_accuracy": round(test_metrics.get("test_accuracy", 0.0), 2),
        "accuracy": round(test_metrics.get("test_accuracy", 0.0), 2),
        "micro_precision": test_metrics["micro_precision"],
        "micro_recall": test_metrics["micro_recall"],
        "micro_f1": test_metrics["micro_f1"],
        "macro_precision": test_metrics["macro_precision"],
        "macro_recall": test_metrics["macro_recall"],
        "macro_f1": test_metrics["macro_f1"],
        "threshold": args.threshold,
        "per_class": test_metrics["per_class"],
        "class_mapping": IDX_TO_LABEL,
        "classes": BEN_CLASSES,
        "num_classes": len(BEN_CLASSES),
        "evaluation_duration_sec": round(eval_duration, 2),
        "evaluation_config": {
            "checkpoint": str(ckpt_path),
            "batch_size": args.batch_size,
            "num_workers": eval_num_workers,
            "pin_memory": pin_memory,
            "threshold": args.threshold,
            "manifest": str(test_manifest),
            "device": str(device),
            "gpu_name": gpu_name,
        },
    }

    # Save test_evaluation.json
    test_eval_path = output_dir / "test_evaluation.json"
    with open(test_eval_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"Saved test evaluation results to: {test_eval_path}")

    # Save metrics.json (for downstream evaluation tools and API consistency)
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"Saved test metrics to: {metrics_path}")

    # 9. Print Comprehensive Summary
    logger.success("=" * 70)
    logger.success("TEST EVALUATION COMPLETE (EVALUATION-ONLY MODE)")
    logger.success("=" * 70)
    logger.info(f"Checkpoint Evaluated:   {ckpt_path}")
    logger.info(f"Checkpoint Epoch:       {ckpt_epoch}")
    logger.info(f"Val Macro F1 (Ep {ckpt_epoch}):  {ckpt_val_macro_f1}")
    logger.info(f"Test Samples Evaluated: {len(test_dataset):,}")
    logger.info(f"Evaluation Duration:    {eval_duration:.2f}s ({eval_duration/60:.2f}m)")
    logger.info(f"Test Loss:              {test_loss:.4f}")
    logger.info(f"Test Accuracy:          {test_metrics.get('test_accuracy', 0.0):.2f}%")
    logger.info(f"Test Micro F1:          {test_metrics['micro_f1']:.4f}")
    logger.info(f"Test Macro F1:          {test_metrics['macro_f1']:.4f}")
    logger.info(f"Test Micro Precision:   {test_metrics['micro_precision']:.4f}")
    logger.info(f"Test Micro Recall:      {test_metrics['micro_recall']:.4f}")
    logger.info(f"Test Macro Precision:   {test_metrics['macro_precision']:.4f}")
    logger.info(f"Test Macro Recall:      {test_metrics['macro_recall']:.4f}")
    logger.info("Preserved Trained Artifacts:")
    logger.info(f"  • Best Model (Epoch 19):  {output_dir / 'best_model.pth'}")
    logger.info(f"  • Latest Model (Epoch 20):{output_dir / 'latest_model.pth'}")
    logger.info(f"  • Final Model (Epoch 20): {output_dir / 'final_model.pth'}")
    logger.info(f"  • Training History:       {output_dir / 'training_history.json'}")
    logger.info("Generated Evaluation Artifacts:")
    logger.info(f"  • Test Evaluation JSON:   {test_eval_path}")
    logger.info(f"  • Test Metrics JSON:      {metrics_path}")
    logger.success("=" * 70)


# ─── Main Execution Pipeline ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Astra AI — BigEarthNet v2 ResNet-50 Classifier Training Pipeline"
    )

    parser.add_argument(
        "--manifest_dir",
        type=str,
        default="datasets/processed/bigearthnet_resnet50_full/manifests",
        help="Directory containing clean manifests (train.csv, val.csv, test.csv) and dataset_statistics.json",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="backend/models/bigearthnet_resnet50_v2_full",
        help="Dedicated output directory for new full training run checkpoints and artifacts",
    )
    parser.add_argument(
        "--repo_root",
        type=str,
        default=str(Path(__file__).resolve().parents[2]),
        help="Absolute path to repo root to resolve relative image paths",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Number of training epochs (default: 20)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=64,
        help="Batch size (default: 64)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Initial learning rate (default: 1e-4)",
    )
    parser.add_argument(
        "--weight_decay",
        type=float,
        default=1e-4,
        help="Weight decay for AdamW optimizer (default: 1e-4)",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=5,
        help="Early stopping patience in epochs based on validation Macro F1 (default: 5, 0 to disable)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Multi-label probability threshold for metrics (default: 0.5)",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=4,
        help="DataLoader worker count (default: 4, optimized for multi-core Windows systems)",
    )
    parser.add_argument(
        "--use_class_weights",
        dest="use_class_weights",
        action="store_true",
        default=True,
        help="Enable positive class weighting in BCE loss using training statistics (default: True)",
    )
    parser.add_argument(
        "--no_class_weights",
        dest="use_class_weights",
        action="store_false",
        help="Disable positive class weighting in BCE loss (use unweighted BCE)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint (.pth) to resume training from",
    )
    parser.add_argument(
        "--sanity_check_only",
        action="store_true",
        help="Run only pre-flight sanity checks and exit without training",
    )
    parser.add_argument(
        "--evaluate_only",
        action="store_true",
        help="Bypass all training and execute evaluation-only on the test set using a specified checkpoint",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint (.pth) to evaluate in evaluate_only mode (defaults to <output_dir>/best_model.pth)",
    )

    args = parser.parse_args()

    # For evaluate_only mode: default num_workers to 0 if not explicitly supplied
    if args.evaluate_only and "--num_workers" not in sys.argv:
        args.num_workers = 0

    # 1. Reproducibility setup
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    # 2. Paths
    repo_root = Path(args.repo_root).resolve()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_absolute():
        manifest_dir = (repo_root / manifest_dir).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()

    # Checkpoint safety check: do not overwrite original checkpoint or baseline directory
    original_ckpt = (repo_root / "backend" / "models" / "baseline" / "ben_classifier.pth").resolve()
    if output_dir == original_ckpt.parent:
        logger.warning(f"Output directory is baseline directory {output_dir}. Creating dedicated training subfolder.")
        output_dir = repo_root / "backend" / "models" / "bigearthnet_resnet50_v2_full"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Environment & Hardware Detection
    cuda_available = torch.cuda.is_available()
    device = torch.device("cuda:0" if cuda_available else "cpu")
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A"
    cuda_version = torch.version.cuda if cuda_available else "N/A"
    torchvision_ver = getattr(models, "__version__", "unknown")
    try:
        import torchvision
        torchvision_ver = torchvision.__version__
    except Exception:
        pass

    # Early Exit: Evaluation-Only Mode (Completely bypasses dataset sanity checks and training loop)
    if args.evaluate_only:
        run_evaluation_only(
            args=args,
            repo_root=repo_root,
            manifest_dir=manifest_dir,
            output_dir=output_dir,
            original_ckpt=original_ckpt,
            device=device,
            gpu_name=gpu_name,
        )
        return

    # 4. Pre-flight Dataset Sanity Checks
    sanity_results = dataset_sanity_check(manifest_dir, repo_root)

    # 5. Transforms (Sentinel-2 uint16 BOA reflectance scaled to [0, 1] float32 tensors)
    train_transform = T.Compose([
        T.Resize((224, 224), antialias=True),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomVerticalFlip(p=0.5),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    eval_transform = T.Compose([
        T.Resize((224, 224), antialias=True),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 6. Instantiate Datasets & DataLoaders
    train_manifest = manifest_dir / "train.csv" if (manifest_dir / "train.csv").exists() else manifest_dir / "bigearthnet_train.csv"
    val_manifest = manifest_dir / "val.csv" if (manifest_dir / "val.csv").exists() else manifest_dir / "bigearthnet_val.csv"
    test_manifest = manifest_dir / "test.csv" if (manifest_dir / "test.csv").exists() else manifest_dir / "bigearthnet_test.csv"

    train_dataset = BigEarthNetManifestDataset(
        train_manifest, repo_root, transform=train_transform
    )
    val_dataset = BigEarthNetManifestDataset(
        val_manifest, repo_root, transform=eval_transform
    )
    test_dataset = BigEarthNetManifestDataset(
        test_manifest, repo_root, transform=eval_transform
    )

    pin_memory = (device.type == "cuda")
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
        persistent_workers=(args.num_workers > 0),
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
        persistent_workers=(args.num_workers > 0),
        drop_last=False,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
        persistent_workers=(args.num_workers > 0),
        drop_last=False,
    )

    # 7. Model Construction
    model = build_model(num_classes=len(BEN_CLASSES), pretrained=True).to(device)

    # 8. Loss Construction (with rigorous class-weight loading)
    if args.use_class_weights:
        pos_weight_tensor = load_and_validate_class_weights(manifest_dir, BEN_CLASSES, device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)
        class_weighting_mode = "weighted (BCEWithLogitsLoss with training pos_weights)"
    else:
        criterion = nn.BCEWithLogitsLoss()
        class_weighting_mode = "unweighted (standard BCEWithLogitsLoss)"
        logger.warning("Class weighting explicitly disabled. Using unweighted BCEWithLogitsLoss.")

    # 9. Optimizer, Scheduler, Scaler
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    # 10. Resume from Checkpoint if requested
    start_epoch = 1
    best_val_macro_f1 = -1.0
    best_epoch = -1
    best_val_metrics: Dict[str, Any] = {}
    training_history: List[Dict[str, Any]] = []

    if args.resume:
        resume_path = Path(args.resume)
        if not resume_path.is_absolute():
            resume_path = (repo_root / resume_path).resolve()

        if not resume_path.exists():
            raise FileNotFoundError(f"FATAL: Resume checkpoint does not exist: {resume_path}")

        # Explicit safety check: reject legacy baseline checkpoint
        if resume_path == original_ckpt or (resume_path.name == "ben_classifier.pth" and "baseline" in str(resume_path)):
            raise ValueError(
                f"FATAL: Incompatible checkpoint rejected! {resume_path}\n"
                f"The legacy baseline checkpoint belongs to the 2019 conference taxonomy and is not a valid v2.0 resumable checkpoint."
            )

        logger.info(f"Loading resume checkpoint: {resume_path}")
        checkpoint = torch.load(str(resume_path), map_location=device)

        required_keys = ["model_state_dict", "epoch"]
        for k in required_keys:
            if k not in checkpoint:
                raise KeyError(f"FATAL: Checkpoint {resume_path.name} missing required key: '{k}'")

        num_ckpt_classes = checkpoint.get("num_classes")
        if num_ckpt_classes is not None and num_ckpt_classes != len(BEN_CLASSES):
            raise ValueError(
                f"FATAL: Architecture mismatch in checkpoint: expected {len(BEN_CLASSES)} classes, found {num_ckpt_classes}"
            )

        state_dict = checkpoint["model_state_dict"]
        if "fc.weight" in state_dict and state_dict["fc.weight"].shape[0] != len(BEN_CLASSES):
            raise ValueError(
                f"FATAL: Classifier head weight shape mismatch: expected {len(BEN_CLASSES)} output classes, "
                f"found {state_dict['fc.weight'].shape[0]}"
            )

        model.load_state_dict(state_dict)

        if "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "scheduler_state_dict" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        start_epoch = checkpoint["epoch"] + 1
        best_val_macro_f1 = checkpoint.get("best_val_macro_f1", -1.0)
        best_epoch = checkpoint.get("best_epoch", checkpoint.get("epoch", -1))
        best_val_metrics = checkpoint.get("val_metrics", {})
        logger.success(
            f"Successfully resumed from epoch {checkpoint['epoch']} "
            f"(best val Macro F1: {best_val_macro_f1:.4f} at epoch {best_epoch}). Next training epoch: {start_epoch}"
        )

    # 11. Environment & Configuration Logging
    logger.info("=" * 70)
    logger.info("ASTRA RESNET-50 BIGEARTHNET V2.0 TRAINING PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Python Version:         {sys.version.split()[0]}")
    logger.info(f"PyTorch Version:        {torch.__version__}")
    logger.info(f"Torchvision Version:    {torchvision_ver}")
    logger.info(f"CUDA Available:         {cuda_available}")
    logger.info(f"CUDA Runtime Version:   {cuda_version}")
    logger.info(f"Selected Device:        {device}")
    logger.info(f"GPU Name:               {gpu_name}")
    if cuda_available:
        cap = torch.cuda.get_device_capability(0)
        logger.info(f"Compute Capability:     {cap[0]}.{cap[1]}")
    logger.info(f"Dataset Name:           BigEarthNet v2.0")
    logger.info(f"Train Samples:          {len(train_dataset):,}")
    logger.info(f"Validation Samples:     {len(val_dataset):,}")
    logger.info(f"Test Samples:           {len(test_dataset):,}")
    logger.info(f"Classes:                {len(BEN_CLASSES)}")
    logger.info(f"Class Weighting:        {class_weighting_mode}")
    logger.info(f"Repo Root:              {repo_root}")
    logger.info(f"Manifest Dir:           {manifest_dir}")
    logger.info(f"Output Dir:             {output_dir}")
    logger.info(f"Total Epochs:           {args.epochs}")
    logger.info(f"Start Epoch:            {start_epoch}")
    logger.info(f"Batch Size:             {args.batch_size}")
    logger.info(f"DataLoader Workers:     {args.num_workers}")
    logger.info(f"Learning Rate:          {args.lr}")
    logger.info(f"Weight Decay:           {args.weight_decay}")
    logger.info(f"Patience (Early Stop):  {args.patience if args.patience > 0 else 'DISABLED'}")
    logger.info(f"Resume Checkpoint:      {args.resume if args.resume else 'None (Fresh training)'}")
    logger.info(f"Random Seed:            {args.seed}")
    logger.info(f"Classification Task:    19-Class Multi-Label LULC")
    logger.info("=" * 70)

    # Report Class Distribution in Training Set
    train_count = len(train_dataset)
    logger.info(f"Class Distribution in Training Set ({train_count:,} samples):")
    for cls_idx, cls_name in enumerate(BEN_CLASSES):
        count = sanity_results["class_counts_train"][cls_name]
        pct = (count / max(train_count, 1)) * 100
        logger.info(f"  [{cls_idx:02d}] {cls_name:<40}: {count:>7,d} pos ({pct:5.2f}%)")

    # 12. DataLoader & Forward Pass Sanity Check
    dataloader_sanity_check(train_loader, model, criterion, device)

    # Save class_mapping.json immediately
    class_mapping_path = output_dir / "class_mapping.json"
    with open(class_mapping_path, "w", encoding="utf-8") as f:
        json.dump(IDX_TO_LABEL, f, indent=2)
    logger.info(f"Saved class mapping to {class_mapping_path}")

    # Save initial config.json
    config_dict = {
        "timestamp": datetime.now().isoformat(),
        "seed": args.seed,
        "python_version": sys.version.split()[0],
        "pytorch_version": torch.__version__,
        "torchvision_version": torchvision_ver,
        "cuda_runtime_version": cuda_version,
        "gpu_name": gpu_name,
        "model_architecture": "resnet50",
        "num_classes": len(BEN_CLASSES),
        "classifier_head": "nn.Linear(2048, 19)",
        "loss_function": "BCEWithLogitsLoss",
        "class_weighting": class_weighting_mode,
        "optimizer": "AdamW",
        "learning_rate": args.lr,
        "weight_decay": args.weight_decay,
        "scheduler": "CosineAnnealingLR",
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "num_workers": args.num_workers,
        "patience": args.patience,
        "threshold": args.threshold,
        "resume": args.resume,
        "dataset_splits": {
            "train": len(train_dataset),
            "val": len(val_dataset),
            "test": len(test_dataset),
        },
        "classes": BEN_CLASSES,
        "class_frequencies_train": sanity_results["class_counts_train"],
        "preprocessing": {
            "resolution": [224, 224],
            "normalization_mean": [0.485, 0.456, 0.406],
            "normalization_std": [0.229, 0.224, 0.225],
            "input_bands": ["B04 (Red)", "B03 (Green)", "B02 (Blue)"],
            "scaling": "Deterministic Level-2A physical reflectance scaling (DN / 10000.0) into [0.0, 1.0]",
        },
    }
    config_path = output_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    logger.info(f"Saved configuration to {config_path}")

    # ─── Training Safety Gate: Sanity Check Mode ─────────────────────────────
    if args.sanity_check_only:
        logger.success("Sanity check mode completed successfully. Exiting cleanly without training.")
        return

    # 13. Training Loop
    logger.info("=" * 70)
    logger.info(f"STARTING TRAINING LOOP: EPOCHS {start_epoch} TO {args.epochs} (Batch Size={args.batch_size})")
    logger.info("=" * 70)

    patience_counter = 0
    early_stop_triggered = False
    total_train_start = time.perf_counter()

    for epoch in range(start_epoch, args.epochs + 1):
        t0 = time.perf_counter()

        train_loss, train_acc = train_one_epoch(
            model=model,
            loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            scaler=scaler,
            device=device,
            epoch=epoch,
            total_epochs=args.epochs,
            threshold=args.threshold,
        )

        val_loss, val_metrics, val_acc = validate_one_epoch(
            model=model,
            loader=val_loader,
            criterion=criterion,
            device=device,
            epoch=epoch,
            total_epochs=args.epochs,
            threshold=args.threshold,
        )

        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step()
        epoch_time = time.perf_counter() - t0

        # Record epoch metrics with numeric accuracy percentages
        history_entry = {
            "epoch": epoch,
            "train_accuracy": round(train_acc, 2),
            "val_accuracy": round(val_acc, 2),
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4),
            "micro_precision": val_metrics["micro_precision"],
            "micro_recall": val_metrics["micro_recall"],
            "micro_f1": val_metrics["micro_f1"],
            "macro_precision": val_metrics["macro_precision"],
            "macro_recall": val_metrics["macro_recall"],
            "macro_f1": val_metrics["macro_f1"],
            "lr": current_lr,
            "epoch_duration_sec": round(epoch_time, 2),
        }
        training_history.append(history_entry)

        # Print Clean Epoch Summary (Concisely focused on Train & Val Accuracy)
        print("=" * 60)
        print(f"Epoch {epoch:02d}/{args.epochs:02d}")
        print(f"Train Accuracy:  {train_acc:6.2f}%")
        print(f"Val Accuracy:    {val_acc:6.2f}%")
        print("=" * 60)

        # Checkpoint selection & Early Stopping based strictly on validation Macro F1
        val_macro_f1 = val_metrics["macro_f1"]
        if val_macro_f1 > best_val_macro_f1:
            best_val_macro_f1 = val_macro_f1
            best_epoch = epoch
            best_val_metrics = val_metrics
            patience_counter = 0  # Reset patience

            best_ckpt_path = output_dir / "best_model.pth"
            save_checkpoint_atomic(
                {
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(),
                    "epoch": epoch,
                    "best_epoch": best_epoch,
                    "best_val_macro_f1": best_val_macro_f1,
                    "val_metrics": val_metrics,
                    "train_accuracy": round(train_acc, 2),
                    "val_accuracy": round(val_acc, 2),
                    "threshold": args.threshold,
                    "class_mapping": IDX_TO_LABEL,
                    "classes": BEN_CLASSES,
                    "num_classes": len(BEN_CLASSES),
                    "architecture": "resnet50",
                    "config": vars(args),
                },
                best_ckpt_path,
            )
            print(f"  ★ New best checkpoint saved: Val Macro F1 = {best_val_macro_f1:.4f} -> {best_ckpt_path.name}")
        else:
            if args.patience > 0:
                patience_counter += 1
                logger.info(
                    f"Early stopping patience: {patience_counter}/{args.patience} "
                    f"(best Val Macro F1: {best_val_macro_f1:.4f} at epoch {best_epoch})"
                )
                if patience_counter >= args.patience:
                    logger.warning(
                        f"Early stopping triggered at epoch {epoch}! "
                        f"Validation Macro F1 did not improve for {args.patience} consecutive epochs."
                    )
                    early_stop_triggered = True

        # Save latest_model.pth atomically at the end of every completed epoch
        latest_ckpt_path = output_dir / "latest_model.pth"
        save_checkpoint_atomic(
            {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "epoch": epoch,
                "best_epoch": best_epoch,
                "best_val_macro_f1": best_val_macro_f1,
                "val_metrics": val_metrics,
                "train_accuracy": round(train_acc, 2),
                "val_accuracy": round(val_acc, 2),
                "threshold": args.threshold,
                "class_mapping": IDX_TO_LABEL,
                "classes": BEN_CLASSES,
                "num_classes": len(BEN_CLASSES),
                "architecture": "resnet50",
                "config": vars(args),
            },
            latest_ckpt_path,
        )

        if early_stop_triggered:
            break

    total_train_duration = time.perf_counter() - total_train_start

    # Save final model
    final_ckpt_path = output_dir / "final_model.pth"
    save_checkpoint_atomic(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "epoch": epoch,
            "best_epoch": best_epoch,
            "best_val_macro_f1": best_val_macro_f1,
            "final_val_loss": val_loss,
            "final_val_macro_f1": val_metrics["macro_f1"],
            "train_accuracy": round(train_acc, 2),
            "val_accuracy": round(val_acc, 2),
            "threshold": args.threshold,
            "class_mapping": IDX_TO_LABEL,
            "classes": BEN_CLASSES,
            "num_classes": len(BEN_CLASSES),
            "architecture": "resnet50",
            "config": vars(args),
        },
        final_ckpt_path,
    )
    logger.info(f"Saved final checkpoint to {final_ckpt_path}")

    # Save training history
    history_path = output_dir / "training_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(training_history, f, indent=2)
    logger.info(f"Saved training history to {history_path}")

    # 14. Final Test Set Evaluation using Best Checkpoint
    logger.info("=" * 70)
    logger.info(f"EVALUATING BEST CHECKPOINT ON UNTOUCHED TEST SET ({len(test_dataset):,} samples)")
    logger.info("=" * 70)

    best_checkpoint = torch.load(str(output_dir / "best_model.pth"), map_location=device)
    model.load_state_dict(best_checkpoint["model_state_dict"])

    # For evaluation stability on Windows, use single process loader (num_workers=0)
    eval_test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
        persistent_workers=False,
        drop_last=False,
    )

    test_loss, test_metrics = evaluate_test_set(
        model=model,
        test_loader=eval_test_loader,
        criterion=criterion,
        device=device,
        threshold=args.threshold,
    )

    test_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "checkpoint_path": str(output_dir / "best_model.pth"),
        "checkpoint_epoch": best_epoch,
        "best_epoch": best_epoch,
        "val_macro_f1_at_selection": best_val_macro_f1,
        "best_val_macro_f1": best_val_macro_f1,
        "test_sample_count": len(test_dataset),
        "test_loss": round(test_loss, 4),
        "test_accuracy": round(test_metrics.get("test_accuracy", 0.0), 2),
        "accuracy": round(test_metrics.get("test_accuracy", 0.0), 2),
        "micro_precision": test_metrics["micro_precision"],
        "micro_recall": test_metrics["micro_recall"],
        "micro_f1": test_metrics["micro_f1"],
        "macro_precision": test_metrics["macro_precision"],
        "macro_recall": test_metrics["macro_recall"],
        "macro_f1": test_metrics["macro_f1"],
        "threshold": args.threshold,
        "per_class": test_metrics["per_class"],
        "class_mapping": IDX_TO_LABEL,
        "classes": BEN_CLASSES,
        "num_classes": len(BEN_CLASSES),
        "evaluation_config": {
            "checkpoint": str(output_dir / "best_model.pth"),
            "batch_size": args.batch_size,
            "num_workers": 0,
            "threshold": args.threshold,
            "manifest": str(test_manifest),
            "device": str(device),
            "gpu_name": gpu_name,
        },
    }

    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"Saved final test metrics to {metrics_path}")

    test_eval_path = output_dir / "test_evaluation.json"
    with open(test_eval_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"Saved complete test evaluation to {test_eval_path}")

    # 15. Final Comprehensive Summary
    logger.success("=" * 70)
    logger.success("TRAINING PIPELINE COMPLETE")
    logger.success("=" * 70)
    logger.info(f"Total Duration:         {total_train_duration:.2f}s ({total_train_duration/60:.2f}m)")
    logger.info(f"Best Validation Epoch:  {best_epoch}/{args.epochs}")
    logger.info(f"Best Val Macro F1:      {best_val_macro_f1:.4f}")
    logger.info(f"Test Loss:              {test_loss:.4f}")
    logger.info(f"Test Micro F1:          {test_metrics['micro_f1']:.4f}")
    logger.info(f"Test Macro F1:          {test_metrics['macro_f1']:.4f}")
    logger.info("Saved Artifacts:")
    logger.info(f"  • Best Model:         {output_dir / 'best_model.pth'}")
    logger.info(f"  • Latest Model:       {output_dir / 'latest_model.pth'}")
    logger.info(f"  • Final Model:        {output_dir / 'final_model.pth'}")
    logger.info(f"  • Training History:   {history_path}")
    logger.info(f"  • Test Metrics:       {metrics_path}")
    logger.info(f"  • Config:             {config_path}")
    logger.info(f"  • Class Mapping:      {class_mapping_path}")
    logger.success("=" * 70)


if __name__ == "__main__":
    main()
