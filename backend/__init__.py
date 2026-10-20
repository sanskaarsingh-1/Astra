"""
Astra AI Backend Package
Ensures repository root is always in sys.path so 'backend.*' imports resolve cleanly
across all execution contexts (CLI, tests, Uvicorn, background workers).
"""

import sys
from pathlib import Path

# Add repository root (parent of backend/) to sys.path if not present
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Also ensure backend directory itself is in sys.path for direct module resolution
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
