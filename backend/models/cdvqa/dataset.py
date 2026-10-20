"""
CDVQA PyTorch Dataset Loader for Change-Based Visual Question Answering.
Links questions, ground truth answers, and co-registered bi-temporal image pairs.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image
from torch.utils.data import Dataset
from loguru import logger


class CDVQADataset(Dataset):
    """
    Dataset for Change-Based Visual Question Answering (CDVQA).
    Supports splits: 'Train', 'Val', 'Test', 'Test2'.
    """

    def __init__(
        self,
        annotations_dir: Union[str, Path] = "datasets/04_CDVQA/CDVQA-main",
        images_dir: Union[str, Path] = "datasets/04_CDVQA/images",
        split: str = "Val",
        max_samples: Optional[int] = None,
    ) -> None:
        self.annotations_dir = Path(annotations_dir)
        self.images_dir = Path(images_dir)
        self.split = split.capitalize()

        self.im1_dir = self.images_dir / "im1"
        self.im2_dir = self.images_dir / "im2"

        q_file = self.annotations_dir / f"{self.split}_questions.json"
        a_file = self.annotations_dir / f"{self.split}_answers.json"
        img_file = self.annotations_dir / f"{self.split}_images.json"

        for p in [q_file, a_file, img_file]:
            if not p.exists():
                raise FileNotFoundError(f"CDVQA annotation file not found: {p}")

        logger.info(f"Loading CDVQA annotations from: {self.annotations_dir} (Split: {self.split})")

        with open(img_file, "r", encoding="utf-8") as f:
            images_data = json.load(f)["images"]
        with open(a_file, "r", encoding="utf-8") as f:
            answers_data = json.load(f)["answers"]
        with open(q_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)["questions"]

        # Build image lookup: img_id -> file_name
        self.img_map: Dict[int, str] = {item["id"]: item["file_name"] for item in images_data}

        # Build answer lookup: question_id -> answer string
        self.ans_map: Dict[int, str] = {item["question_id"]: item["answer"] for item in answers_data}

        # Filter questions with valid images on disk
        self.samples: List[Dict[str, Any]] = []
        for q in questions_data:
            q_id = q["id"]
            img_id = q.get("img_id")
            file_name = self.img_map.get(img_id)
            if not file_name:
                continue

            p1 = self.im1_dir / file_name
            p2 = self.im2_dir / file_name

            if p1.exists() and p2.exists():
                ans = self.ans_map.get(q_id, "unknown")
                self.samples.append({
                    "question_id": q_id,
                    "question": q["question"],
                    "question_type": q.get("type", "general"),
                    "answer": ans,
                    "file_name": file_name,
                    "t1_path": str(p1),
                    "t2_path": str(p2),
                })

        if max_samples:
            self.samples = self.samples[:max_samples]

        logger.success(
            f"CDVQADataset initialized: split='{self.split}', valid_samples={len(self.samples)}"
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.samples[idx]
        return {
            "question_id": item["question_id"],
            "question": item["question"],
            "question_type": item["question_type"],
            "answer": item["answer"],
            "file_name": item["file_name"],
            "t1_path": item["t1_path"],
            "t2_path": item["t2_path"],
        }


def get_cdvqa_samples(
    annotations_dir: Union[str, Path] = "datasets/04_CDVQA/CDVQA-main",
    images_dir: Union[str, Path] = "datasets/04_CDVQA/images",
    split: str = "Val",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Helper to retrieve a list of samples for evaluation or quick testing."""
    dataset = CDVQADataset(
        annotations_dir=annotations_dir,
        images_dir=images_dir,
        split=split,
        max_samples=limit,
    )
    return [dataset[i] for i in range(len(dataset))]
