"""
Engine Tools — Geometric and Area Calculations
Deterministic real-world measurement. No LLM. No hallucination possible.
"""

from pathlib import Path
from typing import Any
import numpy as np
from loguru import logger


def calculate_mask_area(
    mask: list[list[int]] | None,
    crs_epsg: int | None,
    gsd_x: float | None,
    gsd_y: float | None,
) -> dict[str, Any]:
    """
    Calculate the real-world area of all True pixels in a binary mask.
    
    Args:
        mask: 2D binary mask (list of lists, 0/1 values)
        crs_epsg: EPSG code of the raster CRS
        gsd_x: Pixel width in CRS units
        gsd_y: Pixel height in CRS units
    
    Returns:
        Dict with area in m² and km².
    """
    if mask is None:
        return {
            "type": "measurement",
            "subtype": "area",
            "error": "No mask available for area calculation.",
            "confidence": 0.0,
        }

    mask_array = np.array(mask, dtype=np.uint8)
    changed_pixels = int(mask_array.sum())
    total_pixels = int(mask_array.size)
    change_pct = round(changed_pixels / total_pixels * 100, 3) if total_pixels > 0 else 0.0

    # Calculate area if GSD is available
    if gsd_x is not None and gsd_y is not None:
        pixel_area = abs(gsd_x * gsd_y)

        # If CRS is geographic (lat/lon, EPSG:4326), convert degrees² to m²
        if crs_epsg == 4326:
            # 1 degree ≈ 111,320 m at equator (approximate)
            pixel_area_m2 = pixel_area * (111320 ** 2)
        else:
            # Assume projected CRS in meters
            pixel_area_m2 = pixel_area

        total_area_m2 = changed_pixels * pixel_area_m2
        total_area_km2 = total_area_m2 / 1_000_000

        return {
            "type": "measurement",
            "subtype": "area",
            "changed_pixels": changed_pixels,
            "total_pixels": total_pixels,
            "change_percentage": change_pct,
            "area_m2": round(total_area_m2, 2),
            "area_km2": round(total_area_km2, 6),
            "area_ha": round(total_area_m2 / 10_000, 4),
            "crs_epsg": crs_epsg,
            "pixel_gsd_m": round(gsd_x, 4),
            "confidence": 1.0,  # Deterministic
            "confidence_status": "DETERMINISTIC",
            "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
            "note": "Area calculated from binary mask pixel count × pixel area.",
        }
    else:
        # No GSD available — report pixel counts only
        return {
            "type": "measurement",
            "subtype": "area",
            "changed_pixels": changed_pixels,
            "total_pixels": total_pixels,
            "change_percentage": change_pct,
            "area_m2": None,
            "area_km2": None,
            "confidence": 0.7,
            "confidence_status": "DETERMINISTIC",
            "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
            "note": (
                "Image is not georeferenced (no CRS or GSD available). "
                "Area in real-world units cannot be calculated. "
                "Pixel counts are exact."
            ),
        }


