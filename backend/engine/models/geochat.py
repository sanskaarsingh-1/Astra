"""
Engine Layer — GeoChat Model Wrapper
Handles VQA, captioning, and visual grounding using GeoChat-7B.

IMPORTANT: GeoChat is trained on OPTICAL imagery only.
The executor must NEVER route SAR images to this model.
"""

from pathlib import Path
from typing import Any, Tuple
from loguru import logger
from PIL import Image

from config import settings
from engine.models.loader import model_loader
from engine.preprocessing import raster_to_8bit_rgb
from orchestrator.schemas import ModelStatus

MODEL_ID = "MBZUAI/geochat-7B"
_LOADER_KEY = "geochat"

CAPTION_PROMPT = (
    "You are a remote sensing expert. Describe this satellite/aerial image in detail. "
    "Include the scene type, visible land cover, infrastructure, vegetation, water bodies, "
    "and any notable features. Be factual and specific."
)

GROUNDING_PROMPT_TEMPLATE = (
    "Identify and locate all instances of '{text_ref}' in this remote sensing image. "
    "Return the bounding box coordinates for each detected object."
)


def _load_geochat():
    """Load GeoChat model and processor."""
    try:
        from geochat.model.builder import load_pretrained_model
        from geochat.utils import disable_torch_init
        disable_torch_init()

        logger.info(f"Loading GeoChat from {MODEL_ID}...")
        tokenizer, model, image_processor, context_len = load_pretrained_model(
            model_path=MODEL_ID,
            model_base=None,
            model_name="geochat-7B"
        )
        model.eval()
        return model, tokenizer, image_processor
    except ImportError as e:
        logger.error(f"Failed to import GeoChat dependencies: {e}. Run pip install -r requirements-models.txt")
        return None, None, None
    except Exception as e:
        logger.error(f"Failed to load GeoChat model weights: {e}")
        return None, None, None


def get_model_status() -> ModelStatus:
    try:
        import geochat
        # Could check if weights exist locally, but for now we'll assumeAVAILABLE if import works
        return ModelStatus.AVAILABLE
    except ImportError:
        return ModelStatus.NOT_CONFIGURED


def _generate_response(model, tokenizer, image_processor, image_path: Path, prompt: str) -> tuple[str, float | None]:
    """Run real GeoChat inference."""
    if model is None:
        return "Model not configured or unavailable.", 0.0

    try:
        import torch
        from geochat.mm_utils import tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria
        from geochat.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
        from geochat.conversation import conv_templates, SeparatorStyle
    except ImportError:
        return "GeoChat library missing.", 0.0

    try:
        # Preprocess satellite image to RGB JPG
        rgb_path = raster_to_8bit_rgb(str(image_path))
        image = Image.open(rgb_path).convert('RGB')
        
        # Prepare inputs
        image_tensor = image_processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
        
        # Format prompt
        if getattr(model.config, 'mm_use_im_start_end', False):
            qs = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + prompt
        else:
            qs = DEFAULT_IMAGE_TOKEN + '\n' + prompt
            
        conv = conv_templates["llava_v1"].copy()
        conv.append_message(conv.roles[0], qs)
        conv.append_message(conv.roles[1], None)
        prompt_formatted = conv.get_prompt()
        
        input_ids = tokenizer_image_token(prompt_formatted, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).cuda()
        image_tensor = image_tensor.unsqueeze(0).half().cuda()
        
        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)
        
        with torch.inference_mode():
            output_ids = model.generate(
                input_ids,
                images=image_tensor,
                do_sample=True,
                temperature=0.2,
                max_new_tokens=512,
                use_cache=True,
                stopping_criteria=[stopping_criteria],
            )
            
        input_token_len = input_ids.shape[1]
        n_diff_input_output = (input_ids != output_ids[:, :input_token_len]).sum().item()
        if n_diff_input_output > 0:
            logger.warning(f'[WARNING] {n_diff_input_output} output_ids are not the same as the input_ids')
            
        outputs = tokenizer.batch_decode(output_ids[:, input_token_len:], skip_special_tokens=True)[0]
        outputs = outputs.strip()
        if outputs.endswith(stop_str):
            outputs = outputs[:-len(stop_str)]
            
        answer = outputs.strip()
        confidence = 0.85  # Real model gives better results, heuristic for now
        
        return answer, confidence
    except Exception as e:
        logger.error(f"GeoChat inference failed: {e}")
        return f"Inference failed: {str(e)}", 0.0


def run_vqa(image_path: Path, question: str) -> dict[str, Any]:
    model, tokenizer, image_processor = model_loader.load(_LOADER_KEY, _load_geochat)
    logger.info(f"GeoChat VQA: {question!r} on {image_path.name}")
    answer, confidence = _generate_response(model, tokenizer, image_processor, image_path, question)
    return {
        "type": "text",
        "text": answer,
        "question": question,
        "confidence": confidence,
        "model": "geochat-7b",
    }


def run_caption(image_path: Path) -> dict[str, Any]:
    model, tokenizer, image_processor = model_loader.load(_LOADER_KEY, _load_geochat)
    logger.info(f"GeoChat captioning: {image_path.name}")
    caption, confidence = _generate_response(model, tokenizer, image_processor, image_path, CAPTION_PROMPT)
    return {
        "type": "text",
        "text": caption,
        "confidence": confidence,
        "model": "geochat-7b",
    }


def run_grounding(image_path: Path, text_reference: str) -> dict[str, Any]:
    model, tokenizer, image_processor = model_loader.load(_LOADER_KEY, _load_geochat)
    prompt = GROUNDING_PROMPT_TEMPLATE.format(text_ref=text_reference)
    logger.info(f"GeoChat grounding: {text_reference!r} in {image_path.name}")
    answer, confidence = _generate_response(model, tokenizer, image_processor, image_path, prompt)

    import re
    bboxes = []
    pattern = r"[\[\(]\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*[\]\)]"
    matches = re.findall(pattern, answer)
    for match in matches:
        try:
            bbox = [float(v) for v in match]
            bboxes.append(bbox)
        except ValueError:
            continue

    return {
        "type": "bbox",
        "text_reference": text_reference,
        "raw_text": answer,
        "bboxes": bboxes,
        "confidence": confidence,
        "model": "geochat-7b",
    }
