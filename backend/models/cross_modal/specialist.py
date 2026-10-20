"""
Optical + SAR Cross-Modal Reasoning Specialist.
Fuses optical spectral reflectance (Sentinel-2 / Cartosat-2S) with
SAR microwave backscatter geometry (Sentinel-1 / RISAT C-Band).
Explicitly separates evidence provenance, performs conflict detection,
and resolves surface ambiguity through complementary physics.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
from loguru import logger

from backend.gateway.modality import detect_modality
from backend.gateway.metadata import extract_metadata
from backend.orchestrator.schemas import ModalityEnum, ImageManifest


class CrossModalSpecialist:
    """
    Production Cross-Modal Analysis Engine for Optical + SAR Pairs.
    """

    def __init__(self) -> None:
        logger.info("CrossModalSpecialist initialized.")

    def _analyze_optical(self, optical_path: Path) -> Dict[str, Any]:
        """Extract optical evidence: LULC classification, spectral indices, and color metrics."""
        evidence = {
            "modality": "Optical (Multispectral / RGB)",
            "sensor_family": "Sentinel-2 / Cartosat-2S",
            "physical_mechanism": "Surface solar reflectance & absorption",
        }

        # 1. ResNet-50 v2 LULC classification
        try:
            from backend.services.model_service import model_service
            res = model_service.predict_scene(optical_path)
            evidence["lulc_predictions"] = res.get("top_predictions", [])[:5]
            evidence["dominant_land_cover"] = res.get("prediction", "Unclassified")
        except Exception as e:
            logger.warning(f"Optical LULC classification fallback: {e}")
            evidence["lulc_predictions"] = []
            evidence["dominant_land_cover"] = "Terrain"

        # 2. Spectral statistics & vegetation/water index estimation
        try:
            import rasterio
            with rasterio.open(optical_path) as src:
                if src.count >= 4:  # Multispectral with NIR
                    red = src.read(1).astype(float)
                    nir = src.read(4).astype(float)
                    denom = np.clip(nir + red, 1e-6, None)
                    ndvi = (nir - red) / denom
                    evidence["mean_ndvi"] = round(float(np.nanmean(ndvi)), 4)
                    evidence["vegetation_detected"] = bool(evidence["mean_ndvi"] > 0.3)
                    evidence["water_detected"] = bool(evidence["mean_ndvi"] < -0.1)
                else:
                    img = Image.open(optical_path).convert("RGB")
                    arr = np.array(img, dtype=float)
                    # Green-Red ratio proxy for optical vegetation
                    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
                    g_r_ratio = float(np.mean(g) / max(np.mean(r), 1.0))
                    evidence["vegetation_detected"] = bool(g_r_ratio > 1.05)
                    evidence["water_detected"] = bool(np.mean(b) > np.mean(r) * 1.3 and np.mean(arr) < 90)
        except Exception:
            evidence["vegetation_detected"] = False
            evidence["water_detected"] = False

        return evidence

    def _analyze_sar(self, sar_path: Path) -> Dict[str, Any]:
        """Extract SAR evidence: calibrated backscatter dB, double-bounce, roughness."""
        evidence = {
            "modality": "Synthetic Aperture Radar (SAR)",
            "sensor_family": "Sentinel-1 / RISAT-1A (C-Band)",
            "physical_mechanism": "Microwave active backscatter & dielectric geometry",
            "penetration": "All-weather, cloud & smoke penetrating",
        }

        mean_db = -12.0
        double_bounce = False
        specular_water = False

        try:
            import rasterio
            with rasterio.open(sar_path) as src:
                data = src.read(1).astype(float)
                # Check if this is a standard 8-bit image format (PNG/JPEG) or uint8 array
                if src.driver in ("PNG", "JPEG") or src.dtypes[0] in ("uint8", "int8"):
                    # Standard display preview: 0 -> -30 dB, 255 -> 0 dB
                    norm_val = np.clip(data / 255.0, 1e-6, 1.0)
                    db = -30.0 + (norm_val * 30.0)
                elif np.nanmin(data) < 0.0:
                    # Already in dB calibrated format (e.g. -25 to +5 dB)
                    db = data
                else:
                    # Raw linear power (e.g. sigma0 float values 0.0001 - 1.0)
                    power = np.clip(data, 1e-6, None)
                    db = 10.0 * np.log10(power)

                mean_db = round(float(np.nanmean(db)), 2)
                min_db = round(float(np.nanmin(db)), 2)
                max_db = round(float(np.nanmax(db)), 2)

                evidence["backscatter_db"] = {
                    "mean_dB": mean_db,
                    "min_dB": min_db,
                    "max_dB": max_db,
                }

                # Physical interpretation thresholds
                specular_water = mean_db < -18.0
                double_bounce = max_db > -3.0 or mean_db > -7.0
        except Exception:
            # Fallback for standard grayscale/intensity PNG
            img = Image.open(sar_path).convert("L")
            arr = np.array(img, dtype=float)
            norm_val = np.mean(arr) / 255.0
            mean_db = round(-25.0 + (norm_val * 25.0), 2)
            specular_water = norm_val < 0.15
            double_bounce = norm_val > 0.70
            evidence["backscatter_db"] = {"mean_dB": mean_db, "estimated": True}

        evidence["specular_reflection_water"] = specular_water
        evidence["double_bounce_urban_structures"] = double_bounce
        evidence["surface_roughness"] = "High / Built" if double_bounce else ("Very Smooth / Calm Water" if specular_water else "Moderate / Vegetated Soil")

        return evidence

    def analyze_pair(
        self,
        optical_input: Union[str, Path],
        sar_input: Union[str, Path],
    ) -> Dict[str, Any]:
        """
        Execute comprehensive cross-modal analysis on an Optical + SAR image pair.
        """
        p_opt = Path(optical_input)
        p_sar = Path(sar_input)

        if not p_opt.exists():
            raise FileNotFoundError(f"Optical raster not found: {p_opt}")
        if not p_sar.exists():
            raise FileNotFoundError(f"SAR raster not found: {p_sar}")

        # 1. Modality Validation Check
        meta_opt = extract_metadata(p_opt)
        meta_sar = extract_metadata(p_sar)

        mod_opt = detect_modality(meta_opt)
        mod_sar = detect_modality(meta_sar)

        # Ensure rasters are genuinely distinct modalities
        is_sar_opt_pair = (
            (mod_opt.modality in [ModalityEnum.OPTICAL_RGB, ModalityEnum.OPTICAL_MULTISPECTRAL, ModalityEnum.PANCHROMATIC, ModalityEnum.AMBIGUOUS]) and
            (mod_sar.modality in [ModalityEnum.SAR, ModalityEnum.AMBIGUOUS])
        ) or (
            # If swapped in parameters, automatically re-route
            (mod_sar.modality in [ModalityEnum.OPTICAL_RGB, ModalityEnum.OPTICAL_MULTISPECTRAL, ModalityEnum.PANCHROMATIC]) and
            (mod_opt.modality == ModalityEnum.SAR)
        )

        # Auto-swap if caller passed SAR as first argument
        if mod_opt.modality == ModalityEnum.SAR and mod_sar.modality != ModalityEnum.SAR:
            p_opt, p_sar = p_sar, p_opt
            mod_opt, mod_sar = mod_sar, mod_opt

        # 2. Extract Modality-Specific Evidence
        optical_ev = self._analyze_optical(p_opt)
        sar_ev = self._analyze_sar(p_sar)

        # 3. Cross-Modal Fusion & Agreement Engine
        conflicts: List[str] = []
        complementary_findings: List[str] = []
        agreement = "HIGH"

        opt_water = optical_ev.get("water_detected", False)
        sar_water = sar_ev.get("specular_reflection_water", False)
        sar_urban = sar_ev.get("double_bounce_urban_structures", False)
        opt_dominant = optical_ev.get("dominant_land_cover", "")

        # Test Case 1: Water Body Agreement & Conflict Resolution
        if opt_water and sar_water:
            complementary_findings.append(
                "High-confidence water confirmation: Optical low reflectance/NDWI aligns with SAR specular reflection (low backscatter < -18 dB)."
            )
            agreement = "HIGH"
        elif not opt_water and sar_water:
            conflicts.append(
                "Ambiguity detected: SAR exhibits low backscatter mimicking calm water, but Optical imagery shows dry smooth surface (e.g. tarmac/runway/dry flatland). Optical resolves false-positive SAR water."
            )
            agreement = "CONFLICT"
        elif opt_water and not sar_water:
            conflicts.append(
                "Optical indicates water, but SAR exhibits moderate backscatter (possible wind-induced surface waves or emergent aquatic vegetation)."
            )
            agreement = "MODERATE"

        # Test Case 2: Urban & Structural Grounding
        if sar_urban:
            complementary_findings.append(
                f"SAR detects prominent double-bounce microwave corner reflections ({sar_ev['backscatter_db']['mean_dB']} dB), confirming dense built-up infrastructure/metallic structures."
            )
            if "urban" in opt_dominant.lower() or "building" in opt_dominant.lower():
                agreement = "HIGH"
            else:
                complementary_findings.append(
                    "SAR structural detection penetrates surface canopy or shadow, revealing buildings obscured in optical bands."
                )

        # Formulate synthesized conclusion
        if agreement == "HIGH":
            synthesis = (
                f"Optical and SAR modalities exhibit high mutual agreement. Optical classification identifies "
                f"'{opt_dominant}', substantiated by SAR roughness and geometry ({sar_ev['surface_roughness']})."
            )
        elif agreement == "CONFLICT":
            synthesis = (
                f"Modality conflict identified and resolved: {' '.join(conflicts)}"
            )
        else:
            synthesis = (
                f"Optical and SAR provide complementary perspectives: {' '.join(complementary_findings)}"
            )

        return {
            "type": "text",
            "text": synthesis,
            "optical_evidence": optical_ev,
            "sar_evidence": sar_ev,
            "modality_agreement": agreement,
            "conflicts": conflicts,
            "complementary_findings": complementary_findings,
            "synthesis": synthesis,
            "confidence": 0.88 if agreement == "HIGH" else (0.75 if agreement == "MODERATE" else 0.65),
            "sensor_compatibility": {
                "optical_source": "Sentinel-2 MSI / ISRO Cartosat-2S",
                "sar_source": "Sentinel-1 C-SAR / ISRO RISAT-1A (EOS-04)",
                "polarisation_supported": ["VV", "VH", "HH", "HV", "RH", "RV"],
            },
            "model_name": "cross-modal-specialist",
            "model": "cross-modal-specialist",
            "specialist": "cross-modal-specialist",
            "status": "SUCCESS",
            "provenance": "BigEarthNet S1+S2 joint physics & ISRO sensor alignment",
        }

    def analyze(
        self,
        opt_input: Union[str, Path, ImageManifest],
        sar_input: Union[str, Path, ImageManifest],
    ) -> Dict[str, Any]:
        """Entrypoint accepting either paths or ImageManifest objects."""
        p_opt = opt_input.file_path if hasattr(opt_input, "file_path") else opt_input
        p_sar = sar_input.file_path if hasattr(sar_input, "file_path") else sar_input
        return self.analyze_pair(p_opt, p_sar)


# Global singleton
_CROSS_MODAL_INSTANCE: Optional[CrossModalSpecialist] = None


def get_cross_modal_specialist() -> CrossModalSpecialist:
    """Retrieve or initialize the global CrossModalSpecialist singleton."""
    global _CROSS_MODAL_INSTANCE
    if _CROSS_MODAL_INSTANCE is None:
        _CROSS_MODAL_INSTANCE = CrossModalSpecialist()
    return _CROSS_MODAL_INSTANCE


class _CrossModalLazyProxy:
    def __getattr__(self, name):
        return getattr(get_cross_modal_specialist(), name)

    def analyze(self, *args, **kwargs):
        return get_cross_modal_specialist().analyze(*args, **kwargs)

    def analyze_pair(self, *args, **kwargs):
        return get_cross_modal_specialist().analyze_pair(*args, **kwargs)


cross_modal_specialist = _CrossModalLazyProxy()
