"""
Unit tests for LEVIR-CD Bi-Temporal Change Detection Specialist (Phase 04).
Tests dataset parsing, spatial alignment, BIT forward pass, deterministic area calculation,
pre-flight sanity check mode, and the REST endpoint.
"""

import io
from pathlib import Path
import pytest
from PIL import Image
import torch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.change_detection.alignment import verify_spatial_alignment, align_image_pair
from backend.models.change_detection.dataset import LEVIRCDDataset
from backend.models.change_detection.model import BITChangeDetector, get_change_specialist


@pytest.fixture
def sample_pair(tmp_path):
    """Create two synthetic test images with known differences."""
    p1 = tmp_path / "t1.png"
    p2 = tmp_path / "t2.png"

    # T1: solid green image
    img1 = Image.new("RGB", (256, 256), color=(34, 139, 34))
    img1.save(p1)

    # T2: green image with a 64x64 red patch in the center
    img2 = img1.copy()
    patch = Image.new("RGB", (64, 64), color=(220, 20, 60))
    img2.paste(patch, (96, 96))
    img2.save(p2)

    return p1, p2


def test_levir_dataset_loading():
    """Verify loading and tensor structures for LEVIR-CD."""
    dataset = LEVIRCDDataset(
        root_dir="datasets/05_LEVIR_CD",
        split="test",
        img_size=256,
        max_samples=3,
    )
    assert len(dataset) == 3
    sample = dataset[0]

    assert "name" in sample
    assert "A" in sample
    assert "B" in sample
    assert "label" in sample
    assert "original_size" in sample

    assert sample["A"].shape == (3, 256, 256)
    assert sample["B"].shape == (3, 256, 256)
    assert sample["label"].shape == (256, 256)
    # Check binary label values
    unique_vals = torch.unique(sample["label"]).tolist()
    assert all(v in [0, 1] for v in unique_vals)


def test_spatial_alignment_and_resampling(sample_pair, tmp_path):
    """Verify alignment check and dynamic spatial resampling."""
    p1, p2 = sample_pair

    # 1. Matching images
    info = verify_spatial_alignment(p1, p2)
    assert info["aligned"] is True
    assert info["resolution_mismatch"] is False
    assert info["t1_shape"][:2] == info["t2_shape"][:2]

    # 2. Resampling images of different dimensions
    p_diff = tmp_path / "t_diff.png"
    Image.new("RGB", (512, 512), color="blue").save(p_diff)
    info_diff = verify_spatial_alignment(p1, p_diff)
    assert info_diff["aligned"] is False

    t1_pil = Image.open(p1)
    diff_pil = Image.open(p_diff)
    a1, a2, meta = align_image_pair(t1_pil, diff_pil, target_size=(256, 256))
    assert a1.size == (256, 256)
    assert a2.size == (256, 256)
    assert meta["resampled"] is True


def test_bit_model_forward_pass():
    """Verify Siamese BIT architecture tensor dimensions and class channels."""
    model = BITChangeDetector()
    x1 = torch.randn(2, 3, 256, 256, device=model.device)
    x2 = torch.randn(2, 3, 256, 256, device=model.device)

    with torch.no_grad():
        out = model(x1, x2)

    assert out.shape == (2, 2, 256, 256)


def test_change_specialist_deterministic_area(sample_pair):
    """Verify deterministic area calculations (m² and hectares) from GSD."""
    p1, p2 = sample_pair
    specialist = get_change_specialist()

    gsd = 0.5  # 0.5m per pixel -> each pixel is 0.25 m²
    res = specialist.detect_change(p1, p2, gsd=gsd)

    assert "changed" in res
    assert "change_percentage" in res
    assert "changed_pixels" in res
    assert "total_pixels" in res
    assert "area_m2" in res
    assert "area_ha" in res
    assert "regions_count" in res
    assert "confidence" in res
    assert "change_mask_base64" in res
    assert res["model_name"] == "bit-change-detection"
    assert "LEVIR-CD" in res["provenance"]

    # Invariant: deterministic calculation check
    expected_m2 = round(res["changed_pixels"] * (gsd ** 2), 2)
    expected_ha = round(expected_m2 / 10000.0, 4)
    assert res["area_m2"] == expected_m2
    assert res["area_ha"] == expected_ha
    assert 0.0 <= res["confidence"] <= 1.0


def test_specialist_change_rest_endpoint(sample_pair):
    """Verify POST /api/specialists/change REST API endpoint."""
    p1, p2 = sample_pair
    client = TestClient(app)

    with open(p1, "rb") as f1, open(p2, "rb") as f2:
        response = client.post(
            "/api/specialists/change",
            files={
                "file_t1": ("t1.png", f1, "image/png"),
                "file_t2": ("t2.png", f2, "image/png"),
            },
            data={"gsd": 0.5, "threshold": 0.5},
        )

    assert response.status_code == 200
    data = response.json()
    assert "changed" in data
    assert "changed_pixels" in data
    assert "area_m2" in data
    assert "area_ha" in data
    assert "regions_count" in data
    assert "confidence" in data
    assert "change_mask_base64" in data
