import pytest
from pathlib import Path
from backend.models.rsvqa.model import rsvqa_specialist

SAMPLE_IMAGE = Path("datasets/06_RSVQA/Images_LR/0.tif")
FALLBACK_IMAGE = Path("datasets/processed/bigearthnet_resnet50_full/test/images/S2A_MSIL2A_20170613T101031_N9999_R022_T33UUP_26_57.tif")


@pytest.fixture
def image_path():
    if SAMPLE_IMAGE.exists():
        return SAMPLE_IMAGE
    elif FALLBACK_IMAGE.exists():
        return FALLBACK_IMAGE
    pytest.skip("No sample image available for VQA test")


def test_vqa_presence_question(image_path):
    res = rsvqa_specialist.predict(image_path, "Is there arable land present in the image?")
    assert "answer" in res
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["model_name"] == "rsvqa-specialist"
    assert "evidence" in res
    assert res["processing_time_ms"] > 0


def test_vqa_rural_urban_question(image_path):
    res = rsvqa_specialist.predict(image_path, "Is it a rural or an urban area?")
    assert res["answer"] in ["rural", "urban"] or "Uncertain" in res["answer"]
    assert res["question_type"] == "rural_urban"
    assert "urban_score" in res["evidence"]


def test_vqa_count_question(image_path):
    res = rsvqa_specialist.predict(image_path, "What is the amount of residential buildings?")
    assert res["question_type"] == "count"
    assert res["confidence"] > 0.0