def calculate_bbox_area(
    bbox: list[float] | tuple[float, float, float, float],
    crs_epsg: int | None = None,
    gsd_x: float | None = None,
    gsd_y: float | None = None,
    is_pixel_coords: bool = True,
) -> dict[str, Any]:
    """
    Calculate area enclosed by a bounding box [ymin, xmin, ymax, xmax].
    """
    ymin, xmin, ymax, xmax = bbox
    width = abs(xmax - xmin)
    height = abs(ymax - ymin)

    if is_pixel_coords:
        pixel_count = width * height
        if gsd_x is not None and gsd_y is not None:
            pixel_area = abs(gsd_x * gsd_y)
            area_m2 = pixel_count * pixel_area
            return {
                "type": "measurement",
                "subtype": "bbox_area",
                "bbox": [ymin, xmin, ymax, xmax],
                "pixel_width": width,
                "pixel_height": height,
                "pixel_count": round(pixel_count, 1),
                "area_m2": round(area_m2, 2),
                "area_km2": round(area_m2 / 1_000_000, 6),
                "area_ha": round(area_m2 / 10_000, 4),
                "crs_epsg": crs_epsg,
                "gsd_m": round(gsd_x, 4),
                "confidence": 1.0,
                "confidence_status": "DETERMINISTIC",
                "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
            }
        return {
            "type": "measurement",
            "subtype": "bbox_area",
            "bbox": [ymin, xmin, ymax, xmax],
            "pixel_width": width,
            "pixel_height": height,
            "pixel_count": round(pixel_count, 1),
            "area_m2": None,
            "confidence": 0.7,
            "confidence_status": "DETERMINISTIC",
            "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
            "note": "Non-georeferenced bounding box. Pixel count is exact.",
        }

    # Real-world coordinates
    if crs_epsg == 4326:
        from pyproj import Geod
        from shapely.geometry import box
        geod = Geod(ellps="WGS84")
        geom = box(xmin, ymin, xmax, ymax)
        area_m2, _ = geod.geometry_area_perimeter(geom)
        area_m2 = abs(area_m2)
    else:
        area_m2 = width * height

    return {
        "type": "measurement",
        "subtype": "bbox_area",
        "bbox": [ymin, xmin, ymax, xmax],
        "area_m2": round(area_m2, 2),
        "area_km2": round(area_m2 / 1_000_000, 6),
        "area_ha": round(area_m2 / 10_000, 4),
        "crs_epsg": crs_epsg,
        "confidence": 1.0,
        "confidence_status": "DETERMINISTIC",
        "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
    }


def calculate_polygon_area(
    coords: list[list[float]] | list[tuple[float, float]],
    crs_epsg: int | None = None,
    gsd_x: float | None = None,
    gsd_y: float | None = None,
    is_pixel_coords: bool = True,
) -> dict[str, Any]:
    """
    Calculate area enclosed by an arbitrary polygon [[x1, y1], [x2, y2], ...].
    """
    from shapely.geometry import Polygon
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)

    if is_pixel_coords:
        pixel_area = poly.area
        if gsd_x is not None and gsd_y is not None:
            res_area = abs(gsd_x * gsd_y)
            area_m2 = pixel_area * res_area
            return {
                "type": "measurement",
                "subtype": "polygon_area",
                "vertex_count": len(coords),
                "pixel_area": round(pixel_area, 2),
                "area_m2": round(area_m2, 2),
                "area_km2": round(area_m2 / 1_000_000, 6),
                "area_ha": round(area_m2 / 10_000, 4),
                "crs_epsg": crs_epsg,
                "confidence": 1.0,
                "confidence_status": "DETERMINISTIC",
                "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
            }
        return {
            "type": "measurement",
            "subtype": "polygon_area",
            "vertex_count": len(coords),
            "pixel_area": round(pixel_area, 2),
            "area_m2": None,
            "confidence": 0.7,
            "confidence_status": "DETERMINISTIC",
            "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
        }

    if crs_epsg == 4326:
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        area_m2, _ = geod.geometry_area_perimeter(poly)
        area_m2 = abs(area_m2)
    else:
        area_m2 = poly.area

    return {
        "type": "measurement",
        "subtype": "polygon_area",
        "vertex_count": len(coords),
        "area_m2": round(area_m2, 2),
        "area_km2": round(area_m2 / 1_000_000, 6),
        "area_ha": round(area_m2 / 10_000, 4),
        "crs_epsg": crs_epsg,
        "confidence": 1.0,
        "confidence_status": "DETERMINISTIC",
        "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
    }


def geodesic_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> dict[str, Any]:
    """
    Calculate geodesic distance between two geographic coordinates.
    Uses PyProj for accuracy.
    """
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    _, _, distance_m = geod.inv(lon1, lat1, lon2, lat2)
    return {
        "type": "measurement",
        "subtype": "distance",
        "point_a": {"lat": lat1, "lon": lon1},
        "point_b": {"lat": lat2, "lon": lon2},
        "distance_m": round(distance_m, 2),
        "distance_km": round(distance_m / 1000, 4),
        "confidence": 1.0,
        "confidence_status": "DETERMINISTIC",
        "evidence_strength": "GROUND_TRUTH_DETERMINISTIC",
    }
