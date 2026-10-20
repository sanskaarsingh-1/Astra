import numpy as np

def compute_vqa_accuracy(predictions: list[str], ground_truths: list[str]) -> float:
    """Exact match accuracy for VQA."""
    if not predictions or not ground_truths:
        return 0.0
    correct = sum(1 for p, g in zip(predictions, ground_truths) if p.strip().lower() == g.strip().lower())
    return correct / len(predictions)
