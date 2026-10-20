"""
LEVIR-CD PyTorch Dataset Loader for Bi-Temporal Change Detection.
Loads co-registered optical image pairs (T1 and T2) and binary change masks.
Target masks: 0 = unchanged, 1 = changed (converted from 0/255 PNGs).
"""

from pathlib import Path
from typing import Any, Callable, Optional, Tuple
import numpy as np
from PIL import Image
import torch
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T
from loguru import logger


DEFAULT_IMAGENET_MEAN = [0.485, 0.456, 0.406]
DEFAULT_IMAGENET_STD = [0.229, 0.224, 0.225]


class LEVIRCDDataset(Dataset):
    """
    PyTorch Dataset for LEVIR-CD building change detection.
    Directory structure:
        {root_dir}/{split}/A/       -> Image Date 1 (T1)
        {root_dir}/{split}/B/       -> Image Date 2 (T2)
        {root_dir}/{split}/label/   -> Binary change mask (0 or 255)
    """

    def __init__(
        self,
        root_dir: str | Path = "datasets/05_LEVIR_CD",
        split: str = "test",
        img_size: int = 256,
        transform: Optional[Callable] = None,
        max_samples: Optional[int] = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.split = split
        self.img_size = img_size
        self.split_dir = self.root_dir / split

        if not self.split_dir.exists():
            raise FileNotFoundError(f"LEVIR-CD split directory not found: {self.split_dir}")

        self.dir_a = self.split_dir / "A"
        self.dir_b = self.split_dir / "B"
        self.dir_label = self.split_dir / "label"

        for d in [self.dir_a, self.dir_b, self.dir_label]:
            if not d.exists():
                raise FileNotFoundError(f"Subdirectory does not exist: {d}")

        # Scan and verify matching files
        a_files = {f.name: f for f in self.dir_a.glob("*.png")}
        b_files = {f.name: f for f in self.dir_b.glob("*.png")}
        label_files = {f.name: f for f in self.dir_label.glob("*.png")}

        common_keys = sorted(list(set(a_files.keys()) & set(b_files.keys()) & set(label_files.keys())))
        if not common_keys:
            raise ValueError(f"No matching image trios (A, B, label) found in {self.split_dir}")

        if max_samples:
            common_keys = common_keys[:max_samples]

        self.samples = [
            (a_files[k], b_files[k], label_files[k], k)
            for k in common_keys
        ]

        # Standard image normalization
        self.img_transform = transform or T.Compose([
            T.Resize((self.img_size, self.img_size), interpolation=T.InterpolationMode.BILINEAR),
            T.ToTensor(),
            T.Normalize(mean=DEFAULT_IMAGENET_MEAN, std=DEFAULT_IMAGENET_STD),
        ])

        logger.info(
            f"LEVIRCDDataset initialized: split='{self.split}', samples={len(self.samples)}, "
            f"target_size=({self.img_size}x{self.img_size})"
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        path_a, path_b, path_lbl, name = self.samples[idx]

        # Load images
        img_a = Image.open(path_a).convert("RGB")
        img_b = Image.open(path_b).convert("RGB")
        orig_w, orig_h = img_a.size

        # Load mask
        mask_img = Image.open(path_lbl).convert("L")

        # Resize mask using nearest neighbor to keep crisp binary edges
        mask_resized = mask_img.resize(
            (self.img_size, self.img_size),
            resample=Image.Resampling.NEAREST
        )
        mask_arr = np.array(mask_resized, dtype=np.uint8)

        # Convert mask: 0 for unchanged, 1 for changed
        binary_mask = (mask_arr > 127).astype(np.int64)
        mask_tensor = torch.from_numpy(binary_mask)  # Shape: (H, W), dtype: torch.int64

        # Transform images
        tensor_a = self.img_transform(img_a)  # Shape: (3, H, W)
        tensor_b = self.img_transform(img_b)  # Shape: (3, H, W)

        return {
            "name": name,
            "A": tensor_a,
            "B": tensor_b,
            "label": mask_tensor,
            "original_size": (orig_h, orig_w),
        }


def create_levir_dataloader(
    root_dir: str | Path = "datasets/05_LEVIR_CD",
    split: str = "test",
    batch_size: int = 4,
    shuffle: bool = False,
    img_size: int = 256,
    num_workers: int = 0,
    max_samples: Optional[int] = None,
) -> DataLoader:
    """Factory helper to build a PyTorch DataLoader for LEVIR-CD."""
    dataset = LEVIRCDDataset(
        root_dir=root_dir,
        split=split,
        img_size=img_size,
        max_samples=max_samples,
    )
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
