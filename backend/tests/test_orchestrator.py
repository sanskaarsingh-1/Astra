"""
Unit Tests for Layer 2 Orchestrator
Tests:
- Static model and tool registry schemas, aliases, and dynamic status checks
- Plan validation and strict pre-execution guardrails
- Rejection of impossible workflows (single-image change, single-image cross-modal, optical on SAR)
- Intelligent deterministic fallback planner intent classification and routing
"""

import pytest
import uuid
from orchestrator.schemas import (
    ImageManifest, ModalityEnum, ModalityResult, InputManifest,
    InvestigationPlan, PlanStep, TaskType, ModelStatus
)
from orchestrator.registry import (
    TOOL_REGISTRY, MODEL_REGISTRY, get_tool, get_model, is_model, is_tool,
    _check_model_status, get_registry_for_prompt
)
from orchestrator.validator import validate_plan
from orchestrator.planner import _generate_fallback_plan


def _make_optical_manifest(filename="optical_01.tif") -> ImageManifest:
    return ImageManifest(
        file_id=str(uuid.uuid4()),
        filename=filename,
        file_path=f"datasets/{filename}",
        format="GTiff",
        width_px=512,
        height_px=512,
        band_count=3,
        dtype="uint8",
        crs_epsg=3857,
        gsd_x=10.0,
        gsd_y=10.0,
        is_geospatial=True,
        modality=ModalityResult(
            modality=ModalityEnum.OPTICAL_RGB,
            confidence=0.95,
            evidence=["3-band RGB"],
        ),
    )


def _make_sar_manifest(filename="sar_01.tif") -> ImageManifest:
    return ImageManifest(
        file_id=str(uuid.uuid4()),
        filename=filename,
        file_path=f"datasets/{filename}",
        format="GTiff",
        width_px=512,
        height_px=512,
        band_count=2,
        dtype="float32",
        crs_epsg=3857,
        gsd_x=10.0,
        gsd_y=10.0,
        is_geospatial=True,
        modality=ModalityResult(
            modality=ModalityEnum.SAR,
            confidence=0.98,
            evidence=["Sentinel-1 C-Band VV/VH"],
        ),
    )


# ─── 1. Registry Integrity & Dynamic Status Tests ─────────────────────────────

def test_registry_integrity():
    """Verify tool and model registry completeness and required keys."""
    assert len(TOOL_REGISTRY) >= 8
    assert len(MODEL_REGISTRY) >= 7

    for tool_id, tool in TOOL_REGISTRY.items():
        assert "id" in tool
        assert "name" in tool
        assert "description" in tool
        assert "modalities" in tool
        assert "min_images" in tool
        assert is_tool(tool_id)

    for model_id, model in MODEL_REGISTRY.items():
        assert "id" in model
        assert "name" in model
        assert "description" in model
        assert "modalities" in model
        assert is_model(model_id)

    # Test alias lookups
    assert get_tool("mask-area")["id"] == "area-calculator"
    assert get_tool("bbox-area")["id"] == "bbox-area-calculator"
    assert get_model("change-vqa")["id"] == "cdvqa-specialist"
    assert get_model("optical-sar")["id"] == "cross-modal-specialist"


def test_dynamic_model_availability():
    """Verify operational specialist models are detected as AVAILABLE."""
    available_models = [
        "ben-scene-classifier",
        "bit-change-detection",
        "rsvqa-specialist",
        "vrsbench-caption",
        "vrsbench-grounding",
        "cdvqa-specialist",
        "cross-modal-specialist",
    ]
    for model_id in available_models:
        status = _check_model_status(model_id)
        assert status == ModelStatus.AVAILABLE, f"Expected {model_id} to be AVAILABLE, got {status}"


def test_registry_prompt_generation():
    """Verify get_registry_for_prompt() formats correctly for Gemini prompt."""
    prompt_text = get_registry_for_prompt()
    assert "=== AVAILABLE TOOLS" in prompt_text
    assert "=== AVAILABLE SPECIALIST MODELS" in prompt_text
    assert "ben-scene-classifier" in prompt_text
    assert "bit-change-detection" in prompt_text
    assert "cross-modal-specialist" in prompt_text
    assert "area-calculator" in prompt_text


