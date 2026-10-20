"""
Engine Tools — Raster Statistics
All deterministic raster analysis using Rasterio and NumPy.
These tools NEVER hallucinate. They compute and return real values.
"""

from typing import Any
import numpy as np
from loguru import logger
from orchestrator.schemas import ImageManifest


def get_raster_metadata(manifest: ImageManifest) -> dict[str, Any]:
    """Return the pre-extracted raster metadata from the manifest."""
    return {
        "type": "metadata",
        "filename": manifest.filename,
        "width": manifest.width_px,
        "height": manifest.height_px,
        "band_count": manifest.band_count,
        "dtype": manifest.dtype,
        "crs_epsg": manifest.crs_epsg,
        "crs_wkt": manifest.crs_wkt,
        "gsd_x_m": manifest.gsd_x,
        "gsd_y_m": manifest.gsd_y,
        "bounds": manifest.bounds,
        "nodata": manifest.nodata_value,
        "is_geospatial": manifest.is_geospatial,
        "modality": manifest.modality.modality.value,
        "confidence": 1.0,
    }


def get_band_statistics(manifest: ImageManifest) -> dict[str, Any]:
    """Compute per-band statistics for an image."""
    try:
        import rasterio
        with rasterio.open(manifest.file_path) as src:
            stats = []
            for band_idx in range(1, src.count + 1):
                data = src.read(band_idx, masked=True)
                valid = data.compressed()
                if len(valid) == 0:
                    stats.append({"band": band_idx, "empty": True})
                    continue
                stats.append({
                    "band": band_idx,
                    "description": manifest.band_descriptions[band_idx-1] if manifest.band_descriptions and len(manifest.band_descriptions) >= band_idx else f"Band {band_idx}",
                    "min": float(np.min(valid)),
                    "max": float(np.max(valid)),
                    "mean": float(np.mean(valid)),
                    "std": float(np.std(valid)),
                    "median": float(np.median(valid)),
                    "valid_pixel_pct": round(len(valid) / data.size * 100, 2),
                })
            return {
                "type": "raster_stats",
                "filename": manifest.filename,
                "band_statistics": stats,
                "confidence": 1.0,
            }
    except Exception as exc:
        logger.error(f"Band statistics failed: {exc}")
        raise


def get_sar_statistics(manifest: ImageManifest) -> dict[str, Any]:
    """
    Compute SAR-specific backscatter statistics.
    SAR data is typically single or dual-polarisation float32.
    """
    try:
        import rasterio
        
        # Determine polarisations from manifest descriptions or fallback
        polarisations = []
        if manifest.band_descriptions:
            for desc in manifest.band_descriptions:
                d = desc.upper()
                if any(p in d for p in ["VV", "VH", "HH", "HV"]):
                    for p in ["VV", "VH", "HH", "HV"]:
                        if p in d:
                            polarisations.append(p)
                            break
                else:
                    polarisations.append(desc)
        
        if not polarisations:
            polarisations = ["VV", "VH"] if manifest.band_count >= 2 else ["Single-pol"]
            
        with rasterio.open(manifest.file_path) as src:
            stats = []
            for i in range(min(len(polarisations), src.count)):
                pol = polarisations[i]
                data = src.read(i + 1, masked=True)
                valid = data.compressed().astype(float)
                if len(valid) == 0:
                    continue
                    
                # Determine if data is already in dB scale or linear.
                # If there are negative values, it's likely dB. If it's strictly positive and small, linear.
                if np.min(valid) < 0:
                    valid_db = valid
                    is_linear = False
                else:
                    # Convert to dB if linear
                    valid_db = 10 * np.log10(np.maximum(valid, 1e-10))
                    is_linear = True

                stats.append({
                    "polarisation": pol,
                    "original_scale": "Linear" if is_linear else "dB",
                    "mean_dB": round(float(np.mean(valid_db)), 3),
                    "std_dB": round(float(np.std(valid_db)), 3),
                    "min_dB": round(float(np.min(valid_db)), 3),
                    "max_dB": round(float(np.max(valid_db)), 3),
                    "dynamic_range_dB": round(float(np.max(valid_db) - np.min(valid_db)), 3),
                })

            return {
                "type": "raster_stats",
                "subtype": "sar_backscatter",
                "filename": manifest.filename,
                "band_count": src.count,
                "polarisation_statistics": stats,
                "interpretation": (
                    "High backscatter (< -5 dB) = urban/metallic surfaces. "
                    "Medium backscatter (-15 to -5 dB) = vegetation. "
                    "Low backscatter (< -20 dB) = calm water surfaces."
                ),
                "confidence": 1.0,
            }
    except Exception as exc:
        logger.error(f"SAR statistics failed: {exc}")
        raise
