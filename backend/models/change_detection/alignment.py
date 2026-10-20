"""
Spatial Alignment and Resolution Ratio Verification for Bi-Temporal Image Pairs.
Satisfies SIH26167 requirement for co-registration and spatial fidelity checking.
"""

from pathlib import Path
from typing import Any, Optional, Tuple, Union
import numpy as np
from PIL import Image
from loguru import logger


def verify_spatial_alignment(
    t1_path: Union[str, Path],
    t2_path: Union[str, Path],
    max_resolution_ratio: float = 1.5,
) -> dict[str, Any]:
    """
    Verify spatial alignment, CRS, and resolution ratio between two temporal rasters.
    Works for both GeoTIFFs (using rasterio) and standard optical formats (PNG/JPEG/TIFF).
    """
    t1_path = Path(t1_path)
    t2_path = Path(t2_path)

    if not t1_path.exists():
        raise FileNotFoundError(f"Temporal Image 1 (T1) not found: {t1_path}")
    if not t2_path.exists():
        raise FileNotFoundError(f"Temporal Image 2 (T2) not found: {t2_path}")

    # Attempt GeoTIFF metadata extraction first
    is_geotiff = False
    crs_match = None
    bounds_match = None
    res_t1 = None
    res_t2 = None
    gsd_meters = 0.5  # default baseline GSD

    try:
        import rasterio
        with rasterio.open(t1_path) as src1, rasterio.open(t2_path) as src2:
            has_crs = bool(src1.crs and src2.crs)
            has_transform = bool(src1.transform and not src1.transform.is_identity)
            if has_crs and has_transform:
                is_geotiff = True
                crs1 = str(src1.crs)
                crs2 = str(src2.crs)
                crs_match = (crs1 == crs2)
                res_t1 = float(abs(src1.transform[0]))
                res_t2 = float(abs(src2.transform[0]))
                gsd_meters = min(res_t1, res_t2)

                b1, b2 = src1.bounds, src2.bounds
                overlap_left = max(b1.left, b2.left)
                overlap_bottom = max(b1.bottom, b2.bottom)
                overlap_right = min(b1.right, b2.right)
                overlap_top = min(b1.top, b2.top)
                has_overlap = (overlap_left < overlap_right) and (overlap_bottom < overlap_top)
                bounds_match = has_overlap
            else:
                is_geotiff = False
                gsd_meters = None
                res_t1 = 1.0
                res_t2 = 1.0

            shape_t1 = (src1.height, src1.width, src1.count)
            shape_t2 = (src2.height, src2.width, src2.count)
    except Exception:
        # Fall back to standard PIL image inspection
        is_geotiff = False
        with Image.open(t1_path) as img1, Image.open(t2_path) as img2:
            w1, h1 = img1.size
            w2, h2 = img2.size
            c1 = len(img1.getbands())
            c2 = len(img2.getbands())
            shape_t1 = (h1, w1, c1)
            shape_t2 = (h2, w2, c2)
            res_t1 = 1.0
            res_t2 = float(max(w1 / max(w2, 1), h1 / max(h2, 1)))

    # Compute resolution ratio
    ratio = max(res_t1, res_t2) / max(min(res_t1, res_t2), 1e-6)
    resolution_mismatch = ratio > max_resolution_ratio

    # Shape matching check
    dimensions_match = (shape_t1[0] == shape_t2[0]) and (shape_t1[1] == shape_t2[1])

    warning = None
    if resolution_mismatch:
        warning = (
            f"Temporal resolution mismatch detected: ratio {ratio:.2f}x exceeds threshold "
            f"{max_resolution_ratio}x. Automatic resampling will be applied."
        )
    elif not dimensions_match:
        warning = (
            f"Pixel dimensions mismatch: T1={shape_t1[:2]} vs T2={shape_t2[:2]}. "
            f"Automatic spatial resampling will be applied."
        )
    elif crs_match is False:
        warning = "Coordinate Reference System (CRS) mismatch between T1 and T2 rasters."

    result = {
        "aligned": dimensions_match and not resolution_mismatch,
        "is_geotiff": is_geotiff,
        "crs_match": crs_match,
        "bounds_match": bounds_match,
        "resolution_ratio": round(ratio, 3),
        "resolution_mismatch": resolution_mismatch,
        "t1_shape": shape_t1,
        "t2_shape": shape_t2,
        "gsd_meters": round(gsd_meters, 4) if gsd_meters is not None else None,
        "warning": warning,
    }

    if warning:
        logger.warning(f"Bi-temporal alignment: {warning}")
    else:
        logger.info(f"Bi-temporal alignment verified: T1={shape_t1} T2={shape_t2} ratio={ratio:.2f}")

    return result


def align_image_pair(
    t1_image: Union[Image.Image, np.ndarray],
    t2_image: Union[Image.Image, np.ndarray],
    target_size: Optional[Tuple[int, int]] = None,
) -> Tuple[Image.Image, Image.Image, dict[str, Any]]:
    """
    Ensure both images have matching spatial dimensions, resizing if needed.
    Returns:
        (aligned_t1, aligned_t2, metadata)
    """
    # Convert numpy arrays to PIL Images if necessary
    if isinstance(t1_image, np.ndarray):
        t1_pil = Image.fromarray(t1_image)
    else:
        t1_pil = t1_image.copy()

    if isinstance(t2_image, np.ndarray):
        t2_pil = Image.fromarray(t2_image)
    else:
        t2_pil = t2_image.copy()

    w1, h1 = t1_pil.size
    w2, h2 = t2_pil.size

    resampled = False

    if target_size:
        target_w, target_h = target_size
        if (w1, h1) != (target_w, target_h):
            t1_pil = t1_pil.resize((target_w, target_h), resample=Image.Resampling.BILINEAR)
            resampled = True
        if (w2, h2) != (target_w, target_h):
            t2_pil = t2_pil.resize((target_w, target_h), resample=Image.Resampling.BILINEAR)
            resampled = True
    elif (w1, h1) != (w2, h2):
        # Default: resize T2 to match T1
        t2_pil = t2_pil.resize((w1, h1), resample=Image.Resampling.BILINEAR)
        resampled = True

    meta = {
        "original_t1_size": (w1, h1),
        "original_t2_size": (w2, h2),
        "final_size": t1_pil.size,
        "resampled": resampled,
    }

    return t1_pil, t2_pil, meta
