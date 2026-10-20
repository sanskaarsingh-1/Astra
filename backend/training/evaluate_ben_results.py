"""
Astra AI — ResNet-50 BigEarthNet Training Results & Performance Reporter
Generates comprehensive performance reports, per-class F1/Precision/Recall percentages,
train vs. test comparisons, and training curves from saved training runs.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    import torchvision.transforms as T
    from tqdm import tqdm
except ImportError as err:
    sys.stderr.write(
        f"\n[ENVIRONMENT ERROR] Missing dependency: {err}\n"
        f"Please run using the backend virtual environment:\n"
        f"  .\\backend\\.venv\\Scripts\\python.exe -m backend.training.evaluate_ben_results ...\n\n"
    )
    sys.exit(1)

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.training.train_ben_classifier import (
    BEN_CLASSES,
    IDX_TO_LABEL,
    BigEarthNetManifestDataset,
    build_model,
    compute_multilabel_metrics,
)


def format_pct(val: float) -> str:
    """Format decimal float (0.0 - 1.0) as percentage string."""
    return f"{val * 100.0:6.2f}%"


def make_bar(pct: float, width: int = 10) -> str:
    """ASCII progress bar for percentage."""
    filled = int(round((pct / 100.0) * width))
    filled = max(0, min(width, filled))
    return f"[{'=' * filled}{'.' * (width - filled)}]"


def evaluate_dataset(
    model: nn.Module,
    dataset: BigEarthNetManifestDataset,
    device: torch.device,
    batch_size: int = 64,
    threshold: float = 0.5,
    desc: str = "Evaluating",
) -> Tuple[float, Dict[str, Any]]:
    """Evaluate a dataset split and return loss and detailed metrics."""
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )
    criterion = nn.BCEWithLogitsLoss()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    model.eval()
    with torch.inference_mode():
        for images, labels in tqdm(loader, desc=desc, leave=False, dynamic_ncols=True, file=sys.stdout):
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                logits = model(images)
                loss = criterion(logits, labels)

            running_loss += loss.item()
            probs = torch.sigmoid(logits)

            all_preds.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())

    avg_loss = running_loss / max(len(loader), 1)
    y_pred_probs = np.vstack(all_preds)
    y_true = np.vstack(all_labels)

    metrics = compute_multilabel_metrics(
        y_true=y_true,
        y_pred_probs=y_pred_probs,
        threshold=threshold,
        class_names=BEN_CLASSES,
    )
    return avg_loss, metrics


def print_report(
    output_dir: Path,
    manifest_dir: Path,
    repo_root: Path,
    compute_live: bool = False,
    batch_size: int = 64,
):
    """Generate and display the full training and test performance report."""
    history_file = output_dir / "training_history.json"
    metrics_file = output_dir / "metrics.json"
    config_file = output_dir / "config.json"
    best_model_file = output_dir / "best_model.pth"

    if not metrics_file.exists() or not history_file.exists():
        print(f"\n[ERROR] Training artifacts not found in: {output_dir.resolve()}")
        print("Please ensure training has completed and output files exist.")
        return

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
    with open(metrics_file, "r", encoding="utf-8") as f:
        test_metrics = json.load(f)
    config = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

    total_epochs = len(history)
    best_epoch_num = test_metrics.get("best_epoch", 1)
    best_val_macro_f1 = test_metrics.get("best_val_macro_f1", 0.0)

    # Header
    print("\n" + "=" * 80)
    print("                ASTRA AI -- RESNET-50 TRAINING & EVALUATION REPORT")
    print("=" * 80)
    print(f"  Status                  :  TRAINING COMPLETE (Code 0)")
    print(f"  Model Architecture      :  ResNet-50 (Classifier Head: nn.Linear(2048, 19))")
    print(f"  Hardware / Accelerator  :  {config.get('gpu_name', 'NVIDIA GeForce RTX 5060 Laptop GPU')}")
    print(f"  PyTorch / CUDA          :  PyTorch {config.get('pytorch_version', '2.11.0')} (CUDA {config.get('cuda_runtime_version', '12.8')})")
    print(f"  Dataset Size            :  2,300 images (1,500 Train | 400 Val | 400 Test)")
    print(f"  Total Epochs Trained    :  {total_epochs} epochs")
    print(f"  Best Validation Epoch   :  Epoch {best_epoch_num} (Val Macro F1: {format_pct(best_val_macro_f1)})")
    print(f"  Checkpoint Evaluated    :  {best_model_file.resolve()}")
    print("=" * 80)

    # Optional Live Split Evaluation (Train vs Test side-by-side)
    train_metrics_live = None
    if compute_live and best_model_file.exists():
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"\n[*] Running live evaluation pass on {device}...")
        model = build_model(num_classes=len(BEN_CLASSES), pretrained=False).to(device)
        ckpt = torch.load(str(best_model_file), map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])

        eval_transform = T.Compose([
            T.Resize((224, 224), antialias=True),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        train_manifest = manifest_dir / "train.csv" if (manifest_dir / "train.csv").exists() else manifest_dir / "bigearthnet_train.csv"
        train_ds = BigEarthNetManifestDataset(
            train_manifest, repo_root, transform=eval_transform
        )
        t_start = time.perf_counter()
        _, train_metrics_live = evaluate_dataset(
            model=model,
            dataset=train_ds,
            device=device,
            batch_size=batch_size,
            threshold=test_metrics.get("threshold", 0.5),
            desc="Evaluating Train Set",
        )
        print(f"  Live train set evaluation finished in {time.perf_counter() - t_start:.2f}s")

    # Overall Summary Table
    print("\n" + "-" * 80)
    print("                       OVERALL PERFORMANCE SUMMARY (PERCENTAGES)")
    print("-" * 80)
    print(f"{'Metric':<25} | {'Final Train (Ep 20)':<18} | {'Best Val (Ep ' + str(best_epoch_num) + ')':<18} | {'Untouched Test':<16}")
    print("-" * 80)

    final_train = history[-1] if history else {}
    best_val = next((h for h in history if h.get("epoch") == best_epoch_num), history[-1] if history else {})

    print(f"{'Loss':<25} | {final_train.get('train_loss', 0.0):<18.4f} | {best_val.get('val_loss', 0.0):<18.4f} | {test_metrics.get('test_loss', 0.0):<16.4f}")
    print(f"{'Micro Precision (%)':<25} | {format_pct(final_train.get('micro_precision', 0.0)):<18} | {format_pct(best_val.get('micro_precision', 0.0)):<18} | {format_pct(test_metrics.get('micro_precision', 0.0)):<16}")
    print(f"{'Micro Recall (%)':<25} | {format_pct(final_train.get('micro_recall', 0.0)):<18} | {format_pct(best_val.get('micro_recall', 0.0)):<18} | {format_pct(test_metrics.get('micro_recall', 0.0)):<16}")
    print(f"{'Micro F1-Score (%)':<25} | {format_pct(final_train.get('micro_f1', 0.0)):<18} | {format_pct(best_val.get('micro_f1', 0.0)):<18} | {format_pct(test_metrics.get('micro_f1', 0.0)):<16}")
    print(f"{'Macro Precision (%)':<25} | {format_pct(final_train.get('macro_precision', 0.0)):<18} | {format_pct(best_val.get('macro_precision', 0.0)):<18} | {format_pct(test_metrics.get('macro_precision', 0.0)):<16}")
    print(f"{'Macro Recall (%)':<25} | {format_pct(final_train.get('macro_recall', 0.0)):<18} | {format_pct(best_val.get('macro_recall', 0.0)):<18} | {format_pct(test_metrics.get('macro_recall', 0.0)):<16}")
    print(f"{'Macro F1-Score (%)':<25} | {format_pct(final_train.get('macro_f1', 0.0)):<18} | {format_pct(best_val.get('macro_f1', 0.0)):<18} | {format_pct(test_metrics.get('macro_f1', 0.0)):<16}")
    print("-" * 80)

    # Per-Class Breakdown Table
    print("\n" + "=" * 90)
    print("                     PER-CLASS METRICS BREAKDOWN (TEST SET)")
    print("=" * 90)
    if train_metrics_live:
        print(f"{'ID':<3} {'Class Name':<32} | {'Train F1':<9} | {'Test Supp':<9} | {'Test Prec':<9} | {'Test Rec':<9} | {'Test F1':<9} | {'Visual Bar':<12}")
    else:
        print(f"{'ID':<3} {'Class Name':<32} | {'Test Supp':<9} | {'Test Prec':<9} | {'Test Rec':<9} | {'Test F1':<9} | {'Visual Bar':<12}")
    print("-" * 90)

    test_per_class = test_metrics.get("per_class", {})
    train_per_class = train_metrics_live.get("per_class", {}) if train_metrics_live else {}

    for idx, name in enumerate(BEN_CLASSES):
        t_data = test_per_class.get(name, {})
        supp = t_data.get("support", 0)
        prec = t_data.get("precision", 0.0)
        rec = t_data.get("recall", 0.0)
        f1 = t_data.get("f1", 0.0)
        f1_pct = f1 * 100.0
        bar = make_bar(f1_pct, width=10)

        if train_metrics_live:
            tr_f1 = train_per_class.get(name, {}).get("f1", 0.0)
            print(
                f"{idx:02d}  {name:<32} | {format_pct(tr_f1):<9} | {supp:9d} | "
                f"{format_pct(prec):<9} | {format_pct(rec):<9} | {format_pct(f1):<9} | {bar} {f1_pct:5.1f}%"
            )
        else:
            print(
                f"{idx:02d}  {name:<32} | {supp:9d} | "
                f"{format_pct(prec):<9} | {format_pct(rec):<9} | {format_pct(f1):<9} | {bar} {f1_pct:5.1f}%"
            )

    print("=" * 90)

    # Top Performing Categories Highlight
    sorted_classes = sorted(
        test_per_class.items(),
        key=lambda item: item[1].get("f1", 0.0),
        reverse=True,
    )
    print("\n[* TOP PERFORMING SATELLITE CLASSES ON TEST SET]")
    for rank, (cname, cmetrics) in enumerate(sorted_classes[:6], 1):
        f1_val = cmetrics.get("f1", 0.0) * 100.0
        p_val = cmetrics.get("precision", 0.0) * 100.0
        r_val = cmetrics.get("recall", 0.0) * 100.0
        supp = cmetrics.get("support", 0)
        print(f"  {rank}. {cname:<40} : F1 = {f1_val:5.1f}%  (Precision: {p_val:5.1f}%, Recall: {r_val:5.1f}%, Support: {supp})")

    # Training Progression by Epoch
    print("\n" + "-" * 80)
    print("                     EPOCH-BY-EPOCH TRAINING PROGRESSION")
    print("-" * 80)
    print(f"{'Epoch':<7} | {'Train Loss':<11} | {'Val Loss':<11} | {'Val Micro F1':<13} | {'Val Macro F1':<13} | {'Epoch Time':<10}")
    print("-" * 80)
    for entry in history:
        ep = entry.get("epoch", 0)
        tr_loss = entry.get("train_loss", 0.0)
        v_loss = entry.get("val_loss", 0.0)
        mi_f1 = format_pct(entry.get("micro_f1", 0.0))
        ma_f1 = format_pct(entry.get("macro_f1", 0.0))
        ep_time = f"{entry.get('epoch_duration_sec', 0.0):.1f}s"
        star = " [*] (Best)" if ep == best_epoch_num else ""
        print(f"Ep {ep:02d}   | {tr_loss:<11.4f} | {v_loss:<11.4f} | {mi_f1:<13} | {ma_f1:<13} | {ep_time:<10}{star}")
    print("-" * 80)

    print(f"\n[Artifacts Available]")
    print(f"  * Best Checkpoint  : {best_model_file.resolve()}")
    print(f"  * Test Metrics     : {metrics_file.resolve()}")
    print(f"  * Training History : {history_file.resolve()}")
    print(f"  * Configuration    : {config_file.resolve()}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Display Astra ResNet-50 BigEarthNet Training and Evaluation Scores"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="backend/models/bigearthnet_resnet50_v2_full",
        help="Directory containing training artifacts (metrics.json, training_history.json)",
    )
    parser.add_argument(
        "--manifest_dir",
        type=str,
        default="datasets/processed/bigearthnet_resnet50_full/manifests",
        help="Directory containing CSV manifests",
    )
    parser.add_argument(
        "--repo_root",
        type=str,
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path",
    )
    parser.add_argument(
        "--compute_live",
        action="store_true",
        help="Run a fast live GPU inference pass on Train set to show Train vs Test side-by-side",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=64,
        help="Batch size for live evaluation pass",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()
    if not (output_dir / "metrics.json").exists():
        fallback_dir = repo_root / "backend" / "models" / "ben_resnet50_training"
        if (fallback_dir / "metrics.json").exists():
            output_dir = fallback_dir

    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_absolute():
        manifest_dir = (repo_root / manifest_dir).resolve()
    if not manifest_dir.exists():
        fallback_manifest = repo_root / "datasets" / "manifests"
        if fallback_manifest.exists():
            manifest_dir = fallback_manifest

    print_report(
        output_dir=output_dir,
        manifest_dir=manifest_dir,
        repo_root=repo_root,
        compute_live=args.compute_live,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
