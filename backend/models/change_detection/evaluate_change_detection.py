"""
Independent Evaluation Pipeline for LEVIR-CD Bi-Temporal Change Detection.
Computes pixel-level Precision, Recall, F1-Score, IoU, and Overall Accuracy
across the LEVIR-CD test split (128 image pairs).
Features responsive, in-place tqdm progress bar with dynamic postfix metrics.
"""

import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm
from loguru import logger

from backend.models.change_detection.dataset import create_levir_dataloader
from backend.models.change_detection.model import get_change_specialist


def evaluate(
    data_dir: str = "datasets/05_LEVIR_CD",
    split: str = "test",
    batch_size: int = 4,
    img_size: int = 256,
    threshold: float = 0.5,
    max_samples: int | None = None,
    checkpoint_path: str | None = None,
) -> dict[str, float]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Starting LEVIR-CD Change Detection Evaluation on {device}")

    loader = create_levir_dataloader(
        root_dir=data_dir,
        split=split,
        batch_size=batch_size,
        shuffle=False,
        img_size=img_size,
        max_samples=max_samples,
    )

    specialist = get_change_specialist(checkpoint_path=checkpoint_path, device=device)
    model = specialist.model
    model.eval()

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_tn = 0

    num_batches = len(loader)
    logger.info(f"Evaluating {len(loader.dataset)} sample pairs across {num_batches} batches...")

    t0 = time.time()

    with tqdm(enumerate(loader), total=num_batches, desc="Evaluating LEVIR-CD", leave=True) as pbar:
        for step, batch in pbar:
            t1 = batch["A"].to(device)
            t2 = batch["B"].to(device)
            targets = batch["label"].to(device)  # (B, H, W), values {0, 1}

            with torch.no_grad():
                logits = model(t1, t2)
                probs = F.softmax(logits, dim=1)
                preds = (probs[:, 1, :, :] >= threshold).long()

            # Accumulate confusion matrix counts
            tp = ((preds == 1) & (targets == 1)).sum().item()
            fp = ((preds == 1) & (targets == 0)).sum().item()
            fn = ((preds == 0) & (targets == 1)).sum().item()
            tn = ((preds == 0) & (targets == 0)).sum().item()

            total_tp += tp
            total_fp += fp
            total_fn += fn
            total_tn += tn

            batch_iou = tp / max(tp + fp + fn, 1)
            pbar.set_postfix({
                "step": step + 1,
                "batch_iou": f"{batch_iou:.4f}",
                "total_tp": total_tp,
                "total_fp": total_fp,
            })

    elapsed = time.time() - t0

    # Compute global metrics
    precision = total_tp / max(total_tp + total_fp, 1)
    recall = total_tp / max(total_tp + total_fn, 1)
    f1 = (2 * precision * recall) / max(precision + recall, 1e-7)
    iou = total_tp / max(total_tp + total_fp + total_fn, 1)
    total_pixels = total_tp + total_fp + total_fn + total_tn
    accuracy = (total_tp + total_tn) / max(total_pixels, 1)

    metrics = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "iou": round(iou, 4),
        "overall_accuracy": round(accuracy, 4),
        "total_true_positives": int(total_tp),
        "total_false_positives": int(total_fp),
        "total_false_negatives": int(total_fn),
        "total_true_negatives": int(total_tn),
        "samples_evaluated": len(loader.dataset),
        "elapsed_seconds": round(elapsed, 2),
    }

    print("\n" + "=" * 55)
    print("        LEVIR-CD CHANGE DETECTION EVALUATION REPORT")
    print("=" * 55)
    print(f" Samples Evaluated  : {metrics['samples_evaluated']}")
    print(f" Processing Time    : {metrics['elapsed_seconds']}s")
    print(f" Precision          : {metrics['precision']:.4f}")
    print(f" Recall             : {metrics['recall']:.4f}")
    print(f" F1-Score           : {metrics['f1_score']:.4f}")
    print(f" IoU (Change Class) : {metrics['iou']:.4f}")
    print(f" Overall Accuracy   : {metrics['overall_accuracy']:.4f}")
    print("=" * 55 + "\n")

    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="LEVIR-CD Change Detection Evaluator")
    parser.add_argument("--data_dir", type=str, default="datasets/05_LEVIR_CD")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--img_size", type=int, default=256)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--output_report", type=str, default="datasets/05_LEVIR_CD/evaluation_report.json")
    args = parser.parse_args()

    metrics = evaluate(
        data_dir=args.data_dir,
        split=args.split,
        batch_size=args.batch_size,
        img_size=args.img_size,
        threshold=args.threshold,
        max_samples=args.max_samples,
        checkpoint_path=args.checkpoint,
    )

    out_file = Path(args.output_report)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.success(f"Evaluation report saved to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
