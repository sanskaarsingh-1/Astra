"""
Engine Layer — BIT Change Detection Model Wrapper.
Bitemporal Image Transformer for binary change detection.
Input: two co-registered optical images (T1 and T2).
Output: binary change mask + deterministic change statistics (Phase 04).
"""

from pathlib import Path
from typing import Any, Optional
import numpy as np
from loguru import logger
from PIL import Image

MODEL_KEY = "bit-change-detection"


def _pure_numpy_otsu(diff: np.ndarray) -> float:
    """Fast, pure-numpy Otsu thresholding without requiring skimage."""
    flat = diff.flatten()
    pixel_counts, bin_edges = np.histogram(flat, bins=256, range=(0.0, 1.0))
    total = flat.size
    current_max, threshold = 0.0, 0.3
    weight_bg, sum_bg = 0.0, 0.0
    sum_total = np.dot(np.arange(256), pixel_counts)

    for i in range(256):
        weight_bg += pixel_counts[i]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += i * pixel_counts[i]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        var_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if var_between > current_max:
            current_max = var_between
            threshold = float((bin_edges[i] + bin_edges[i + 1]) / 2.0)

    return threshold


def _pixel_difference_fallback(t1_path: Path, t2_path: Path) -> np.ndarray:
    """Robust pixel-difference fallback if deep model inference encounters an issue."""
    def load_gray(path: Path) -> np.ndarray:
        try:
            import rasterio
            with rasterio.open(path) as src:
                data = src.read(1).astype(float)
                denom = max(data.max() - data.min(), 1e-6)
                return (data - data.min()) / denom
        except Exception:
            img = Image.open(path).convert("L")
            return np.array(img, dtype=float) / 255.0

    t1 = load_gray(t1_path)
    t2 = load_gray(t2_path)

    if t1.shape != t2.shape:
        pil1 = Image.fromarray((t1 * 255).astype(np.uint8)).resize((256, 256))
        pil2 = Image.fromarray((t2 * 255).astype(np.uint8)).resize((256, 256))
        t1 = np.array(pil1, dtype=float) / 255.0
        t2 = np.array(pil2, dtype=float) / 255.0

    diff = np.abs(t1 - t2)
    thresh = _pure_numpy_otsu(diff)
    return (diff > thresh).astype(np.uint8)


def run_change_detection(t1_path: Path, t2_path: Path, gsd: float = 0.5) -> dict[str, Any]:
    """
    Detect binary change between two co-registered images.
    Returns change mask + statistics compliant with Phase 04 specifications.
    """
    if t1_path is None or t2_path is None:
        raise ValueError("Change detection requires exactly 2 images.")

    logger.info(f"Change detection: {t1_path.name} → {t2_path.name}")

    try:
        from backend.models.change_detection.model import get_change_specialist
        specialist = get_change_specialist()
        result = specialist.detect_change(t1_path, t2_path, gsd=gsd)

        # Ensure full backward compatibility with engine executor schema
        result["type"] = "change_map"
        result["change_pixels"] = result["changed_pixels"]
        result["method"] = "BIT"
        result["model"] = "bit-change-detection"
        result["specialist_status"] = "SUCCESS"
        result["fallback_used"] = False
        result["provenance"] = "LEVIR-CD trained BIT architecture (Siamese ResNet-18 + Transformer)"
        return result

    except Exception as e:
        logger.warning(f"Failed deep BIT inference ({e}); using pixel-difference fallback.")
        change_mask = _pixel_difference_fallback(t1_path, t2_path)
        changed_pixels = int(change_mask.sum())
        total_pixels = int(change_mask.size)
        change_pct = round(changed_pixels / total_pixels * 100, 2)
        area_m2 = round(changed_pixels * (gsd ** 2), 2)
        area_ha = round(area_m2 / 10000.0, 4)

        return {
            "type": "change_map",
            "changed": bool(change_pct > 0.05),
            "change_percentage": change_pct,
            "changed_pixels": changed_pixels,
            "change_pixels": changed_pixels,
            "total_pixels": total_pixels,
            "area_m2": area_m2,
            "area_ha": area_ha,
            "regions_count": 1,
            "confidence": 0.40,
            "change_mask_base64": "",
            "method": "pixel_difference_fallback",
            "model": "bit-change-detection",
            "specialist_status": "FAILED",
            "fallback_used": True,
            "fallback_reason": str(e),
            "fallback_method": "Otsu thresholded pixel differencing",
            "provenance": f"Fallback: Pixel differencing (Primary BIT specialist failed: {e})",
            "narrative": f"Primary BIT specialist failed ({e}). Fallback pixel differencing detected {change_pct}% variation between rasters.",
            "alignment": {"aligned": True, "warning": f"Primary BIT specialist failed ({e}). Fallback diff used."},
        }
