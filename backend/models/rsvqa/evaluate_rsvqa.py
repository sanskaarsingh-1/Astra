"""
Astra AI — RSVQA Benchmark Evaluation Pipeline
Evaluates the RSVQA specialist on the official test split (33,212 questions).
"""

import argparse
import json
import time
from pathlib import Path
from loguru import logger
from backend.models.rsvqa.dataset import RSVQADataset
from backend.models.rsvqa.model import rsvqa_specialist


def parse_args():
    parser = argparse.ArgumentParser(description="Astra AI — RSVQA Benchmark Evaluation")
    parser.add_argument("--annotations_dir", type=str, default="datasets/06_RSVQA/annotations")
    parser.add_argument("--images_dir", type=str, default="datasets/06_RSVQA/Images_LR")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--sample_limit", type=int, default=20, help="Number of questions to evaluate for validation")
    parser.add_argument("--output_json", type=str, default="backend/models/rsvqa/eval_results.json")
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("=" * 60)
    logger.info("ASTRA RSVQA BENCHMARK EVALUATION")
    logger.info("=" * 60)
    logger.info(f"Target Split : {args.split}")
    logger.info(f"Sample Limit : {args.sample_limit}")

    dataset = RSVQADataset(
        annotations_dir=args.annotations_dir,
        images_dir=args.images_dir,
        split=args.split,
        max_samples=args.sample_limit,
    )

    correct_by_type = {}
    total_by_type = {}
    total_correct = 0

    t0 = time.time()
    for i in range(len(dataset)):
        sample = dataset[i]
        q_text = sample["question"]
        ref_ans = str(sample["answer"]).strip().lower()
        q_type = sample["type"]

        res = rsvqa_specialist.predict(sample["image_path"], q_text)
        pred_ans = str(res["answer"]).strip().lower()

        is_match = (pred_ans == ref_ans) or (ref_ans in pred_ans)
        if is_match:
            total_correct += 1

        correct_by_type[q_type] = correct_by_type.get(q_type, 0) + (1 if is_match else 0)
        total_by_type[q_type] = total_by_type.get(q_type, 0) + 1

    total_samples = len(dataset)
    accuracy = round((total_correct / max(total_samples, 1)) * 100, 2)
    duration = time.time() - t0

    logger.info("-" * 60)
    logger.info(f"Evaluated {total_samples} samples in {duration:.2f}s ({duration/max(total_samples, 1)*1000:.1f}ms/sample)")
    logger.info(f"Overall Accuracy: {accuracy}% ({total_correct}/{total_samples})")

    type_accuracies = {}
    for q_type, count in total_by_type.items():
        corr = correct_by_type.get(q_type, 0)
        acc = round((corr / count) * 100, 2)
        type_accuracies[q_type] = {"correct": corr, "total": count, "accuracy_pct": acc}
        logger.info(f"  - {q_type:<15}: {acc:>6.2f}% ({corr}/{count})")

    out_summary = {
        "dataset": "RSVQA-LR",
        "split": args.split,
        "sample_count": total_samples,
        "overall_accuracy_pct": accuracy,
        "per_type_accuracy": type_accuracies,
        "avg_latency_ms": round((duration / max(total_samples, 1)) * 1000, 2),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_summary, f, indent=2)

    logger.success(f"RSVQA evaluation results saved to {out_path}")


if __name__ == "__main__":
    main()
