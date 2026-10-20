"""
Orchestrator Layer — Plan Validator
Ensures LLM-generated investigation plans conform to the schema, reference real registered
tools/models, and strictly satisfy modality, temporal, and spatial compatibility invariants.
"""

from typing import Any
from loguru import logger
from orchestrator.schemas import InvestigationPlan, InputManifest, ModalityEnum, TaskType
from orchestrator.registry import get_tool, get_model


def validate_plan(plan_dict: dict[str, Any], manifest: InputManifest) -> InvestigationPlan:
    """
    Validates a raw dictionary (from LLM JSON output or deterministic planner) into an InvestigationPlan.
    Enforces strict pre-execution guardrails:
    - Tool/model must exist in the static registry (no hallucinations).
    - Step dependencies must be acyclic and reference prior steps.
    - Image indices must be valid.
    - Multi-image workflows (change detection, cross-modal) must have adequate images.
    - Modality constraints (optical vs. SAR) must be strictly respected.

    Raises ValueError if any invariant is violated.
    """
    try:
        plan = InvestigationPlan.model_validate(plan_dict)
    except Exception as e:
        logger.error(f"Plan schema validation failed: {e}")
        raise ValueError(f"Plan does not conform to InvestigationPlan schema: {e}")

    # Check high-level task classification against manifest inputs
    task_class = plan.task_classification
    if task_class in (TaskType.CHANGE_DETECTION.value, TaskType.CHANGE_VQA.value, "change_detection", "change_vqa"):
        if manifest.image_count < 2:
            raise ValueError(
                f"Task classification '{task_class}' requires at least 2 images, but received {manifest.image_count}."
            )

    if task_class in (TaskType.CROSS_MODAL_ANALYSIS.value, "cross_modal_analysis"):
        if manifest.image_count < 2:
            raise ValueError(
                f"Cross-modal analysis requires at least 2 images, but received {manifest.image_count}."
            )
        if not manifest.is_cross_modal:
            modalities = [img.modality.modality.value for img in manifest.images]
            if len(set(modalities)) < 2:
                raise ValueError(
                    f"Cross-modal analysis requires differing modalities (e.g. Optical + SAR), but found: {modalities}"
                )

    step_ids: set[str] = set()

    for step in plan.steps:
        # 1. Unknown tool or model check (Anti-Hallucination)
        tool_info = get_tool(step.tool_id) or get_model(step.tool_id)
        if not tool_info:
            raise ValueError(
                f"Step '{step.step_id}' references unknown tool/model: '{step.tool_id}'. "
                "Planner is strictly restricted to verified registry entries."
            )

        # 2. Dependency ordering and existence check
        for dep in step.depends_on:
            if dep not in step_ids:
                raise ValueError(
                    f"Step '{step.step_id}' depends on unknown or future step '{dep}'."
                )

        # 3. Minimum & Maximum images check per tool/model
        min_imgs = tool_info.get("min_images", 1)
        if manifest.image_count < min_imgs:
            raise ValueError(
                f"Step '{step.step_id}' ({step.tool_id}) requires at least {min_imgs} image(s), "
                f"but manifest only contains {manifest.image_count}."
            )

        # 4. Multi-image change detection step requirements
        if step.tool_id in ("bit-change-detection", "cdvqa-specialist", "change-area"):
            if manifest.image_count < 2:
                raise ValueError(
                    f"Step '{step.step_id}' ({step.tool_id}) requires at least 2 temporal images, "
                    f"but manifest only has {manifest.image_count}."
                )

        # 5. Cross-modal step requirements
        if step.tool_id == "cross-modal-specialist":
            if manifest.image_count < 2:
                raise ValueError(
                    f"Step '{step.step_id}' (cross-modal-specialist) requires at least 2 images, "
                    f"but manifest only has {manifest.image_count}."
                )
            if not manifest.is_cross_modal:
                modalities = [img.modality.modality.value for img in manifest.images]
                if len(set(modalities)) < 2:
                    raise ValueError(
                        f"Step '{step.step_id}' (cross-modal-specialist) requires differing modalities "
                        f"(Optical and SAR), but found: {modalities}"
                    )

        # 6. Image index bounds check
        if step.image_index is not None:
            if step.image_index < 0 or step.image_index >= manifest.image_count:
                raise ValueError(
                    f"Step '{step.step_id}' references out-of-bounds image index: {step.image_index} "
                    f"(valid indices: 0 to {max(0, manifest.image_count - 1)})."
                )

            # 7. Modality constraints check
            img = manifest.images[step.image_index]
            img_modality = img.modality.modality

            # Optical tools/models applied to SAR
            optical_only_tools = {
                "ben-scene-classifier",
                "rsvqa-specialist",
                "vrsbench-caption",
                "vrsbench-grounding",
                "ndvi-calculator",
                "geochat-vqa",
                "geochat-caption",
                "geochat-grounding",
            }
            if step.tool_id in optical_only_tools and img_modality == ModalityEnum.SAR:
                raise ValueError(
                    f"Step '{step.step_id}' attempts to use optical tool/model '{step.tool_id}' "
                    f"on a SAR image (Image {step.image_index}). Optical tools cannot process microwave backscatter."
                )

            # SAR-only tools applied to Optical
            sar_only_tools = {"sar-stats"}
            if step.tool_id in sar_only_tools and img_modality in (
                ModalityEnum.OPTICAL_RGB,
                ModalityEnum.OPTICAL_MULTISPECTRAL,
            ):
                raise ValueError(
                    f"Step '{step.step_id}' attempts to use SAR tool '{step.tool_id}' "
                    f"on an optical image (Image {step.image_index})."
                )

        step_ids.add(step.step_id)

    return plan
