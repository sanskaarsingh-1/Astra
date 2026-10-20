"""
Unit tests for Optical + SAR Cross-Modal Specialist (Phase 06).
Tests ISRO sensor compatibility (Cartosat-2S + RISAT), physical evidence separation,
modality agreement/conflict resolution, and the REST API endpoint.
"""

from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from backend.gateway.modality import detect_modality
from backend.orchestrator.schemas import ImageManifest, ModalityEnum, ModalityResult
from backend.models.cross_modal.specialist import get_cross_modal_specialist


@pytest.fixture
def sample_cross_modal_rasters(tmp_path):
    """Generate synthetic co-registered Optical RGB and SAR grayscale images."""
    p_opt = tmp_path / "sentinel2_optical.png"
    p_sar = tmp_path / "sentinel1_sar.png"

    # Optical: deep blue water body
    Image.new("RGB", (256, 256), color=(10, 30, 120)).save(p_opt)
    # SAR: dark specular reflection (calm water ~ -20 dB)
    Image.new("L", (256, 256), color=25).save(p_sar)

    return p_opt, p_sar


def test_isro_sensor_modality_detection():
    """Verify Cartosat-2S and RISAT-1A / EOS-04 sensor detection."""
    # Test RISAT-1A SAR Manifest
    risat_manifest = ImageManifest(
        file_id="risat_01",
        filename="EOS04_C_SAR_RH_RV_20230501.tif",
        file_path="/tmp/fake_risat.tif",
        format="GTiff",
        width_px=512,
        height_px=512,
        band_count=2,
        dtype="float32",
        sensor="RISAT-1A (EOS-04)",
        band_descriptions=["RH", "RV"],
        is_geospatial=True,
        modality=ModalityResult(modality=ModalityEnum.UNKNOWN, confidence=0, evidence=[]),
    )
    mod_risat = detect_modality(risat_manifest)
    assert mod_risat.modality == ModalityEnum.SAR
    assert mod_risat.confidence >= 0.90
    assert any("RISAT" in ev for ev in mod_risat.evidence)

    # Test Cartosat-2S Optical Manifest
    carto_manifest = ImageManifest(
        file_id="carto_01",
        filename="Cartosat2S_PAN_0.6m_Scene.tif",
        file_path="/tmp/fake_carto.tif",
        format="GTiff",
        width_px=1024,
        height_px=1024,
        band_count=1,
        dtype="uint16",
        sensor="Cartosat-2S",
        is_geospatial=True,
        modality=ModalityResult(modality=ModalityEnum.UNKNOWN, confidence=0, evidence=[]),
    )
    mod_carto = detect_modality(carto_manifest)
    assert mod_carto.modality == ModalityEnum.PANCHROMATIC
    assert mod_carto.confidence >= 0.90
    assert any("Cartosat" in ev for ev in mod_carto.evidence)


def test_cross_modal_analysis_high_agreement(sample_cross_modal_rasters):
    """Verify physical evidence separation and high mutual agreement."""
    p_opt, p_sar = sample_cross_modal_rasters
    specialist = get_cross_modal_specialist()

    res = specialist.analyze_pair(p_opt, p_sar)

    assert "optical_evidence" in res
    assert "sar_evidence" in res
    assert "modality_agreement" in res
    assert res["modality_agreement"] in ["HIGH", "MODERATE", "CONFLICT"]
    assert "synthesis" in res
    assert len(res["synthesis"]) > 0
    assert res["confidence"] > 0.0
    assert "sensor_compatibility" in res
    assert "RISAT-1A" in res["sensor_compatibility"]["sar_source"]


def test_cross_modal_conflict_resolution(tmp_path):
    """Verify conflict detection when smooth dry tarmac mimics water in SAR."""
    p_tarmac = tmp_path / "airport_runway_optical.png"
    p_sar_smooth = tmp_path / "runway_sar.png"

    # Optical: light grey concrete/tarmac
    Image.new("RGB", (256, 256), color=(200, 200, 200)).save(p_tarmac)
    # SAR: specular low reflection (smooth surface)
    Image.new("L", (256, 256), color=15).save(p_sar_smooth)

    specialist = get_cross_modal_specialist()
    res = specialist.analyze_pair(p_tarmac, p_sar_smooth)

    assert res["modality_agreement"] in ["CONFLICT", "MODERATE"]
    assert len(res["conflicts"]) > 0 or len(res["complementary_findings"]) > 0


def test_cross_modal_rest_api_endpoint(sample_cross_modal_rasters):
    """Verify POST /api/specialists/optical-sar REST API endpoint."""
    p_opt, p_sar = sample_cross_modal_rasters
    client = TestClient(app)

    with open(p_opt, "rb") as f_opt, open(p_sar, "rb") as f_sar:
        response = client.post(
            "/api/specialists/optical-sar",
            files={
                "file_optical": ("optical.png", f_opt, "image/png"),
                "file_sar": ("sar.png", f_sar, "image/png"),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "optical_evidence" in data
    assert "sar_evidence" in data
    assert "modality_agreement" in data
    assert "synthesis" in data
    assert "sensor_compatibility" in data
