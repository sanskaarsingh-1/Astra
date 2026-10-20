"""
End-to-End Integration & System Verification Tests (Phases 09 through 17)
Tests:
- POST /api/validate (format, size, GeoTIFF spatial tags, bitemporal compatibility)
- End-to-end investigation execution pipeline (_run_investigation) across multiple tasks:
  1. Single-image optical VQA & LULC scene classification
  2. Bi-temporal change detection with Siamese BIT and area quantification
  3. Optical + SAR cross-modal synthesis with physical conflict detection
- Report download endpoint (GET /api/report/{job_id}/download as Markdown and HTML)
- ISRO sensor evaluation robustness (Cartosat-2S PAN & RISAT-1A SAR)
"""

import pytest
import asyncio
import io
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_origin
from starlette.testclient import TestClient

from backend.main import app, _run_investigation, _investigation_store
from backend.orchestrator.schemas import (
    ImageManifest, ModalityEnum, ModalityResult, InputManifest
)
from backend.gateway.modality import detect_modality


@pytest.fixture
def sample_geotiff(tmp_path):
    """Create a minimal valid GeoTIFF in EPSG:3857."""
    p = tmp_path / "sample_georeferenced.tif"
    data = np.full((3, 64, 64), fill_value=128, dtype=np.uint8)
    transform = from_origin(100000.0, 200000.0, 10.0, 10.0)
    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=3,
        dtype="uint8",
        crs="EPSG:3857",
        transform=transform,
    ) as dst:
        dst.write(data)
    return p


@pytest.fixture
def sample_sar_geotiff(tmp_path):
    """Create a minimal valid SAR GeoTIFF in EPSG:3857."""
    p = tmp_path / "sample_sar.tif"
    data = np.full((2, 64, 64), fill_value=25, dtype=np.uint8)
    transform = from_origin(100000.0, 200000.0, 10.0, 10.0)
    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=2,
        dtype="uint8",
        crs="EPSG:3857",
        transform=transform,
    ) as dst:
        dst.write(data)
    return p


# ─── 1. Validation Endpoint Tests (Phase 09) ──────────────────────────────────

