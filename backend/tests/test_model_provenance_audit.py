"""
Model Provenance and Identity Audit Test Suite
Verifies:
1. Current production model loads with exact architecture (ResNet-50 v2, 19 classes).
2. Historical ResNet-50 baseline loads with exact architecture (ResNet-50, 19 classes).
3. BIT change detection loads with Siamese ResNet-18 backbone (10 epochs).
4. Model registry schema integrity and metric provenance.
5. Report metadata exporter reflects verified active models and deterministic calculation status.
"""

import json
from pathlib import Path
import pytest
import torch
import torch.nn as nn
import torchvision.models as models

from orchestrator.schemas import (
    Report, EvidencePackage, EvidenceFinding, FindingType,
    EvidenceStrength, ConfidenceStatus, ExecutedStep, StepStatus,
    ExecutionTrace, InvestigationPlan
)
from report.exporter import export_markdown_report


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"


def test_production_resnet50_checkpoint_loads():
    """Verify production ResNet-50 loads cleanly without altering weights."""
    ckpt_path = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth"
    assert ckpt_path.exists(), f"Production checkpoint missing: {ckpt_path}"
    
    state = torch.load(str(ckpt_path), map_location="cpu")
    sd = state.get("model_state_dict", state)
    
    # Verify ResNet-50 Bottleneck signatures
    assert "layer1.0.conv3.weight" in sd, "Model must have Bottleneck conv3 (ResNet-50)"
    assert "layer4.2.conv3.weight" in sd, "Model must have 3 blocks in layer4 (ResNet-50)"
    
    # Verify 19-class linear head
    fc_weight = sd["fc.weight"]
    assert fc_weight.shape == (19, 2048), f"Expected (19, 2048) head, got {fc_weight.shape}"
    
    # Construct model and load state_dict
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(2048, 19)
    model.load_state_dict(sd)
    model.eval()
    
    # Forward pass sanity
    dummy = torch.randn(2, 3, 224, 224)
    with torch.no_grad():
        out = model(dummy)
    assert out.shape == (2, 19)


def test_historical_resnet50_baseline_checkpoint_loads():
    """Verify historical baseline ResNet-50 loads cleanly and remains preserved."""
    ckpt_path = BACKEND_DIR / "models" / "baseline" / "ben_classifier.pth"
    assert ckpt_path.exists(), f"Historical baseline missing: {ckpt_path}"
    
    state = torch.load(str(ckpt_path), map_location="cpu")
    sd = state.get("model_state_dict", state)
    
    assert "layer1.0.conv3.weight" in sd, "Baseline model must have Bottleneck conv3 (ResNet-50)"
    fc_weight = sd["fc.weight"]
    assert fc_weight.shape == (19, 2048), f"Expected (19, 2048) head, got {fc_weight.shape}"
    
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(2048, 19)
    model.load_state_dict(sd)
    model.eval()
    
    dummy = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        out = model(dummy)
    assert out.shape == (1, 19)


def test_bit_change_detection_siamese_resnet18_loads():
    """Verify BIT change detection specialist uses Siamese ResNet-18 backbone (10 epochs)."""
    from backend.models.change_detection.model import BITChangeDetector
    ckpt_path = BACKEND_DIR / "models" / "change_detection" / "checkpoints" / "best_model.pth"
    assert ckpt_path.exists(), f"BIT checkpoint missing: {ckpt_path}"
    
    state = torch.load(str(ckpt_path), map_location="cpu")
    assert state.get("epoch") == 10, f"Expected 10 epochs training metadata, got {state.get('epoch')}"
    
    # Instantiate detector and load state
    detector = BITChangeDetector(checkpoint_path=ckpt_path, device=torch.device("cpu"))
    assert hasattr(detector.net, "resnet"), "BIT model must contain Siamese ResNet backbone"
    # Verify backbone is ResNet-18: layer1[0] is BasicBlock without conv3
    layer1_block0 = detector.net.resnet.layer1[0]
    assert hasattr(layer1_block0, "conv1") and hasattr(layer1_block0, "conv2")
    assert not hasattr(layer1_block0, "conv3"), "ResNet-18 BasicBlock does not contain conv3"


