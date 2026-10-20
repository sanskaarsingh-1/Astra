"""
Engine Tools — Vegetation and Spectral Indices
Deterministic computation. No LLM involvement.
"""

from typing import Any
import numpy as np
from loguru import logger
from orchestrator.schemas import ImageManifest


def compute_ndvi(manifest: ImageManifest) -> dict[str, Any]:
    """
    Compute Normalized Difference Vegetation Index.
    NDVI = (NIR - Red) / (NIR + Red)
    Uses semantic band mapping based on band descriptions or wavelengths.
    """
    import rasterio
    
    if manifest.band_count < 2:
        raise ValueError(f"NDVI requires at least 2 bands (Red + NIR). Image has {manifest.band_count} bands.")

    red_idx, nir_idx = _identify_bands(manifest)
    
    if red_idx is None or nir_idx is None:
        if manifest.band_count >= 4:
            logger.warning("Could not definitively map Red/NIR bands. Falling back to Sentinel-2 defaults (B3=Red, B4=NIR)")
            red_idx, nir_idx = 3, 4
        elif manifest.band_count == 3:
            logger.warning("Could not definitively map Red/NIR bands for 3-band image. Assuming B1=Red, B2=NIR (unlikely to be accurate).")
            red_idx, nir_idx = 1, 2
        else:
            raise ValueError("Could not identify Red and NIR bands from metadata.")

    logger.info(f"Computing NDVI using Band {red_idx} (Red) and Band {nir_idx} (NIR).")

    with rasterio.open(manifest.file_path) as src:
        red = src.read(red_idx).astype(float)
        nir = src.read(nir_idx).astype(float)

        if manifest.nodata_value is not None:
            mask = (red == manifest.nodata_value) | (nir == manifest.nodata_value)
            red[mask] = np.nan
            nir[mask] = np.nan

        # Avoid division by zero
        denominator = nir + red
        ndvi = np.where(
            denominator != 0,
            (nir - red) / denominator,
            np.nan
        )

        valid_ndvi = ndvi[~np.isnan(ndvi)]
        if len(valid_ndvi) == 0:
            raise ValueError("No valid NDVI pixels computed.")

        stats = {
            "mean": round(float(np.mean(valid_ndvi)), 4),
            "std": round(float(np.std(valid_ndvi)), 4),
            "min": round(float(np.min(valid_ndvi)), 4),
            "max": round(float(np.max(valid_ndvi)), 4),
            "pct_vegetation": round(float((valid_ndvi > 0.3).mean() * 100), 2),
            "pct_dense_vegetation": round(float((valid_ndvi > 0.5).mean() * 100), 2),
            "pct_bare_soil": round(float(((valid_ndvi >= -0.1) & (valid_ndvi <= 0.2)).mean() * 100), 2),
            "pct_water": round(float((valid_ndvi < -0.1).mean() * 100), 2),
        }

        return {
            "type": "measurement",
            "subtype": "ndvi",
            "filename": manifest.filename,
            "ndvi_statistics": stats,
            "interpretation": _interpret_ndvi(stats),
            "confidence": 1.0,  # Deterministic computation
        }


def _identify_bands(manifest: ImageManifest) -> tuple[int | None, int | None]:
    """Helper to semantically map Red and NIR bands based on metadata."""
    red_idx, nir_idx = None, None
    
    # 1. Try mapping by wavelength (Red: ~600-700nm, NIR: ~750-1000nm)
    if manifest.band_wavelengths and len(manifest.band_wavelengths) == manifest.band_count:
        for i, w in enumerate(manifest.band_wavelengths, 1):
            if 600 <= w <= 700:
                red_idx = i
            elif 750 <= w <= 1000:
                nir_idx = i
        if red_idx and nir_idx:
            return red_idx, nir_idx
            
    # 2. Try mapping by description names
    if manifest.band_descriptions:
        for i, desc in enumerate(manifest.band_descriptions, 1):
            d = desc.lower()
            if "red" in d and not "edge" in d:
                red_idx = i
            elif "nir" in d or "near infrared" in d or "near-infrared" in d:
                nir_idx = i
                
    return red_idx, nir_idx


def _interpret_ndvi(stats: dict) -> str:
    """Generate a factual interpretation of NDVI statistics."""
    mean_ndvi = stats["mean"]
    pct_veg = stats["pct_vegetation"]
    pct_water = stats["pct_water"]

    parts = []
    if mean_ndvi < 0:
        parts.append("The scene is dominated by water, snow, or bare rock (negative mean NDVI).")
    elif mean_ndvi < 0.2:
        parts.append("The scene shows sparse or no vegetation (mean NDVI < 0.2).")
    elif mean_ndvi < 0.5:
        parts.append("The scene has moderate vegetation density (mean NDVI 0.2–0.5).")
    else:
        parts.append("The scene has dense, healthy vegetation (mean NDVI > 0.5).")

    if pct_veg > 0:
        parts.append(f"{pct_veg:.1f}% of valid pixels show vegetation (NDVI > 0.3).")
    if pct_water > 5:
        parts.append(f"{pct_water:.1f}% of pixels indicate water or wet surfaces (NDVI < -0.1).")

    return " ".join(parts)