# ─── 2. Plan Validation & Guardrails Tests ────────────────────────────────────

def test_plan_validation_success():
    """Verify a well-formed plan passes validation."""
    opt_img = _make_optical_manifest()
    manifest = InputManifest(query="Classify land cover", images=[opt_img])
    
    plan_dict = {
        "plan_id": "test_plan_01",
        "query": manifest.query,
        "task_classification": "scene_classification",
        "plan_rationale": "Classify scene using ResNet-50",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "raster-metadata",
                "task_type": "geospatial_measurement",
                "description": "Get metadata",
                "image_index": 0,
            },
            {
                "step_id": "step_2",
                "tool_id": "ben-scene-classifier",
                "task_type": "scene_classification",
                "description": "Classify land cover",
                "depends_on": ["step_1"],
                "image_index": 0,
            },
        ],
        "estimated_duration_seconds": 10,
    }
    validated = validate_plan(plan_dict, manifest)
    assert len(validated.steps) == 2
    assert validated.task_classification == "scene_classification"


def test_plan_validation_unknown_tool_rejection():
    """Verify hallucinated tools are rejected immediately."""
    opt_img = _make_optical_manifest()
    manifest = InputManifest(query="Detect aliens", images=[opt_img])
    
    plan_dict = {
        "plan_id": "bad_plan",
        "query": manifest.query,
        "task_classification": "single_image_vqa",
        "plan_rationale": "Hallucinated tool",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "hallucinated-space-scanner-v99",
                "task_type": "vqa",
                "description": "Fake tool",
                "image_index": 0,
            }
        ],
    }
    with pytest.raises(ValueError, match="references unknown tool/model"):
        validate_plan(plan_dict, manifest)


def test_plan_validation_single_image_change_rejection():
    """Verify attempting change detection on 1 image is strictly rejected."""
    opt_img = _make_optical_manifest()
    manifest = InputManifest(query="What changed?", images=[opt_img])
    
    plan_dict = {
        "plan_id": "change_plan_fail",
        "query": manifest.query,
        "task_classification": "change_detection",
        "plan_rationale": "Attempt change with 1 image",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "bit-change-detection",
                "task_type": "change_detection",
                "description": "BIT change",
            }
        ],
    }
    with pytest.raises(ValueError, match="requires at least 2"):
        validate_plan(plan_dict, manifest)


def test_plan_validation_cross_modal_rejection():
    """Verify cross-modal analysis on single image or identical modalities is rejected."""
    opt1 = _make_optical_manifest("opt_1.tif")
    opt2 = _make_optical_manifest("opt_2.tif")
    manifest = InputManifest(query="Analyze optical and SAR", images=[opt1, opt2])
    
    plan_dict = {
        "plan_id": "cross_modal_fail",
        "query": manifest.query,
        "task_classification": "cross_modal_analysis",
        "plan_rationale": "Attempt cross-modal with 2 optical images",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "cross-modal-specialist",
                "task_type": "cross_modal_analysis",
                "description": "Cross modal",
            }
        ],
    }
    with pytest.raises(ValueError, match="differing modalities"):
        validate_plan(plan_dict, manifest)


def test_plan_validation_optical_on_sar_rejection():
    """Verify optical models applied to SAR imagery are strictly rejected."""
    sar_img = _make_sar_manifest()
    manifest = InputManifest(query="What is in this radar image?", images=[sar_img])
    
    plan_dict = {
        "plan_id": "sar_optical_fail",
        "query": manifest.query,
        "task_classification": "single_image_vqa",
        "plan_rationale": "Attempt optical VQA on SAR",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "rsvqa-specialist",
                "task_type": "single_image_vqa",
                "description": "RSVQA on SAR",
                "image_index": 0,
            }
        ],
    }
    with pytest.raises(ValueError, match="attempts to use optical tool/model .* on a SAR image"):
        validate_plan(plan_dict, manifest)


