import os
import random
import numpy as np
import torch
import json
from datetime import datetime

def set_seed(seed: int = 42):
    """Set all seeds to make results reproducible."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)

def generate_training_summary(run_dir: str, config: dict, final_metrics: dict, baseline_metrics: dict = None):
    """Generate reproducible training summary json."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "config": config,
        "metrics": final_metrics,
        "baseline_metrics": baseline_metrics,
        "software_versions": {
            "torch": torch.__version__,
            "numpy": np.__version__
        }
    }
    with open(os.path.join(run_dir, "training_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary
