"""
Evidence Layer — Evidence Assembler & Conflict Engine
Validates execution results, computes calibrated confidence, detects multi-source
physical conflicts (Optical vs. SAR), and builds the complete EvidencePackage and ExecutionTrace.
"""

import uuid
from datetime import datetime, timezone
from typing import Any
from loguru import logger

from config import settings
from orchestrator.schemas import (
    ExecutedStep, StepStatus, InputManifest, InvestigationPlan,
    EvidenceFinding, FindingType, EvidencePackage, ExecutionTrace,
    ConflictRecord, EvidenceStrength, ConfidenceStatus
)


DETERMINISTIC_TOOLS = {
    "area-calculator",
    "mask-area",
    "bbox-area-calculator",
    "bbox-area",
    "polygon-area-calculator",
    "polygon-area",
    "geodesic-distance-calculator",
    "geodesic-distance",
    "raster-metadata",
    "raster-stats",
    "sar-stats",
    "ndvi-calculator",
    "change-area",
}


def assemble_evidence(
    executed_steps: list[ExecutedStep],
    manifest: InputManifest,
    plan: InvestigationPlan | None = None,
) -> EvidencePackage:
    """
    Convert raw execution step outputs into a structured, validated EvidencePackage
    with calibrated confidence scoring, physical conflict detection, and execution trace.
    """
    all_quality_flags: list[str] = []
    for img in manifest.images:
        all_quality_flags.extend(img.quality_flags)

    findings: list[EvidenceFinding] = []
    models_used: list[str] = []
    tools_used: list[str] = []
    total_inference_ms = 0
    coverage_gaps: list[str] = []

    for step in executed_steps:
        total_inference_ms += step.duration_ms or 0

        if step.status != StepStatus.SUCCESS or step.raw_output is None:
            err = step.error_message or "Execution failed or timed out"
            clean_reason = f"Runtime module import failure ({err})" if "No module named" in err else err
            coverage_gaps.append(
                f"{step.tool_id} execution failed or timed out: {clean_reason}"
            )
            # Phase 15: Failed specialist must explicitly appear as FAILED / UNAVAILABLE with 0 confidence
            failed_finding = EvidenceFinding(
                finding_id=str(uuid.uuid4()),
                type=FindingType.TEXT,
                value=f"SPECIALIST STATUS: FAILED / UNAVAILABLE (Reason: {clean_reason})",
                source_model=step.tool_id,
                strength=EvidenceStrength(
                    model_confidence=0.0,
                    data_quality="Unavailable",
                    spatial_consistency="Unverified",
                    evidence_strength="Failed",
                    confidence_status=ConfidenceStatus.UNVERIFIED,
                ),
                visual_evidence=None,
                provenance=(
                    f"Specialist {step.tool_id} failed | Execution Time: {step.duration_ms or 0}ms | "
                    f"Status: {step.status.value.upper()} | Confidence Status: {ConfidenceStatus.UNVERIFIED.value}"
                ),
                source_step_id=step.step_id,
            )
            findings.append(failed_finding)
            continue

        finding = _step_to_finding(step)
        if finding:
            findings.append(finding)

        from orchestrator.registry import is_model
        if is_model(step.tool_id):
            models_used.append(step.tool_id)
        else:
            tools_used.append(step.tool_id)

    conflicts = _detect_conflicts(findings, manifest)
    overall_confidence = _compute_overall_confidence(findings, executed_steps, conflicts)
    trace = _build_trace(executed_steps, manifest, plan)

    return EvidencePackage(
        request_id=str(uuid.uuid4()),
        query=manifest.query,
        findings=findings,
        conflicts=conflicts,
        overall_confidence=overall_confidence,
        data_quality_flags=list(set(all_quality_flags)),
        coverage_gaps=coverage_gaps,
        models_used=list(set(models_used)),
        tools_used=list(set(tools_used)),
        total_inference_time_ms=total_inference_ms,
        trace=trace,
    )


def _step_to_finding(step: ExecutedStep) -> EvidenceFinding | None:
    raw = step.raw_output
    if not isinstance(raw, dict):
        return None

    out_type = raw.get("type", "text")
    finding_type = _map_output_type(out_type)

    visual = raw.get("visual_evidence") or raw.get("overlay_image_base64")

    # Determine confidence status and calibrated value
    if step.tool_id in DETERMINISTIC_TOOLS or out_type in ("measurement", "raster_stats", "metadata"):
        status = ConfidenceStatus.DETERMINISTIC
        strength_desc = "GROUND_TRUTH_DETERMINISTIC"
        conf = 1.0
    else:
        status = ConfidenceStatus.CALIBRATED_PROBABILITY
        conf = raw.get("confidence") or step.confidence or 0.75
        # Clamp to [0.05, 0.99] for ML probabilities
        conf = round(max(0.05, min(0.99, float(conf))), 3)
        strength_desc = "Strong" if conf >= 0.8 else ("Moderate" if conf >= 0.55 else "Low")

    strength = EvidenceStrength(
        model_confidence=conf,
        data_quality="High" if conf >= 0.8 else "Medium",
        spatial_consistency="Verified" if step.status == StepStatus.SUCCESS else "Unverified",
        evidence_strength=strength_desc,
        confidence_status=status,
    )

    provenance = (
        f"Generated by {step.tool_id} | "
        f"Execution Time: {step.duration_ms or 0}ms | "
        f"Status: {step.status.value} | "
        f"Confidence Status: {status.value}"
    )

    return EvidenceFinding(
        finding_id=str(uuid.uuid4()),
        type=finding_type,
        value=_extract_primary_value(raw),
        source_model=step.tool_id,
        strength=strength,
        visual_evidence=visual,
        provenance=provenance,
        source_step_id=step.step_id,
    )


