import pynvml
import torch
from loguru import logger

def check_gpu_available() -> bool:
    """Check if GPU is available. Halt if not."""
    if not torch.cuda.is_available():
        logger.error("GPU_UNAVAILABLE: Training requires a CUDA-compatible GPU.")
        return False
    return True

def get_gpu_info() -> dict:
    """Return dict of current GPU info."""
    info = {
        "available": False,
        "name": "None",
        "vram_total_gb": 0.0,
        "vram_used_gb": 0.0,
        "utilization_pct": 0
    }
    if torch.cuda.is_available():
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            info["available"] = True
            info["name"] = pynvml.nvmlDeviceGetName(handle)
            if isinstance(info["name"], bytes):
                info["name"] = info["name"].decode()
            info["vram_total_gb"] = meminfo.total / (1024**3)
            info["vram_used_gb"] = meminfo.used / (1024**3)
            info["utilization_pct"] = util.gpu
        except Exception as e:
            logger.warning(f"Could not get NVML GPU info: {e}")
            # Fallback to PyTorch
            info["available"] = True
            info["name"] = torch.cuda.get_device_name(0)
            info["vram_total_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            info["vram_used_gb"] = torch.cuda.memory_allocated(0) / (1024**3)
    return info

class GPUMonitor:
    @staticmethod
    def log_vram():
        info = get_gpu_info()
        if info["available"]:
            logger.info(f"GPU VRAM: {info['vram_used_gb']:.1f} / {info['vram_total_gb']:.1f} GB")
