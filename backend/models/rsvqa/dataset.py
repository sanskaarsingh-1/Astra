"""
Astra AI — RSVQA Dataset Loader
Reads questions, answers, and images from the RSVQA-LR benchmark dataset.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import rasterio
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset
from loguru import logger


class RSVQADataset(Dataset):
    """
    PyTorch Dataset for RSVQA (Remote Sensing Visual Question Answering).
    Maps questions to answers and physical 256x256 GeoTIFF images in Images_LR.
    """
    def __init__(
        self,
        annotations_dir: Path | str = "datasets/06_RSVQA/annotations",
        images_dir: Path | str = "datasets/06_RSVQA/Images_LR",
        split: str = "train",
        max_samples: Optional[int] = None,
    ):
        self.annotations_dir = Path(annotations_dir)
        self.images_dir = Path(images_dir)
        self.split = split

        q_file = self.annotations_dir / f"LR_split_{split}_questions.json"
        a_file = self.annotations_dir / f"LR_split_{split}_answers.json"
        img_file = self.annotations_dir / f"LR_split_{split}_images.json"

        if not q_file.exists():
            raise FileNotFoundError(f"RSVQA questions file not found: {q_file}")

        logger.info(f"Loading RSVQA annotations for split='{split}'...")
        with open(q_file, "r", encoding="utf-8") as f:
            raw_questions = json.load(f)["questions"]
            self.questions = [q for q in raw_questions if q.get("active", True)]

        # Build answer lookup by question_id
        self.answers_by_qid: Dict[int, str] = {}
        if a_file.exists():
            with open(a_file, "r", encoding="utf-8") as f:
                ans_list = json.load(f)["answers"]
                for a in ans_list:
                    if a.get("active", True) and "question_id" in a:
                        self.answers_by_qid[a["question_id"]] = a.get("answer", "")

        # Limit samples if requested
        if max_samples is not None:
            self.questions = self.questions[:max_samples]

        logger.success(f"RSVQA split '{split}' loaded: {len(self.questions):,} questions.")

    def __len__(self) -> int:
        return len(self.questions)

    def _load_image(self, img_id: int) -> Image.Image:
        img_path = self.images_dir / f"{img_id}.tif"
        if not img_path.exists():
            # Return blank image if not found
            return Image.fromarray(np.zeros((256, 256, 3), dtype=np.uint8), mode="RGB")

        with rasterio.open(str(img_path)) as src:
            arr = src.read([1, 2, 3])
            arr = np.transpose(arr, (1, 2, 0))
            if arr.dtype != np.uint8:
                arr = (np.clip(arr / 10000.0, 0.0, 1.0) * 255).astype(np.uint8)
            return Image.fromarray(arr, mode="RGB")

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        q_info = self.questions[idx]
        qid = q_info["id"]
        img_id = q_info["img_id"]
        question_text = q_info["question"]
        q_type = q_info.get("type", "unknown")
        answer_text = self.answers_by_qid.get(qid, "")

        image = self._load_image(img_id)

        return {
            "question_id": qid,
            "img_id": img_id,
            "image": image,
            "image_path": str(self.images_dir / f"{img_id}.tif"),
            "question": question_text,
            "answer": answer_text,
            "type": q_type,
        }
