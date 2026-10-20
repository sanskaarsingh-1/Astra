"""
Astra AI — Remote Sensing VLM Evaluation Pipeline
Evaluates model predictions on the official BigEarthNet.txt benchmark split (1,082 verified pairs).
Computes Exact Match accuracy, Substring Match, and per-task performance metrics.
"""

import argparse
import json
import time
from pathlib import Path
import torch
from loguru import logger
from peft import PeftModel
from transformers import BlipProcessor, BlipForConditionalGeneration
from tqdm import tqdm

from backend.models.remote_sensing_vlm.dataset import BigEarthNetTxtDataset


def parse_args():
    parser = argparse.ArgumentParser(description="Astra AI — Remote Sensing VLM Benchmark Evaluation")
    parser.add_argument("--parquet_path", type=str, default="datasets/02_BigEarthNet_txt/BigEarthNet.txt/BigEarthNet.txt.parquet")
    parser.add_argument("--images_dir", type=str, default="datasets/processed/bigearthnet_resnet50_full")
    parser.add_argument("--adapter_path", type=str, default="backend/models/remote_sensing_vlm/checkpoints/best_adapter")
    parser.add_argument("--base_model", type=str, default="Salesforce/blip-image-captioning-base")
    parser.add_argument("--sample_limit", type=int, default=50, help="Evaluate on subset of benchmark samples")
    parser.add_argument("--output_json", type=str, default="backend/models/remote_sensing_vlm/eval_results.json")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    return text.strip().lower().rstrip(".").strip()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logger.info("=" * 60)
    logger.info("ASTRA RS-VLM BENCHMARK EVALUATION")
    logger.info("=" * 60)
    logger.info(f"Target Split : bench")
    logger.info(f"Sample Limit : {args.sample_limit}")
    logger.info(f"Base Model   : {args.base_model}")
    logger.info(f"Adapter Path : {args.adapter_path}")
    logger.info(f"Device       : {device}")

    # 1. Load Dataset
    t0 = time.time()
    dataset = BigEarthNetTxtDataset(
        parquet_path=args.parquet_path,
        images_dir=args.images_dir,
        split="bench",
        max_samples=args.sample_limit,
    )
    logger.info(f"Loaded {len(dataset)} benchmark evaluation samples in {time.time() - t0:.2f}s")

    # 2. Load Model & Adapter
    logger.info("Loading processor and base VLM...")
    processor = BlipProcessor.from_pretrained(args.base_model)
    dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
    base_model = BlipForConditionalGeneration.from_pretrained(
        args.base_model,
        torch_dtype=dtype if device.type == "cuda" else torch.float32,
    ).to(device)

    adapter_path = Path(args.adapter_path)
    if adapter_path.exists() and (adapter_path / "adapter_model.safetensors").exists() or (adapter_path / "adapter_model.bin").exists():
        logger.info(f"Loading LoRA adapter weights from {adapter_path}...")
        model = PeftModel.from_pretrained(base_model, str(adapter_path)).to(device)
        logger.success("LoRA adapter merged for evaluation.")
    else:
        logger.warning(f"No adapter found at {adapter_path}; evaluating base model zero-shot.")
        model = base_model

    model.eval()

    # 3. Evaluation Loop
    exact_matches = 0
    substring_matches = 0
    task_stats = {}
    sample_records = []

    logger.info("Running inference across benchmark samples...")
    for idx in tqdm(range(len(dataset)), desc="Evaluating Benchmark", dynamic_ncols=True, unit="sample"):
        sample = dataset[idx]
        q = sample["question"]
        expected = sample["answer"]
        task_type = sample["task_type"]
        image = sample["image"]

        prompt = f"Question: {q} Answer:"
        inputs = processor(images=image, text=prompt, return_tensors="pt").to(device)

        with torch.inference_mode():
            out_ids = model.generate(
                **inputs,
                max_new_tokens=32,
                do_sample=False,
            )
        generated = processor.decode(out_ids[0], skip_special_tokens=True).strip()

        # Clean and extract answer from generated text
        gen_lower = generated.lower().strip()
        if "answer :" in gen_lower:
            answer_text = gen_lower.split("answer :")[-1].strip()
        elif "answer:" in gen_lower:
            answer_text = gen_lower.split("answer:")[-1].strip()
        elif gen_lower.startswith(prompt.lower()):
            answer_text = gen_lower[len(prompt):].strip()
        else:
            answer_text = gen_lower

        norm_gen = normalize_text(answer_text)
        norm_exp = normalize_text(expected)

        is_exact = norm_gen == norm_exp
        is_sub = (norm_exp in norm_gen) or (norm_gen in norm_exp)

        if is_exact:
            exact_matches += 1
        if is_sub:
            substring_matches += 1

        if task_type not in task_stats:
            task_stats[task_type] = {"total": 0, "exact": 0, "substring": 0}
        task_stats[task_type]["total"] += 1
        if is_exact:
            task_stats[task_type]["exact"] += 1
        if is_sub:
            task_stats[task_type]["substring"] += 1

        if idx < 10 or not is_exact:
            sample_records.append({
                "patch_id": sample["patch_id"],
                "task_type": task_type,
                "question": q,
                "expected": expected,
                "predicted": generated,
                "exact_match": is_exact,
            })

    total_evaluated = len(dataset)
    em_rate = 100.0 * exact_matches / max(1, total_evaluated)
    sub_rate = 100.0 * substring_matches / max(1, total_evaluated)

    logger.info("=" * 60)
    logger.info("BENCHMARK EVALUATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total Samples Evaluated : {total_evaluated}")
    logger.success(f"Exact Match Accuracy    : {exact_matches}/{total_evaluated} ({em_rate:.2f}%)")
    logger.info(f"Substring Match Accuracy: {substring_matches}/{total_evaluated} ({sub_rate:.2f}%)")
    logger.info("-" * 60)
    logger.info("Per-Task Performance:")
    for t_name, stats in task_stats.items():
        t_tot = stats["total"]
        t_em = 100.0 * stats["exact"] / max(1, t_tot)
        t_sub = 100.0 * stats["substring"] / max(1, t_tot)
        logger.info(f"  - {t_name:<15}: EM = {t_em:5.1f}% | Sub = {t_sub:5.1f}% (N={t_tot})")
    logger.info("=" * 60)

    # Save detailed JSON report
    eval_summary = {
        "samples_evaluated": total_evaluated,
        "exact_match_accuracy": round(em_rate, 2),
        "substring_match_accuracy": round(sub_rate, 2),
        "per_task": task_stats,
        "sample_predictions": sample_records[:20],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)

    logger.success(f"Saved evaluation report to {out_path}")


if __name__ == "__main__":
    main()
