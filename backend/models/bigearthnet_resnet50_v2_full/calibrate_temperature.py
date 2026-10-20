"""
Astra AI - ResNet-50 Temperature Scaling Calibration
SIH26167 | Post-hoc confidence calibration for the BigEarthNet v2 classifier.

Temperature scaling fits a single scalar T on the validation set such that:
  calibrated_prob = sigmoid(logit / T)

This is the Platt-style post-hoc calibration approach (Guo et al., 2017):
  "On Calibration of Modern Neural Networks"

USAGE (manual, no retraining):
  cd <repo-root>/backend
  .\.venv\Scripts\python.exe models/bigearthnet_resnet50_v2_full/calibrate_temperature.py

OUTPUT:
  models/bigearthnet_resnet50_v2_full/temp_scaler.json
  {
    "temperature": T,
    "calibrated_at": "2026-09-20T...",
    "n_samples": N,
    "pre_calibration_nll": X.XX,
    "post_calibration_nll": X.XX,
    "method": "temperature_scaling"
  }
"""

import json
import time
import torch
import torch.nn as nn
import torchvision.models as tvm
import torchvision.transforms as T
from pathlib import Path
from typing import Optional
from loguru import logger

# ─── Configuration ─────────────────────────────────────────────────────────

CHECKPOINT_PATH = Path(__file__).parent / "best_model.pth"
SCALER_OUTPUT   = Path(__file__).parent / "temp_scaler.json"
IMAGES_DIR      = Path("datasets/processed/bigearthnet_resnet50_full/val/images")
LABELS_FILE     = Path("datasets/processed/bigearthnet_resnet50_full/val/labels.csv")
N_SAMPLES       = 256
NUM_CLASSES     = 19

BEN_CLASSES = [
    "Urban fabric", "Industrial or commercial units", "Arable land",
    "Permanent crops", "Pastures", "Complex cultivation patterns",
    "Land occupied by agriculture with natural vegetation", "Agro-forestry areas",
    "Broad-leaved forest", "Coniferous forest", "Mixed forest",
    "Natural grassland", "Moors and heathland", "Sclerophyllous vegetation",
    "Transitional woodland shrub", "Beaches, dunes, and sands",
    "Inland wetlands", "Coastal wetlands", "Water bodies",
]

TRANSFORM = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ─── Model Loading ───────────────────────────────────────────────────────────

def load_resnet50():
    model = tvm.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    state = torch.load(str(CHECKPOINT_PATH), map_location="cpu", weights_only=True)
    if "model_state_dict" in state:
        state = state["model_state_dict"]
    elif "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state)
    model.eval()
    return model


# ─── Logit Collection ────────────────────────────────────────────────────────

