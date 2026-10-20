"""
Orchestrator Layer — Gemini Investigation Planner
Converts a user's natural language query + InputManifest into a structured InvestigationPlan.
Routes queries dynamically to real registered specialists and deterministic geospatial tools.
"""

import json
import uuid
import re
from loguru import logger

from config import settings
from orchestrator.schemas import (
    InputManifest, InvestigationPlan, PlanStep, TaskType, ModalityEnum
)
from orchestrator.registry import get_registry_for_prompt
from orchestrator.validator import validate_plan

import google.generativeai as genai


# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


PLANNER_SYSTEM_PROMPT = """You are the Lead Investigation Planner for Astra AI, an agentic multimodal remote sensing intelligence platform (SIH26167).

Your mission is to:
1. Thoroughly parse the user's natural language query and uploaded satellite/aerial imagery metadata.
2. Select the optimal Task Classification from the supported domain tasks.
3. Construct a concise, executable, dependency-ordered InvestigationPlan.

CRITICAL INVARIANTS & ROUTING RULES:
1. ONLY USE TOOLS AND MODELS LISTED IN THE REGISTRY BELOW. Any invented tool/model ID will cause immediate rejection.
2. OPTICAL VS. SAR CONSTRAINTS:
   - Optical models (ben-scene-classifier, rsvqa-specialist, vrsbench-caption, vrsbench-grounding, ndvi-calculator) CANNOT be used on SAR images.
   - For pure SAR imagery, use deterministic SAR tools (sar-stats, raster-metadata).
3. MULTI-IMAGE TEMPORAL & CROSS-MODAL CONSTRAINTS:
   - Change detection (bit-change-detection, change-area, cdvqa-specialist) STRICTLY requires at least 2 temporal optical images.
   - Cross-modal analysis (cross-modal-specialist) STRICTLY requires at least 2 images of differing modalities (1 Optical + 1 SAR).
4. MATHEMATICAL DETERMINISM:
   - NEVER ask a vision-language model to estimate real-world numerical measurements (area, distance, coordinates).
   - All spatial metrics MUST be computed using deterministic tools (area-calculator, bbox-area-calculator, polygon-area-calculator, geodesic-distance-calculator, change-area).
5. HUMAN & CASUALTY DETECTION HONESTY:
   - NEVER claim to detect individual people, victims, or casualties from satellite imagery.
   - If asked about individual people or casualties, route through rsvqa-specialist with an explicit disclaimer that individual-person detection is unsupported at current satellite resolution.
6. Maximum {max_steps} steps in an investigation plan.
7. If the request cannot be answered with available tools/models, classify as "unsupported" and explain why.

{registry}

USER QUERY: {query}

INPUT IMAGES:
{image_summary}

Respond ONLY with a valid JSON object matching this schema exactly:
{{
  "task_classification": "<one of: single_image_vqa | single_image_caption | single_image_grounding | scene_classification | change_detection | change_vqa | cross_modal_analysis | geospatial_measurement | composite | unsupported>",
  "plan_rationale": "<1-2 sentences explaining the investigative strategy and tool selection>",
  "steps": [
    {{
      "step_id": "<e.g. step_1>",
      "tool_id": "<exact ID from registry>",
      "task_type": "<task type string>",
      "description": "<concise description of this step's purpose>",
      "depends_on": [],
      "parameters": {{}},
      "image_index": <0 or 1 or null>
    }}
  ],
  "estimated_duration_seconds": <integer between 5 and 60>
}}
"""


