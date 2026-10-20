"""
Engine Layer — BigEarthNet Scene Classifier Wrapper
ResNet-50 scene classifier trained on BigEarthNet v2 (19 LULC classes).
This satisfies the SIH26167 mandatory requirement:
"at least one remote-sensing visual/VLM component adapted using BigEarthNet"
"""

from pathlib import Path
from typing import Any
import numpy as np
from loguru import logger
from orchestrator.schemas import ModelStatus
from engine.preprocessing import raster_to_8bit_rgb

# BigEarthNet v2 — 19 LULC class labels
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

def _resolve_checkpoint() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth",
        Path(__file__).resolve().parent.parent.parent / "models" / "ben_classifier.pth",
        Path("./backend/models/bigearthnet_resnet50_v2_full/best_model.pth"),
        Path("./models/bigearthnet_resnet50_v2_full/best_model.pth"),
        Path("./models/ben_classifier.pth"),
        Path("../models/ben_classifier.pth"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path("./models/ben_classifier.pth")

MODEL_CHECKPOINT = _resolve_checkpoint()


def get_model_status() -> ModelStatus:
    if MODEL_CHECKPOINT.exists():
        return ModelStatus.AVAILABLE
    return ModelStatus.NOT_CONFIGURED


def _load_classifier():
    """Load BigEarthNet ResNet-50 classifier. Returns (model, None)."""
    from services.model_service import model_service
    try:
        model = model_service.load_ben_classifier()
        return model, None
    except Exception as e:
        logger.error(f"Failed to load classifier: {e}")
        return None, None


def run_scene_classification(image_path: Path) -> dict[str, Any]:
    """
    Classify the scene using the BigEarthNet-trained ResNet-50 on GPU.
    Automatically applies windowed tiling for large GeoTIFF rasters (>512px).
    Returns structured multi-label class probabilities and spatial coverage.
    """
    logger.info(f"BigEarthNet GPU classification: {image_path.name}")
    try:
        from services.model_service import model_service

        # Check if raster is large and warrants spatial tiling
        is_geotiff = image_path.suffix.lower() in (".tif", ".tiff")
        if is_geotiff:
            try:
                import rasterio
                with rasterio.open(image_path) as src:
                    if max(src.width, src.height) > 512:
                        logger.info(f"Large GeoTIFF detected ({src.width}x{src.height}). Dispatching to TiledRasterProcessor.")
                        from engine.tiler import tiled_processor
                        return tiled_processor.process_raster(image_path, classifier_fn=model_service.predict_scene)
            except Exception as e:
                logger.warning(f"Could not open GeoTIFF for tiling check: {e}. Falling back to standard scene pass.")

        res = model_service.predict_scene(image_path)
        return {
            "type": "classification",
            "labels": res["labels"],
            "top_predictions": res["top_predictions"],
            "all_probabilities": res["all_probabilities"],
            "confidence": res["confidence"],
            "model": "ben-scene-classifier",
            "trained_on": "BigEarthNet v2 (19 LULC classes)",
            "timings": res.get("timings"),
            "device": res.get("device"),
            "calibration_applied": res.get("calibration_applied", False),
            "temperature_T": res.get("temperature_T", 1.0),
        }
    except Exception as exc:
        logger.error(f"BigEarthNet classification failed: {exc}")
        return {
            "type": "error",
            "message": f"Classification failed: {exc}"
        }
