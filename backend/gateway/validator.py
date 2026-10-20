"""
Gateway - Input Validation Engine
Validates remote sensing files against format, size, MIME type, GeoTIFF spatial tags,
CRS definitions, bounding box validity, and GSD resolution constraints.
"""

from pathlib import Path
from typing import List, Optional, Any
from fastapi import UploadFile
import magic
import rasterio

from config import settings

try:
    from engine.format_normalizer import ensure_rasterio_compatible
except ImportError:
    from backend.engine.format_normalizer import ensure_rasterio_compatible


ALLOWED_EXTENSIONS = {
    ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".webp", ".jp2", ".img", ".hdf", ".h5", ".nc", ".bmp"
}

ALLOWED_MIME_TYPES = {
    "image/tiff", "image/png", "image/jpeg", "image/webp", "image/bmp",
    "application/octet-stream", "image/x-geotiff", "image/jp2", "image/x-portable-pixmap"
}


async def validate_upload_files(files: List[UploadFile]) -> Optional[List[str]]:
    """
    Validates uploaded remote sensing files against configured format, size, and MIME constraints.
    Returns a list of error strings if invalid, otherwise None.
    """
    errors = []

    if not files:
        return ["No files provided."]

    if len(files) > settings.MAX_FILES_PER_REQUEST:
        errors.append(f"Maximum {settings.MAX_FILES_PER_REQUEST} files allowed per investigation request.")

    for idx, file in enumerate(files):
        if not file.filename:
            errors.append(f"File {idx + 1} is missing a filename.")
            continue

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"File '{file.filename}' has unsupported extension '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
            continue

        # File size check
        content = await file.read()
        size_bytes = len(content)
        await file.seek(0)

        if size_bytes == 0:
            errors.append(f"File '{file.filename}' is empty (0 bytes).")
            continue

        if size_bytes > settings.max_file_size_bytes:
            errors.append(
                f"File '{file.filename}' ({size_bytes / (1024*1024):.1f}MB) exceeds "
                f"{settings.MAX_FILE_SIZE_MB}MB limit."
            )
            continue

        # Check MIME type
        try:
            detected_mime = magic.from_buffer(content[:2048], mime=True)
            if detected_mime not in ALLOWED_MIME_TYPES and not detected_mime.startswith("image/"):
                errors.append(f"File '{file.filename}' has unsupported MIME type '{detected_mime}'.")
                continue
        except Exception:
            if ext in {".tif", ".tiff"} and not (content.startswith(b"II*\x00") or content.startswith(b"MM\x00*")):
                errors.append(f"File '{file.filename}' has unsupported MIME type (invalid TIFF header).")
                continue
            if ext == ".png" and not content.startswith(b"\x89PNG"):
                errors.append(f"File '{file.filename}' has unsupported MIME type (invalid PNG header).")
                continue
            if ext in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8\xff"):
                errors.append(f"File '{file.filename}' has unsupported MIME type (invalid JPEG header).")
                continue

    return errors if errors else None


def validate_geotiff_spatial(file_path: Path | str) -> dict[str, Any]:
    """
    Deep spatial validation of a raster/GeoTIFF file on disk.
    Checks:
    - GeoTIFF tags and GDAL readability
    - Coordinate Reference System (CRS) and EPSG definition
    - Affine transform and pixel resolution (GSD)
    - Valid non-degenerate bounding box bounds
    - Degenerate dimensions (width <= 0, height <= 0)
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        return {
            "is_valid": False,
            "errors": [f"File not found: {file_path}"],
            "warnings": [],
            "is_geospatial": False,
        }

    errors: list[str] = []
    warnings: list[str] = []
    spatial_info: dict[str, Any] = {
        "is_valid": True,
        "is_geospatial": False,
        "crs_epsg": None,
        "crs_wkt": None,
        "bounds": None,
        "gsd_x": None,
        "gsd_y": None,
        "width": 0,
        "height": 0,
        "band_count": 0,
        "nodata": None,
        "errors": errors,
        "warnings": warnings,
    }

    try:
        # Convert WebP/JPEG/PNG/BMP to a temp GeoTIFF if rasterio can't open the format
        rasterio_path = ensure_rasterio_compatible(path_obj)
        with rasterio.open(rasterio_path) as src:
            spatial_info["width"] = src.width
            spatial_info["height"] = src.height
            spatial_info["band_count"] = src.count
            spatial_info["nodata"] = src.nodata

            if src.width <= 0 or src.height <= 0:
                errors.append(f"Degenerate raster dimensions: {src.width}x{src.height}")

            if src.count <= 0:
                errors.append("Raster contains 0 raster bands.")

            # Spatial Reference / CRS
            if src.crs:
                spatial_info["is_geospatial"] = True
                spatial_info["crs_wkt"] = src.crs.to_wkt()
                spatial_info["crs_epsg"] = src.crs.to_epsg()
                if not spatial_info["crs_epsg"]:
                    warnings.append(
                        "CRS is defined via custom WKT but has no registered standard EPSG code."
                    )
            else:
                warnings.append(
                    f"File '{path_obj.name}' has no georeferencing/CRS tags. "
                    "Spatial calculations will default to pixel-space coordinates."
                )

            # Transform & GSD
            if src.transform and spatial_info["is_geospatial"]:
                spatial_info["gsd_x"] = abs(src.transform.a)
                spatial_info["gsd_y"] = abs(src.transform.e)
                if spatial_info["gsd_x"] == 0 or spatial_info["gsd_y"] == 0:
                    errors.append("Invalid pixel resolution (GSD): zero pixel size in affine transform.")

            # Bounds
            if src.bounds and spatial_info["is_geospatial"]:
                b = src.bounds
                if b.left >= b.right or b.bottom >= b.top:
                    errors.append(f"Degenerate bounding box coordinates: left={b.left}, right={b.right}, bottom={b.bottom}, top={b.top}")
                else:
                    spatial_info["bounds"] = {
                        "left": float(b.left),
                        "bottom": float(b.bottom),
                        "right": float(b.right),
                        "top": float(b.top),
                    }

    except Exception as exc:
        errors.append(f"Failed to read raster tags: {exc}")

    spatial_info["is_valid"] = len(errors) == 0
    return spatial_info
