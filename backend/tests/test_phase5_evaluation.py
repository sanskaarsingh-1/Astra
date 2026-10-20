"""
Phase 5 Comprehensive Evaluation & Demonstration Test Suite
SatQuery AI / Astra AI — SIH26167 | Space Technology (ISRO SAC)

Validates:
1. Evaluation manifest structure and integrity
2. Representative Cartosat/RISAT test datasets (CRS, affine, tags)
3. Offline evaluation CLI execution (single, bi-temporal, cross-modal)
4. Graceful fail-safe handling on corrupted rasters
5. Publication-grade HTML/Markdown report generation
6. Download report API endpoint contract
"""

import os
import json
import pytest
import rasterio
from pathlib import Path
from starlette.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT_DIR / "evaluation"
TEST_DATA_DIR = EVAL_DIR / "test_data"
MANIFEST_PATH = EVAL_DIR / "evaluation_manifest.json"

from backend.main import app, _investigation_store
from backend.report.exporter import export_markdown_report, export_html_report
from backend.orchestrator.schemas import Report, EvidencePackage, EvidenceFinding, FindingType, StepStatus
from evaluation.run_eval import evaluate_single_case


def test_manifest_schema_and_integrity():
    """Verify that evaluation_manifest.json exists and adheres to the evaluation specification."""
    assert MANIFEST_PATH.exists(), f"Manifest missing at {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("sih_problem") == "SIH26167"
    assert "cases" in data
    cases = data["cases"]
    assert len(cases) >= 10

    required_fields = ["case_id", "inputs", "modality", "temporal_relationship", "query", "expected_capability", "evaluation_notes"]
    case_ids = set()
    for c in cases:
        for f in required_fields:
            assert f in c, f"Case {c.get('case_id')} missing required field: {f}"
        assert c["case_id"] not in case_ids, f"Duplicate case ID: {c['case_id']}"
        case_ids.add(c["case_id"])
        assert len(c["inputs"]) > 0


def test_representative_test_datasets_integrity():
    """Verify representative Cartosat and RISAT test datasets exist with valid CRS and metadata tags."""
    expected_files = [
        "representative_cartosat_optical.tif",
        "representative_risat_sar.tif",
        "representative_bitemporal_t1.tif",
        "representative_bitemporal_t2.tif",
        "representative_large_scene.tif",
        "corrupted_sample.tif",
    ]
    for filename in expected_files:
        path = TEST_DATA_DIR / filename
        assert path.exists(), f"Representative test file missing: {path}"

    # Verify optical CRS and dimensions
    opt_path = TEST_DATA_DIR / "representative_cartosat_optical.tif"
    with rasterio.open(opt_path) as src:
        assert src.width == 512
        assert src.height == 512
        assert src.count == 3
        assert src.crs is not None
        assert "32643" in str(src.crs)
        tags = src.tags()
        assert tags.get("DATASET_ROLE") == "REPRESENTATIVE TEST DATA"

    # Verify SAR CRS and dimensions
    sar_path = TEST_DATA_DIR / "representative_risat_sar.tif"
    with rasterio.open(sar_path) as src:
        assert src.width == 512
        assert src.height == 512
        assert src.count == 1
        assert "32643" in str(src.crs)


@pytest.mark.asyncio
async def test_offline_eval_cli_single_optical(tmp_path):
    """Test evaluate_single_case on representative optical imagery."""
    opt_file = TEST_DATA_DIR / "representative_cartosat_optical.tif"
    res = await evaluate_single_case(
        case_id="TEST_OPTICAL",
        query="What type of land cover dominates this scene?",
        file_paths=[opt_file],
        output_dir=tmp_path,
        report_format="all",
    )
    assert res["status"] == "COMPLETED"
    assert "tools_invoked" in res
    assert "ben-scene-classifier" in res["tools_invoked"]
    assert (tmp_path / "TEST_OPTICAL_report.md").exists()
    assert (tmp_path / "TEST_OPTICAL_report.html").exists()
    assert (tmp_path / "TEST_OPTICAL_result.json").exists()


@pytest.mark.asyncio
async def test_offline_eval_cli_bitemporal_change(tmp_path):
    """Test evaluate_single_case on bi-temporal pair."""
    t1 = TEST_DATA_DIR / "representative_bitemporal_t1.tif"
    t2 = TEST_DATA_DIR / "representative_bitemporal_t2.tif"
    res = await evaluate_single_case(
        case_id="TEST_BITEMPORAL",
        query="What changed between these two dates?",
        file_paths=[t1, t2],
        output_dir=tmp_path,
        report_format="all",
    )
    assert res["status"] == "COMPLETED"
    assert "bit-change-detection" in res["tools_invoked"]
    assert "cdvqa-specialist" in res["tools_invoked"]


