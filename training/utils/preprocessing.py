from pathlib import Path
import numpy as np
import rasterio
from PIL import Image
import os
import uuid

def raster_to_8bit_rgb(file_path: str, output_dir: str = "datasets/processed") -> str:
    """
    Converts a raster file to an 8-bit RGB JPEG.
    Standalone copy of the backend's preprocessing logic for training.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"rgb_{uuid.uuid4().hex[:8]}.jpg")
    
    with rasterio.open(file_path) as src:
        count = src.count
        
        if count >= 3:
            r = src.read(1)
            g = src.read(2)
            b = src.read(3)
        elif count == 1:
            v = src.read(1)
            r = g = b = v
        else: 
            r = src.read(1)
            g = src.read(2)
            b = np.zeros_like(r)
            
        rgb = np.dstack((r, g, b))
        rgb = rgb.astype(float)
        
        if src.nodata is not None:
            mask = (r == src.nodata) | (g == src.nodata) | (b == src.nodata)
            rgb[mask] = 0
            
        if rgb.max() > 255:
            p2, p98 = np.percentile(rgb[rgb > 0], (2, 98))
            rgb = np.clip((rgb - p2) / (p98 - p2) * 255.0, 0, 255)
            
        rgb = rgb.astype(np.uint8)
        img = Image.fromarray(rgb)
        img.save(out_path, format="JPEG", quality=90)
        
    return out_path
