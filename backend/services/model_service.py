"""
Astra AI - Model Service
Centralized GPU device management, model registry, and inference pipeline.
"""

import json
import time
from pathlib import Path
from typing import Any, Optional
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image
from loguru import logger

# Temperature scaler JSON path (written by calibrate_temperature.py)
_TEMP_SCALER_PATH = Path(__file__).resolve().parent.parent / "models" / "bigearthnet_resnet50_v2_full" / "temp_scaler.json"

# ─── Centralized Device Selection ───────────────────────────────────────────────
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# ─── Authoritative 19 BigEarthNet Classes ───────────────────────────────────────
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
    "Natural grassland",
    "Moors and heathland",
    "Sclerophyllous vegetation",
    "Transitional woodland shrub",
    "Beaches, dunes, and sands",
    "Inland wetlands",
    "Coastal wetlands",
    "Water bodies",
]

IDX_TO_LABEL: dict[int, str] = {i: label for i, label in enumerate(BEN_CLASSES)}
LABEL_TO_IDX: dict[str, int] = {label: i for i, label in enumerate(BEN_CLASSES)}

# ─── Model Registry ─────────────────────────────────────────────────────────────
class ModelService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.device = DEVICE
            cls._instance.models = {}
            cls._instance.transforms = {}
            cls._instance.manifests = {}
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        """Log engine startup and initialize transforms."""
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
        cap = torch.cuda.get_device_capability(0) if cuda_avail else (0, 0)
        
        logger.info("=" * 50)
        logger.info("ASTRA GPU ENGINE")
        logger.info("=" * 50)
        logger.info(f"Device:             {self.device}")
        logger.info(f"GPU:                {gpu_name}")
        logger.info(f"Compute Capability: {cap}")
        logger.info(f"PyTorch:            {torch.__version__}")
        logger.info(f"PyTorch CUDA:       {torch.version.cuda}")
        logger.info("=" * 50)

        # Standard BigEarthNet evaluation transform
        self.transforms["ben_classifier"] = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Load temperature scaler if available
        self.temperature: float = 1.0
        self.calibration_applied: bool = False
        if _TEMP_SCALER_PATH.exists():
            try:
                with open(_TEMP_SCALER_PATH) as f:
                    scaler = json.load(f)
                self.temperature = float(scaler.get("temperature", 1.0))
                self.calibration_applied = True
                logger.success(
                    f"Temperature scaler loaded: T={self.temperature:.4f} "
                    f"(NLL: {scaler.get('pre_calibration_nll', '?')} -> {scaler.get('post_calibration_nll', '?')})"
                )
            except Exception as e:
                logger.warning(f"Could not load temperature scaler: {e}. Using T=1.0.")
        else:
            logger.info("No temperature scaler found. Using raw sigmoid (T=1.0). "
                        "Run calibrate_temperature.py to generate scaler.")

    def get_checkpoint_path(self, filename: str = "best_model.pth") -> Optional[Path]:
        """Resolve checkpoint path safely across runtime directories, prioritizing the v2 full production model."""
        base_dir = Path(__file__).resolve().parent.parent
        candidates = [
            base_dir / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth",
            Path("./backend/models/bigearthnet_resnet50_v2_full/best_model.pth"),
            base_dir / "models" / filename,
            Path("./models") / filename,
            Path("../models") / filename,
            base_dir.parent / "models" / filename,
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def load_ben_classifier(self) -> nn.Module:
        """Load and keep ResNet-50 resident in GPU memory."""
        if "ben_classifier" in self.models and self.models["ben_classifier"] is not None:
            return self.models["ben_classifier"]

        ckpt_path = self.get_checkpoint_path("best_model.pth")
        if not ckpt_path:
            ckpt_path = self.get_checkpoint_path("ben_classifier.pth")
        if not ckpt_path:
            raise FileNotFoundError("ResNet-50 BigEarthNet checkpoint not found in models directories.")

        logger.info(f"Loading ResNet-50 BigEarthNet weights from {ckpt_path} onto {self.device}...")
        model = models.resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(BEN_CLASSES))

        state_dict = torch.load(str(ckpt_path), map_location=self.device)
        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        elif "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        model.load_state_dict(state_dict)
        model.eval()
        for param in model.parameters():
            param.requires_grad = False
        model.to(self.device)

        self.models["ben_classifier"] = model
        logger.success(f"ResNet-50 BigEarthNet classifier resident on {self.device}.")
        return model

    def validate_image(self, image_path: Path) -> Path:
        """Verify image exists and can be opened."""
        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            raise ValueError(f"Corrupted or invalid image at {image_path}: {e}")
        return image_path

    def preprocess(self, image_path: Path) -> torch.Tensor:
        """Convert input image to model tensor."""
        self.validate_image(image_path)
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB")
            transform = self.transforms["ben_classifier"]
            tensor = transform(rgb_img).unsqueeze(0)
        return tensor

    def predict_scene(self, image_path: Path | str) -> dict[str, Any]:
        """
        Execute GPU inference on ResNet-50 BigEarthNet classifier.
        Returns structured multi-label prediction with accurate synchronized timings.
        """
        image_path = Path(image_path)
        t_total_start = time.perf_counter()

        # 1. Preprocessing
        t_pre_start = time.perf_counter()
        tensor = self.preprocess(image_path).to(self.device, non_blocking=True)
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        t_pre_end = time.perf_counter()

        # 2. Model Forward Pass
        model = self.load_ben_classifier()
        t_inf_start = time.perf_counter()
        with torch.inference_mode():
            logits = model(tensor)
            if self.device.type == "cuda":
                torch.cuda.synchronize(self.device)
        t_inf_end = time.perf_counter()

        # 3. Postprocessing
        t_post_start = time.perf_counter()
        # Raw probabilities before temperature scaling
        raw_probs = torch.sigmoid(logits).squeeze(0).cpu().numpy()
        raw_logits_list = [round(float(x), 4) for x in logits.squeeze(0).cpu().numpy().tolist()]

        # Apply temperature scaling if calibrated (T != 1.0)
        logits_calibrated = logits / self.temperature
        probs = torch.sigmoid(logits_calibrated).squeeze(0).cpu().numpy()
        
        # Multi-label threshold at 0.5
        threshold = 0.5
        predicted_indices = np.where(probs >= threshold)[0].tolist()
        if not predicted_indices:
            # Fallback to top-3 highest confidence classes
            predicted_indices = np.argsort(probs)[-3:][::-1].tolist()

        label_probs = {IDX_TO_LABEL[i]: round(float(probs[i]), 4) for i in range(len(BEN_CLASSES))}
        raw_label_probs = {IDX_TO_LABEL[i]: round(float(raw_probs[i]), 4) for i in range(len(BEN_CLASSES))}
        top_predictions = [
            {"label": IDX_TO_LABEL[i], "probability": round(float(probs[i]), 4)}
            for i in np.argsort(probs)[::-1][:5]
        ]
        
        top_class = top_predictions[0]["label"]
        top_confidence = top_predictions[0]["probability"]

        t_post_end = time.perf_counter()
        t_total_end = time.perf_counter()

        # Timings in milliseconds
        timings = {
            "preprocess_ms": round((t_pre_end - t_pre_start) * 1000, 2),
            "inference_ms": round((t_inf_end - t_inf_start) * 1000, 2),
            "postprocess_ms": round((t_post_end - t_post_start) * 1000, 2),
            "total_ms": round((t_total_end - t_total_start) * 1000, 2),
        }

        # Memory diagnostics
        vram_stats = {}
        if self.device.type == "cuda":
            props = torch.cuda.get_device_properties(self.device)
            vram_stats = {
                "allocated_mb": round(torch.cuda.memory_allocated(self.device) / (1024 ** 2), 2),
                "reserved_mb": round(torch.cuda.memory_reserved(self.device) / (1024 ** 2), 2),
                "total_mb": round(props.total_memory / (1024 ** 2), 2),
            }

        return {
            "type": "classification",
            "model_id": "resnet50-bigearthnet",
            "device": str(self.device),
            "prediction": top_class,
            "confidence": top_confidence,
            "labels": [IDX_TO_LABEL[i] for i in predicted_indices],
            "top_predictions": top_predictions,
            "all_probabilities": label_probs,
            "raw_probabilities": raw_label_probs,
            "raw_logits": raw_logits_list,
            "timings": timings,
            "vram": vram_stats,
            "calibration_applied": self.calibration_applied,
            "temperature_T": round(self.temperature, 4),
        }

    def offload_ben_classifier(self, to_cpu: bool = True) -> None:
        """Controlled offload of ResNet-50 from GPU memory to CPU or eviction."""
        if "ben_classifier" in self.models and self.models["ben_classifier"] is not None:
            if to_cpu:
                self.models["ben_classifier"] = self.models["ben_classifier"].to("cpu")
                self.device = torch.device("cpu")
                logger.info("ResNet-50 BigEarthNet classifier offloaded to CPU.")
            else:
                del self.models["ben_classifier"]
                self.models["ben_classifier"] = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                logger.info("ResNet-50 BigEarthNet classifier evicted from memory.")

# Global singleton
model_service = ModelService()