def _build_image_summary(manifest: InputManifest) -> str:
    """Format the image metadata for the Gemini prompt."""
    lines = []
    for i, img in enumerate(manifest.images):
        filename = getattr(img, "filename", None) if not isinstance(img, dict) else img.get("filename")
        modality = getattr(img, "modality", None) if not isinstance(img, dict) else img.get("modality")
        modality_val = modality.modality.value if hasattr(modality, "modality") else str(modality)
        bands = getattr(img, "band_count", None) if not isinstance(img, dict) else img.get("band_count")
        width = getattr(img, "width_px", None) if not isinstance(img, dict) else img.get("width_px")
        height = getattr(img, "height_px", None) if not isinstance(img, dict) else img.get("height_px")
        geospatial = getattr(img, "is_geospatial", None) if not isinstance(img, dict) else img.get("is_geospatial")
        quality = getattr(img, "quality_flags", []) if not isinstance(img, dict) else img.get("quality_flags", [])
        sensor = getattr(img, "sensor", None) if not isinstance(img, dict) else img.get("sensor")
        lines.append(
            f"Image {i}: filename={filename} | "
            f"modality={modality_val} | "
            f"sensor={sensor} | "
            f"bands={bands} | "
            f"size={width}x{height}px | "
            f"geospatial={geospatial} | "
            f"quality_flags={quality}"
        )
    if manifest.is_bitemporal:
        lines.append("RELATIONSHIP: bi-temporal pair (co-registered, temporal change analysis possible)")
    if manifest.is_cross_modal:
        lines.append("RELATIONSHIP: cross-modal pair (Optical + SAR co-registered, multi-sensor synthesis possible)")
    return "\n".join(lines)


