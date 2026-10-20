"""
Astra AI — Remote Sensing VLM Dataset
Loads multimodal pairs from BigEarthNet.txt (parquet) and maps them to physical
Sentinel-2 optical rasters from the processed BigEarthNet v2.0 dataset.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pyarrow.parquet as pq
import torch
from torch.utils.data import Dataset
from PIL import Image
from loguru import logger
import rasterio

# Sentinel-2 Level-2A BOA reflectance normalizer: DN = 10,000 * BOA
def load_and_scale_geotiff(raster_path: Path) -> np.ndarray:
    """Reads a 3-band GeoTIFF (B04, B03, B02) and normalizes to [0, 1] float32."""
    with rasterio.open(str(raster_path)) as src:
        arr = src.read([1, 2, 3])  # Shape: (3, H, W)
        arr = np.clip(arr.astype(np.float32) / 10000.0, 0.0, 1.0)
        # Convert to HWC for image processors or PIL
        arr = np.transpose(arr, (1, 2, 0))
        return (arr * 255.0).astype(np.uint8)


class BigEarthNetTxtDataset(Dataset):
    """
    PyTorch Dataset reading from BigEarthNet.txt.parquet.
    Links each parquet row's `patch_id` to its corresponding physical GeoTIFF on disk.
    """
    def __init__(
        self,
        parquet_path: Path | str = "datasets/02_BigEarthNet_txt/BigEarthNet.txt/BigEarthNet.txt.parquet",
        images_dir: Path | str = "datasets/processed/bigearthnet_resnet50_full",
        split: Optional[str] = "train",
        task_types: Optional[List[str]] = None,
        max_samples: Optional[int] = None,
    ):
        self.parquet_path = Path(parquet_path)
        self.images_root = Path(images_dir)
        self.split = split
        self.task_types = task_types

        if not self.parquet_path.exists():
            raise FileNotFoundError(f"BigEarthNet.txt.parquet not found at {self.parquet_path}")

        logger.info(f"Loading BigEarthNet.txt metadata from {self.parquet_path} (split={split})...")
        
        # Read parquet columns
        cols = ["ID", "s1_name", "patch_id", "input", "output", "type", "category", "split"]
        table = pq.read_table(str(self.parquet_path), columns=cols)
        
        import pyarrow.compute as pc
        import pyarrow as pa
        
        # Fast C++ vector filter by split if specified
        if split is not None:
            mask = pc.equal(table["split"], split)
            table = table.filter(mask)

        # Fast C++ vector filter by task types if specified
        if task_types is not None:
            mask = pc.is_in(table["type"], value_set=pa.array(task_types))
            table = table.filter(mask)

        if max_samples is not None and max_samples < table.num_rows:
            table = table.slice(0, max_samples)

        self.data = table.to_pydict()
        self.num_samples = len(self.data["ID"])
        logger.info(f"Loaded {self.num_samples:,} samples for split='{split}'")

        # Build index of image directories for fast file resolution
        self._image_cache: Dict[str, Path] = {}
        self._candidate_dirs = [
            self.images_root / "test" / "images",
            self.images_root / "val" / "images",
            self.images_root / "train" / "images",
        ]

    def _resolve_image_path(self, patch_id: str) -> Optional[Path]:
        """Resolves the physical GeoTIFF path for a patch_id."""
        if patch_id in self._image_cache:
            return self._image_cache[patch_id]

        filename = f"{patch_id}.tif"
        for d in self._candidate_dirs:
            p = d / filename
            if p.exists():
                self._image_cache[patch_id] = p
                return p
        return None

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        patch_id = self.data["patch_id"][idx]
        question = self.data["input"][idx]
        answer = self.data["output"][idx]
        task_type = self.data["type"][idx]
        category = self.data["category"][idx]
        s1_name = self.data["s1_name"][idx]

        image_path = self._resolve_image_path(patch_id)
        if image_path is not None and image_path.exists():
            rgb_arr = load_and_scale_geotiff(image_path)
            pil_image = Image.fromarray(rgb_arr, mode="RGB")
        else:
            # Synthetic 120x120 dummy for missing patches to prevent crash
            rgb_arr = np.zeros((120, 120, 3), dtype=np.uint8)
            pil_image = Image.fromarray(rgb_arr, mode="RGB")

        return {
            "patch_id": patch_id,
            "s1_name": s1_name,
            "image": pil_image,
            "image_path": str(image_path) if image_path else None,
            "question": question,
            "answer": answer,
            "task_type": task_type,
            "category": category,
        }
