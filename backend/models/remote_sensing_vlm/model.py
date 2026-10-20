"""
Astra AI — Remote Sensing VLM Architecture & Adaptation Module
Provides model loading, LoRA configuration, and inference wrapper for
remote-sensing visual-language processing.

ADAPTER STATUS (as of September 20, 2026):
  - Base Model: Salesforce/blip-image-captioning-base
  - Adapter: checkpoints/best_adapter/ (2.37 MB safetensors, LoRA r=16)
  - Training: 1 epoch, 1,000 steps on BigEarthNet.txt
  - Benchmark: 44.0% EM on 50-sample bench split (binary: 70.8%, MCQ: 25%)
  - Status: PARTIAL_ADAPTATION — real trained adapter, not zero-shot.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import torch
import torch.nn as nn
from PIL import Image
from loguru import logger

@dataclass
class RSVLMConfig:
    base_model_id: str = "Salesforce/blip-image-captioning-base"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: Optional[tuple] = None
    torch_dtype: str = "bfloat16" if torch.cuda.is_bf16_supported() else "float16"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    max_length: int = 256


class RSVLMModel(nn.Module):
    """
    Remote-Sensing Vision-Language Model with PEFT / LoRA adapter.
    Accepts optical / remote sensing image + natural language question
    and generates evidence-grounded answers.
    """
    def __init__(self, config: RSVLMConfig):
        super().__init__()
        self.config = config
        self.device = torch.device(config.device)
        self.model = None
        self.processor = None
        self.tokenizer = None
        self._is_lora_applied = False

    def load_base_model(self, use_lora: bool = True):
        """Loads processor and base VLM weights with PEFT/LoRA adapter."""
        from transformers import AutoProcessor, AutoModelForVision2Seq
        
        logger.info(f"Loading processor for {self.config.base_model_id}...")
        self.processor = AutoProcessor.from_pretrained(self.config.base_model_id)

        dtype = getattr(torch, self.config.torch_dtype, torch.float16) if self.config.device != "cpu" else torch.float32
        logger.info(f"Loading base VLM {self.config.base_model_id} (dtype={dtype}) on {self.device}...")
        
        self.model = AutoModelForVision2Seq.from_pretrained(
            self.config.base_model_id,
            torch_dtype=dtype,
        ).to(self.device)

        if use_lora and not self._is_lora_applied:
            self._apply_lora()

        self.model.eval()
        logger.success(f"RS-VLM ready on {self.device} (LoRA={use_lora}).")
        return self

    def _apply_lora(self):
        """Applies Parameter-Efficient Fine-Tuning (LoRA) to linear projections."""
        try:
            from peft import LoraConfig, get_peft_model
            
            # Select target modules according to architecture
            if self.config.target_modules is not None:
                targets = list(self.config.target_modules)
            elif "blip" in self.config.base_model_id.lower():
                targets = ["query", "value"]
            else:
                targets = ["q_proj", "v_proj"]

            lora_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                target_modules=targets,
                lora_dropout=self.config.lora_dropout,
                bias="none",
            )
            self.model = get_peft_model(self.model, lora_config)
            self._is_lora_applied = True
            trainable, total = self.get_trainable_parameters()
            logger.info(f"Applied LoRA: {trainable:,} trainable params / {total:,} total ({100 * trainable / total:.2f}%)")
        except ImportError:
            logger.warning("peft library not available; running base model in full precision.")

    def get_trainable_parameters(self) -> tuple[int, int]:
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        return trainable, total

    def forward(self, *args, **kwargs):
        """Standard VLM forward pass for training and loss calculation."""
        return self.model(*args, **kwargs)

    def save_adapter(self, output_dir: Path | str):
        """Saves LoRA adapter weights and processor configuration."""
        save_path = Path(output_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        if self._is_lora_applied and hasattr(self.model, "save_pretrained"):
            self.model.save_pretrained(str(save_path))
        if self.processor is not None:
            self.processor.save_pretrained(str(save_path))
        logger.success(f"Saved RS-VLM adapter checkpoint to {save_path}")

    @classmethod
    def load_adapter_for_inference(
        cls,
        adapter_dir: Path | str,
        base_model_id: str = "Salesforce/blip-image-captioning-base",
        device: Optional[str] = None,
    ) -> "RSVLMModel":
        """
        Load base VLM + LoRA adapter from checkpoint directory for inference.
        This is the production inference loader — does NOT start any training.

        Args:
            adapter_dir: Path to the adapter directory (must contain adapter_config.json
                         and adapter_model.safetensors or adapter_model.bin).
            base_model_id: HuggingFace model ID for the base model.
            device: Optional device override.

        Returns:
            RSVLMModel instance with adapter loaded in eval mode.
        """
        from transformers import AutoProcessor, AutoModelForVision2Seq
        from peft import PeftModel

        adapter_path = Path(adapter_dir)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter directory not found: {adapter_path}")

        has_adapter = (
            (adapter_path / "adapter_model.safetensors").exists()
            or (adapter_path / "adapter_model.bin").exists()
        )
        if not has_adapter:
            raise FileNotFoundError(
                f"No adapter weights found in {adapter_path}. "
                "Expected adapter_model.safetensors or adapter_model.bin."
            )

        _device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        device_obj = torch.device(_device)
        dtype = (
            torch.bfloat16
            if (device_obj.type == "cuda" and torch.cuda.is_bf16_supported())
            else (torch.float16 if device_obj.type == "cuda" else torch.float32)
        )

        logger.info(f"[RS-VLM] Loading processor: {base_model_id}")
        processor = AutoProcessor.from_pretrained(base_model_id)

        logger.info(f"[RS-VLM] Loading base model: {base_model_id} (dtype={dtype}, device={device_obj})")
        base_model = AutoModelForVision2Seq.from_pretrained(
            base_model_id,
            torch_dtype=dtype,
        ).to(device_obj)

        logger.info(f"[RS-VLM] Applying LoRA adapter from: {adapter_path}")
        peft_model = PeftModel.from_pretrained(base_model, str(adapter_path)).to(device_obj)
        peft_model.eval()

        # Wrap in RSVLMModel container
        config = RSVLMConfig(
            base_model_id=base_model_id,
            device=_device,
        )
        instance = cls(config)
        instance.model = peft_model
        instance.processor = processor
        instance._is_lora_applied = True
        logger.success(
            f"[RS-VLM] Adapter loaded. Base: {base_model_id} | "
            f"Adapter: {adapter_path.name} | Device: {device_obj}"
        )
        return instance

    def generate(self, image: Image.Image, prompt: str, max_new_tokens: int = 64) -> str:
        """Inference forward pass for visual question answering / captioning."""
        if self.model is None or self.processor is None:
            raise RuntimeError("Model is not loaded. Call load_base_model() or load_adapter_for_inference() first.")

        inputs = self.processor(text=prompt, images=image, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                repetition_penalty=1.3,
                no_repeat_ngram_size=3,
                do_sample=False,
            )
        output_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        lower = output_text.lower().strip()
        if "answer :" in lower:
            output_text = output_text.split("answer :")[-1].strip()
        elif "answer:" in lower:
            output_text = output_text.split("answer:")[-1].strip()
        elif output_text.startswith(prompt):
            output_text = output_text[len(prompt):].strip()
        return output_text.strip()


# ─── Singleton VLM Inference Instance ────────────────────────────────────────
# Lazily initialized on first call; never loaded at import time.
_vlm_inference_instance: Optional[RSVLMModel] = None
_VLM_ADAPTER_DIR = Path(__file__).parent / "checkpoints" / "best_adapter"
_VLM_BASE_MODEL = "Salesforce/blip-image-captioning-base"


def get_vlm_inference() -> Optional[RSVLMModel]:
    """
    Returns the singleton RS-VLM inference instance with LoRA adapter loaded.
    Returns None if the adapter checkpoint does not exist (safe degradation).
    Never starts training. Never blocks long.
    """
    global _vlm_inference_instance
    if _vlm_inference_instance is not None:
        return _vlm_inference_instance

    adapter_path = _VLM_ADAPTER_DIR
    has_weights = (
        (adapter_path / "adapter_model.safetensors").exists()
        or (adapter_path / "adapter_model.bin").exists()
    )

    if not has_weights:
        logger.warning(
            f"[RS-VLM] No adapter checkpoint found at {adapter_path}. "
            "VLM inference will be unavailable. Run manual training to generate adapter."
        )
        return None

    try:
        _vlm_inference_instance = RSVLMModel.load_adapter_for_inference(
            adapter_dir=adapter_path,
            base_model_id=_VLM_BASE_MODEL,
        )
        return _vlm_inference_instance
    except Exception as e:
        logger.error(f"[RS-VLM] Failed to load adapter for inference: {e}")
        return None
