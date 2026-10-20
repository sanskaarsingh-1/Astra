"""
Engine - Geospatial Alignment
Aligns two images to a common grid for change detection or cross-modal analysis.
"""
from pathlib import Path
from typing import Dict, Any
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from orchestrator.schemas import ImageManifest
import uuid
import os

class AlignmentResult:
    def __init__(self, aligned_path1: str, aligned_path2: str, transform: list, crs_wkt: str, width: int, height: int):
        self.aligned_path1 = aligned_path1
        self.aligned_path2 = aligned_path2
        self.transform = transform
        self.crs_wkt = crs_wkt
        self.width = width
        self.height = height

def align_to_common_grid(manifest1: ImageManifest, manifest2: ImageManifest, output_dir: str = "outputs") -> AlignmentResult:
    """
    Aligns img2 to the grid of img1. If CRS differs, img2 is reprojected.
    Outputs new temporary files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    path1 = manifest1.file_path
    path2 = manifest2.file_path
    
    out_path1 = os.path.join(output_dir, f"aligned_1_{uuid.uuid4().hex[:8]}.tif")
    out_path2 = os.path.join(output_dir, f"aligned_2_{uuid.uuid4().hex[:8]}.tif")
    
    # Fast path: if not geospatial, or same CRS & transform & shape, just return them or copy
    if not manifest1.is_geospatial or not manifest2.is_geospatial:
        # Fallback to simple resize if not geospatial (using PIL/cv2 later, but here just copy)
        import shutil
        shutil.copy(path1, out_path1)
        # We assume downstream tools handle non-geospatial resizing if needed
        shutil.copy(path2, out_path2)
        return AlignmentResult(out_path1, out_path2, None, None, manifest1.width_px, manifest1.height_px)
        
    with rasterio.open(path1) as src1, rasterio.open(path2) as src2:
        # Define common grid based on src1
        dst_crs = src1.crs
        dst_transform = src1.transform
        dst_width = src1.width
        dst_height = src1.height
        
        # Copy src1 to out_path1
        kwargs1 = src1.meta.copy()
        with rasterio.open(out_path1, 'w', **kwargs1) as dst1:
            for i in range(1, src1.count + 1):
                dst1.write(src1.read(i), i)
                
        # Reproject/Resample src2 to match src1
        kwargs2 = src2.meta.copy()
        kwargs2.update({
            'crs': dst_crs,
            'transform': dst_transform,
            'width': dst_width,
            'height': dst_height
        })
        
        with rasterio.open(out_path2, 'w', **kwargs2) as dst2:
            for i in range(1, src2.count + 1):
                reproject(
                    source=rasterio.band(src2, i),
                    destination=rasterio.band(dst2, i),
                    src_transform=src2.transform,
                    src_crs=src2.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear
                )
                
        return AlignmentResult(
            aligned_path1=out_path1,
            aligned_path2=out_path2,
            transform=list(dst_transform),
            crs_wkt=dst_crs.to_string(),
            width=dst_width,
            height=dst_height
        )
