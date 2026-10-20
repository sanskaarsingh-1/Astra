"""
Unit tests for VRSBench Captioning and Visual Grounding Specialist (Phase 03).
"""

import io
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.captioning.dataset import VRSBenchDataset
from backend.models.captioning.model import VRSBenchSpecialist


@pytest.fixture
def sample_pil_image():
    return Image.new("RGB", (256, 256), color="forestgreen")


def test_vrsbench_dataset_loading():
    """Verify loading and parsing of VRSBench annotations."""
    dataset = VRSBenchDataset(
        annotations_dir="datasets/07_VRSBench/annotations",
        images_dir="datasets/07_VRSBench/Images",
        task="both",
        split="val",
        max_samples=10,
    )
    assert len(dataset) > 0
    sample = dataset[0]
    assert "image" in sample
    assert "task_type" in sample
    assert sample["image"].size == (512, 512) or sample["image"].size[0] > 0


def test_vrsbench_captioning_generation(sample_pil_image):
    """Verify scene description generation and salient keyword extraction."""
    specialist = VRSBenchSpecialist()
    result = specialist.describe_scene(sample_pil_image)
    assert "caption" in result
    assert isinstance(result["caption"], str)
    assert len(result["caption"]) > 0
    assert "salient_features" in result
    assert "confidence" in result
    assert 0.0 <= result["confidence"] <= 1.0


def test_vrsbench_grounding_bounding_boxes(sample_pil_image):
    """Verify visual grounding generates valid normalized bounding boxes."""
    specialist = VRSBenchSpecialist()
    boxes = specialist.ground_expression(sample_pil_image, "green forest area")
    assert isinstance(boxes, list)
    if boxes:
        box = boxes[0]
        assert "box_2d" in box
        ymin, xmin, ymax, xmax = box["box_2d"]
        assert 0.0 <= ymin <= 1.0
        assert 0.0 <= xmin <= 1.0
        assert 0.0 <= ymax <= 1.0
        assert 0.0 <= xmax <= 1.0
        assert ymin <= ymax
        assert xmin <= xmax
        assert "confidence" in box


def test_caption_api_endpoint(sample_pil_image):
    """Verify POST /api/specialists/caption returns valid description."""
    client = TestClient(app)
    img_byte_arr = io.BytesIO()
    sample_pil_image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    response = client.post(
        "/api/specialists/caption",
        files={"file": ("test.png", img_byte_arr, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "caption" in data
    assert "salient_features" in data
    assert "confidence" in data


def test_grounding_api_endpoint(sample_pil_image):
    """Verify POST /api/specialists/grounding returns localized bounding boxes."""
    client = TestClient(app)
    img_byte_arr = io.BytesIO()
    sample_pil_image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    response = client.post(
        "/api/specialists/grounding",
        data={"query": "vegetation and trees"},
        files={"file": ("test.png", img_byte_arr, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "boxes" in data
    assert "detections_count" in data
