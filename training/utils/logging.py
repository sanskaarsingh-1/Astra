import sys
import os
from datetime import datetime
from loguru import logger

def setup_logging(run_dir: str):
    """Setup structured JSON logging to file, and standard formatting to stdout."""
    os.makedirs(run_dir, exist_ok=True)
    log_file = os.path.join(run_dir, f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # Add JSON file handler
    logger.add(log_file, serialize=True, level="INFO")
    
    logger.info("Logging initialized.")
    return log_file
