"""
Orchestrator Layer — Model & Tool Registry
Defines the complete, static registry of all available models and deterministic tools.
The Gemini planner can ONLY select from entries in this registry.
This prevents hallucinated tool invocations and ensures strict spatial guardrails.
"""

from typing import Any
from pathlib import Path
from orchestrator.schemas import ModelStatus


def _get_backend_dir() -> Path:
    """Resolve the absolute path to the backend directory."""
    current = Path(__file__).resolve().parent
    if current.name == "orchestrator":
        return current.parent
    return Path("backend").resolve()


# ─── Tool Registry ────────────────────────────────────────────────────────────
# These are deterministic, non-ML geospatial ground-truth tools.

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "raster-metadata": {
        "id": "raster-metadata",
        "name": "Raster Metadata Extractor",
        "description": "Extracts CRS, resolution, bounds, band count, and statistics from a raster image.",
        "inputs": ["image_path"],
        "outputs": ["metadata_json"],
        "modalities": ["optical_rgb", "optical_ms", "sar", "panchromatic", "unknown"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "raster-stats": {
        "id": "raster-stats",
        "name": "Raster Band Statistics",
        "description": "Computes per-band statistics (mean, std, min, max, histogram) for a raster.",
        "inputs": ["image_path"],
        "outputs": ["band_stats_json"],
        "modalities": ["optical_rgb", "optical_ms", "sar", "panchromatic", "unknown"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "sar-stats": {
        "id": "sar-stats",
        "name": "SAR Raster Statistics",
        "description": "Computes backscatter statistics, intensity distribution, and calibrated dB values for SAR imagery.",
        "inputs": ["image_path"],
        "outputs": ["backscatter_stats", "intensity_histogram", "calibrated_db"],
        "modalities": ["sar"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "ndvi-calculator": {
        "id": "ndvi-calculator",
        "name": "NDVI Calculator",
        "description": "Computes Normalized Difference Vegetation Index from NIR and Red bands. Requires 4+ band multispectral imagery.",
        "inputs": ["image_path"],
        "outputs": ["ndvi_raster", "ndvi_stats"],
        "modalities": ["optical_ms"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "area-calculator": {
        "id": "area-calculator",
        "name": "Mask Area Calculator",
        "description": "Calculates real-world area of a binary mask in m², km², and hectares using pixel resolution (GSD).",
        "inputs": ["mask_or_geojson", "crs", "resolution"],
        "outputs": ["area_m2", "area_km2", "area_hectares"],
        "modalities": ["optical_rgb", "optical_ms", "sar", "panchromatic"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 2,
    },
    "bbox-area-calculator": {
        "id": "bbox-area-calculator",
        "name": "Bounding Box Area Calculator",
        "description": "Calculates the deterministic ground-truth area enclosed by a bounding box using pixel resolution or WGS84 geodesic coordinates.",
        "inputs": ["bbox", "resolution_or_crs"],
        "outputs": ["area_m2", "area_km2", "confidence_status"],
        "modalities": ["optical_rgb", "optical_ms", "sar", "panchromatic"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "polygon-area-calculator": {
        "id": "polygon-area-calculator",
        "name": "Polygon Geodesic Area Calculator",
        "description": "Calculates the ground-truth geodesic area of an arbitrary polygon on the WGS84 ellipsoid using Shapely and PyProj.",
        "inputs": ["coordinates"],
        "outputs": ["area_m2", "area_km2", "area_hectares", "confidence_status"],
        "modalities": ["optical_rgb", "optical_ms", "sar", "panchromatic"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "geodesic-distance-calculator": {
        "id": "geodesic-distance-calculator",
        "name": "Geodesic Distance Calculator",
        "description": "Calculates the exact great-circle distance in meters and kilometers between two geographical coordinates on WGS84.",
        "inputs": ["point1", "point2"],
        "outputs": ["distance_m", "distance_km", "confidence_status"],
        "modalities": ["optical_rgb", "optical_ms", "sar", "panchromatic"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 1,
    },
    "mask-overlay": {
        "id": "mask-overlay",
        "name": "Mask Overlay Visualizer",
        "description": "Overlays a binary mask on the source image and returns a composite PNG visualization.",
        "inputs": ["image_path", "mask_array"],
        "outputs": ["overlay_image_base64"],
        "modalities": ["optical_rgb", "optical_ms", "sar"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 1,
        "max_images": 2,
    },
    "change-area": {
        "id": "change-area",
        "name": "Change Area Calculator",
        "description": "Calculates total area of detected change from a binary change mask in m², km², and percentage.",
        "inputs": ["change_mask", "crs", "resolution"],
        "outputs": ["changed_area_m2", "changed_area_km2", "change_percentage"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": False,
        "is_deterministic": True,
        "min_images": 2,
        "max_images": 2,
    },
}


# ─── Model Registry ───────────────────────────────────────────────────────────
# These are specialized ML / Deep Learning models for satellite imagery analysis.

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "ben-scene-classifier": {
        "id": "ben-scene-classifier",
        "name": "BigEarthNet Scene Classifier (ResNet-50 v2)",
        "description": "Multi-label land use / land cover scene classifier trained on BigEarthNet v2. Classifies scene into 19 standard categories with calibrated probabilities.",
        "inputs": ["image_path"],
        "outputs": ["class_labels", "class_probabilities"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": False,
        "min_images": 1,
        "max_images": 1,
        "checkpoint": "models/bigearthnet_resnet50_v2_full/best_model.pth",
    },
    "bit-change-detection": {
        "id": "bit-change-detection",
        "name": "Siamese BIT Change Detector",
        "description": "Bitemporal Image Transformer for binary change detection on optical pairs. Generates high-resolution change mask, change area percentage, and region clusters.",
        "inputs": ["image_path_t1", "image_path_t2"],
        "outputs": ["change_mask", "change_percentage", "confidence"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": True,
        "min_images": 2,
        "max_images": 2,
        "checkpoint": "models/change_detection/checkpoints/best_model.pth",
    },
    "rsvqa-specialist": {
        "id": "rsvqa-specialist",
        "name": "RSVQA Visual Question Answering Specialist",
        "description": "Answers natural language questions about optical remote sensing scenes, conditioned on land cover classifications and spatial context.",
        "inputs": ["image_path", "question"],
        "outputs": ["answer_text", "confidence", "reasoning"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": False,
        "min_images": 1,
        "max_images": 1,
    },
    "vrsbench-caption": {
        "id": "vrsbench-caption",
        "name": "VRSBench Scene Captioner",
        "description": "Generates detailed, multi-sentence narrative captions of optical remote sensing scenes, describing buildings, terrain, roads, and land cover.",
        "inputs": ["image_path"],
        "outputs": ["caption_text", "salient_features", "confidence"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": False,
        "min_images": 1,
        "max_images": 1,
    },
    "vrsbench-grounding": {
        "id": "vrsbench-grounding",
        "name": "VRSBench Visual Grounding Specialist",
        "description": "Localizes objects or geographic regions specified by natural language text. Returns normalized bounding boxes [ymin, xmin, ymax, xmax].",
        "inputs": ["image_path", "text_reference"],
        "outputs": ["bounding_boxes", "detections_count", "confidence"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": False,
        "min_images": 1,
        "max_images": 1,
    },
    "cdvqa-specialist": {
        "id": "cdvqa-specialist",
        "name": "CDVQA Change-Based VQA Specialist",
        "description": "Answers natural language questions regarding bi-temporal changes between two co-registered optical scenes, conditioned on BIT change masks and LULC shift distributions.",
        "inputs": ["image_path_t1", "image_path_t2", "question"],
        "outputs": ["answer_text", "question_type", "evidence", "confidence"],
        "modalities": ["optical_rgb", "optical_ms"],
        "requires_gpu": True,
        "min_images": 2,
        "max_images": 2,
    },
    "cross-modal-specialist": {
        "id": "cross-modal-specialist",
        "name": "Optical + SAR Cross-Modal Specialist",
        "description": "Joint analysis of paired Optical (multispectral/RGB) and SAR (Sentinel-1 / RISAT) imagery. Disambiguates surface reflectance from microwave backscatter (dB) with strict evidence provenance.",
        "inputs": ["optical_image", "sar_image"],
        "outputs": ["optical_evidence", "sar_evidence", "cross_modal_synthesis", "confidence"],
        "modalities": ["cross_modal"],
        "requires_gpu": False,
        "min_images": 2,
        "max_images": 2,
    },
}


def _check_model_status(model_id: str) -> ModelStatus:
    """Dynamically check if a model's weights and dependencies are available."""
    backend_dir = _get_backend_dir()
    
    if model_id == "ben-scene-classifier":
        ckpt = backend_dir / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth"
        return ModelStatus.AVAILABLE if ckpt.exists() else ModelStatus.MODEL_UNAVAILABLE

    elif model_id == "bit-change-detection":
        ckpt1 = backend_dir / "models" / "change_detection" / "checkpoints" / "best_model.pth"
        ckpt2 = backend_dir / "models" / "change_detection" / "best_model.pth"
        return ModelStatus.AVAILABLE if (ckpt1.exists() or ckpt2.exists()) else ModelStatus.MODEL_UNAVAILABLE

    elif model_id == "rsvqa-specialist":
        module_path = backend_dir / "models" / "rsvqa" / "model.py"
        return ModelStatus.AVAILABLE if module_path.exists() else ModelStatus.MODEL_UNAVAILABLE

    elif model_id in ("vrsbench-caption", "vrsbench-grounding"):
        module_path = backend_dir / "models" / "captioning" / "model.py"
        return ModelStatus.AVAILABLE if module_path.exists() else ModelStatus.MODEL_UNAVAILABLE

    elif model_id == "cdvqa-specialist":
        module_path = backend_dir / "models" / "cdvqa" / "model.py"
        return ModelStatus.AVAILABLE if module_path.exists() else ModelStatus.MODEL_UNAVAILABLE

    elif model_id == "cross-modal-specialist":
        module_path = backend_dir / "models" / "cross_modal" / "specialist.py"
        return ModelStatus.AVAILABLE if module_path.exists() else ModelStatus.MODEL_UNAVAILABLE

    return ModelStatus.AVAILABLE


# ─── Combined Registry (for Gemini prompt) ────────────────────────────────────

def get_registry_for_prompt() -> str:
    """
    Returns a compact text representation of the full registry
    for injection into the Gemini planning prompt.
    Filters out models that are unavailable.
    """
    lines = ["=== AVAILABLE TOOLS (Deterministic, Non-ML) ==="]
    for tool in TOOL_REGISTRY.values():
        modalities = ", ".join(tool["modalities"])
        lines.append(
            f"- {tool['id']}: {tool['description']} "
            f"[modalities: {modalities}] [requires_gpu: {tool['requires_gpu']}] [min_images: {tool['min_images']}]"
        )

    lines.append("\n=== AVAILABLE SPECIALIST MODELS (ML / Deep Learning) ===")
    for model_key, model in MODEL_REGISTRY.items():
        status = _check_model_status(model_key)
        if status == ModelStatus.MODEL_UNAVAILABLE:
            continue
            
        modalities = ", ".join(model["modalities"])
        lines.append(
            f"- {model['id']}: {model['description']} "
            f"[modalities: {modalities}] [requires_gpu: {model['requires_gpu']}] "
            f"[min_images: {model['min_images']}] [status: {status.value}]"
        )

    return "\n".join(lines)


def get_tool(tool_id: str) -> dict[str, Any] | None:
    """Look up a tool by ID (supports common aliases)."""
    if tool_id in TOOL_REGISTRY:
        return TOOL_REGISTRY[tool_id]
    # Aliases
    alias_map = {
        "mask-area": "area-calculator",
        "bbox-area": "bbox-area-calculator",
        "polygon-area": "polygon-area-calculator",
        "geodesic-distance": "geodesic-distance-calculator",
    }
    canonical = alias_map.get(tool_id)
    return TOOL_REGISTRY.get(canonical) if canonical else None


def get_model(model_id: str) -> dict[str, Any] | None:
    """Look up a model by ID (supports common aliases)."""
    if model_id in MODEL_REGISTRY:
        return MODEL_REGISTRY[model_id]
    alias_map = {
        "geochat-vqa": "rsvqa-specialist",
        "geochat-caption": "vrsbench-caption",
        "geochat-grounding": "vrsbench-grounding",
        "captioning-specialist": "vrsbench-caption",
        "grounding-specialist": "vrsbench-grounding",
        "change-vqa": "cdvqa-specialist",
        "optical-sar": "cross-modal-specialist",
    }
    canonical = alias_map.get(model_id)
    return MODEL_REGISTRY.get(canonical) if canonical else None


def is_model(tool_id: str) -> bool:
    return get_model(tool_id) is not None


def is_tool(tool_id: str) -> bool:
    return get_tool(tool_id) is not None
