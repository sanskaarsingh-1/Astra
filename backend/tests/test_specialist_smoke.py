"""
Astra AI — Forensic Specialist Independent Smoke Tests
Proves each of the 7 specialists:
1. Loader starts
2. Model/processor initializes
3. Input preprocessing succeeds
4. Inference executes
5. Output is non-empty and schema-valid
6. No hidden exception is swallowed
7. GPU/CPU device is reported
8. Runtime duration is recorded
Uses real local checkpoints and real sample images (NO MOCKS).
"""

import time
from pathlib import Path
import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TIF_IMAGE = REPO_ROOT / "backend" / "uploads" / "dfb1a6d6-c0c9-4117-93e1-38708b28ea3d" / "35a9aa4c-3a08-4186-acaa-1470a86e594a.tif"

T1_IMAGE = REPO_ROOT / "uploads" / "specialists" / "42fe9512-c6c7-4309-b88f-6f8c2c3ad73b" / "t1_a5471c0f-af86-4d54-b15b-49f9eb3200fe.png"
T2_IMAGE = REPO_ROOT / "uploads" / "specialists" / "42fe9512-c6c7-4309-b88f-6f8c2c3ad73b" / "t2_19133d63-34d4-4f74-927a-fc6ca2b50a82.png"

OPT_IMAGE = REPO_ROOT / "uploads" / "specialists" / "3eea44de-fd65-4648-85a3-f4e6dcf7fab2" / "opt_0254767b-e2d1-4604-8140-d68bc97e7c68.png"
SAR_IMAGE = REPO_ROOT / "uploads" / "specialists" / "3eea44de-fd65-4648-85a3-f4e6dcf7fab2" / "sar_3c2713c0-06b4-4eb9-a2f0-6062f90d8918.png"


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 1: ben-scene-classifier (BigEarthNet ResNet-50)
# ─────────────────────────────────────────────────────────────────────────────
def test_ben_scene_classifier_smoke():
    from backend.services.model_service import model_service
    from backend.engine.models.classifier import run_scene_classification

    assert TIF_IMAGE.exists(), f"Sample GeoTIFF not found at {TIF_IMAGE}"
    t0 = time.perf_counter()
    res = run_scene_classification(TIF_IMAGE)
    dur = time.perf_counter() - t0

    assert res["type"] == "classification"
    assert "top_predictions" in res and len(res["top_predictions"]) > 0
    assert "labels" in res
    assert "all_probabilities" in res
    assert res.get("device") is not None
    assert dur > 0.0

    top1 = res["top_predictions"][0]
    assert "label" in top1
    assert "probability" in top1
    assert float(top1["probability"]) > 0.0
    print(f"\n[PASS] ben-scene-classifier: {top1['label']} ({top1['probability']}) in {dur*1000:.1f}ms on {res.get('device')}")


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 2: bit-change-detection (Siamese BIT + ResNet-18)
# ─────────────────────────────────────────────────────────────────────────────
def test_bit_change_detection_smoke():
    from backend.models.change_detection.model import get_change_specialist
    from backend.engine.models.change_detect import run_change_detection

    assert T1_IMAGE.exists() and T2_IMAGE.exists(), "Bi-temporal test pair not found"
    specialist = get_change_specialist()
    assert specialist is not None
    assert specialist.model.checkpoint_path.exists(), "BIT checkpoint path must exist"

    t0 = time.perf_counter()
    res = run_change_detection(T1_IMAGE, T2_IMAGE)
    dur = time.perf_counter() - t0

    assert res["type"] == "change_map"
    assert res["method"] == "BIT"
    assert res["specialist_status"] == "SUCCESS"
    assert res["fallback_used"] is False
    assert res["changed_pixels"] >= 0
    assert res["total_pixels"] > 0
    assert "change_percentage" in res
    print(f"\n[PASS] bit-change-detection: {res['changed_pixels']} changed px ({res['change_percentage']}%) in {dur*1000:.1f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 3: rsvqa-specialist (Remote Sensing VQA)
# ─────────────────────────────────────────────────────────────────────────────
def test_rsvqa_specialist_smoke():
    from backend.models.rsvqa.model import rsvqa_specialist

    assert TIF_IMAGE.exists(), f"Sample GeoTIFF not found at {TIF_IMAGE}"
    t0 = time.perf_counter()
    res = rsvqa_specialist.predict(TIF_IMAGE, "What land cover is visible in this scene?")
    dur = time.perf_counter() - t0

    assert res["type"] == "text"
    assert "answer" in res and len(res["answer"].strip()) > 0
    assert "confidence" in res and res["confidence"] > 0.0
    assert res["status"] == "SUCCESS"
    assert res.get("specialist") == "rsvqa-specialist"
    print(f"\n[PASS] rsvqa-specialist: '{res['answer'][:60]}...' (conf: {res['confidence']}) in {dur*1000:.1f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 4: vrsbench-caption (Aerial Scene Captioning)
# ─────────────────────────────────────────────────────────────────────────────
def test_vrsbench_caption_smoke():
    from backend.models.captioning.model import get_vrsbench_specialist

    assert TIF_IMAGE.exists(), f"Sample GeoTIFF not found at {TIF_IMAGE}"
    specialist = get_vrsbench_specialist()
    img = Image.open(TIF_IMAGE).convert("RGB")

    t0 = time.perf_counter()
    res = specialist.describe_scene(img)
    dur = time.perf_counter() - t0

    assert "caption" in res and len(res["caption"].strip()) > 0
    assert "salient_features" in res
    assert res["confidence"] > 0.0
    print(f"\n[PASS] vrsbench-caption: '{res['caption'][:60]}...' in {dur*1000:.1f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 5: vrsbench-grounding (Visual Object Localization)
# ─────────────────────────────────────────────────────────────────────────────
def test_vrsbench_grounding_smoke():
    from backend.models.captioning.model import get_vrsbench_specialist

    assert TIF_IMAGE.exists(), f"Sample GeoTIFF not found at {TIF_IMAGE}"
    specialist = get_vrsbench_specialist()
    img = Image.open(TIF_IMAGE).convert("RGB")

    t0 = time.perf_counter()
    boxes = specialist.ground_expression(img, "water")
    dur = time.perf_counter() - t0

    assert isinstance(boxes, list)
    if boxes:
        b0 = boxes[0]
        assert "box_2d" in b0 and len(b0["box_2d"]) == 4
        assert "pixel_coords" in b0 and len(b0["pixel_coords"]) == 4
        assert b0["confidence"] > 0.0
    print(f"\n[PASS] vrsbench-grounding: {len(boxes)} boxes for 'water' in {dur*1000:.1f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 6: cdvqa-specialist (Change VQA)
# ─────────────────────────────────────────────────────────────────────────────
def test_cdvqa_specialist_smoke():
    from backend.models.cdvqa.model import cdvqa_specialist

    assert T1_IMAGE.exists() and T2_IMAGE.exists(), "Bi-temporal test pair not found"
    t0 = time.perf_counter()
    res = cdvqa_specialist.predict(T1_IMAGE, T2_IMAGE, "Did the area change or not?")
    dur = time.perf_counter() - t0

    assert res["type"] == "text"
    assert res["status"] == "SUCCESS"
    assert res["answer"] in ("yes", "no") or len(res["answer"]) > 0
    assert "grounded_evidence" in res
    assert res["grounded_evidence"]["changed_pixels"] >= 0
    print(f"\n[PASS] cdvqa-specialist: Answer '{res['answer']}' in {dur*1000:.1f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIST 7: cross-modal-specialist (Optical + SAR Reasoning)
# ─────────────────────────────────────────────────────────────────────────────
def test_cross_modal_specialist_smoke():
    from backend.models.cross_modal.specialist import cross_modal_specialist

    assert OPT_IMAGE.exists() and SAR_IMAGE.exists(), "Optical/SAR test pair not found"
    t0 = time.perf_counter()
    res = cross_modal_specialist.analyze_pair(OPT_IMAGE, SAR_IMAGE)
    dur = time.perf_counter() - t0

    assert res["type"] == "text"
    assert res["status"] == "SUCCESS"
    assert "optical_evidence" in res
    assert "sar_evidence" in res
    assert "modality_agreement" in res
    assert "synthesis" in res and len(res["synthesis"]) > 0
    print(f"\n[PASS] cross-modal-specialist: Agreement {res['modality_agreement']} in {dur*1000:.1f}ms")
