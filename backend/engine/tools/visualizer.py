"""
Engine Tools — Visualization
Creates visual evidence: mask overlays, comparison images.
All output is Base64-encoded PNG for JSON transport.
"""

import base64
import io
from pathlib import Path
from typing import Any
import numpy as np
from loguru import logger


def create_mask_overlay(
    image_path: Path,
    mask: list[list[int]] | None,
    color: tuple[int, int, int] = (255, 50, 50),
    alpha: float = 0.5,
) -> dict[str, Any]:
    """
    Create a visualization overlaying a binary mask on the source image.
    Changed regions are highlighted in red (by default).
    Returns a Base64-encoded PNG.
    """
    from PIL import Image, ImageDraw
    import rasterio

    if mask is None:
        return {
            "type": "visualization",
            "subtype": "mask_overlay",
            "error": "No mask provided.",
            "visual_evidence": None,
            "confidence": 0.0,
        }

    # Load source image as RGB
    try:
        with rasterio.open(image_path) as src:
            if src.count >= 3:
                data = src.read([1, 2, 3])
                data = np.transpose(data, (1, 2, 0))
                for c in range(3):
                    ch = data[:, :, c].astype(float)
                    p2, p98 = np.percentile(ch[ch > 0], [2, 98]) if (ch > 0).any() else (0, 1)
                    data[:, :, c] = np.clip((ch - p2) / max(p98 - p2, 1) * 255, 0, 255).astype(np.uint8)
                base_img = Image.fromarray(data, mode="RGB")
            else:
                ch = src.read(1).astype(float)
                ch = ((ch - ch.min()) / max(ch.max() - ch.min(), 1) * 255).astype(np.uint8)
                base_img = Image.fromarray(ch, mode="L").convert("RGB")
    except Exception:
        base_img = Image.open(image_path).convert("RGB")

    # Resize mask to match image
    mask_array = np.array(mask, dtype=np.uint8)
    mask_pil = Image.fromarray(mask_array * 255, mode="L").resize(
        base_img.size, Image.NEAREST
    )
    mask_resized = np.array(mask_pil) > 127

    # Create overlay
    base_array = np.array(base_img).copy()
    overlay = base_array.copy()
    for c, col_val in enumerate(color):
        overlay[:, :, c][mask_resized] = col_val

    blended = (base_array * (1 - alpha) + overlay * alpha).astype(np.uint8)
    result_img = Image.fromarray(blended, mode="RGB")

    # Encode to Base64 PNG
    buffer = io.BytesIO()
    result_img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "type": "visualization",
        "subtype": "mask_overlay",
        "visual_evidence": f"data:image/png;base64,{b64}",
        "confidence": 1.0,
        "description": f"Red overlay highlights detected change regions ({color} at {int(alpha*100)}% opacity).",
    }


def create_thumbnail(image_path: Path, max_size: int = 512) -> str:
    """Create a Base64-encoded thumbnail of an image."""
    from PIL import Image
    import rasterio

    try:
        with rasterio.open(image_path) as src:
            bands = min(src.count, 3)
            data = src.read(list(range(1, bands + 1)))
            data = np.transpose(data, (1, 2, 0))
            if data.dtype != np.uint8:
                for c in range(data.shape[2]):
                    ch = data[:, :, c].astype(float)
                    p2, p98 = np.percentile(ch[ch > 0], [2, 98]) if (ch > 0).any() else (0, 1)
                    data[:, :, c] = np.clip((ch - p2) / max(p98 - p2, 1) * 255, 0, 255).astype(np.uint8)
            if bands == 1:
                data = np.repeat(data, 3, axis=2)
            pil = Image.fromarray(data[:, :, :3], mode="RGB")
    except Exception:
        pil = Image.open(image_path).convert("RGB")

    pil.thumbnail((max_size, max_size), Image.LANCZOS)
    buffer = io.BytesIO()
    pil.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
