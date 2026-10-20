"""
Astra AI — VRSBench Captioning & Visual Grounding Dataset
Loads authentic remote-sensing multimodal samples from VRSBench:
1. Captioning: Detailed narrative scene descriptions.
2. Referring Expression Grounding: Object queries resolved to spatial bounding boxes.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import torch
from torch.utils.data import Dataset
from PIL import Image
from loguru import logger


class VRSBenchDataset(Dataset):
    """
    PyTorch Dataset reading from VRSBench annotations:
    - Captioning: VRSBench_EVAL_Cap.json
    - Referring: VRSBench_EVAL_referring.json
    - Training: VRSBench_train.json
    """
    def __init__(
        self,
        annotations_dir: Path | str = "datasets/07_VRSBench/annotations",
        images_dir: Path | str = "datasets/07_VRSBench/Images",
        task: str = "caption",  # "caption", "grounding", or "both"
        split: str = "val",     # "val" or "train"
        max_samples: Optional[int] = None,
    ):
        self.annotations_dir = Path(annotations_dir)
        self.images_root = Path(images_dir)
        self.task = task
        self.split = split

        # Candidate image subdirectories
        self._image_dirs = [
            self.images_root / "val" / "Images_val",
            self.images_root / "train" / "Images_train",
            self.images_root / "val",
            self.images_root / "train",
        ]
        self._image_cache: Dict[str, Path] = {}

        self.samples: List[Dict[str, Any]] = []
        self._load_annotations(max_samples)

    def _resolve_image_path(self, img_id: str) -> Optional[Path]:
        if img_id in self._image_cache:
            return self._image_cache[img_id]

        for d in self._image_dirs:
            p = d / img_id
            if p.exists():
                self._image_cache[img_id] = p
                return p
        return None

    def _load_annotations(self, max_samples: Optional[int]):
        # Select annotation files based on task and split
        target_files = []
        if self.split == "val":
            if self.task in ("caption", "both"):
                cap_file = self.annotations_dir / "VRSBench_EVAL_Cap.json"
                if cap_file.exists():
                    target_files.append((cap_file, "caption"))
            if self.task in ("grounding", "both"):
                ref_file = self.annotations_dir / "VRSBench_EVAL_referring.json"
                if ref_file.exists():
                    target_files.append((ref_file, "grounding"))
        else:
            train_file = self.annotations_dir / "VRSBench_train.json"
            if train_file.exists():
                target_files.append((train_file, "train"))

        for file_path, item_type in target_files:
            logger.info(f"Loading VRSBench {item_type} data from {file_path.name}...")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                entry = {
                    "image_id": item.get("image_id"),
                    "question_id": item.get("question_id"),
                    "task_type": item.get("type", item_type),
                    "prompt": item.get("question", "Describe this remote sensing image in detail."),
                    "caption": item.get("ground_truth") if item.get("type") == "caption" else None,
                    "target_text": item.get("question") if item.get("type") == "ref" else item.get("ground_truth"),
                    "obj_cls": item.get("obj_cls"),
                    "bbox": None,
                }

                # Convert obj_corner polygon to [xmin, ymin, xmax, ymax]
                if "obj_corner" in item and item["obj_corner"]:
                    corner = item["obj_corner"]
                    xs = corner[0::2]
                    ys = corner[1::2]
                    entry["bbox"] = [
                        round(float(min(xs)), 4),
                        round(float(min(ys)), 4),
                        round(float(max(xs)), 4),
                        round(float(max(ys)), 4),
                    ]

                self.samples.append(entry)
                if max_samples is not None and len(self.samples) >= max_samples:
                    break

            if max_samples is not None and len(self.samples) >= max_samples:
                break

        logger.info(f"VRSBenchDataset loaded {len(self.samples):,} samples (task={self.task}, split={self.split}).")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.samples[idx]
        img_path = self._resolve_image_path(item["image_id"])

        if img_path is not None and img_path.exists():
            image = Image.open(img_path).convert("RGB")
        else:
            image = Image.new("RGB", (512, 512), color="gray")

        return {
            "image_id": item["image_id"],
            "image": image,
            "image_path": str(img_path) if img_path else None,
            "task_type": item["task_type"],
            "prompt": item["prompt"],
            "caption": item["caption"],
            "target_text": item["target_text"],
            "bbox": item["bbox"],
            "obj_cls": item["obj_cls"],
        }


def vrsbench_collate_fn(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "image_id": [x["image_id"] for x in items],
        "image": [x["image"] for x in items],
        "task_type": [x["task_type"] for x in items],
        "prompt": [x["prompt"] for x in items],
        "caption": [x["caption"] for x in items],
        "target_text": [x["target_text"] for x in items],
        "bbox": [x["bbox"] for x in items],
        "obj_cls": [x["obj_cls"] for x in items],
    }