def test_model_registry_schema_and_metrics():
    """Verify backend/models/model_registry.json has valid structure, metrics, and roles."""
    reg_path = BACKEND_DIR / "models" / "model_registry.json"
    assert reg_path.exists(), f"Registry file missing: {reg_path}"
    
    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    models_dict = data["models"]
    assert "ben-scene-classifier" in models_dict
    assert "bigearthnet_resnet50_baseline_historical" in models_dict
    assert "bit-change-detection" in models_dict
    
    ben = models_dict["ben-scene-classifier"]
    assert ben["model_role"] == "CURRENT_PRODUCTION_MODEL"
    assert ben["architecture"] == "ResNet-50"
    assert ben["training_epochs"] == 20
    assert ben["best_epoch"] == 19
    assert ben["metrics"]["validation_accuracy"] == 91.79
    assert ben["metrics"]["validation_macro_f1"] == 0.7038
    assert "NOT mAP" in ben["metrics"]["metric_notes"]
    
    hist = models_dict["bigearthnet_resnet50_baseline_historical"]
    assert hist["model_role"] == "HISTORICAL_BASELINE"
    assert hist["architecture"] == "ResNet-50"
    
    bit = models_dict["bit-change-detection"]
    assert bit["architecture"] == "Bitemporal Image Transformer (BIT) with Siamese ResNet-18 backbone"
    assert bit["training_epochs"] == 10
    assert bit["metrics"]["overall_accuracy"] == 96.98
    assert bit["metrics"]["f1_score"] == 69.56
    
    # Verify deterministic tools
    tools_dict = data["deterministic_tools"]
    assert len(tools_dict) == 10
    for t_id, tool in tools_dict.items():
        assert tool["calculation_status"] == "DETERMINISTIC"


def test_report_exporter_includes_model_provenance_and_deterministic_note():
    """Verify that report export includes model provenance table and deterministic note."""
    from datetime import datetime, timezone
    report = Report(
        narrative="Investigation into agricultural land conversion.",
        methodology="Multi-specialist neural network reasoning.",
        limitations=["Atmospheric optical scattering"],
        confidence_summary="Calibrated multi-source assessment."
    )
    strength = EvidenceStrength(
        model_confidence=1.0,
        confidence_status=ConfidenceStatus.DETERMINISTIC,
        evidence_strength="GROUND_TRUTH_DETERMINISTIC"
    )
    finding = EvidenceFinding(
        finding_id="f-1",
        type=FindingType.MEASUREMENT,
        value={"area_ha": 14.52, "calculation_status": "DETERMINISTIC"},
        source_model="area-calculator",
        strength=strength,
        provenance="area-calculator calculation"
    )
    step = ExecutedStep(
        step_id="step_1",
        tool_id="ben-scene-classifier",
        status=StepStatus.SUCCESS,
        input_summary="image.tif",
        output_summary="Arable land: 92.4%",
        duration_ms=45
    )
    plan = InvestigationPlan(
        plan_id="plan-1",
        query="Identify land cover and area",
        task_classification="scene_classification",
        plan_rationale="Classify land cover using ResNet-50",
        steps=[]
    )
    trace = ExecutionTrace(
        trace_id="tr-1",
        timestamp_start=datetime.now(timezone.utc),
        plan=plan,
        executed_steps=[step]
    )
    evidence = EvidencePackage(
        request_id="req-123",
        query="Identify land cover and area",
        findings=[finding],
        overall_confidence=0.91,
        models_used=["ben-scene-classifier"],
        tools_used=["area-calculator"],
        total_inference_time_ms=45,
        trace=trace
    )
    
    md = export_markdown_report(report, evidence, "job-test-456")
    assert "Active Specialist Models Deployed" in md
    assert "ben-scene-classifier" in md
    assert "ResNet-50" in md
    assert "Val Acc: 91.79%" in md
    assert "Note on Calculation Certainty" in md
    assert "DETERMINISTIC" in md
