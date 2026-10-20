"""
Manual Training & Pre-Flight Sanity Script for LEVIR-CD Bi-Temporal Change Detection.
Strict Rule 2 Compliance: Automated environments MUST ONLY execute with `--sanity_check_only`.
Human operator executes full training using the generated command or run script.
Features responsive, in-place tqdm progress bars with dynamic postfix metrics.
"""

import argparse
import os
from pathlib import Path
import sys
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm
from loguru import logger

from backend.models.change_detection.dataset import create_levir_dataloader
from backend.models.change_detection.model import BITChangeDetector


class CrossEntropyDiceLoss(nn.Module):
    """Hybrid Cross-Entropy + Dice Loss for binary change detection with class imbalance."""

    def __init__(self, ce_weight: float = 1.0, dice_weight: float = 1.0) -> None:
        super().__init__()
        self.ce_weight = ce_weight
        self.dice_weight = dice_weight
        self.ce = nn.CrossEntropyLoss()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Cross Entropy
        ce_loss = self.ce(logits, targets)

        # Dice Loss for change class (class 1)
        probs = F.softmax(logits, dim=1)[:, 1, :, :]
        targets_f = targets.float()
        intersection = (probs * targets_f).sum(dim=(1, 2))
        union = probs.sum(dim=(1, 2)) + targets_f.sum(dim=(1, 2))
        dice = 1.0 - (2.0 * intersection + 1e-6) / (union + 1e-6)
        dice_loss = dice.mean()

        return self.ce_weight * ce_loss + self.dice_weight * dice_loss


def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    total_epochs: int,
) -> float:
    model.train()
    total_loss = 0.0
    num_batches = len(loader)

    with tqdm(enumerate(loader), total=num_batches, desc=f"Epoch {epoch}/{total_epochs}", leave=True) as pbar:
        for step, batch in pbar:
            t1 = batch["A"].to(device)
            t2 = batch["B"].to(device)
            targets = batch["label"].to(device)

            optimizer.zero_grad()
            logits = model(t1, t2)
            loss = criterion(logits, targets)

            loss.backward()
            optimizer.step()

            loss_val = loss.item()
            total_loss += loss_val

            current_lr = optimizer.param_groups[0]["lr"]
            pbar.set_postfix({
                "loss": f"{loss_val:.4f}",
                "avg_loss": f"{total_loss / (step + 1):.4f}",
                "lr": f"{current_lr:.6f}",
            })

    return total_loss / max(num_batches, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="LEVIR-CD Bi-Temporal Change Detection Trainer")
    parser.add_argument("--data_dir", type=str, default="datasets/05_LEVIR_CD")
    parser.add_argument("--output_dir", type=str, default="backend/models/change_detection/checkpoints")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--img_size", type=int, default=256)
    parser.add_argument("--sanity_check_only", action="store_true", help="Run 1 pre-flight verification batch only")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using compute device: {device}")

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Sanity Check Mode (Rule 2 Compliance)
    if args.sanity_check_only:
        logger.info("=" * 60)
        logger.info("Executing Pre-Flight Sanity Check (--sanity_check_only)")
        logger.info("=" * 60)

        t0 = time.time()
        loader = create_levir_dataloader(
            root_dir=args.data_dir,
            split="Train",
            batch_size=2,
            shuffle=False,
            img_size=args.img_size,
            max_samples=2,
        )

        batch = next(iter(loader))
        t1, t2, lbl = batch["A"].to(device), batch["B"].to(device), batch["label"].to(device)

        model = BITChangeDetector(device=device)
        criterion = CrossEntropyDiceLoss()

        with torch.no_grad():
            logits = model(t1, t2)
            loss = criterion(logits, lbl)

        elapsed = time.time() - t0
        logger.success(
            f"Pre-flight verification passed in {elapsed:.3f}s! "
            f"T1 shape={t1.shape}, T2 shape={t2.shape}, Logits shape={logits.shape}, Loss={loss.item():.4f}"
        )
        logger.info("Rule 2 invariant preserved: zero weights modified during sanity check.")
        return 0

    # 2. Human-Authorized Full Training Pipeline
    logger.info("=" * 60)
    logger.info("Starting Full Model Training Pipeline (Human-Authorized Operator Mode)")
    logger.info(f"Target: {args.epochs} epochs, batch_size={args.batch_size}, lr={args.lr}")
    logger.info("=" * 60)

    train_loader = create_levir_dataloader(
        root_dir=args.data_dir,
        split="Train",
        batch_size=args.batch_size,
        shuffle=True,
        img_size=args.img_size,
    )
    val_loader = create_levir_dataloader(
        root_dir=args.data_dir,
        split="val",
        batch_size=args.batch_size,
        shuffle=False,
        img_size=args.img_size,
    )

    model = BITChangeDetector(device=device)
    criterion = CrossEntropyDiceLoss()
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)

    best_loss = float("inf")
    best_ckpt_path = output_path / "best_model.pth"

    for epoch in range(1, args.epochs + 1):
        epoch_loss = train_one_epoch(
            model=model,
            loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            epoch=epoch,
            total_epochs=args.epochs,
        )
        scheduler.step()

        logger.info(f"Epoch {epoch}/{args.epochs} completed — Train Loss: {epoch_loss:.4f}")

        # Save checkpoint if loss improves
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(
                {
                    "epoch": epoch,
                    "model_G_state_dict": model.net.state_dict(),
                    "best_loss": best_loss,
                    "optimizer_state_dict": optimizer.state_dict(),
                },
                str(best_ckpt_path),
            )
            logger.success(f"New best model saved to: {best_ckpt_path} (Loss: {best_loss:.4f})")

    logger.success("LEVIR-CD Change Detection training completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
