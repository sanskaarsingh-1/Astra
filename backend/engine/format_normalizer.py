"""
Engine - Image Format Normalizer
Converts non-rasterio-compatible image formats (WebP, JPEG, PNG, BMP, AVIF, etc.)
to a temporary GeoTIFF so the entire backend pipeline can use rasterio consistently.

PIL/Pillow supports: WebP, JPEG, PNG, BMP, GIF, TIFF, AVIF, and many more.
Rasterio supports: GeoTIFF, GeoJPEG2000, VRT, HDF, NetCDF, and other geospatial formats.

When a WebP/JPEG/PNG/etc. comes in, rasterio.open() fails. This module converts it
to a temporary single-scene GeoTIFF (no CRS, pixel-space coords) so rasterio can work.
"""

from pathlib import Path
from typing import Optional
import tempfile
import uuid
import numpy as np

# Formats that rasterio natively supports — skip conversion for these
RASTERIO_NATIVE_EXTENSIONS = {
    ".tif", ".tiff", ".img", ".nc", ".hdf", ".hdf5", ".h5",
    ".vrt", ".jp2", ".j2k", ".asc", ".grd",
}

# Formats that need PIL → GeoTIFF conversion
PIL_ONLY_EXTENSIONS = {
    ".webp", ".bmp", ".gif", ".avif", ".heic", ".heif",
    ".ico", ".psd", ".tga",
}


def needs_conversion(file_path: Path) -> bool:
    """Returns True if the file cannot be opened by rasterio directly."""
    ext = file_path.suffix.lower()
    # Definitely needs conversion
    if ext in PIL_ONLY_EXTENSIONS:
        return True
    # JPEG and PNG *can* be opened by rasterio but may fail on some builds —
    # convert them too for safety
    if ext in {".jpg", ".jpeg", ".png"}:
        return True
    return False


def pil_to_geotiff(file_path: Path, output_dir: Optional[Path] = None) -> Path:
    """
    Opens an image with PIL and writes it as a pixel-space GeoTIFF.
    Returns the path to the temporary GeoTIFF file.

    The output GeoTIFF has:
    - No CRS (is_geospatial=False — the validator already handles this gracefully)
    - An identity affine transform
    - uint8 dtype (converted from any depth)
    - RGB or Grayscale bands
    """
    from PIL import Image
    import rasterio
    from rasterio.transform import from_bounds

    if output_dir is None:
        output_dir = Path(tempfile.gettempdir()) / "astra_converted"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_name = f"converted_{uuid.uuid4().hex[:8]}.tif"
    out_path = output_dir / out_name

    with Image.open(file_path) as img:
        # Normalize to RGB (handles RGBA, L, P modes)
        if img.mode == "RGBA":
            # Composite over white background
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        arr = np.array(img)

        if arr.ndim == 2:
            # Grayscale → (1, H, W)
            arr = arr[np.newaxis, :, :]
            count = 1
        else:
            # (H, W, C) → (C, H, W)
            arr = np.transpose(arr, (2, 0, 1))
            count = arr.shape[0]

        height, width = arr.shape[1], arr.shape[2]

        # Write as pixel-space GeoTIFF (no CRS)
        with rasterio.open(
            out_path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=count,
            dtype=arr.dtype,
        ) as dst:
            dst.write(arr)

    return out_path


def ensure_rasterio_compatible(file_path: Path, output_dir: Optional[Path] = None) -> Path:
    """
    If the file format is not natively supported by rasterio, converts it to
    a temporary GeoTIFF and returns the new path. Otherwise returns the original path.

    Use this as a drop-in replacement wherever rasterio.open(file_path) is called
    on user-uploaded files.
    """
    if needs_conversion(file_path):
        return pil_to_geotiff(file_path, output_dir=output_dir)
    return file_path