def collect_logits_and_labels(model: nn.Module, device: torch.device, n_samples: int):
    """
    Collect raw logits and labels from val images.
    Loads images from IMAGES_DIR; reads multi-label targets from LABELS_FILE if present.
    Falls back to synthetic labels if dataset files are absent.
    """
    from PIL import Image
    import csv

    all_logits = []
    all_labels = []

    images_dir = IMAGES_DIR
    if not images_dir.exists():
        raise FileNotFoundError(
            f"Val images not found at {images_dir}. "
            "Run dataset preprocessing before calibration."
        )

    # Load labels if available
    label_map: dict[str, list[int]] = {}
    if LABELS_FILE.exists():
        with open(LABELS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                patch_id = row["patch_id"]
                labels = [int(x) for x in row["labels"].split(",") if x.strip().isdigit()]
                label_map[patch_id] = labels

    image_files = sorted(images_dir.glob("*.tif"))[:n_samples]
    if len(image_files) == 0:
        image_files = sorted(images_dir.glob("*.png"))[:n_samples]
    if len(image_files) == 0:
        image_files = sorted(images_dir.glob("*.jpg"))[:n_samples]

    if len(image_files) == 0:
        raise FileNotFoundError(f"No image files found in {images_dir}")

    logger.info(f"Collecting logits from {len(image_files)} val images...")
    model = model.to(device)

    for img_path in image_files:
        try:
            with Image.open(img_path) as pil_img:
                rgb = pil_img.convert("RGB")
                tensor = TRANSFORM(rgb).unsqueeze(0).to(device)
            with torch.inference_mode():
                logit = model(tensor).squeeze(0).cpu()
            all_logits.append(logit)

            # Build multi-hot label vector
            patch_id = img_path.stem
            label_vec = torch.zeros(NUM_CLASSES)
            if patch_id in label_map:
                for idx in label_map[patch_id]:
                    if 0 <= idx < NUM_CLASSES:
                        label_vec[idx] = 1.0
            all_labels.append(label_vec)
        except Exception as e:
            logger.warning(f"Skipping {img_path.name}: {e}")

    if len(all_logits) == 0:
        raise RuntimeError("No logits collected — check image files.")

    return torch.stack(all_logits), torch.stack(all_labels)


# ─── Temperature Optimization ────────────────────────────────────────────────

def _bce_nll(logits: torch.Tensor, labels: torch.Tensor, temperature: float) -> float:
    """Binary cross-entropy NLL for multi-label classification at given temperature."""
    scaled = logits / temperature
    loss = nn.BCEWithLogitsLoss()(scaled, labels)
    return loss.item()


def optimize_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """
    Find optimal temperature T via golden-section search over [0.1, 10.0].
    Minimizes multi-label BCE NLL on validation logits.
    """
    from scipy.optimize import minimize_scalar
    result = minimize_scalar(
        lambda t: _bce_nll(logits, labels, t),
        bounds=(0.1, 10.0),
        method="bounded",
        options={"xatol": 1e-4, "maxiter": 200},
    )
    return float(result.x)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("ASTRA RESNET-50 TEMPERATURE SCALING CALIBRATION")
    logger.info("=" * 60)
    logger.info(f"Checkpoint: {CHECKPOINT_PATH}")
    logger.info(f"Val Images: {IMAGES_DIR}")
    logger.info(f"N Samples : {N_SAMPLES}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device    : {device}")

    if not CHECKPOINT_PATH.exists():
        logger.error(f"Checkpoint not found: {CHECKPOINT_PATH}")
        return

    model = load_resnet50()
    logger.success("ResNet-50 loaded successfully.")

    logits, labels = collect_logits_and_labels(model, device, N_SAMPLES)
    logger.success(f"Collected {len(logits)} samples. Logit shape: {logits.shape}")

    pre_nll = _bce_nll(logits, labels, temperature=1.0)
    logger.info(f"Pre-calibration  NLL (T=1.0): {pre_nll:.4f}")

    logger.info("Optimizing temperature scalar...")
    t_start = time.time()
    T_opt = optimize_temperature(logits, labels)
    elapsed = time.time() - t_start

    post_nll = _bce_nll(logits, labels, temperature=T_opt)
    logger.success(f"Optimal Temperature T = {T_opt:.4f}  (optimized in {elapsed:.2f}s)")
    logger.success(f"Post-calibration NLL (T={T_opt:.4f}): {post_nll:.4f}")
    logger.info(f"NLL improvement: {pre_nll - post_nll:.4f}")

    scaler_data = {
        "temperature": round(T_opt, 6),
        "calibrated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_samples": len(logits),
        "pre_calibration_nll": round(pre_nll, 6),
        "post_calibration_nll": round(post_nll, 6),
        "method": "temperature_scaling",
        "model_checkpoint": str(CHECKPOINT_PATH),
        "notes": "Single scalar T; calibrated probability = sigmoid(logit / T). Applied in model_service.predict_scene().",
    }

    with open(SCALER_OUTPUT, "w") as f:
        json.dump(scaler_data, f, indent=2)
    logger.success(f"Temperature scaler saved to {SCALER_OUTPUT}")
    logger.info(f"  temperature = {T_opt:.4f}")


if __name__ == "__main__":
    main()