def test_plan_validation_dependency_order_rejection():
    """Verify step referencing a future or unknown dependency is rejected."""
    opt_img = _make_optical_manifest()
    manifest = InputManifest(query="Calculate area", images=[opt_img])
    
    plan_dict = {
        "plan_id": "bad_dependency",
        "query": manifest.query,
        "task_classification": "geospatial_measurement",
        "plan_rationale": "Invalid forward dependency",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "area-calculator",
                "task_type": "geospatial_measurement",
                "description": "Area calc",
                "depends_on": ["step_99"],  # Non-existent step
                "image_index": 0,
            }
        ],
    }
    with pytest.raises(ValueError, match="depends on unknown or future step"):
        validate_plan(plan_dict, manifest)


# ─── 3. Deterministic Fallback Planner Intent Routing Tests ───────────────────

def test_fallback_planner_bitemporal_question_routing():
    """Bi-temporal image pair with question query routes to change_vqa."""
    img1 = _make_optical_manifest("t1.tif")
    img2 = _make_optical_manifest("t2.tif")
    manifest = InputManifest(
        query="What changed between these two dates? Has new construction occurred?",
        images=[img1, img2],
    )
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.CHANGE_VQA.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "bit-change-detection" in tool_ids
    assert "change-area" in tool_ids
    assert "cdvqa-specialist" in tool_ids


def test_fallback_planner_bitemporal_detection_routing():
    """Bi-temporal image pair with change mapping query routes to change_detection."""
    img1 = _make_optical_manifest("t1.tif")
    img2 = _make_optical_manifest("t2.tif")
    manifest = InputManifest(
        query="Detect and map changes between before and after images",
        images=[img1, img2],
    )
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.CHANGE_DETECTION.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "bit-change-detection" in tool_ids
    assert "change-area" in tool_ids
    assert "mask-overlay" in tool_ids


def test_fallback_planner_cross_modal_routing():
    """Optical + SAR pair routes to cross_modal_analysis."""
    opt = _make_optical_manifest("opt.tif")
    sar = _make_sar_manifest("sar.tif")
    manifest = InputManifest(
        query="Analyze optical reflectance and SAR backscatter",
        images=[opt, sar],
    )
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.CROSS_MODAL_ANALYSIS.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "cross-modal-specialist" in tool_ids


def test_fallback_planner_single_sar_routing():
    """Single SAR image routes to geospatial_measurement with sar-stats."""
    sar = _make_sar_manifest("sar.tif")
    manifest = InputManifest(
        query="Analyze radar backscatter and water boundaries",
        images=[sar],
    )
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.GEOSPATIAL_MEASUREMENT.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "sar-stats" in tool_ids
    assert "raster-metadata" in tool_ids


def test_fallback_planner_captioning_routing():
    """Single optical image with 'describe scene' query routes to captioning."""
    opt = _make_optical_manifest()
    manifest = InputManifest(query="Describe this scene in detail", images=[opt])
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.SINGLE_IMAGE_CAPTION.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "vrsbench-caption" in tool_ids


def test_fallback_planner_grounding_routing():
    """Single optical image with 'find runway' query routes to visual grounding."""
    opt = _make_optical_manifest()
    manifest = InputManifest(query="Find the airport runway bounding box", images=[opt])
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.SINGLE_IMAGE_GROUNDING.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "vrsbench-grounding" in tool_ids


def test_fallback_planner_default_vqa_routing():
    """Single optical image with generic query routes to single_image_vqa."""
    opt = _make_optical_manifest()
    manifest = InputManifest(query="Are there industrial buildings here?", images=[opt])
    plan = _generate_fallback_plan(manifest)
    assert plan.task_classification == TaskType.SINGLE_IMAGE_VQA.value
    tool_ids = [s.tool_id for s in plan.steps]
    assert "ben-scene-classifier" in tool_ids
    assert "rsvqa-specialist" in tool_ids
