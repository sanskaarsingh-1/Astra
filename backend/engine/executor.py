"""
Engine Layer — Plan Executor
Executes the investigation plan step by step.
Routes each step to the correct model wrapper or geospatial tool.
Emits SSE progress events.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import settings
from orchestrator.schemas import (
    InvestigationPlan, InputManifest, ExecutedStep, StepStatus
)
from orchestrator.registry import is_model, is_tool


def _get_image_path(manifest: InputManifest, image_index: int | None) -> Path | None:
    """Resolve image path from manifest by index."""
    if not manifest.images:
        return None
    idx = image_index if image_index is not None else 0
    idx = min(idx, len(manifest.images) - 1)
    img = manifest.images[idx]
    if isinstance(img, dict):
        p = img.get("file_path") or img.get("path")
    else:
        p = getattr(img, "file_path", None) or getattr(img, "path", None)
    return Path(p) if p else None


async def execute_plan(
    plan: InvestigationPlan,
    manifest: InputManifest,
    job_id: str,
    queue: asyncio.Queue,
) -> list[ExecutedStep]:
    """
    Execute all steps in the investigation plan.
    Returns list of ExecutedStep records.
    """
    executed: list[ExecutedStep] = []
    step_outputs: dict[str, Any] = {}  # step_id → raw output (for dependent steps)

    total = len(plan.steps)
    for i, step in enumerate(plan.steps):
        pct = 30 + int((i / total) * 45)  # Progress 30%→75% during execution

        await queue.put({
            "event": "progress",
            "data": json.dumps({
                "step": f"executing_{step.tool_id}",
                "pct": pct,
                "message": f"Step {i+1}/{total}: {step.description}",
                "step_id": step.step_id,
            }),
        })

        executed_step = await _execute_single_step(
            step=step,
            manifest=manifest,
            step_outputs=step_outputs,
            job_id=job_id,
        )
        executed.append(executed_step)

        if executed_step.status == StepStatus.SUCCESS:
            step_outputs[step.step_id] = executed_step.raw_output
            logger.info(f"[{job_id}] ✅ {step.step_id} ({step.tool_id}) → {executed_step.output_summary}")
        else:
            logger.warning(f"[{job_id}] ❌ {step.step_id} failed: {executed_step.error_message}")

    return executed


async def _execute_single_step(
    step,
    manifest: InputManifest,
    step_outputs: dict[str, Any],
    job_id: str = "",
) -> ExecutedStep:
    """Execute one plan step with timeout and retry."""
    log_prefix = f"[{job_id}][{step.step_id}]" if job_id else f"[{step.step_id}]"
    started_at = datetime.now(timezone.utc)
    executed = ExecutedStep(
        step_id=step.step_id,
        tool_id=step.tool_id,
        status=StepStatus.RUNNING,
        input_summary=f"tool={step.tool_id}, image_index={step.image_index}",
        output_summary="",
        started_at=started_at,
    )

    for attempt in range(settings.MAX_RETRIES_PER_STEP + 1):
        try:
            raw_output = await asyncio.wait_for(
                _dispatch(step, manifest, step_outputs, job_id=job_id),
                timeout=settings.STEP_TIMEOUT_SECONDS,
            )

            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            executed.status = StepStatus.SUCCESS
            executed.raw_output = raw_output
            executed.completed_at = completed_at
            executed.duration_ms = duration_ms
            executed.output_summary = _summarise_output(raw_output)
            executed.output_type = raw_output.get("type", "text") if isinstance(raw_output, dict) else "text"
            executed.confidence = raw_output.get("confidence") if isinstance(raw_output, dict) else None
            logger.debug(f"{log_prefix} step complete in {duration_ms}ms | {executed.output_summary[:80]}")
            return executed

        except asyncio.TimeoutError:
            logger.warning(f"{log_prefix} timed out after {settings.STEP_TIMEOUT_SECONDS}s (attempt {attempt+1})")
            executed.error_message = f"Timed out after {settings.STEP_TIMEOUT_SECONDS}s"
            executed.retry_count = attempt

        except Exception as exc:
            logger.exception(f"{log_prefix} error (attempt {attempt+1}): {exc}")
            executed.error_message = str(exc)
            executed.retry_count = attempt

            # Retry only once
            if attempt < settings.MAX_RETRIES_PER_STEP:
                await asyncio.sleep(2)
            else:
                break

    executed.status = StepStatus.FAILED
    executed.completed_at = datetime.now(timezone.utc)
    executed.duration_ms = int(
        (executed.completed_at - started_at).total_seconds() * 1000
    )
    if "No module named" in (executed.error_message or ""):
        executed.output_summary = f"FAILED / UNAVAILABLE (Reason: Runtime module import failure: {executed.error_message})"
    else:
        executed.output_summary = f"FAILED / UNAVAILABLE: {executed.error_message or 'Step execution failed'}"
    logger.error(f"{log_prefix} FAILED after {executed.duration_ms}ms: {executed.error_message}")
    return executed


async def _dispatch(step, manifest: InputManifest, step_outputs: dict, job_id: str = "") -> dict:
    """Route a plan step to the correct handler."""
    tool_id = step.tool_id
    image_path = _get_image_path(manifest, step.image_index)
    log_prefix = f"[{job_id}][{step.step_id}]" if job_id else f"[{step.step_id}]"
    logger.info(f"{log_prefix} dispatching tool_id={tool_id} image_index={step.image_index}")

    # ── Deterministic Tools (no GPU) ──────────────────────────────────────
    img_manifest = manifest.images[step.image_index if step.image_index is not None else 0]
    if tool_id == "raster-metadata":
        from engine.tools.raster_stats import get_raster_metadata
        return await asyncio.to_thread(get_raster_metadata, img_manifest)

    elif tool_id == "raster-stats":
        from engine.tools.raster_stats import get_band_statistics
        return await asyncio.to_thread(get_band_statistics, img_manifest)

    elif tool_id == "sar-stats":
        from engine.tools.raster_stats import get_sar_statistics
        return await asyncio.to_thread(get_sar_statistics, img_manifest)

    elif tool_id == "ndvi-calculator":
        from engine.tools.indices import compute_ndvi
        return await asyncio.to_thread(compute_ndvi, img_manifest)

    elif tool_id in ("area-calculator", "mask-area"):
        from engine.tools.geometry import calculate_mask_area
        # Get mask from a dependent step if available
        mask_data = None
        for dep_id in step.depends_on:
            dep_output = step_outputs.get(dep_id, {})
            if isinstance(dep_output, dict) and "change_mask" in dep_output:
                mask_data = dep_output["change_mask"]
                break
        meta = manifest.images[step.image_index or 0]
        epsg = meta.get("crs_epsg") if isinstance(meta, dict) else getattr(meta, "crs_epsg", None)
        gsd_x = meta.get("gsd_x") if isinstance(meta, dict) else getattr(meta, "gsd_x", None)
        gsd_y = meta.get("gsd_y") if isinstance(meta, dict) else getattr(meta, "gsd_y", None)
        return await asyncio.to_thread(
            calculate_mask_area,
            mask_data,
            epsg,
            gsd_x,
            gsd_y,
        )

    elif tool_id in ("bbox-area-calculator", "bbox-area"):
        from engine.tools.geometry import calculate_bbox_area
        bbox = step.parameters.get("bbox", [0, 0, 100, 100])
        res = step.parameters.get("resolution", 10.0)
        crs = step.parameters.get("crs")
        return await asyncio.to_thread(
            calculate_bbox_area,
            bbox=bbox,
            pixel_resolution_m=res,
            crs=crs,
        )

    elif tool_id in ("polygon-area-calculator", "polygon-area"):
        from engine.tools.geometry import calculate_polygon_area
        coords = step.parameters.get("coordinates", [])
        return await asyncio.to_thread(
            calculate_polygon_area,
            coordinates=coords,
        )

    elif tool_id in ("geodesic-distance-calculator", "geodesic-distance"):
        from engine.tools.geometry import geodesic_distance
        pt1 = step.parameters.get("point1", (0.0, 0.0))
        pt2 = step.parameters.get("point2", (0.0, 0.0))
        return await asyncio.to_thread(
            geodesic_distance,
            pt1,
            pt2,
        )

    elif tool_id == "change-area":
        from engine.tools.geometry import calculate_mask_area
        # Look for change_mask in dependent step outputs
        mask_data = None
        for dep_id in step.depends_on:
            dep_output = step_outputs.get(dep_id, {})
            if isinstance(dep_output, dict) and "change_mask" in dep_output:
                mask_data = dep_output["change_mask"]
                break
        meta = manifest.images[0]
        epsg = meta.get("crs_epsg") if isinstance(meta, dict) else getattr(meta, "crs_epsg", None)
        gsd_x = meta.get("gsd_x") if isinstance(meta, dict) else getattr(meta, "gsd_x", None)
        gsd_y = meta.get("gsd_y") if isinstance(meta, dict) else getattr(meta, "gsd_y", None)
        return await asyncio.to_thread(
            calculate_mask_area,
            mask_data,
            epsg,
            gsd_x,
            gsd_y,
        )

    elif tool_id == "mask-overlay":
        from engine.tools.visualizer import create_mask_overlay
        mask_data = None
        for dep_id in step.depends_on:
            dep_output = step_outputs.get(dep_id, {})
            if isinstance(dep_output, dict) and "change_mask" in dep_output:
                mask_data = dep_output["change_mask"]
                break
        return await asyncio.to_thread(create_mask_overlay, image_path, mask_data)

    # ── ML Models (GPU / Deep Learning) ──────────────────────────────────
    elif tool_id in ("rsvqa-specialist", "geochat-vqa"):
        try:
            from backend.models.rsvqa.model import rsvqa_specialist
        except ImportError:
            from models.rsvqa.model import rsvqa_specialist
        question = step.parameters.get("question", manifest.query)
        return await asyncio.to_thread(rsvqa_specialist.predict, image_path, question)

    elif tool_id in ("vrsbench-caption", "captioning-specialist", "geochat-caption"):
        from PIL import Image
        try:
            from backend.models.captioning.model import get_vrsbench_specialist
        except ImportError:
            from models.captioning.model import get_vrsbench_specialist
        specialist = get_vrsbench_specialist()
        img = Image.open(image_path).convert("RGB")
        res = await asyncio.to_thread(specialist.describe_scene, img)
        return {
            "type": "text",
            "text": res["caption"],
            "caption": res["caption"],
            "salient_features": res["salient_features"],
            "confidence": res["confidence"],
            "model": "vrsbench-captioning-specialist",
        }

    elif tool_id in ("vrsbench-grounding", "grounding-specialist", "geochat-grounding"):
        from PIL import Image
        try:
            from backend.models.captioning.model import get_vrsbench_specialist
        except ImportError:
            from models.captioning.model import get_vrsbench_specialist
        specialist = get_vrsbench_specialist()
        img = Image.open(image_path).convert("RGB")
        text_ref = step.parameters.get("text_reference", manifest.query)
        boxes = await asyncio.to_thread(specialist.ground_expression, img, text_ref)
        return {
            "type": "detection",
            "text": f"Grounded {len(boxes)} regions for {text_ref!r}",
            "boxes": boxes,
            "detections_count": len(boxes),
            "confidence": 0.88 if boxes else 0.5,
            "model": "vrsbench-grounding-specialist",
        }

    elif tool_id == "bit-change-detection":
        from engine.models.change_detect import run_change_detection
        t1_path = _get_image_path(manifest, 0)
        t2_path = _get_image_path(manifest, 1)
        return await asyncio.to_thread(run_change_detection, t1_path, t2_path)

    elif tool_id in ("cdvqa-specialist", "change-vqa"):
        try:
            from backend.models.cdvqa.model import cdvqa_specialist
        except ImportError:
            from models.cdvqa.model import cdvqa_specialist
        t1_path = _get_image_path(manifest, 0)
        t2_path = _get_image_path(manifest, 1)
        question = step.parameters.get("question", manifest.query)
        return await asyncio.to_thread(cdvqa_specialist.predict, t1_path, t2_path, question)

    elif tool_id in ("cross-modal-specialist", "optical-sar"):
        try:
            from backend.models.cross_modal.specialist import cross_modal_specialist
        except ImportError:
            from models.cross_modal.specialist import cross_modal_specialist
        img0 = manifest.images[0]
        img1 = manifest.images[1]
        modality0 = img0.modality.modality.value if hasattr(img0.modality, "modality") else str(img0.modality)
        if modality0 == "SAR":
            sar_manifest, opt_manifest = img0, img1
        else:
            opt_manifest, sar_manifest = img0, img1
        return await asyncio.to_thread(cross_modal_specialist.analyze, opt_manifest, sar_manifest)

    elif tool_id == "ben-scene-classifier":
        from engine.models.classifier import run_scene_classification
        return await asyncio.to_thread(run_scene_classification, image_path)

    else:
        raise ValueError(f"Unknown tool_id: {tool_id!r}. This should not happen if the registry is correct.")


def _summarise_output(raw_output: Any) -> str:
    """Create a short human-readable summary of a step's raw output."""
    if not isinstance(raw_output, dict):
        return str(raw_output)[:200]
    out_type = raw_output.get("type", "unknown")
    if out_type == "text":
        return (raw_output.get("text", "") or "")[:150]
    if out_type == "classification":
        labels = raw_output.get("labels", [])
        return f"Classified as: {', '.join(labels[:3])}"
    if out_type == "change_mask":
        pct = raw_output.get("change_percentage", "?")
        return f"Change detected: {pct}% of area changed"
    if out_type == "measurement":
        return str(raw_output.get("value", ""))
    if out_type == "metadata":
        return f"Extracted metadata ({raw_output.get('band_count', '?')} bands)"
    return str(raw_output)[:200]
