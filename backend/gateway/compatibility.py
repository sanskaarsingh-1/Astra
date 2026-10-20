"""
Gateway - Input Compatibility Engine
Validates multi-raster inputs for joint analytical workflows:
- Bi-temporal change detection (temporal alignment, CRS, spatial overlap, resolution ratio)
- Cross-modal optical + SAR fusion (modality pairings, extent overlap, spatial consistency)
"""

from orchestrator.schemas import ImageManifest, CompatibilityReport


def validate_bitemporal_pair(img1: ImageManifest, img2: ImageManifest) -> CompatibilityReport:
    """
    Validates if two images can be compared for bi-temporal change detection.
    Enforces:
    - Same sensor modality family
    - Valid spatial overlap (> 5% minimum)
    - Compatible ground sample distance (GSD resolution ratio <= 4.0x)
    """
    reasons: list[str] = []
    warnings: list[str] = []
    overlap_percentage: float | None = None
    resolution_ratio: float | None = None

    # 1. Modality check
    if img1.modality.modality != img2.modality.modality:
        reasons.append(
            f"Modality mismatch: Image 1 is {img1.modality.modality.value}, "
            f"while Image 2 is {img2.modality.modality.value}. "
            "Bi-temporal change detection requires both images to be from the same modality family."
        )

    # 2. CRS & Spatial Overlap
    if img1.is_geospatial and img2.is_geospatial:
        crs_match = (
            img1.crs_epsg and img2.crs_epsg and img1.crs_epsg == img2.crs_epsg
        ) or (img1.crs_wkt and img2.crs_wkt and img1.crs_wkt == img2.crs_wkt)

        if not crs_match:
            warnings.append(
                f"CRS mismatch: Image 1 is EPSG:{img1.crs_epsg}, Image 2 is EPSG:{img2.crs_epsg}. "
                "Resampling and re-projection to a shared spatial grid will be applied dynamically."
            )

        if crs_match and img1.bounds and img2.bounds:
            b1, b2 = img1.bounds, img2.bounds
            overlap_x = max(0.0, min(b1["right"], b2["right"]) - max(b1["left"], b2["left"]))
            overlap_y = max(0.0, min(b1["top"], b2["top"]) - max(b1["bottom"], b2["bottom"]))

            if overlap_x <= 0 or overlap_y <= 0:
                reasons.append("Spatial bounding boxes have zero overlap. The scenes represent disjoint geographic areas.")
            else:
                area1 = max(1e-6, (b1["right"] - b1["left"]) * (b1["top"] - b1["bottom"]))
                area2 = max(1e-6, (b2["right"] - b2["left"]) * (b2["top"] - b2["bottom"]))
                overlap_area = overlap_x * overlap_y
                overlap_percentage = round((overlap_area / min(area1, area2)) * 100.0, 1)

                if overlap_percentage < 5.0:
                    reasons.append(
                        f"Inadequate spatial overlap ({overlap_percentage}%). "
                        "A minimum of 5% geographic overlap is required for change detection."
                    )
                elif overlap_percentage < 25.0:
                    warnings.append(
                        f"Low spatial overlap ({overlap_percentage}%). "
                        "Analysis will be constrained to the intersecting sub-region."
                    )
    elif img1.is_geospatial != img2.is_geospatial:
        warnings.append(
            "One image is georeferenced while the other is not. "
            "Analysis will rely on pixel-space alignment."
        )

    # 3. Resolution checking
    if img1.gsd_x and img2.gsd_x and img1.gsd_x > 0 and img2.gsd_x > 0:
        resolution_ratio = round(max(img1.gsd_x, img2.gsd_x) / min(img1.gsd_x, img2.gsd_x), 2)
        if resolution_ratio > 4.0:
            reasons.append(
                f"Resolution disparity is too high: GSD ratio is {resolution_ratio:.1f}x "
                f"({img1.gsd_x}m vs {img2.gsd_x}m). Maximum allowable ratio is 4.0x."
            )
        elif resolution_ratio > 2.0:
            warnings.append(
                f"Moderate resolution difference: GSD ratio is {resolution_ratio:.1f}x. "
                "Coarser image will be bicubic-resampled to match finer resolution."
            )

    is_compatible = len(reasons) == 0
    return CompatibilityReport(
        is_compatible=is_compatible,
        reasons=reasons,
        warnings=warnings,
        resolution_ratio=resolution_ratio,
        overlap_percentage=overlap_percentage,
    )


def validate_cross_modal_pair(img1: ImageManifest, img2: ImageManifest) -> CompatibilityReport:
    """
    Validates if two images (one optical, one SAR) can be fused for cross-modal analysis.
    Enforces:
    - Exactly one SAR image and one Optical/Panchromatic image
    - Compatible spatial coverage
    """
    reasons: list[str] = []
    warnings: list[str] = []
    overlap_percentage: float | None = None
    resolution_ratio: float | None = None

    modalities = {img1.modality.modality.value, img2.modality.modality.value}

    if "SAR" not in modalities:
        reasons.append("Cross-modal analysis requires at least one Synthetic Aperture Radar (SAR) image.")

    optical_modalities = {"OPTICAL_RGB", "OPTICAL_MULTISPECTRAL", "PANCHROMATIC"}
    if not any(m in optical_modalities for m in modalities):
        reasons.append(
            "Cross-modal analysis requires at least one Optical (RGB, Multispectral) or Panchromatic image."
        )

    if img1.is_geospatial and img2.is_geospatial:
        crs_match = (
            img1.crs_epsg and img2.crs_epsg and img1.crs_epsg == img2.crs_epsg
        ) or (img1.crs_wkt and img2.crs_wkt and img1.crs_wkt == img2.crs_wkt)

        if not crs_match:
            warnings.append(
                f"CRS mismatch: Optical is EPSG:{img1.crs_epsg}, SAR is EPSG:{img2.crs_epsg}. "
                "Spatial alignment will reproject to shared spatial coordinate system."
            )

        if crs_match and img1.bounds and img2.bounds:
            b1, b2 = img1.bounds, img2.bounds
            overlap_x = max(0.0, min(b1["right"], b2["right"]) - max(b1["left"], b2["left"]))
            overlap_y = max(0.0, min(b1["top"], b2["top"]) - max(b1["bottom"], b2["bottom"]))

            if overlap_x <= 0 or overlap_y <= 0:
                warnings.append("Scenes have no georeferenced bounding box overlap.")
            else:
                area1 = max(1e-6, (b1["right"] - b1["left"]) * (b1["top"] - b1["bottom"]))
                area2 = max(1e-6, (b2["right"] - b2["left"]) * (b2["top"] - b2["bottom"]))
                overlap_percentage = round((overlap_x * overlap_y / min(area1, area2)) * 100.0, 1)

    if img1.gsd_x and img2.gsd_x and img1.gsd_x > 0 and img2.gsd_x > 0:
        resolution_ratio = round(max(img1.gsd_x, img2.gsd_x) / min(img1.gsd_x, img2.gsd_x), 2)
        if resolution_ratio > 5.0:
            warnings.append(
                f"Substantial resolution difference between Optical and SAR ({resolution_ratio:.1f}x). "
                "Feature fusion will use multi-scale alignment."
            )

    is_compatible = len(reasons) == 0
    return CompatibilityReport(
        is_compatible=is_compatible,
        reasons=reasons,
        warnings=warnings,
        resolution_ratio=resolution_ratio,
        overlap_percentage=overlap_percentage,
    )