@pytest.mark.asyncio
async def test_offline_eval_cli_cross_modal(tmp_path):
    """Test evaluate_single_case on optical-SAR pair."""
    opt = TEST_DATA_DIR / "representative_cartosat_optical.tif"
    sar = TEST_DATA_DIR / "representative_risat_sar.tif"
    res = await evaluate_single_case(
        case_id="TEST_CROSS_MODAL",
        query="Compare optical and SAR observations for surface structures.",
        file_paths=[opt, sar],
        output_dir=tmp_path,
        report_format="all",
    )
    assert res["status"] == "COMPLETED"
    assert "cross-modal-specialist" in res["tools_invoked"]


@pytest.mark.asyncio
async def test_offline_eval_cli_corrupted_failsafe(tmp_path):
    """Test evaluate_single_case on corrupted raster handles error safely."""
    corrupt = TEST_DATA_DIR / "corrupted_sample.tif"
    res = await evaluate_single_case(
        case_id="TEST_CORRUPT",
        query="What is in this image?",
        file_paths=[corrupt],
        output_dir=tmp_path,
        report_format="all",
    )
    assert res["status"] == "ERROR"
    assert "error" in res
    assert "Unable to parse image data" in str(res["error"])


from datetime import datetime, timezone
from backend.orchestrator.schemas import (
    Report, EvidencePackage, EvidenceFinding, FindingType,
    StepStatus, ExecutedStep, ExecutionTrace, InvestigationPlan
)


def _make_mock_evidence(query: str = "Test query") -> EvidencePackage:
    step = ExecutedStep(
        step_id="step_1",
        tool_id="ben-scene-classifier",
        status=StepStatus.SUCCESS,
        input_summary="image.tif",
        output_summary="Coniferous forest: 89.0%",
        duration_ms=45,
    )
    plan = InvestigationPlan(
        plan_id="plan-1",
        query=query,
        task_classification="scene_classification",
        plan_rationale="Classify scene using ResNet-50",
        steps=[],
    )
    trace = ExecutionTrace(
        trace_id="tr-1",
        timestamp_start=datetime.now(timezone.utc),
        plan=plan,
        executed_steps=[step],
    )
    return EvidencePackage(
        request_id="req-123",
        query=query,
        overall_confidence="HIGH",
        findings=[
            EvidenceFinding(
                finding_id="f_001",
                type=FindingType.CLASSIFICATION,
                source_model="ben-scene-classifier",
                value="Coniferous forest (0.89)",
                provenance="Model inference benchmark",
            )
        ],
        models_used=["ben-scene-classifier", "bit-change-detection"],
        tools_used=["raster-metadata"],
        total_inference_time_ms=120,
        trace=trace,
    )


def test_html_report_formatting_and_print_styles():
    """Verify semantic HTML report generator includes required SIH headers, print styles, and separated metrics."""
    mock_report = Report(
        executive_summary="Simulated test summary.",
        narrative="Simulated test narrative.",
        spatial_findings="Terrain bounds verified.",
        methodology="Multi-specialist orchestration pipeline.",
        limitations=["Simulated test run."],
        assumptions=["Standard geometry."],
        confidence_summary="High confidence.",
    )
    mock_evidence = _make_mock_evidence("Test query")
    html_out = export_html_report(mock_report, mock_evidence, "job_test_123")

    assert "<!DOCTYPE html>" in html_out
    assert "SIH26167" in html_out
    assert "@media print" in html_out
    assert "window.print()" in html_out
    assert "<table>" in html_out
    assert "ben-scene-classifier" in html_out
    assert "bit-change-detection" in html_out
    assert "Val Acc: 91.79%" in html_out
    assert "OA: 96.98%" in html_out


def test_report_download_api_endpoints():
    """Verify GET /api/report/{job_id}/download serves markdown, html, and json formats correctly."""
    client = TestClient(app)
    test_job_id = "test_download_endpoint_job"

    # Seed mock report into _investigation_store
    mock_report = Report(
        executive_summary="API download test summary.",
        narrative="API download narrative.",
        methodology="Multi-specialist pipeline.",
        limitations=["Testing only."],
        confidence_summary="Deterministic test confidence.",
    )
    mock_evidence = _make_mock_evidence("Test download query")
    _investigation_store[test_job_id] = (mock_report, mock_evidence, "Test download query")

    # 1. Download Markdown
    res_md = client.get(f"/api/report/{test_job_id}/download?format=markdown")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    assert f"astra_report_{test_job_id}.md" in res_md.headers["content-disposition"]
    assert "# Astra AI" in res_md.text

    # 2. Download HTML
    res_html = client.get(f"/api/report/{test_job_id}/download?format=html")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert f"astra_report_{test_job_id}.html" in res_html.headers["content-disposition"]
    assert "<!DOCTYPE html>" in res_html.text

    # 3. Download JSON
    res_json = client.get(f"/api/report/{test_job_id}/download?format=json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    data = res_json.json()
    assert data["job_id"] == test_job_id
    assert "report" in data

    # 4. Non-existent job
    res_404 = client.get("/api/report/non_existent_job_xyz/download?format=markdown")
    assert res_404.status_code == 404

