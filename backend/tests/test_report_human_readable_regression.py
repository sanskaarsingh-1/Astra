"""
Regression test for Human-Readable Astra AI Investigation Report Rebuild.
Tests the exact regression case specified in the prompt:
- Query: "What is the dominant land cover in this image?"
- Raster: 35a9aa4c-3a08-4186-acaa-1470a86e594a.tif
- Checks for elimination of raw Python dict dumps, display of prediction graph,
  image preview rendering, metadata tables, and conditional hiding of irrelevant sections.
"""

import pytest
from datetime import datetime, timezone
from orchestrator.schemas import (
    EvidencePackage, EvidenceFinding, FindingType, EvidenceStrength,
    ConfidenceStatus, ExecutionTrace, ExecutedStep, StepStatus,
    InvestigationPlan, PlanStep, InputManifest, ImageManifest,
    ModalityResult, ModalityEnum
)
from report.synthesizer import synthesize_report
from report.exporter import export_markdown_report, export_html_report


@pytest.mark.asyncio
async def test_human_readable_report_regression_actual_case():
    query = "What is the dominant land cover in this image?"
    job_id = "dfb1a6d6-c0c9-4117-93e1-38708b28ea3d"

    manifest = InputManifest(
        query=query,
        images=[
            ImageManifest(
                file_id="img_0",
                filename="35a9aa4c-3a08-4186-acaa-1470a86e594a.tif",
                file_path=f"backend/uploads/{job_id}/35a9aa4c-3a08-4186-acaa-1470a86e594a.tif",
                format="GeoTIFF",
                width_px=120,
                height_px=120,
                band_count=3,
                dtype="uint16",
                crs_epsg=32633,
                is_geospatial=True,
                modality=ModalityResult(
                    modality=ModalityEnum.OPTICAL_RGB,
                    confidence=0.99,
                    evidence=["RGB bands present"],
                ),
            )
        ]
    )

    plan = InvestigationPlan(
        plan_id="plan_actual_case",
        query=query,
        task_classification="single_image_classification",
        plan_rationale="Single-scene land cover classification",
        steps=[
            PlanStep(step_id="step_1", tool_id="raster-metadata", task_type="metadata", description="Validate image metadata"),
            PlanStep(step_id="step_2", tool_id="ben-scene-classifier", task_type="scene_classification", description="Execute scene classification"),
        ]
    )

    raster_stats_val = {
        "filename": "35a9aa4c-3a08-4186-acaa-1470a86e594a.tif",
        "width": 120,
        "height": 120,
        "bands": 3,
        "dtype": "uint16",
        "crs": "EPSG:32633",
        "gsd": [10.0, 10.0],
        "bounds": [439800.0, 6088800.0, 441000.0, 6090000.0],
        "has_spatial_ref": True,
        "nodata": 0,
        "modality": "OPTICAL_RGB",
    }

    classification_val = {
        "labels": [
            "Beaches, dunes, sands",
            "Water bodies",
            "Coniferous forest",
            "Mixed forest",
            "Sclerophyllous vegetation"
        ],
        "top_predictions": [
            {"label": "Beaches, dunes, sands", "probability": 0.9377},
            {"label": "Water bodies", "probability": 0.5327},
            {"label": "Coniferous forest", "probability": 0.5204},
            {"label": "Mixed forest", "probability": 0.3865},
            {"label": "Sclerophyllous vegetation", "probability": 0.3183},
        ]
    }

    f1 = EvidenceFinding(
        finding_id="f_meta",
        type=FindingType.RASTER_STATS,
        value=raster_stats_val,
        source_model="raster-metadata",
        strength=EvidenceStrength(
            model_confidence=1.0,
            confidence_status=ConfidenceStatus.DETERMINISTIC,
            evidence_strength="GROUND_TRUTH_DETERMINISTIC"
        ),
        provenance="Extracted from GeoTIFF header",
    )

    f2 = EvidenceFinding(
        finding_id="f_class",
        type=FindingType.CLASSIFICATION,
        value=classification_val,
        source_model="ben-scene-classifier",
        strength=EvidenceStrength(
            model_confidence=0.9377,
            confidence_status=ConfidenceStatus.CALIBRATED_PROBABILITY,
            evidence_strength="Strong"
        ),
        provenance="Inference from BigEarthNet ResNet-50",
    )

    trace = ExecutionTrace(
        trace_id="tr_1",
        timestamp_start=datetime.now(timezone.utc),
        plan=plan,
        executed_steps=[
            ExecutedStep(
                step_id="step_1",
                tool_id="raster-metadata",
                status=StepStatus.SUCCESS,
                input_summary="35a9aa4c-3a08-4186-acaa-1470a86e594a.tif",
                output_summary="Raster telemetry extracted (120x120, EPSG:32633)",
                duration_ms=7,
            ),
            ExecutedStep(
                step_id="step_2",
                tool_id="ben-scene-classifier",
                status=StepStatus.SUCCESS,
                input_summary="Optical RGB tensor (120x120)",
                output_summary="Classified: Beaches, dunes, sands (93.77%)",
                duration_ms=1173,
            ),
        ],
        steps_planned=2,
        steps_executed=2,
        steps_succeeded=2,
        steps_failed=0,
    )

    evidence = EvidencePackage(
        request_id="req_test",
        query=query,
        findings=[f1, f2],
        overall_confidence=0.938,
        models_used=["ben-scene-classifier"],
        tools_used=["raster-metadata"],
        total_inference_time_ms=1180,
        trace=trace,
    )

    # 1. Test Report Synthesis
    report = await synthesize_report(query, evidence, plan, manifest)

    # Assert no raw python dict strings leaked into narrative or executive summary
    assert "{'filename':" not in report.executive_summary
    assert "{'labels':" not in report.executive_summary
    assert "{'top_predictions':" not in report.executive_summary
    assert "{'filename':" not in report.narrative
    assert "{'labels':" not in report.narrative

    # Assert dominant predicted class and probability lead the executive finding
    assert "Beaches, dunes, sands" in report.executive_summary
    assert "93.77%" in report.executive_summary
    assert "Water bodies" in report.executive_summary
    assert "53.27%" in report.executive_summary

    # Assert fallback synthesis is clearly reported when unconfigured
    assert "[FALLBACK SYNTHESIS]" in report.executive_summary
    assert any("FALLBACK SYNTHESIS" in lim for lim in report.limitations)

    # 2. Test Markdown Export
    md = export_markdown_report(report, evidence, job_id)
    assert "{'filename':" not in md
    assert "{'top_predictions':" not in md
    assert "Beaches, dunes, sands" in md
    assert "93.77%" in md
    assert "Model Prediction Probabilities" in md
    assert "EPSG:32633" in md
    assert "120 × 120 px" in md
    assert "Key Findings Summary" in md
    assert "Image & Spatial Metadata" in md

    # Assert single-image hides irrelevant sections (Temporal, SAR)
    assert "## Temporal Analysis & Change Findings" not in md
    assert "## SAR Microwave Evidence" not in md

    # Assert benchmark performance metrics are distinct and present
    assert "Val Acc: 91.79%" in md
    assert "Macro F1: 0.7038" in md

    # 3. Test HTML Export
    html = export_html_report(report, evidence, job_id)
    assert "{'filename':" not in html
    assert "{'top_predictions':" not in html
    assert "Beaches, dunes, sands" in html
    assert "93.77%" in html
    assert "data:image/png;base64," in html
    assert "Visualization of analyzed raster" in html
    assert "EPSG:32633" in html
    assert "10.0m × 10.0m" in html or "10 m × 10 m" in html
    assert "Model Prediction Probabilities" in html
    assert "Specialist Model Confidence" in html
    assert "Temporal Analysis" not in html
    assert "SAR Microwave Evidence" not in html