def _map_output_type(out_type: str) -> FindingType:
    mapping = {
        "text": FindingType.TEXT,
        "measurement": FindingType.MEASUREMENT,
        "classification": FindingType.CLASSIFICATION,
        "change_mask": FindingType.CHANGE_MAP,
        "bbox": FindingType.BBOX,
        "detection": FindingType.BBOX,
        "mask": FindingType.MASK,
        "raster_stats": FindingType.RASTER_STATS,
        "metadata": FindingType.RASTER_STATS,
        "visualization": FindingType.MASK,
    }
    return mapping.get(out_type, FindingType.TEXT)


def _extract_primary_value(raw: dict) -> Any:
    if not isinstance(raw, dict):
        return raw

    out_type = raw.get("type")

    # Text-based answers (VQA, caption, narrative)
    if "text" in raw and raw["text"]:
        return raw["text"]
    if "answer" in raw and raw["answer"]:
        return raw["answer"]
    if "caption" in raw and raw["caption"]:
        return raw["caption"]
    if out_type == "text":
        return raw.get("text", "")

    # Classification
    if out_type == "classification" or "top_predictions" in raw:
        return {
            "dominant_class": raw.get("prediction") or raw.get("dominant_class") or (raw.get("top_predictions", [{}])[0].get("label", "Unknown")),
            "confidence": raw.get("confidence", 0.0),
            "labels": raw.get("labels", []),
            "top_predictions": raw.get("top_predictions", []),
            "all_probabilities": raw.get("all_probabilities", {}),
        }

    # Change Detection
    if out_type == "change_map" or "changed_pixels" in raw:
        return {
            "changed": raw.get("changed", False),
            "change_percentage": raw.get("change_percentage", 0.0),
            "changed_pixels": raw.get("changed_pixels", 0),
            "total_pixels": raw.get("total_pixels", 0),
            "area_m2": raw.get("area_m2", 0.0),
            "area_ha": raw.get("area_ha", 0.0),
            "regions_count": raw.get("regions_count", 0),
            "method": raw.get("method", "BIT"),
            "specialist_status": raw.get("specialist_status", "SUCCESS"),
            "fallback_used": raw.get("fallback_used", False),
            "fallback_reason": raw.get("fallback_reason", ""),
        }

    # Bounding Box / Detection
    if out_type in ("bbox", "detection") or "boxes" in raw:
        return {
            "boxes": raw.get("boxes", raw.get("bboxes", [])),
            "detections_count": raw.get("detections_count", len(raw.get("boxes", []))),
            "text_reference": raw.get("text_reference", ""),
        }

    # Raster Metadata / Stats
    if out_type in ("raster_stats", "metadata") or "crs" in raw or "width" in raw:
        return {k: v for k, v in raw.items() if k not in ("type", "confidence")}

    # Measurement
    if out_type == "measurement":
        return {k: v for k, v in raw.items() if k not in ("type", "confidence", "model")}

    # Synthesis / Narrative
    if "synthesis" in raw and isinstance(raw["synthesis"], str):
        return raw["synthesis"]

    return raw


