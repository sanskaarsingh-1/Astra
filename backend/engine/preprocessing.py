"""
Engine - Preprocessing
Converts raw satellite rasters (16-bit, multi-band) to 8-bit RGB for vision models like GeoChat.
"""
from pathlib import Path
import numpy as np
import rasterio
from PIL import Image
import os
import uuid

try:
    from engine.format_normalizer import ensure_rasterio_compatible
except ImportError:
    from backend.engine.format_normalizer import ensure_rasterio_compatible

def raster_to_8bit_rgb(file_path: str, output_dir: str = "outputs/preprocessed") -> str:
    """
    Converts a raster file to an 8-bit RGB JPEG for vision models.
    Handles percentile clipping for 16-bit imagery.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"rgb_{uuid.uuid4().hex[:8]}.jpg")

    # Convert WebP/JPEG/PNG/BMP to a rasterio-compatible temp GeoTIFF if needed
    file_path = ensure_rasterio_compatible(Path(file_path))

    with rasterio.open(file_path) as src:
        count = src.count
        
        if count >= 3:
            # Assume first 3 bands are RGB or map properly
            r = src.read(1)
            g = src.read(2)
            b = src.read(3)
        elif count == 1:
            # Duplicate single band to RGB
            v = src.read(1)
            r = g = b = v
        else: # 2 bands
            r = src.read(1)
            g = src.read(2)
            b = np.zeros_like(r)
            
        # Stack to shape (H, W, 3)
        rgb = np.dstack((r, g, b))
        
        # Convert to float for processing
        rgb = rgb.astype(float)
        
        # Handle nodata
        if src.nodata is not None:
            mask = (r == src.nodata) | (g == src.nodata) | (b == src.nodata)
            rgb[mask] = 0
            
        # Percentile clipping (2nd to 98th) to enhance contrast, typical for 16-bit
        if rgb.max() > 255:
            p2, p98 = np.percentile(rgb[rgb > 0], (2, 98))
            rgb = np.clip((rgb - p2) / (p98 - p2) * 255.0, 0, 255)
            
        rgb = rgb.astype(np.uint8)
        
        # Save as JPEG
        img = Image.fromarray(rgb)
        img.save(out_path, format="JPEG", quality=90)
        
    return out_path
