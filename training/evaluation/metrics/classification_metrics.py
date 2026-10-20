import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

def compute_classification_metrics(predictions: np.ndarray, ground_truths: np.ndarray, is_multilabel: bool = True):
    """Compute classification metrics."""
    if is_multilabel:
        avg = 'samples'
    else:
        avg = 'macro'
        
    return {
        "accuracy": accuracy_score(ground_truths, predictions),
        "f1": f1_score(ground_truths, predictions, average=avg, zero_division=0),
        "precision": precision_score(ground_truths, predictions, average=avg, zero_division=0),
        "recall": recall_score(ground_truths, predictions, average=avg, zero_division=0)
    }
