import numpy as np
from sklearn.metrics import confusion_matrix

def compute_cd_metrics(predictions: np.ndarray, ground_truths: np.ndarray):
    """
    Compute binary change detection metrics: IoU, F1, Precision, Recall, OA.
    Assumes 0 = no change, 1 = change.
    """
    y_pred = predictions.flatten()
    y_true = ground_truths.flatten()
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    oa = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    
    return {
        "iou": iou,
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "overall_accuracy": oa
    }
