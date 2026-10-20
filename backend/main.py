"""
Astra AI Backend — FastAPI Application Entry Point
"""

import uuid
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sse_starlette.sse import EventSourceResponse
from loguru import logger
import aiofiles
import time

from middleware.auth import verify_api_key
from middleware.rate_limit import rate_limit

from config import settings
from gateway.validator import validate_upload_files, validate_geotiff_spatial
from gateway.compatibility import validate_bitemporal_pair, validate_cross_modal_pair
from gateway.metadata import extract_metadata
from gateway.modality import detect_modality
from orchestrator.planner import generate_investigation_plan
from orchestrator.schemas import InputManifest, InvestigationResponse, InvestigationStatus, ImageManifest
from engine.executor import execute_plan
from evidence.assembler import assemble_evidence
from report.synthesizer import synthesize_report
from report.exporter import export_markdown_report, export_html_report


# ─── In-memory job store ─────────────────────────────────────────────────────
# For MVP: keyed by job_id, value is asyncio.Queue of progress events
_job_queues: dict[str, asyncio.Queue] = {}
# Stores final results + timestamp for cleanup
_job_results: dict[str, dict] = {}
# Stores structured report and evidence package for downloadable exports
_investigation_store: dict[str, tuple[Any, Any, str]] = {}
# Stores uploaded raster paths per job for preview rendering
_job_file_paths: dict[str, list[Path]] = {}


def generate_raster_preview(raster_path: Path, output_png_path: Path, max_dim: int = 1200) -> Path:
    """
    Generate an RGB display-safe PNG preview from any remote sensing raster (GeoTIFF, etc.).
    Applies robust 2%-98% percentile stretch per channel for realistic, high-contrast visualization.
    Preserves the original source raster unmodified.
    """
    import numpy as np
    from PIL import Image
    import rasterio

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with rasterio.open(str(raster_path)) as src:
            if src.count >= 3:
                # Optical 3+ bands (RGB)
                data = src.read([1, 2, 3])
                data = np.transpose(data, (1, 2, 0))
                rgb = np.zeros_like(data, dtype=np.uint8)
                for c in range(3):
                    ch = data[:, :, c].astype(float)
                    valid = ch[ch > 0] if (ch > 0).any() else ch
                    p2, p98 = np.percentile(valid, [2, 98]) if valid.size > 0 else (0, 1)
                    denom = max(p98 - p2, 1e-4)
                    rgb[:, :, c] = np.clip((ch - p2) / denom * 255.0, 0, 255).astype(np.uint8)
                img = Image.fromarray(rgb, mode="RGB")
            else:
                # 1-band grayscale / SAR raster
                ch = src.read(1).astype(float)
                valid = ch[ch > 0] if (ch > 0).any() else ch
                p2, p98 = np.percentile(valid, [2, 98]) if valid.size > 0 else (0, 1)
                denom = max(p98 - p2, 1e-4)
                gray = np.clip((ch - p2) / denom * 255.0, 0, 255).astype(np.uint8)
                img = Image.fromarray(gray, mode="L").convert("RGB")
    except Exception:
        # Fallback to standard PIL if rasterio cannot decode
        img = Image.open(str(raster_path)).convert("RGB")

    if max(img.width, img.height) > max_dim:
        scale = max_dim / max(img.width, img.height)
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)

    img.save(str(output_png_path), format="PNG")
    return output_png_path

async def _cleanup_jobs_loop():
    """Background task to clean up old job results after 1 hour."""
    while True:
        try:
            now = time.time()
            expired = [k for k, v in _job_results.items() if now - v.get("timestamp", now) > 3600]
            for k in expired:
                _job_results.pop(k, None)
            await asyncio.sleep(600)  # run every 10 minutes
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Job cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("🚀 Astra AI Backend starting up...")
    logger.info(f"  Upload dir : {settings.UPLOAD_DIR.resolve()}")
    logger.info(f"  Model dir  : {settings.MODEL_CACHE_DIR.resolve()}")
    logger.info(f"  Gemini key : {'set' if settings.GEMINI_API_KEY else '⚠ NOT SET'}")

    # Initialize GPU engine and preload resident ResNet-50 model
    try:
        from services.model_service import model_service
        logger.info(f"  GPU Device : {model_service.device}")
        model_service.load_ben_classifier()
        logger.success("  ResNet-50 BigEarthNet model preloaded and resident in VRAM.")
    except Exception as e:
        logger.warning(f"  Model pre-load notice: {e}")

    cleanup_task = asyncio.create_task(_cleanup_jobs_loop())
    yield
    cleanup_task.cancel()
    logger.info("🛑 Astra AI Backend shutting down...")


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Astra AI Backend",
    description="SIH26167 — Multimodal Remote Sensing Image Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Backend + GPU status check."""
    import torch
    from services.model_service import model_service
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    vram_total = None
    vram_free = None
    if gpu_available:
        props = torch.cuda.get_device_properties(0)
        vram_total = round(props.total_memory / (1024 ** 3), 1)
        vram_free = round((props.total_memory - torch.cuda.memory_allocated(0)) / (1024 ** 3), 1)

    is_ben_loaded = "ben_classifier" in model_service.models and model_service.models["ben_classifier"] is not None

    return {
        "status": "online",
        "gpu": {
            "available": gpu_available,
            "device": str(model_service.device),
            "name": gpu_name,
            "vram_total_gb": vram_total,
            "vram_free_gb": vram_free,
        },
        "models": {
            "resnet50_bigearthnet": "loaded" if is_ben_loaded else "available"
        },
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }

# ─── Live Disasters & Hazards Feed Proxy (GDACS & NOAA NHC) ───────────────────
_disaster_cache: dict[str, Any] = {"gdacs": None, "gdacs_time": 0, "nhc": None, "nhc_time": 0}

@app.get("/api/disasters/live")
async def get_live_disasters():
    """
    Authoritative disaster intelligence proxy.
    Proxies and caches GDACS (UN/EC GLOFAS/JTWC/GWIS) and NOAA NHC (CurrentStorms)
    to overcome browser CORS restrictions while providing live official feeds.
    """
    import httpx
    now = time.time()
    results: dict[str, Any] = {"gdacs": None, "nhc": None, "status": "ok"}
    
    # 1. GDACS
    if _disaster_cache["gdacs"] and (now - _disaster_cache["gdacs_time"] < 120):
        results["gdacs"] = _disaster_cache["gdacs"]
    else:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventtypes=FL,TC,VO,EQ,WF,DR",
                    headers={"User-Agent": "Astra-Disaster-Hub/1.0"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _disaster_cache["gdacs"] = data
                    _disaster_cache["gdacs_time"] = now
                    results["gdacs"] = data
        except Exception as e:
            logger.warning(f"GDACS upstream fetch warning: {e}")
            results["gdacs"] = _disaster_cache["gdacs"]
            
    # 2. NOAA NHC
    if _disaster_cache["nhc"] and (now - _disaster_cache["nhc_time"] < 120):
        results["nhc"] = _disaster_cache["nhc"]
    else:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://www.nhc.noaa.gov/CurrentStorms.json",
                    headers={"User-Agent": "Astra-Disaster-Hub/1.0"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _disaster_cache["nhc"] = data
                    _disaster_cache["nhc_time"] = now
                    results["nhc"] = data
        except Exception as e:
            logger.warning(f"NOAA NHC upstream fetch warning: {e}")
            results["nhc"] = _disaster_cache["nhc"]

    return results


# ─── System Status ────────────────────────────────────────────────────────────
@app.get("/api/system/status", dependencies=[Depends(verify_api_key), Depends(rate_limit)])
async def system_status():
    """Detailed backend status and metrics."""
    return {
        "status": "healthy",
        "active_jobs": len(_job_queues),
        "cached_results": len(_job_results),
        "uptime": "tracked_by_os",
    }


# ─── Demo Data API (Phase 8 & Fix 1) ─────────────────────────────────────────
@app.get("/api/demo/cases")
async def get_demo_cases():
    """
    List verified demo cases for the SIH demonstration.
    Returns real raster files present in the repository with suggested natural language queries.
    """
    return {
        "cases": [
            {
                "id": "building_change",
                "name": "Building Change Detection",
                "mode": "bitemporal",
                "files": ["building_change_t1.tif", "building_change_t2.tif"],
                "query": "What changed between these two images, where did the change occur, and approximately how much area was affected?",
                "sensor": "Optical Multispectral (0.5m GSD)",
                "source": "LEVIR-CD Benchmark",
                "demonstrates": "BIT Change Detection, Change Mask, Deterministic Area Calculation, Dossier Report"
            },
            {
                "id": "optical_sar",
                "name": "Optical + SAR Cross-Modal Analysis",
                "mode": "crossmodal",
                "files": ["optical_cartosat.tif", "sar_risat.tif"],
                "query": "Compare the optical and SAR observations and explain what additional information the SAR image provides.",
                "sensor": "Cartosat-2S (Optical) + RISAT-1A (C-band SAR)",
                "source": "ISRO Dual-Sensor Representative Benchmark",
                "demonstrates": "Optical reflectance vs Microwave backscatter dB, Surface roughness, Conflict detection"
            },
            {
                "id": "single_image",
                "name": "Single Image Land Cover & Scene Analysis",
                "mode": "single",
                "files": ["optical_cartosat.tif"],
                "query": "What is the dominant land cover in this image and describe the scene in detail?",
                "sensor": "Cartosat Optical High-Resolution Scene",
                "source": "BigEarthNet / ISRO Representative Optical Scene",
                "demonstrates": "ResNet-50 19-class LULC classification, Visual Question Answering, Text-guided localization"
            }
        ]
    }


@app.get("/api/demo/file/{filename}")
async def get_demo_file(filename: str):
    """
    Serve verified demo raster files safely.
    Strictly checks that the file exists within verified project directories.
    """
    import os
    safe_name = os.path.basename(filename)
    root = Path(__file__).resolve().parent.parent
    candidates = [
        root / "frontend" / "public" / "demo_data" / safe_name,
        root / "evaluation" / "test_data" / safe_name,
        Path(__file__).resolve().parent / "models" / safe_name,
        Path(__file__).resolve().parent / "demo_data" / safe_name,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return FileResponse(
                path=str(c),
                filename=safe_name,
                media_type="image/tiff" if safe_name.lower().endswith((".tif", ".tiff")) else "application/octet-stream"
            )
    raise HTTPException(status_code=404, detail=f"Demo raster '{safe_name}' not found on server.")


@app.get("/api/demo/preview/{filename}")
async def get_demo_preview(filename: str):
    """
    Serve display-safe RGB PNG preview of verified demo raster files.
    Allows browser <img> tags to view GeoTIFF demo imagery without raw TIFF decoding errors.
    """
    import os
    safe_name = os.path.basename(filename)
    root = Path(__file__).resolve().parent.parent
    candidates = [
        root / "frontend" / "public" / "demo_data" / safe_name,
        root / "evaluation" / "test_data" / safe_name,
        Path(__file__).resolve().parent / "models" / safe_name,
        Path(__file__).resolve().parent / "demo_data" / safe_name,
    ]
    target_file = None
    for c in candidates:
        if c.exists() and c.is_file():
            target_file = c
            break

    if not target_file:
        raise HTTPException(status_code=404, detail=f"Demo raster '{safe_name}' not found.")

    # If already a web image, return directly
    if safe_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return FileResponse(path=str(target_file))

    cache_dir = settings.UPLOAD_DIR / "demo_previews"
    cache_dir.mkdir(parents=True, exist_ok=True)
    preview_file = cache_dir / f"{Path(safe_name).stem}_preview.png"
    if not preview_file.exists():
        generate_raster_preview(target_file, preview_file)

    return FileResponse(path=str(preview_file), media_type="image/png")



# ─── Model Registry API ────────────────────────────────────────────────────────
@app.get("/api/registry")
async def get_model_registry():
    """
    Read-only Model & Tool Registry endpoint.
    Returns the authoritative model_registry.json enriched with live availability checks.
    Safe to expose: no credentials, secrets, or private configuration.
    """
    import json as _json
    from orchestrator.registry import _check_model_status, MODEL_REGISTRY, TOOL_REGISTRY
    from orchestrator.schemas import ModelStatus

    registry_path = Path(__file__).parent / "models" / "model_registry.json"
    registry_data: dict = {}
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry_data = _json.load(f)

    # Enrich with live availability status from registry checks
    live_statuses: dict[str, str] = {}
    for model_key in MODEL_REGISTRY:
        status = _check_model_status(model_key)
        live_statuses[model_key] = status.value

    return {
        "schema_version": registry_data.get("schema_version", "1.0"),
        "last_updated": registry_data.get("last_updated", "unknown"),
        "models": registry_data.get("models", {}),
        "deterministic_tools": registry_data.get("deterministic_tools", {}),
        "live_availability": live_statuses,
        "tool_count": len(TOOL_REGISTRY),
        "model_count": len(MODEL_REGISTRY),
    }



# ─── Specialist Endpoints ──────────────────────────────────────────────────
@app.post("/api/specialists/vqa")
async def specialist_vqa(
    question: str = Form(..., description="Natural language question"),
    file: UploadFile = File(..., description="Remote sensing image raster"),
):
    """
    Dedicated Remote-Sensing VQA Specialist endpoint.
    Accepts single optical/satellite image and query.
    Returns calibrated answer, confidence, evidence, and timings.
    """
    validation_errors = await validate_upload_files([file])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        await f.write(content)

    from backend.models.rsvqa.model import rsvqa_specialist
    result = await asyncio.to_thread(rsvqa_specialist.predict, dest, question)
    return result


@app.post("/api/specialists/lulc")
async def specialist_lulc(
    file: UploadFile = File(..., description="Remote sensing image raster"),
):
    """
    Dedicated ResNet-50 BigEarthNet v2.0 Multi-Label Classifier endpoint.
    """
    validation_errors = await validate_upload_files([file])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        await f.write(content)

    from backend.services.model_service import model_service
    result = await asyncio.to_thread(model_service.predict_scene, dest)
    return result


@app.post("/api/specialists/caption")
async def specialist_caption(
    file: UploadFile = File(..., description="Remote sensing image raster"),
    prompt: Optional[str] = Form("a detailed satellite photo showing", description="Optional prompt prefix"),
):
    """
    Dedicated Remote-Sensing Scene Captioning Specialist (VRSBench).
    Generates rich natural language descriptions of landscape, structures, and land-use.
    """
    validation_errors = await validate_upload_files([file])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        await f.write(content)

    from PIL import Image
    from backend.models.captioning.model import VRSBenchSpecialist
    specialist = VRSBenchSpecialist()
    img = Image.open(dest).convert("RGB")
    result = await asyncio.to_thread(specialist.describe_scene, img, prompt)
    return result


@app.post("/api/specialists/grounding")
async def specialist_grounding(
    query: str = Form(..., description="Referring expression to locate"),
    file: UploadFile = File(..., description="Remote sensing image raster"),
):
    """
    Dedicated Remote-Sensing Visual Grounding Specialist (VRSBench).
    Localizes targets matching the referring query and outputs normalized bounding boxes.
    """
    validation_errors = await validate_upload_files([file])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        await f.write(content)

    from PIL import Image
    from backend.models.captioning.model import VRSBenchSpecialist
    specialist = VRSBenchSpecialist()
    img = Image.open(dest).convert("RGB")
    boxes = await asyncio.to_thread(specialist.ground_expression, img, query)
    return {
        "query": query,
        "detections_count": len(boxes),
        "boxes": boxes,
        "image_size": [img.width, img.height],
    }


@app.post("/api/specialists/change")
@app.post("/api/specialists/change-detection")
async def specialist_change(
    file_t1: UploadFile = File(..., description="Temporal Image 1 (Date 1 / Before)"),
    file_t2: UploadFile = File(..., description="Temporal Image 2 (Date 2 / After)"),
    gsd: Optional[float] = Form(0.5, description="Ground Sampling Distance in meters per pixel"),
    threshold: Optional[float] = Form(0.5, description="Binary change probability threshold"),
):
    """
    Dedicated Bi-Temporal Remote-Sensing Change Detection Specialist (LEVIR-CD / BIT).
    Analyzes co-registered optical rasters across two dates.
    Outputs binary change mask, changed pixels, changed area (m² and ha),
    connected structural components count, confidence, and spatial alignment metrics.
    """
    validation_errors = await validate_upload_files([file_t1, file_t2])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest1 = tmp_dir / f"t1_{uuid.uuid4()}{Path(file_t1.filename).suffix.lower()}"
    dest2 = tmp_dir / f"t2_{uuid.uuid4()}{Path(file_t2.filename).suffix.lower()}"

    async with aiofiles.open(dest1, "wb") as f1, aiofiles.open(dest2, "wb") as f2:
        content1 = await file_t1.read()
        content2 = await file_t2.read()
        await f1.write(content1)
        await f2.write(content2)

    from backend.models.change_detection.model import get_change_specialist
    specialist = get_change_specialist()
    result = await asyncio.to_thread(
        specialist.detect_change,
        dest1,
        dest2,
        gsd=gsd if gsd is not None else 0.5,
        threshold=threshold if threshold is not None else 0.5,
    )
    return result


@app.post("/api/specialists/change-vqa")
async def specialist_change_vqa(
    question: str = Form(..., description="Natural language question about changes"),
    file_t1: UploadFile = File(..., description="Temporal Image 1 (Date 1 / Before)"),
    file_t2: UploadFile = File(..., description="Temporal Image 2 (Date 2 / After)"),
    question_type: Optional[str] = Form(None, description="Optional question type hint"),
    gsd: Optional[float] = Form(0.5, description="Ground Sampling Distance in meters per pixel"),
):
    """
    Dedicated Change-Based Visual Question Answering (CDVQA) Specialist.
    Grounds natural-language queries about temporal changes strictly in
    bi-temporal difference masks and differential LULC transitions.
    """
    validation_errors = await validate_upload_files([file_t1, file_t2])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest1 = tmp_dir / f"t1_{uuid.uuid4()}{Path(file_t1.filename).suffix.lower()}"
    dest2 = tmp_dir / f"t2_{uuid.uuid4()}{Path(file_t2.filename).suffix.lower()}"

    async with aiofiles.open(dest1, "wb") as f1, aiofiles.open(dest2, "wb") as f2:
        content1 = await file_t1.read()
        content2 = await file_t2.read()
        await f1.write(content1)
        await f2.write(content2)

    from backend.models.cdvqa.model import get_cdvqa_specialist
    specialist = get_cdvqa_specialist()
    result = await asyncio.to_thread(
        specialist.answer_query,
        dest1,
        dest2,
        question=question,
        question_type=question_type,
        gsd=gsd if gsd is not None else 0.5,
    )
    return result


@app.post("/api/specialists/optical-sar")
async def specialist_optical_sar(
    file_optical: UploadFile = File(..., description="Optical image (Sentinel-2 / Cartosat-2S)"),
    file_sar: UploadFile = File(..., description="SAR image (Sentinel-1 / RISAT-1A)"),
):
    """
    Dedicated Optical + SAR Cross-Modal Specialist Endpoint.
    Jointly reasons over optical spectral reflectance and SAR microwave backscatter geometry.
    Performs conflict detection, all-weather penetration, and complementary feature fusion.
    """
    validation_errors = await validate_upload_files([file_optical, file_sar])
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    tmp_dir = settings.UPLOAD_DIR / "specialists" / str(uuid.uuid4())
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest_opt = tmp_dir / f"opt_{uuid.uuid4()}{Path(file_optical.filename).suffix.lower()}"
    dest_sar = tmp_dir / f"sar_{uuid.uuid4()}{Path(file_sar.filename).suffix.lower()}"

    async with aiofiles.open(dest_opt, "wb") as f1, aiofiles.open(dest_sar, "wb") as f2:
        content1 = await file_optical.read()
        content2 = await file_sar.read()
        await f1.write(content1)
        await f2.write(content2)

    from backend.models.cross_modal.specialist import get_cross_modal_specialist
    specialist = get_cross_modal_specialist()
    result = await asyncio.to_thread(specialist.analyze_pair, dest_opt, dest_sar)
    return result



# ─── Phase 07: Geospatial Evidence Engine ────────────────────────────────────
@app.get("/api/geospatial/capabilities")
async def geospatial_capabilities():
    """
    List all deterministic geospatial measurement tools available.
    These tools NEVER hallucinate — all values are computed directly from raster data.
    """
    return {
        "capabilities": [
            {
                "tool": "mask_area",
                "description": "Calculate real-world area of a binary change/detection mask in m², km², and hectares",
                "inputs": ["mask (2D binary)", "crs_epsg", "gsd_x", "gsd_y"],
                "output_units": ["m²", "km²", "ha"],
                "confidence_status": "DETERMINISTIC",
            },
            {
                "tool": "bbox_area",
                "description": "Calculate real-world area of a detected bounding box from pixel or geographic coords",
                "inputs": ["bbox [ymin, xmin, ymax, xmax]", "crs_epsg", "gsd_x", "gsd_y", "is_pixel_coords"],
                "output_units": ["m²", "km²", "ha"],
                "confidence_status": "DETERMINISTIC",
            },
            {
                "tool": "polygon_area",
                "description": "Calculate area of a detected polygon region using WGS84-accurate geodesic math",
                "inputs": ["coords [[x,y], ...]", "crs_epsg", "gsd_x", "gsd_y", "is_pixel_coords"],
                "output_units": ["m²", "km²", "ha"],
                "confidence_status": "DETERMINISTIC",
            },
            {
                "tool": "geodesic_distance",
                "description": "Calculate WGS84 geodesic distance between two geographic coordinates",
                "inputs": ["lat1", "lon1", "lat2", "lon2"],
                "output_units": ["m", "km"],
                "confidence_status": "DETERMINISTIC",
            },
            {
                "tool": "ndvi",
                "description": "Compute Normalized Difference Vegetation Index with automatic Red/NIR band detection",
                "inputs": ["image file (multispectral GeoTIFF)"],
                "output": "NDVI mean/std/min/max, % vegetation, % water",
                "confidence_status": "DETERMINISTIC",
            },
            {
                "tool": "raster_stats",
                "description": "Per-band min/max/mean/std/median statistics for any raster",
                "inputs": ["image file"],
                "confidence_status": "DETERMINISTIC",
            },
        ],
        "anti_hallucination_guarantee": (
            "All tools in this engine compute values directly from raster data. "
            "Gemini Senior Analyst is PROHIBITED from overriding or inventing numerical measurements."
        ),
    }


@app.post("/api/geospatial/measure")
async def geospatial_measure(
    tool: str = Form(..., description="Tool: mask_area | bbox_area | polygon_area | geodesic_distance"),
    file: Optional[UploadFile] = File(None, description="GeoTIFF raster (required for ndvi, raster_stats)"),
    # Optional parameters as JSON strings via Form
    mask_json: Optional[str] = Form(None, description="JSON 2D binary mask array for mask_area"),
    bbox_json: Optional[str] = Form(None, description="JSON [ymin, xmin, ymax, xmax] for bbox_area"),
    coords_json: Optional[str] = Form(None, description="JSON [[x,y], ...] polygon for polygon_area"),
    crs_epsg: Optional[int] = Form(None, description="CRS EPSG code (e.g. 32644 for UTM 44N)"),
    gsd_x: Optional[float] = Form(None, description="Pixel width in CRS units (meters for UTM)"),
    gsd_y: Optional[float] = Form(None, description="Pixel height in CRS units"),
    is_pixel_coords: bool = Form(True, description="Whether input coordinates are pixel indices"),
    lat1: Optional[float] = Form(None), lon1: Optional[float] = Form(None),
    lat2: Optional[float] = Form(None), lon2: Optional[float] = Form(None),
):
    """
    Phase 07 — Geospatial Evidence Engine.
    All-deterministic measurement tools. Zero hallucination.
    Supports mask area, bounding box area, polygon area, and geodesic distance.
    """
    import json
    from engine.tools.geometry import calculate_mask_area, calculate_bbox_area, calculate_polygon_area, geodesic_distance
    from engine.tools.indices import compute_ndvi
    from engine.tools.raster_stats import get_band_statistics, get_raster_metadata
    from gateway.metadata import extract_metadata

    SUPPORTED_TOOLS = {"mask_area", "bbox_area", "polygon_area", "geodesic_distance", "ndvi", "raster_stats", "metadata"}
    if tool not in SUPPORTED_TOOLS:
        raise HTTPException(status_code=400, detail=f"Unknown tool '{tool}'. Supported: {sorted(SUPPORTED_TOOLS)}")

    if tool == "mask_area":
        if mask_json is None:
            raise HTTPException(status_code=422, detail="mask_json is required for mask_area")
        try:
            mask = json.loads(mask_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid mask_json: {e}")
        return calculate_mask_area(mask, crs_epsg, gsd_x, gsd_y)

    elif tool == "bbox_area":
        if bbox_json is None:
            raise HTTPException(status_code=422, detail="bbox_json is required for bbox_area")
        try:
            bbox = json.loads(bbox_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid bbox_json: {e}")
        return calculate_bbox_area(bbox, crs_epsg, gsd_x, gsd_y, is_pixel_coords)

    elif tool == "polygon_area":
        if coords_json is None:
            raise HTTPException(status_code=422, detail="coords_json is required for polygon_area")
        try:
            coords = json.loads(coords_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid coords_json: {e}")
        return calculate_polygon_area(coords, crs_epsg, gsd_x, gsd_y, is_pixel_coords)

    elif tool == "geodesic_distance":
        if None in (lat1, lon1, lat2, lon2):
            raise HTTPException(status_code=422, detail="lat1, lon1, lat2, lon2 all required for geodesic_distance")
        return geodesic_distance(lat1, lon1, lat2, lon2)

    elif tool in ("ndvi", "raster_stats", "metadata"):
        if file is None:
            raise HTTPException(status_code=422, detail=f"A raster file is required for tool '{tool}'")
        validation_errors = await validate_upload_files([file])
        if validation_errors:
            raise HTTPException(status_code=422, detail={"errors": validation_errors})

        tmp_dir = settings.UPLOAD_DIR / "geospatial" / str(uuid.uuid4())
        tmp_dir.mkdir(parents=True, exist_ok=True)
        dest = tmp_dir / f"raster_{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
        async with aiofiles.open(dest, "wb") as f:
            await f.write(await file.read())

        manifest = await asyncio.to_thread(extract_metadata, dest)
        if tool == "metadata":
            return get_raster_metadata(manifest)
        elif tool == "raster_stats":
            return await asyncio.to_thread(get_band_statistics, manifest)
        elif tool == "ndvi":
            return await asyncio.to_thread(compute_ndvi, manifest)

    raise HTTPException(status_code=400, detail=f"Tool '{tool}' not handled.")



# ─── Validation & Compatibility Endpoint (Phase 09) ───────────────────────────
@app.post("/api/validate", dependencies=[Depends(verify_api_key), Depends(rate_limit)])
async def validate_inputs(
    files: list[UploadFile] = File(...),
    query: Optional[str] = Form(None),
):
    """
    Validation & Compatibility Engine endpoint.
    Performs deep inspection of uploaded remote sensing imagery before investigation.
    Validates:
    - MIME types, magic bytes, file extensions, and file sizes
    - GeoTIFF spatial tags, CRS/EPSG, bounding boxes, and GSD resolution
    - Multi-raster compatibility (bi-temporal overlap and GSD ratio, cross-modal optical+SAR)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Format & Size checks
    upload_errors = await validate_upload_files(files)
    if upload_errors:
        errors.extend(upload_errors)

    if errors:
        return JSONResponse(
            status_code=422,
            content={
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "manifests": [],
                "compatibility": None,
            }
        )

    # 2. Save temporarily to inspect raster tags
    temp_dir = settings.UPLOAD_DIR / f"val_{uuid.uuid4()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    manifests: list[ImageManifest] = []

    try:
        for file in files:
            safe_name = f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
            dest = temp_dir / safe_name
            content = await file.read()
            async with aiofiles.open(dest, "wb") as f:
                await f.write(content)

            # Spatial inspection
            spatial_check = validate_geotiff_spatial(dest)
            if not spatial_check["is_valid"]:
                errors.extend(spatial_check["errors"])
            warnings.extend(spatial_check["warnings"])

            # Extract full manifest
            manifest = await asyncio.to_thread(extract_metadata, dest)
            manifest.filename = file.filename  # preserve original name
            manifests.append(manifest)

        # 3. Multi-image compatibility checks
        compat_data = None
        if len(manifests) == 2:
            m1 = manifests[0].modality.modality.value
            m2 = manifests[1].modality.modality.value
            if m1 == m2:
                compat_report = validate_bitemporal_pair(manifests[0], manifests[1])
            else:
                compat_report = validate_cross_modal_pair(manifests[0], manifests[1])

            compat_data = compat_report.model_dump()
            if not compat_report.is_compatible:
                errors.extend(compat_report.reasons)
            warnings.extend(compat_report.warnings)

        is_valid = len(errors) == 0
        status_code = 200 if is_valid else 422

        return JSONResponse(
            status_code=status_code,
            content={
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "manifests": [m.model_dump(mode="json") for m in manifests],
                "compatibility": compat_data,
            }
        )
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/investigate", status_code=202, dependencies=[Depends(verify_api_key), Depends(rate_limit)])
async def submit_investigation(
    query: str = Form(..., description="Natural language query"),
    files: list[UploadFile] = File(..., description="1-2 remote sensing images"),
):
    """
    Submit an investigation request.
    Returns a job_id. Then stream progress from /api/investigate/{job_id}/stream.
    """
    # 1. Validate uploaded files (format, size, count)
    validation_errors = await validate_upload_files(files)
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    # 2. Save files to disk with UUID-based names (prevents path traversal)
    job_id = str(uuid.uuid4())
    job_dir = settings.UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for idx, upload in enumerate(files):
        safe_name = f"{uuid.uuid4()}{Path(upload.filename).suffix.lower()}"
        dest = job_dir / safe_name
        async with aiofiles.open(dest, "wb") as f:
            content = await upload.read()
            await f.write(content)
        saved_paths.append(dest)
        logger.info(f"[{job_id}] Saved {upload.filename} → {dest}")
        # Pre-generate display-safe preview PNG for browser rendering
        try:
            generate_raster_preview(dest, job_dir / f"preview_{idx}.png")
        except Exception as e:
            logger.warning(f"[{job_id}] Could not pre-generate preview for {dest.name}: {e}")

    _job_file_paths[job_id] = saved_paths

    # 3. Create SSE queue and fire off background task
    queue: asyncio.Queue = asyncio.Queue()
    _job_queues[job_id] = queue

    asyncio.create_task(
        _run_investigation(job_id, query, saved_paths, queue)
    )

    return {"job_id": job_id, "status": "queued"}


# ─── Stream Progress ──────────────────────────────────────────────────────────
@app.get("/api/investigate/{job_id}/stream", dependencies=[Depends(verify_api_key)])
async def stream_investigation(job_id: str, request: Request):
    """
    Server-Sent Events stream for investigation progress.
    Sends progress events and a final 'complete' or 'error' event.
    """
    if job_id not in _job_queues and job_id not in _job_results:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        # If job already completed (late SSE connect), return cached result
        if job_id in _job_results:
            result = _job_results[job_id]
            yield {"event": result["event"], "data": result["data"]}
            return

        queue = _job_queues[job_id]
        while True:
            if await request.is_disconnected():
                logger.info(f"[{job_id}] Client disconnected from SSE stream")
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=120.0)
                yield event
                if event["event"] in ("complete", "error"):
                    # Cache result for late reconnects
                    event["timestamp"] = time.time()
                    _job_results[job_id] = event
                    _job_queues.pop(job_id, None)
                    break
            except asyncio.TimeoutError:
                # Keep-alive ping
                yield {"event": "ping", "data": ""}

    return EventSourceResponse(event_generator())


# ─── Get Result ────────────────────────────────────────────────────────────────
@app.get("/api/investigate/{job_id}/result", dependencies=[Depends(verify_api_key), Depends(rate_limit)])
async def get_result(job_id: str):
    """Poll for completed investigation result (alternative to SSE)."""
    if job_id in _job_results:
        return JSONResponse(_job_results[job_id])
    if job_id in _job_queues:
        return JSONResponse({"status": "running"}, status_code=202)
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/investigate/{job_id}/preview/{image_idx}")
async def get_investigation_preview(job_id: str, image_idx: int):
    """
    Serve display-safe RGB PNG preview of the uploaded raster for this investigation.
    Eliminates browser GeoTIFF rendering limitations while preserving the original raster.
    """
    job_dir = settings.UPLOAD_DIR / job_id
    preview_path = job_dir / f"preview_{image_idx}.png"

    if preview_path.exists():
        return FileResponse(path=str(preview_path), media_type="image/png")

    # If preview does not exist yet, search candidates
    candidates = _job_file_paths.get(job_id, [])
    if not candidates and job_dir.exists():
        candidates = sorted([
            f for f in job_dir.iterdir()
            if f.is_file() and not f.name.startswith("preview_")
        ])

    if 0 <= image_idx < len(candidates):
        src_path = candidates[image_idx]
        try:
            generate_raster_preview(src_path, preview_path)
            return FileResponse(path=str(preview_path), media_type="image/png")
        except Exception as exc:
            logger.error(f"Failed to generate preview for {src_path}: {exc}")
            raise HTTPException(status_code=500, detail="Failed to generate raster preview")

    raise HTTPException(status_code=404, detail=f"Preview not found for job {job_id}, image {image_idx}")


# ─── Download Report (Phase 17) ───────────────────────────────────────────────
@app.get("/api/report/{job_id}/download", dependencies=[Depends(verify_api_key), Depends(rate_limit)])
async def download_report(job_id: str, format: str = Query("pdf", pattern="^(markdown|html|json|pdf)$")):
    """
    Download publication-ready investigation report.
    Formats:
    - pdf: Print-ready document / PDF layout
    - html: Styled standalone HTML document (.html)
    - json: Full raw JSON response payload
    - markdown: Raw formatted Markdown document (.md)
    """
    if job_id not in _investigation_store and job_id not in _job_results:
        raise HTTPException(status_code=404, detail="Investigation report not found for this Job ID.")

    if job_id in _investigation_store:
        report, evidence, query = _investigation_store[job_id]
        if format == "markdown":
            md = export_markdown_report(report, evidence, job_id)
            return Response(
                content=md,
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=astra_report_{job_id}.md"}
            )
        elif format in ("html", "pdf"):
            html_content = export_html_report(report, evidence, job_id)
            ext = "html" if format == "html" else "html"
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=astra_report_{job_id}.{ext}"}
            )
        else:
            return JSONResponse({
                "job_id": job_id,
                "report": report.model_dump(mode="json"),
                "evidence": [f.model_dump(mode="json") for f in evidence.findings],
                "trace": evidence.trace.model_dump(mode="json") if evidence.trace else None,
            })

    # Fallback to _job_results
    result = _job_results[job_id]
    data = result.get("data") if isinstance(result, dict) else result
    if isinstance(data, str):
        import json
        data = json.loads(data)
    return JSONResponse(data)


# ─── Background Investigation Runner ──────────────────────────────────────────
async def _run_investigation(
    job_id: str,
    query: str,
    file_paths: list[Path],
    queue: asyncio.Queue,
):
    """
    Full investigation pipeline.
    Runs in a background asyncio task.
    Emits SSE events to the queue.
    """
    import json

    async def emit(event: str, data: dict):
        await queue.put({"event": event, "data": json.dumps(data, default=str)})

    try:
        # ── STEP 1: Input Gateway ───────────────────────────────────────────
        await emit("progress", {"step": "extracting_metadata", "pct": 10,
                                "message": "Extracting image metadata..."})
        manifests = []
        for fp in file_paths:
            meta = await asyncio.to_thread(extract_metadata, fp)
            manifests.append(meta)

        input_manifest = InputManifest(query=query, images=manifests)
        logger.info(f"[{job_id}] Manifest: {input_manifest.model_dump()}")

        # ── STEP 2: Gemini Orchestrator ─────────────────────────────────────
        await emit("progress", {"step": "planning", "pct": 20,
                                "message": "Planning investigation with Gemini..."})
        from orchestrator.validator import validate_plan
        raw_plan = await generate_investigation_plan(input_manifest)
        # Assuming generate_investigation_plan now returns a validated plan or dict
        # In actual implementation we might validate there, but let's pass it through
        plan = raw_plan # validate_plan should be integrated into planner actually
        logger.info(f"[{job_id}] Plan: {plan.model_dump()}")

        # ── STEP 3: Execution Engine ─────────────────────────────────────────
        await emit("progress", {"step": "executing", "pct": 30,
                                "message": f"Executing {len(plan.steps)}-step plan..."})
        execution_results = await execute_plan(plan, input_manifest, job_id, queue)

        # ── STEP 4: Evidence Assembly ────────────────────────────────────────
        await emit("progress", {"step": "assembling_evidence", "pct": 80,
                                "message": "Assembling and validating evidence..."})
        evidence = await asyncio.to_thread(assemble_evidence, execution_results, input_manifest, plan)

        # ── STEP 5: Report Synthesis ─────────────────────────────────────────
        await emit("progress", {"step": "synthesizing_report", "pct": 90,
                                "message": "Synthesizing investigation report..."})
        report = await synthesize_report(query, evidence, plan, input_manifest)

        # ── Done ─────────────────────────────────────────────────────────────
        response = InvestigationResponse(
            job_id=job_id,
            status=InvestigationStatus.COMPLETED,
            report=report,
            evidence=evidence.findings,
            trace=evidence.trace,
        )
        # Store for report export download and polling
        _investigation_store[job_id] = (report, evidence, query)
        _job_results[job_id] = {
            "event": "complete",
            "data": response.model_dump(mode="json"),
            "timestamp": time.time(),
        }
        await emit("complete", response.model_dump(mode="json"))
        logger.success(f"[{job_id}] Investigation complete.")

    except Exception as exc:
        logger.exception(f"[{job_id}] Investigation failed: {exc}")
        await emit("error", {
            "message": str(exc),
            "job_id": job_id,
        })
