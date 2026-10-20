"""
Engine Layer — Lazy Model Loader
Loads models on-demand and unloads the current model when switching,
so only one large model occupies GPU VRAM at a time.
This is MANDATORY on consumer GPUs with < 16GB VRAM.
"""

import gc
from typing import Any
from loguru import logger


class LazyModelLoader:
    """
    Singleton that manages GPU model lifecycle.
    Only one model is loaded in VRAM at any time.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_model_id: str | None = None
            cls._instance._current_model: Any = None
            cls._instance._current_processor: Any = None
        return cls._instance

    def load(self, model_id: str, loader_fn) -> tuple[Any, Any]:
        """
        Load a model, unloading any currently loaded model first.
        loader_fn should return (model, processor).
        """
        if self._current_model_id == model_id and self._current_model is not None:
            logger.debug(f"Model {model_id} already loaded. Reusing.")
            return self._current_model, self._current_processor

        if self._current_model is not None:
            logger.info(f"Unloading model {self._current_model_id} to free VRAM...")
            self._unload_current()

        logger.info(f"Loading model {model_id}...")
        model, processor = loader_fn()
        self._current_model_id = model_id
        self._current_model = model
        self._current_processor = processor
        logger.success(f"Model {model_id} loaded.")
        return model, processor

    def _unload_current(self):
        import torch
        del self._current_model
        if self._current_processor:
            del self._current_processor
        self._current_model = None
        self._current_processor = None
        self._current_model_id = None
        gc.collect()
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass

    def unload_all(self):
        if self._current_model is not None:
            self._unload_current()


# Global singleton instance
model_loader = LazyModelLoader()
