import pytest
from gateway.modality import detect_modality
from orchestrator.schemas import ImageManifest, ModalityEnum, ModalityResult

def create_mock_manifest(filename: str, count: int, sensor: str = None, band_desc: list = None) -> ImageManifest:
    return ImageManifest(
        file_id="test",
        filename=filename,
        file_path="/dummy/path",
        format="GTiff",
        width_px=100,
        height_px=100,
        band_count=count,
        dtype="uint16",
        is_geospatial=True,
        modality=ModalityResult(modality=ModalityEnum.UNKNOWN, confidence=0, evidence=[]),
        sensor=sensor,
        band_descriptions=band_desc or []
    )

def test_modality_sar_by_name():
    manifest = create_mock_manifest("S1A_IW_GRDH_1SDV.tiff", 1)
    result = detect_modality(manifest)
    assert result.modality == ModalityEnum.SAR
    assert result.confidence >= 0.8

def test_modality_sar_by_sensor():
    manifest = create_mock_manifest("image.tif", 1, sensor="Sentinel-1")
    result = detect_modality(manifest)
    assert result.modality == ModalityEnum.SAR
    assert result.confidence == 0.95

def test_modality_sar_by_bands():
    manifest = create_mock_manifest("image.tif", 2, band_desc=["VV", "VH"])
    result = detect_modality(manifest)
    assert result.modality == ModalityEnum.SAR
    assert result.confidence >= 0.9

def test_modality_optical_rgb():
    manifest = create_mock_manifest("landsat_image.tif", 3)
    result = detect_modality(manifest)
    assert result.modality == ModalityEnum.OPTICAL_RGB

def test_modality_multispectral():
    manifest = create_mock_manifest("sentinel2_l2a.tif", 4)
    result = detect_modality(manifest)
    assert result.modality == ModalityEnum.OPTICAL_MULTISPECTRAL

def test_modality_fallback():
    manifest = create_mock_manifest("unknown_file.png", 0)
    result = detect_modality(manifest)
    assert result.modality == ModalityEnum.UNKNOWN
