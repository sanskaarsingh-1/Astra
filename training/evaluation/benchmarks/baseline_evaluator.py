import json
import os
from loguru import logger

class BaselineEvaluator:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.baseline_file = os.path.join(run_dir, "baseline_metrics.json")
        self.comparison_file = os.path.join(run_dir, "baseline_vs_finetuned.json")

    def save_baseline(self, metrics: dict):
        """Save baseline evaluation results."""
        with open(self.baseline_file, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Baseline metrics saved to {self.baseline_file}")

    def compare(self, finetuned_metrics: dict) -> dict:
        """Compare fine-tuned metrics against baseline."""
        if not os.path.exists(self.baseline_file):
            logger.warning("No baseline found to compare against.")
            return {}

        with open(self.baseline_file, "r") as f:
            baseline_metrics = json.load(f)

        comparison = {}
        adopted = False
        
        # Simple comparison logic (e.g., if F1 or Accuracy improved)
        for key in baseline_metrics:
            if key in finetuned_metrics:
                diff = finetuned_metrics[key] - baseline_metrics[key]
                comparison[key] = {
                    "baseline": baseline_metrics[key],
                    "finetuned": finetuned_metrics[key],
                    "improvement": diff
                }
                if diff > 0:
                    adopted = True

        comparison["FINE_TUNING_ADOPTED"] = adopted

        with open(self.comparison_file, "w") as f:
            json.dump(comparison, f, indent=2)
            
        logger.info(f"Comparison report saved to {self.comparison_file}")
        if adopted:
            logger.success("Fine-tuning shows improvement over baseline. Ready for export.")
        else:
            logger.warning("FINE_TUNING_NOT_ADOPTED: Model did not improve over baseline.")

        return comparison
