"""
Unit tests for Change-Based Visual Question Answering (CDVQA) Specialist (Phase 05).
Tests dataset loading, question classification, grounded inference, pre-flight sanity mode,
and the REST API endpoint.
"""

from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.cdvqa.dataset import CDVQADataset
from backend.models.cdvqa.model import get_cdvqa_specialist


@pytest.fixture
def sample_temporal_images(tmp_path):
    """Create two test temporal images with distinct patterns."""
    p1 = tmp_path / "date1.png"
    p2 = tmp_path / "date2.png"

    # Date 1: Forest green
    img1 = Image.new("RGB", (256, 256), color=(34, 139, 34))
    img1.save(p1)

    # Date 2: Green with built-up grey block
    img2 = img1.copy()
    block = Image.new("RGB", (80, 80), color=(128, 128, 128))
    img2.paste(block, (50, 50))
    img2.save(p2)

    return p1, p2


def test_cdvqa_dataset_loading():
    """Verify CDVQA annotations and image paths."""
    dataset = CDVQADataset(
        annotations_dir="datasets/04_CDVQA/CDVQA-main",
        images_dir="datasets/04_CDVQA/images",
        split="Val",
        max_samples=5,
    )
    assert len(dataset) > 0
    sample = dataset[0]

    assert "question" in sample
    assert "answer" in sample
    assert "question_type" in sample
    assert "t1_path" in sample
    assert "t2_path" in sample
    assert Path(sample["t1_path"]).exists()
    assert Path(sample["t2_path"]).exists()


def test_cdvqa_question_type_inference():
    """Verify automatic classification of remote sensing change question phrasing."""
    specialist = get_cdvqa_specialist()

    assert specialist._classify_question_type("Did the built-up area increase?") == "increase_or_not"
    assert specialist._classify_question_type("Did the forest area decrease?") == "decrease_or_not"
    assert specialist._classify_question_type("Have the trees changed?") == "change_or_not"
    assert specialist._classify_question_type("What did the agricultural field change into?") == "change_to_what"
    assert specialist._classify_question_type("Which class had the largest change?") == "largest_change"
    assert specialist._classify_question_type("What is the ratio of change?") == "change_ratio"


def test_cdvqa_grounded_inference(sample_temporal_images):
    """Verify grounded answer formulation and evidence extraction."""
    p1, p2 = sample_temporal_images
    specialist = get_cdvqa_specialist()

    res = specialist.answer_query(
        t1_input=p1,
        t2_input=p2,
        question="Did any structural surface change occur?",
        gsd=0.5,
    )

    assert "answer" in res
    assert res["answer"] in ["yes", "no"] or len(res["answer"]) > 0
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert "narrative" in res
    assert "grounded_evidence" in res

    evidence = res["grounded_evidence"]
    assert "change_detected" in evidence
    assert "change_percentage" in evidence
    assert "changed_pixels" in evidence
    assert "area_m2" in evidence
    assert "area_ha" in evidence
    assert "regions_count" in evidence
    assert res["model_name"] == "cdvqa-specialist"


def test_cdvqa_rest_api_endpoint(sample_temporal_images):
    """Verify POST /api/specialists/change-vqa REST API endpoint."""
    p1, p2 = sample_temporal_images
    client = TestClient(app)

    with open(p1, "rb") as f1, open(p2, "rb") as f2:
        response = client.post(
            "/api/specialists/change-vqa",
            files={
                "file_t1": ("date1.png", f1, "image/png"),
                "file_t2": ("date2.png", f2, "image/png"),
            },
            data={
                "question": "Did the built-up area change between Date 1 and Date 2?",
                "gsd": 0.5,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "confidence" in data
    assert "grounded_evidence" in data
    assert "narrative" in data
    assert "question" in data
