"""
Independent Evaluation Pipeline for Change-Based Visual Question Answering (CDVQA).
Evaluates accuracy across question categories (change_or_not, increase/decrease, transitions)
with a responsive, in-place tqdm progress bar.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict
from tqdm import tqdm
from loguru import logger

from backend.models.cdvqa.dataset import CDVQADataset
from backend.models.cdvqa.model import get_cdvqa_specialist


def normalize_answer(text: str) -> str:
    """Normalize answer string for exact and fuzzy matching."""
    t = text.lower().strip()
    t = t.rstrip(".,;!?:")
    if t in ["yes", "true", "y"]:
        return "yes"
    if t in ["no", "false", "n"]:
        return "no"
    return t


def evaluate_cdvqa(
    annotations_dir: str = "datasets/04_CDVQA/CDVQA-main",
    images_dir: str = "datasets/04_CDVQA/images",
    split: str = "Val",
    max_samples: int | None = 50,
) -> Dict[str, Any]:
    logger.info(f"Starting CDVQA Evaluation on split='{split}' (max_samples={max_samples})")

    dataset = CDVQADataset(
        annotations_dir=annotations_dir,
        images_dir=images_dir,
        split=split,
        max_samples=max_samples,
    )

    specialist = get_cdvqa_specialist()
    total = len(dataset)
    correct = 0

    type_total = defaultdict(int)
    type_correct = defaultdict(int)

    t0 = time.time()

    with tqdm(enumerate(dataset), total=total, desc="Evaluating CDVQA", leave=True) as pbar:
        for idx, sample in pbar:
            q = sample["question"]
            gt = normalize_answer(sample["answer"])
            q_type = sample["question_type"]

            res = specialist.answer_query(
                t1_input=sample["t1_path"],
                t2_input=sample["t2_path"],
                question=q,
                question_type=q_type,
            )
            pred = normalize_answer(res["answer"])

            # Check matching
            is_match = (pred == gt) or (gt in pred) or (pred in gt)
            if is_match:
                correct += 1
                type_correct[q_type] += 1
            type_total[q_type] += 1

            current_acc = (correct / (idx + 1)) * 100.0
            pbar.set_postfix({
                "step": idx + 1,
                "acc": f"{current_acc:.1f}%",
                "correct": f"{correct}/{idx + 1}",
                "type": q_type[:12],
            })

    elapsed = time.time() - t0
    overall_acc = (correct / max(total, 1)) * 100.0

    breakdown = {}
    for t, tot in type_total.items():
        c = type_correct[t]
        breakdown[t] = {
            "correct": c,
            "total": tot,
            "accuracy": round((c / max(tot, 1)) * 100.0, 2),
        }

    report = {
        "samples_evaluated": total,
        "overall_accuracy": round(overall_acc, 2),
        "total_correct": correct,
        "elapsed_seconds": round(elapsed, 2),
        "accuracy_by_question_type": breakdown,
    }

    print("\n" + "=" * 55)
    print("         CDVQA EVALUATION BENCHMARK REPORT")
    print("=" * 55)
    print(f" Total Samples Evaluated : {report['samples_evaluated']}")
    print(f" Processing Time         : {report['elapsed_seconds']}s")
    print(f" Overall VQA Accuracy    : {report['overall_accuracy']}%\n")
    print(" Accuracy by Question Type:")
    for q_type, stats in breakdown.items():
        print(f"   - {q_type:<22}: {stats['accuracy']:>6.2f}% ({stats['correct']}/{stats['total']})")
    print("=" * 55 + "\n")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="CDVQA Evaluation Pipeline")
    parser.add_argument("--annotations_dir", type=str, default="datasets/04_CDVQA/CDVQA-main")
    parser.add_argument("--images_dir", type=str, default="datasets/04_CDVQA/images")
    parser.add_argument("--split", type=str, default="Val")
    parser.add_argument("--max_samples", type=int, default=30)
    parser.add_argument("--output_report", type=str, default="datasets/04_CDVQA/evaluation_report.json")
    args = parser.parse_args()

    report = evaluate_cdvqa(
        annotations_dir=args.annotations_dir,
        images_dir=args.images_dir,
        split=args.split,
        max_samples=args.max_samples,
    )

    out_path = Path(args.output_report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.success(f"CDVQA evaluation report saved to: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