def _generate_fallback_plan(manifest: InputManifest) -> InvestigationPlan:
    """
    Intelligent, deterministic fallback planner.
    Constructs a valid, grounded InvestigationPlan based on intent keywords,
    modality signatures, and temporal relationships when Gemini is offline.
    """
    query_lower = manifest.query.lower()
    steps: list[PlanStep] = []
    task_classification = TaskType.SINGLE_IMAGE_VQA.value
    rationale = "Deterministic fallback routing based on input modality and query intent."

    # ── CASE 1: Cross-Modal Analysis ──────────────────────────────────────────
    if manifest.is_cross_modal or (
        manifest.image_count >= 2
        and len({img.modality.modality for img in manifest.images}) >= 2
    ):
        task_classification = TaskType.CROSS_MODAL_ANALYSIS.value
        rationale = "Cross-modal investigation combining optical reflectance with microwave SAR backscatter."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract raster metadata and georeference for Image 0.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract raster metadata and georeference for Image 1.",
                image_index=1,
            ),
            PlanStep(
                step_id="step_3",
                tool_id="cross-modal-specialist",
                task_type="cross_modal_analysis",
                description="Synthesize optical multispectral reflectance with SAR backscatter (dB) and surface roughness.",
                depends_on=["step_1", "step_2"],
            ),
        ]
        return InvestigationPlan(
            plan_id=str(uuid.uuid4()),
            query=manifest.query,
            task_classification=task_classification,
            plan_rationale=rationale,
            steps=steps,
            estimated_duration_seconds=10,
        )

    # ── CASE 2: Bi-Temporal Change Analysis ───────────────────────────────────
    if manifest.is_bitemporal or (
        manifest.image_count >= 2
        and any(k in query_lower for k in ("change", "differ", "new", "built", "removed", "before", "after"))
    ):
        is_question = bool(re.search(r"\?|\b(what|how|where|is|has|any|increase|decrease|ratio)\b", query_lower))
        if is_question:
            task_classification = TaskType.CHANGE_VQA.value
            rationale = "Bi-temporal change visual question answering using Siamese BIT change tokens and delta LULC."
            steps = [
                PlanStep(
                    step_id="step_1",
                    tool_id="raster-metadata",
                    task_type="geospatial_measurement",
                    description="Extract spatial reference and resolution for pre-change scene.",
                    image_index=0,
                ),
                PlanStep(
                    step_id="step_2",
                    tool_id="bit-change-detection",
                    task_type="change_detection",
                    description="Extract bitemporal change mask using Siamese BIT architecture.",
                    depends_on=["step_1"],
                ),
                PlanStep(
                    step_id="step_3",
                    tool_id="change-area",
                    task_type="geospatial_measurement",
                    description="Calculate exact changed area in m², km², and percentage from change mask.",
                    image_index=0,
                    depends_on=["step_2"],
                ),
                PlanStep(
                    step_id="step_4",
                    tool_id="cdvqa-specialist",
                    task_type="change_vqa",
                    description="Answer change query strictly conditioned on change mask and LULC shift distribution.",
                    parameters={"question": manifest.query},
                    depends_on=["step_2"],
                ),
            ]
        else:
            task_classification = TaskType.CHANGE_DETECTION.value
            rationale = "Bi-temporal change detection and spatial area quantification using Siamese BIT."
            steps = [
                PlanStep(
                    step_id="step_1",
                    tool_id="raster-metadata",
                    task_type="geospatial_measurement",
                    description="Extract spatial reference and resolution for pre-change scene.",
                    image_index=0,
                ),
                PlanStep(
                    step_id="step_2",
                    tool_id="bit-change-detection",
                    task_type="change_detection",
                    description="Extract bitemporal change mask using Siamese BIT architecture.",
                    depends_on=["step_1"],
                ),
                PlanStep(
                    step_id="step_3",
                    tool_id="change-area",
                    task_type="geospatial_measurement",
                    description="Calculate exact changed area in m², km², and percentage from change mask.",
                    image_index=0,
                    depends_on=["step_2"],
                ),
                PlanStep(
                    step_id="step_4",
                    tool_id="mask-overlay",
                    task_type="visualization",
                    description="Generate visual composite overlay highlighting detected change regions.",
                    image_index=0,
                    depends_on=["step_2"],
                ),
            ]
        return InvestigationPlan(
            plan_id=str(uuid.uuid4()),
            query=manifest.query,
            task_classification=task_classification,
            plan_rationale=rationale,
            steps=steps,
            estimated_duration_seconds=12,
        )

    # ── CASE 3: Single SAR Image ──────────────────────────────────────────────
    first_modality = manifest.images[0].modality.modality if manifest.images else ModalityEnum.UNKNOWN
    if first_modality == ModalityEnum.SAR:
        task_classification = TaskType.GEOSPATIAL_MEASUREMENT.value
        rationale = "SAR microwave radar characterization using calibrated dB statistics and metadata."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract SAR radar geometry, resolution, and georeferencing metadata.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="sar-stats",
                task_type="geospatial_measurement",
                description="Compute calibrated backscatter intensity distribution and dB statistics.",
                image_index=0,
                depends_on=["step_1"],
            ),
        ]
        return InvestigationPlan(
            plan_id=str(uuid.uuid4()),
            query=manifest.query,
            task_classification=task_classification,
            plan_rationale=rationale,
            steps=steps,
            estimated_duration_seconds=6,
        )

    # ── CASE 4: Single Optical Image Intent Routing ───────────────────────────
    # Subcase 4A: Scene Captioning
    if any(k in query_lower for k in ("caption", "describe", "description", "overview", "narrative", "summarize scene")):
        task_classification = TaskType.SINGLE_IMAGE_CAPTION.value
        rationale = "Detailed multi-sentence narrative scene captioning using VRSBench specialist."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract CRS and GSD resolution metadata.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="vrsbench-caption",
                task_type="single_image_caption",
                description="Generate comprehensive scene caption describing buildings, terrain, and structures.",
                image_index=0,
                depends_on=["step_1"],
            ),
        ]

    # Subcase 4B: Visual Grounding / Object Localization
    elif any(k in query_lower for k in ("find", "locate", "ground", "bounding box", "detect", "where is", "where are", "bbox")):
        task_classification = TaskType.SINGLE_IMAGE_GROUNDING.value
        rationale = "Remote sensing referring expression visual grounding using VRSBench specialist."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract spatial reference and resolution.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="vrsbench-grounding",
                task_type="single_image_grounding",
                description="Localize referred objects/regions with normalized bounding coordinates.",
                parameters={"text_reference": manifest.query},
                image_index=0,
                depends_on=["step_1"],
            ),
        ]

    # Subcase 4C: Vegetation Index (NDVI)
    elif any(k in query_lower for k in ("ndvi", "vegetation", "chlorophyll", "greenness", "crop health")):
        task_classification = TaskType.GEOSPATIAL_MEASUREMENT.value
        rationale = "Multispectral NDVI calculation from Red and NIR bands."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract multispectral band configuration.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="ndvi-calculator",
                task_type="geospatial_measurement",
                description="Compute Normalized Difference Vegetation Index raster and statistical histogram.",
                image_index=0,
                depends_on=["step_1"],
            ),
        ]

    # Subcase 4D: Land Cover Scene Classification
    elif any(k in query_lower for k in ("classify", "land cover", "land use", "lulc", "classes", "category")):
        task_classification = TaskType.SCENE_CLASSIFICATION.value
        rationale = "Multi-label LULC classification using ResNet-50 v2 trained on BigEarthNet."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract CRS and GSD resolution.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="ben-scene-classifier",
                task_type="scene_classification",
                description="Classify land use/land cover into 19 BigEarthNet categories with calibrated probabilities.",
                image_index=0,
                depends_on=["step_1"],
            ),
        ]

    # Subcase 4E: Optical Visual Question Answering (RSVQA) with honesty guardrails
    else:
        task_classification = TaskType.SINGLE_IMAGE_VQA.value
        person_terms = ["person", "people", "human", "victim", "casualty", "survivor"]
        if any(w in query_lower for w in person_terms):
            rationale = "Remote sensing VQA with mandatory disclaimer: individual-person resolution is unsupported."
        else:
            rationale = "Remote sensing visual question answering conditioned on BigEarthNet LULC spatial context."
        steps = [
            PlanStep(
                step_id="step_1",
                tool_id="raster-metadata",
                task_type="geospatial_measurement",
                description="Extract metadata and image dimensions.",
                image_index=0,
            ),
            PlanStep(
                step_id="step_2",
                tool_id="ben-scene-classifier",
                task_type="scene_classification",
                description="Classify scene land cover context.",
                image_index=0,
                depends_on=["step_1"],
            ),
            PlanStep(
                step_id="step_3",
                tool_id="rsvqa-specialist",
                task_type="single_image_vqa",
                description="Answer query grounded in visual features and land cover classifications.",
                parameters={"question": manifest.query},
                image_index=0,
                depends_on=["step_2"],
            ),
        ]

    return InvestigationPlan(
        plan_id=str(uuid.uuid4()),
        query=manifest.query,
        task_classification=task_classification,
        plan_rationale=rationale,
        steps=steps,
        estimated_duration_seconds=8,
    )