def test_validate_endpoint_valid_geotiff(sample_geotiff):
    """Test POST /api/validate on a valid GeoTIFF."""
    client = TestClient(app)
    with open(sample_geotiff, "rb") as f:
        resp = client.post(
            "/api/validate",
            files={"files": ("sample.tif", f, "image/tiff")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert len(data["manifests"]) == 1
    assert data["manifests"][0]["is_geospatial"] is True
    assert data["manifests"][0]["crs_epsg"] == 3857
    assert data["manifests"][0]["gsd_x"] == 10.0


def test_validate_endpoint_bitemporal_compatibility(sample_geotiff):
    """Test POST /api/validate on two identical images (100% overlap)."""
    client = TestClient(app)
    with open(sample_geotiff, "rb") as f1, open(sample_geotiff, "rb") as f2:
        resp = client.post(
            "/api/validate",
            files=[
                ("files", ("t1.tif", f1, "image/tiff")),
                ("files", ("t2.tif", f2, "image/tiff")),
            ],
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["compatibility"] is not None
    assert data["compatibility"]["is_compatible"] is True
    assert data["compatibility"]["overlap_percentage"] == 100.0


def test_validate_endpoint_invalid_extension():
    """Test POST /api/validate rejects forbidden file types."""
    client = TestClient(app)
    fake_txt = io.BytesIO(b"Hello remote sensing")
    resp = client.post(
        "/api/validate",
        files={"files": ("report.txt", fake_txt, "text/plain")},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["is_valid"] is False
    assert any("unsupported extension" in err for err in data["errors"])


def test_validate_endpoint_empty_file():
    """Test POST /api/validate rejects 0-byte files."""
    client = TestClient(app)
    empty_file = io.BytesIO(b"")
    resp = client.post(
        "/api/validate",
        files={"files": ("empty.tif", empty_file, "image/tiff")},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["is_valid"] is False
    assert any("is empty" in err for err in data["errors"])


# ─── 2. End-to-End Investigation Pipeline Tests (Phases 10-14) ────────────────

@pytest.mark.asyncio
async def test_e2e_investigation_single_optical_vqa(sample_geotiff):
    """Test full investigation workflow for single-image optical VQA."""
    queue = asyncio.Queue()
    job_id = "test-job-optical-vqa-01"
    
    await _run_investigation(
        job_id=job_id,
        query="What land cover features are present in this scene?",
        file_paths=[sample_geotiff],
        queue=queue,
    )

    # Drain events
    events = []
    while not queue.empty():
        events.append(await queue.get())

    assert len(events) >= 5
    complete_events = [e for e in events if e.get("event") == "complete"]
    assert len(complete_events) == 1

    # Verify report is stored in _investigation_store
    assert job_id in _investigation_store
    report, evidence, query = _investigation_store[job_id]
    assert report.narrative is not None
    assert len(evidence.findings) >= 1
    assert evidence.trace.steps_executed >= 2
    assert evidence.trace.steps_succeeded >= 2


@pytest.mark.asyncio
async def test_e2e_investigation_bitemporal_change(sample_geotiff):
    """Test full investigation workflow for bi-temporal change detection."""
    queue = asyncio.Queue()
    job_id = "test-job-bitemporal-01"

    await _run_investigation(
        job_id=job_id,
        query="Detect and quantify what changed between these two dates.",
        file_paths=[sample_geotiff, sample_geotiff],
        queue=queue,
    )

    events = []
    while not queue.empty():
        events.append(await queue.get())

    complete_events = [e for e in events if e.get("event") == "complete"]
    assert len(complete_events) == 1

    assert job_id in _investigation_store
    report, evidence, query = _investigation_store[job_id]
    # Check that change-detection or change-area was executed
    tool_names = [s.tool_id for s in evidence.trace.executed_steps]
    assert "bit-change-detection" in tool_names or "change-area" in tool_names


@pytest.mark.asyncio
async def test_e2e_investigation_cross_modal(sample_geotiff, sample_sar_geotiff):
    """Test full investigation workflow for Optical + SAR cross-modal fusion."""
    queue = asyncio.Queue()
    job_id = "test-job-cross-modal-01"

    await _run_investigation(
        job_id=job_id,
        query="Perform cross-modal analysis fusing optical reflectance and radar backscatter.",
        file_paths=[sample_geotiff, sample_sar_geotiff],
        queue=queue,
    )

    events = []
    while not queue.empty():
        events.append(await queue.get())

    complete_events = [e for e in events if e.get("event") == "complete"]
    assert len(complete_events) == 1

    assert job_id in _investigation_store
    report, evidence, query = _investigation_store[job_id]
    tool_names = [s.tool_id for s in evidence.trace.executed_steps]
    assert "cross-modal-specialist" in tool_names


# ─── 3. Report Exporter & Download Endpoint Tests (Phase 17) ──────────────────

@pytest.mark.asyncio
async def test_report_download_markdown(sample_geotiff):
    """Test GET /api/report/{job_id}/download?format=markdown."""
    queue = asyncio.Queue()
    job_id = "test-job-report-md"

    await _run_investigation(
        job_id=job_id,
        query="Analyze vegetation and land cover",
        file_paths=[sample_geotiff],
        queue=queue,
    )

    client = TestClient(app)
    resp = client.get(f"/api/report/{job_id}/download?format=markdown")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    text = resp.text
    assert "# Astra AI — Geospatial Investigation Report" in text
    assert job_id in text
    assert "## 1. Executive Summary" in text
    assert "## 7. Verified Findings Provenance" in text
    assert "## Appendix: Auditable Execution Trace" in text


@pytest.mark.asyncio
async def test_report_download_html(sample_geotiff):
    """Test GET /api/report/{job_id}/download?format=html."""
    queue = asyncio.Queue()
    job_id = "test-job-report-html"

    await _run_investigation(
        job_id=job_id,
        query="Analyze urban development",
        file_paths=[sample_geotiff],
        queue=queue,
    )

    client = TestClient(app)
    resp = client.get(f"/api/report/{job_id}/download?format=html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "<!DOCTYPE html>" in resp.text
    assert "Astra AI Investigation Report" in resp.text


# ─── 4. ISRO Evaluation Robustness (Phase 16) ──────────────────────────────────

def test_isro_cartosat_and_risat_sensor_robustness(tmp_path):
    """
    Simulate ISRO Cartosat-2S PAN (high-res panchromatic) and RISAT-1A / EOS-04 SAR
    imagery to verify robust modality classification and zero pipeline exceptions.
    """
    from backend.gateway.metadata import extract_metadata

    # 1. Simulate Cartosat-2S Panchromatic (Single band, 8-bit or 16-bit)
    cartosat_path = tmp_path / "CARTOSAT_2S_PAN_2024.tif"
    data_pan = np.full((1, 128, 128), fill_value=140, dtype=np.uint8)
    with rasterio.open(
        cartosat_path,
        "w",
        driver="GTiff",
        height=128,
        width=128,
        count=1,
        dtype="uint8",
    ) as dst:
        dst.write(data_pan)

    manifest_pan = extract_metadata(cartosat_path)
    assert manifest_pan.modality.modality in [ModalityEnum.PANCHROMATIC, ModalityEnum.OPTICAL_RGB]
    assert manifest_pan.modality.confidence >= 0.8

    # 2. Simulate RISAT-1A (EOS-04) Dual-Pol C-Band SAR
    risat_path = tmp_path / "RISAT_1A_FRS_RH_RV.tif"
    data_sar = np.full((2, 128, 128), fill_value=30, dtype=np.uint8)
    with rasterio.open(
        risat_path,
        "w",
        driver="GTiff",
        height=128,
        width=128,
        count=2,
        dtype="uint8",
    ) as dst:
        dst.write(data_sar)

    manifest_sar = extract_metadata(risat_path)
    assert manifest_sar.modality.modality == ModalityEnum.SAR
    assert manifest_sar.modality.confidence >= 0.85