def _detect_conflicts(findings: list[EvidenceFinding], manifest: InputManifest) -> list[ConflictRecord]:
    """
    Detects logical and physical discrepancies between multi-specialist evidence.
    Covers:
    1. Direct conflict signals emitted by cross-modal analysis
    2. Optical LULC vs. SAR backscatter physical contradictions (e.g. water vs. high backscatter)
    3. Contradictory text responses from multiple VQA specialists
    """
    conflicts: list[ConflictRecord] = []

    # 1. Cross-modal specialist conflicts
    for f in findings:
        if f.source_model in ("cross-modal-specialist", "cross-modal-fusion"):
            val = f.value
            if isinstance(val, dict):
                cm_conflicts = val.get("conflicts", val.get("potential_conflicts", []))
                for c_item in cm_conflicts:
                    conflicts.append(
                        ConflictRecord(
                            finding_ids=[f.finding_id],
                            description=c_item if isinstance(c_item, str) else str(c_item),
                            impact="High",
                        )
                    )

    # 2. Physical Cross-Modal Contradiction: Optical LULC vs. SAR Backscatter
    lulc_findings = [f for f in findings if f.source_model == "ben-scene-classifier"]
    sar_findings = [f for f in findings if f.source_model in ("sar-stats", "cross-modal-specialist")]

    if lulc_findings and sar_findings:
        lulc_val = lulc_findings[0].value
        top_labels = []
        if isinstance(lulc_val, dict):
            top_labels = [l.lower() for l in lulc_val.get("labels", [])]

        sar_val = sar_findings[0].value
        mean_db = None
        double_bounce = False
        specular = False
        if isinstance(sar_val, dict):
            if "sar_evidence" in sar_val:
                db_stats = sar_val["sar_evidence"].get("backscatter_db", {})
                mean_db = db_stats.get("mean_dB")
                double_bounce = sar_val["sar_evidence"].get("double_bounce_urban_structures", False)
                specular = sar_val["sar_evidence"].get("specular_reflection_water", False)
            elif "calibrated_db" in sar_val:
                mean_db = sar_val["calibrated_db"].get("mean_db")

        # Conflict 2A: Optical says water, but SAR backscatter shows double-bounce / high roughness
        water_indicated = any("water" in lbl for lbl in top_labels)
        if water_indicated and ((mean_db is not None and mean_db > -11.0) or double_bounce):
            conflicts.append(
                ConflictRecord(
                    finding_ids=[lulc_findings[0].finding_id, sar_findings[0].finding_id],
                    description=(
                        "Physical Conflict: Optical reflectance indicates Water Bodies, "
                        f"but SAR microwave backscatter is elevated ({mean_db} dB / double-bounce), "
                        "indicating rough surface structures rather than specular water reflection."
                    ),
                    impact="High",
                )
            )

        # Conflict 2B: Optical says urban, but SAR shows specular reflection
        urban_indicated = any("urban" in lbl or "industrial" in lbl for lbl in top_labels)
        if urban_indicated and (specular or (mean_db is not None and mean_db < -22.0)):
            conflicts.append(
                ConflictRecord(
                    finding_ids=[lulc_findings[0].finding_id, sar_findings[0].finding_id],
                    description=(
                        "Physical Conflict: Optical classification indicates Urban Fabric, "
                        f"but SAR backscatter is strongly attenuated ({mean_db} dB), "
                        "exhibiting specular reflection characteristic of flat asphalt, calm water, or runway."
                    ),
                    impact="Medium",
                )
            )

    return conflicts


def _compute_overall_confidence(
    findings: list[EvidenceFinding],
    executed_steps: list[ExecutedStep],
    conflicts: list[ConflictRecord],
) -> float:
    """
    Computes an aggregate, calibrated confidence score across all executed steps.
    Applies penalties for failed steps and detected physical conflicts.
    """
    conf_values = [
        f.strength.model_confidence
        for f in findings
        if f.strength and f.strength.model_confidence is not None
    ]
    if not conf_values:
        return 0.4

    avg = sum(conf_values) / len(conf_values)

    failed = sum(1 for s in executed_steps if s.status == StepStatus.FAILED)
    total = len(executed_steps)
    failure_penalty = (failed / total) * 0.25 if total > 0 else 0.0

    # Conflict penalty: each high-impact conflict docks 0.08, medium docks 0.04
    conflict_penalty = 0.0
    for c in conflicts:
        if c.impact == "High":
            conflict_penalty += 0.08
        else:
            conflict_penalty += 0.04

    calibrated = avg - failure_penalty - conflict_penalty
    return round(max(0.1, min(1.0, calibrated)), 3)


def _build_trace(
    executed_steps: list[ExecutedStep],
    manifest: InputManifest,
    plan: InvestigationPlan | None = None,
) -> ExecutionTrace:
    """
    Builds a sanitized, user-observable execution trace.
    Ensures no private chain-of-thought, internal prompt artifacts,
    or sensitive server details leak into the trace.
    """
    from orchestrator.schemas import InvestigationPlan, PlanStep

    used_plan = plan
    if not used_plan:
        used_plan = InvestigationPlan(
            plan_id="assembled-from-trace",
            query=manifest.query,
            task_classification="composite",
            plan_rationale="Assembled directly from executed pipeline steps.",
            steps=[
                PlanStep(
                    step_id=s.step_id,
                    tool_id=s.tool_id,
                    task_type=s.tool_id,
                    description=s.input_summary,
                )
                for s in executed_steps
            ],
        )

    now = datetime.now(timezone.utc)
    start_times = [s.started_at for s in executed_steps if s.started_at]
    end_times = [s.completed_at for s in executed_steps if s.completed_at]

    # Sanitize each step summary to prevent prompt leaking
    sanitized_steps = []
    for s in executed_steps:
        clean_step = s.model_copy()
        if clean_step.input_summary:
            # Strip prompt markers if any
            clean_step.input_summary = clean_step.input_summary.split("System:")[0].split("Human:")[0].strip()
        sanitized_steps.append(clean_step)

    return ExecutionTrace(
        trace_id=str(uuid.uuid4()),
        timestamp_start=min(start_times) if start_times else now,
        timestamp_end=max(end_times) if end_times else now,
        plan=used_plan,
        executed_steps=sanitized_steps,
        steps_planned=len(used_plan.steps),
        steps_executed=len(sanitized_steps),
        steps_succeeded=sum(1 for s in sanitized_steps if s.status == StepStatus.SUCCESS),
        steps_failed=sum(1 for s in sanitized_steps if s.status == StepStatus.FAILED),
    )