async def generate_investigation_plan(manifest: InputManifest) -> InvestigationPlan:
    """
    Call Gemini to generate a structured investigation plan.
    Falls back gracefully to intelligent deterministic plan on any failure or missing key.
    Validates all plans against registry schemas and spatial guardrails.
    """
    registry_text = get_registry_for_prompt()
    image_summary = _build_image_summary(manifest)

    prompt = PLANNER_SYSTEM_PROMPT.format(
        max_steps=settings.MAX_PLAN_STEPS,
        registry=registry_text,
        query=manifest.query,
        image_summary=image_summary,
    )

    plan_data = None
    if settings.GEMINI_API_KEY:
        try:
            logger.info(f"Calling Gemini planner for query: {manifest.query!r}")
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
                    "response_mime_type": "application/json",
                },
            )
            response = model.generate_content(prompt)
            raw_json = response.text
            plan_data = json.loads(raw_json)
        except Exception as exc:
            logger.warning(
                f"Gemini planner execution failed or returned invalid output: {exc}. "
                "Engaging deterministic fallback planner."
            )

    if plan_data:
        try:
            plan = validate_plan(plan_data, manifest)
            if not plan.plan_id:
                plan.plan_id = str(uuid.uuid4())
            logger.info(f"Gemini plan validated successfully: {plan.task_classification} ({len(plan.steps)} steps)")
            return plan
        except ValueError as e:
            logger.warning(f"Gemini plan validation failed: {e}. Falling back to deterministic plan.")

    # Intelligent deterministic fallback
    fallback_plan = _generate_fallback_plan(manifest)
    # Double check that fallback plan itself passes validation
    validated_fallback = validate_plan(fallback_plan.model_dump(), manifest)
    logger.info(
        f"Deterministic plan active: {validated_fallback.task_classification} | "
        f"{len(validated_fallback.steps)} steps | "
        f"est. {validated_fallback.estimated_duration_seconds}s"
    )
    return validated_fallback
