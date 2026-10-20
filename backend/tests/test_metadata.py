import pytest
from pathlib import Path
from gateway.metadata import extract_metadata
from PIL import Image

@pytest.fixture
def dummy_image(tmp_path):
    img_path = tmp_path / "test_image.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)
    return img_path

def test_extract_metadata_fallback(dummy_image):
    meta = extract_metadata(dummy_image)
    assert meta.width_px == 100
    assert meta.height_px == 100
    assert meta.format == "PNG"
    assert meta.is_geospatial is False
