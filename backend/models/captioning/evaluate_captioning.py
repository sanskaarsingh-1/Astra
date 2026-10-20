"""
Astra AI — VRSBench Captioning & Visual Grounding Evaluation
Evaluates:
1. Scene description quality on VRSBench_EVAL_Cap.json (BLEU / token overlap).
2. Referring expression localization on VRSBench_EVAL_referring.json (IoU metric).
Includes responsive tqdm progress bar.
"""

import argparse
import json
import time
from pathlib import Path
from loguru import logger
from tqdm import tqdm
from PIL import Image

from backend.models.captioning.dataset import VRSBenchDataset
from backend.models.captioning.model import VRSBenchSpecialist


def parse_args():
    parser = argparse.ArgumentParser(description="Astra AI — VRSBench Benchmark Evaluation")
    parser.add_argument("--annotations_dir", type=str, default="datasets/07_VRSBench/annotations")
    parser.add_argument("--images_dir", type=str, default="datasets/07_VRSBench/Images")
    parser.add_argument("--adapter_path", type=str, default="backend/models/remote_sensing_vlm/checkpoints/best_adapter")
    parser.add_argument("--sample_limit", type=int, default=30)
    parser.add_argument("--output_json", type=str, default="backend/models/captioning/eval_results.json")
    return parser.parse_args()


def compute_token_overlap(pred: str, ref: str) -> float:
    pred_tokens = set(pred.lower().split())
    ref_tokens = set(ref.lower().split())
    if not ref_tokens or not pred_tokens:
        return 0.0
    return len(pred_tokens.intersection(ref_tokens)) / len(ref_tokens)


def compute_iou(boxA: list, boxB: list) -> float:
    # box format: [xmin, ymin, xmax, ymax]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    unionArea = boxAArea + boxBArea - interArea

    return interArea / unionArea if unionArea > 0 else 0.0


def main():
    args = parse_args()
    logger.info("=" * 60)
    logger.info("ASTRA VRSBENCH SPECIALIST BENCHMARK EVALUATION")
    logger.info("=" * 60)
    logger.info(f"Sample Limit : {args.sample_limit}")
    logger.info(f"Adapter Path : {args.adapter_path}")

    # 1. Initialize specialist
    specialist = VRSBenchSpecialist(adapter_path=args.adapter_path).load()

    # 2. Evaluate Captioning
    cap_dataset = VRSBenchDataset(
        annotations_dir=args.annotations_dir,
        images_dir=args.images_dir,
        task="caption",
        split="val",
        max_samples=args.sample_limit,
    )

    cap_scores = []
    cap_records = []
    logger.info(f"Evaluating {len(cap_dataset)} captioning samples...")
    for idx in tqdm(range(len(cap_dataset)), desc="Captioning Eval", dynamic_ncols=True, unit="sample"):
        sample = cap_dataset[idx]
        result = specialist.describe_scene(sample["image"])
        overlap = compute_token_overlap(result["caption"], sample["caption"])
        cap_scores.append(overlap)

        if idx < 5:
            cap_records.append({
                "image_id": sample["image_id"],
                "expected": sample["caption"][:100] + "...",
                "generated": result["caption"],
                "overlap_score": round(overlap, 3),
            })

    avg_cap_overlap = sum(cap_scores) / max(1, len(cap_scores))

    # 3. Evaluate Visual Grounding
    ref_dataset = VRSBenchDataset(
        annotations_dir=args.annotations_dir,
        images_dir=args.images_dir,
        task="grounding",
        split="val",
        max_samples=args.sample_limit,
    )

    grounding_records = []
    valid_boxes = 0
    logger.info(f"Evaluating {len(ref_dataset)} referring expression samples...")
    for idx in tqdm(range(len(ref_dataset)), desc="Grounding Eval", dynamic_ncols=True, unit="sample"):
        sample = ref_dataset[idx]
        query = sample["target_text"]
        expected_box = sample["bbox"]
        boxes = specialist.ground_expression(sample["image"], query)

        if boxes:
            valid_boxes += 1
            pred_box = [boxes[0]["box_2d"][1], boxes[0]["box_2d"][0], boxes[0]["box_2d"][3], boxes[0]["box_2d"][2]]
            iou = compute_iou(pred_box, expected_box) if expected_box else 0.0
        else:
            iou = 0.0

        if idx < 5:
            grounding_records.append({
                "image_id": sample["image_id"],
                "query": query,
                "expected_box": expected_box,
                "predicted_box": boxes[0]["box_2d"] if boxes else None,
                "iou": round(iou, 3),
            })

    grounding_rate = 100.0 * valid_boxes / max(1, len(ref_dataset))

    logger.info("=" * 60)
    logger.info("VRSBENCH EVALUATION SUMMARY")
    logger.info("=" * 60)
    logger.success(f"Captioning Token Overlap : {avg_cap_overlap * 100:.1f}%")
    logger.success(f"Grounding Box Generation : {valid_boxes}/{len(ref_dataset)} ({grounding_rate:.1f}%)")
    logger.info("=" * 60)

    # Save summary
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "captioning_evaluated": len(cap_dataset),
        "captioning_overlap": round(avg_cap_overlap, 4),
        "grounding_evaluated": len(ref_dataset),
        "grounding_valid_boxes": valid_boxes,
        "sample_captions": cap_records,
        "sample_grounding": grounding_records,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.success(f"Saved VRSBench evaluation report to {out_path}")


if __name__ == "__main__":
    main()
