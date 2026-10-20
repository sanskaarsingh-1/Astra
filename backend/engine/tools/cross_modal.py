"""
Engine Tools — Cross-Modal Analysis
Combines optical and SAR insights for a joint finding.
"""

from pathlib import Path
from typing import Any
from loguru import logger
from orchestrator.schemas import ImageManifest
from engine.tools.indices import compute_ndvi
from engine.tools.raster_stats import get_sar_statistics
from engine.models.classifier import run_scene_classification

def analyze_cross_modal(optical_manifest: ImageManifest, sar_manifest: ImageManifest) -> dict[str, Any]:
    """
    Performs joint analysis on an Optical and SAR pair.
    """
    logger.info(f"Cross-modal analysis: {optical_manifest.filename} (Optical) + {sar_manifest.filename} (SAR)")
    
    optical_insights = {}
    sar_insights = {}
    
    # 1. Optical Insights
    # Run classification if possible
    try:
        class_res = run_scene_classification(Path(optical_manifest.file_path))
        if class_res.get("type") != "error":
            optical_insights["classification"] = class_res["top_predictions"]
    except Exception as e:
        logger.warning(f"Classification failed in cross-modal: {e}")
        
    # Run NDVI if applicable (needs 4+ bands generally, or mapped)
    if optical_manifest.band_count >= 2:
        try:
            ndvi_res = compute_ndvi(optical_manifest)
            optical_insights["ndvi"] = ndvi_res["interpretation"]
            optical_insights["pct_water"] = ndvi_res["ndvi_statistics"]["pct_water"]
            optical_insights["pct_veg"] = ndvi_res["ndvi_statistics"]["pct_vegetation"]
        except Exception as e:
            logger.warning(f"NDVI failed in cross-modal: {e}")
            
    # 2. SAR Insights
    try:
        sar_stats = get_sar_statistics(sar_manifest)
        sar_insights["stats"] = sar_stats["polarisation_statistics"]
        
        # Check for water bodies in SAR
        # Usually water has low backscatter (e.g. < -18 dB in VV)
        for stat in sar_insights["stats"]:
            if stat["polarisation"] in ["VV", "HH"] and stat["mean_dB"] < -15:
                sar_insights["water_detection"] = "High probability of calm water surfaces based on low SAR backscatter."
            elif stat["polarisation"] in ["VV", "HH"] and stat["mean_dB"] > -5:
                sar_insights["urban_detection"] = "High probability of built-up/urban areas or metallic structures based on high SAR backscatter."
    except Exception as e:
        logger.warning(f"SAR stats failed in cross-modal: {e}")
        
    # 3. Fusion & Conflict Detection
    fusion_notes = []
    conflicts = []
    
    opt_water = optical_insights.get("pct_water", 0) > 30
    sar_water = "water_detection" in sar_insights
    
    if opt_water and sar_water:
        fusion_notes.append("Optical and SAR strongly agree on the presence of significant water bodies.")
    elif opt_water and not sar_water:
        conflicts.append("Optical NDVI indicates water, but SAR backscatter is not low enough (possible rough water, wind, or flooding with vegetation).")
    elif not opt_water and sar_water:
        conflicts.append("SAR indicates water (low backscatter), but Optical NDVI does not. This could be a smooth dry surface (e.g., tarmac/sand) mimicking water in SAR.")
        
    return {
        "type": "text",
        "optical_insights": optical_insights,
        "sar_insights": sar_insights,
        "fusion_summary": " ".join(fusion_notes) if fusion_notes else "Optical and SAR provide complementary features.",
        "potential_conflicts": conflicts,
        "confidence": 0.8
    }
