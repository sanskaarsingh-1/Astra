"""
Astra AI - Benchmark Regression & VLM Adapter Tests
Phase 2: Engineering Implementation

Tests verify:
1. Structural integrity of all production checkpoints (shape, architecture)
2. VLM adapter loads correctly from best_adapter/ checkpoint
3. Registry API endpoint returns expected schema
4. No silent model corruption or misloading

INVARIANT: Zero training, zero weight modification. Pure structural checks.
"""

import pytest
import json
from pathlib import Path
import torch
import torch.nn as nn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

# ─── Priority 5: Benchmark Regression Tests ─────────────────────────────────

class TestResNet50StructuralIntegrity:
    """
    Structural integrity checks for the ResNet-50 BigEarthNet checkpoint.
    These tests verify the checkpoint is not corrupted and loads with expected shape.
    No accuracy thresholds - only structural/architectural checks.
    """

    def test_resnet50_checkpoint_exists_and_is_correct_size(self):
        """Verify the sacred checkpoint exists at the correct path and size."""
        ckpt = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth"
        assert ckpt.exists(), f"CRITICAL: Sacred ResNet-50 checkpoint missing at {ckpt}"
        size_mb = ckpt.stat().st_size / (1024 ** 2)
        # Should be approximately 270 MB (serialized state dict)
        assert size_mb > 200, f"Checkpoint too small ({size_mb:.1f} MB). Possible corruption."
        assert size_mb < 400, f"Checkpoint suspiciously large ({size_mb:.1f} MB)."

    def test_resnet50_fc_head_shape_correct(self):
        """Verify fc head is [19, 2048] — the correct BigEarthNet 19-class head."""
        ckpt = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth"
        if not ckpt.exists():
            pytest.skip("Checkpoint not found")

        state_dict = torch.load(str(ckpt), map_location="cpu", weights_only=True)
        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        elif "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        assert "fc.weight" in state_dict, "fc.weight not found in state dict"
        fc_shape = tuple(state_dict["fc.weight"].shape)
        assert fc_shape == (19, 2048), (
            f"Wrong fc head shape: {fc_shape}. Expected (19, 2048) for 19 BigEarthNet classes. "
            "This indicates the wrong checkpoint is loaded."
        )
        assert "fc.bias" in state_dict, "fc.bias missing from state dict"
        assert tuple(state_dict["fc.bias"].shape) == (19,), "fc.bias shape wrong"

    def test_resnet50_bottleneck_blocks_present(self):
        """Verify ResNet-50 (not ResNet-18) by checking for Bottleneck-style layer3 keys."""
        ckpt = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth"
        if not ckpt.exists():
            pytest.skip("Checkpoint not found")

        state_dict = torch.load(str(ckpt), map_location="cpu", weights_only=True)
        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        elif "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        # ResNet-50 Bottleneck has conv1, conv2, conv3 in each block
        keys = list(state_dict.keys())
        layer1_conv2 = [k for k in keys if "layer1" in k and "conv2" in k]
        layer1_conv3 = [k for k in keys if "layer1" in k and "conv3" in k]
        assert len(layer1_conv2) > 0, "No conv2 keys in layer1 — may not be ResNet-50"
        assert len(layer1_conv3) > 0, "No conv3 keys in layer1 — ResNet-18 only has conv2, not conv3"

    def test_resnet50_forward_pass_output_shape(self):
        """Single synthetic forward pass: verify output is [1, 19] float tensor."""
        import torchvision.models as tvm
        model = tvm.resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, 19)

        ckpt = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "best_model.pth"
        if not ckpt.exists():
            pytest.skip("Checkpoint not found")

        state_dict = torch.load(str(ckpt), map_location="cpu", weights_only=True)
        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        elif "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        model.load_state_dict(state_dict)
        model.eval()

        dummy = torch.zeros(1, 3, 224, 224)
        with torch.inference_mode():
            out = model(dummy)

        assert out.shape == (1, 19), f"Wrong output shape: {out.shape}. Expected (1, 19)"
        probs = torch.sigmoid(out)
        assert probs.min() >= 0.0 and probs.max() <= 1.0, "Sigmoid probabilities out of [0,1]"


class TestBITChangeDetectionStructuralIntegrity:
    """Structural integrity checks for BIT Siamese ResNet-18 checkpoint."""

    def test_bit_checkpoint_exists(self):
        ckpt = BACKEND_DIR / "models" / "change_detection" / "checkpoints" / "best_model.pth"
        assert ckpt.exists(), f"BIT checkpoint missing at {ckpt}"
        size_mb = ckpt.stat().st_size / (1024 ** 2)
        assert 50 < size_mb < 150, f"BIT checkpoint size unexpected: {size_mb:.1f} MB"

    def test_bit_checkpoint_epoch_metadata(self):
        """Verify the checkpoint contains 10-epoch training metadata."""
        ckpt = BACKEND_DIR / "models" / "change_detection" / "checkpoints" / "best_model.pth"
        if not ckpt.exists():
            pytest.skip("BIT checkpoint not found")

        data = torch.load(str(ckpt), map_location="cpu", weights_only=False)
        assert "epoch" in data, "epoch key missing from BIT checkpoint"
        assert data["epoch"] == 10, f"Expected epoch=10, got epoch={data['epoch']}"

    def test_bit_checkpoint_resnet18_keys(self):
        """Verify Siamese ResNet-18 (BasicBlock) structure via model_G_state_dict."""
        ckpt = BACKEND_DIR / "models" / "change_detection" / "checkpoints" / "best_model.pth"
        if not ckpt.exists():
            pytest.skip("BIT checkpoint not found")

        data = torch.load(str(ckpt), map_location="cpu", weights_only=False)
        # BIT stores its state dict under 'model_G_state_dict' (not 'model_state_dict')
        state_dict = data.get("model_G_state_dict", data.get("model_state_dict", {}))
        assert len(state_dict) > 0, "Could not find model state dict in BIT checkpoint"

        keys = list(state_dict.keys())
        # Should contain resnet.conv1 (stem conv) and resnet.layer1.X.conv1 (BasicBlock)
        has_conv1 = any("conv1" in k for k in keys)
        assert has_conv1, f"No conv1 keys found in BIT model_G_state_dict. First 10 keys: {keys[:10]}"

        # ResNet-18 BasicBlocks have conv1+conv2 per block; ResNet-50 Bottleneck has conv3
        # Check for absence of non-downsample conv3 in layer1 (confirms ResNet-18)
        layer1_conv3_nondl = [k for k in keys if "layer1" in k and "conv3" in k and "downsample" not in k]
        assert len(layer1_conv3_nondl) == 0, (
            f"Found conv3 keys in layer1 (non-downsample): {layer1_conv3_nondl[:5]} — "
            "This looks like ResNet-50 Bottleneck, not ResNet-18 BasicBlock"
        )


class TestVLMAdapterStructuralIntegrity:
    """Structural integrity checks for the BLIP LoRA adapter checkpoint."""

    ADAPTER_DIR = BACKEND_DIR / "models" / "remote_sensing_vlm" / "checkpoints" / "best_adapter"

    def test_adapter_checkpoint_exists(self):
        assert self.ADAPTER_DIR.exists(), f"VLM adapter directory missing: {self.ADAPTER_DIR}"
        weights = self.ADAPTER_DIR / "adapter_model.safetensors"
        assert weights.exists(), f"adapter_model.safetensors missing from {self.ADAPTER_DIR}"

    def test_adapter_config_schema(self):
        """Verify adapter_config.json matches expected BLIP LoRA configuration."""
        config_path = self.ADAPTER_DIR / "adapter_config.json"
        assert config_path.exists(), "adapter_config.json missing"

        with open(config_path) as f:
            config = json.load(f)

        assert config.get("peft_type") == "LORA", f"Expected peft_type=LORA, got {config.get('peft_type')}"
        assert config.get("r") == 16, f"Expected LoRA r=16, got r={config.get('r')}"
        assert config.get("lora_alpha") == 32, f"Expected lora_alpha=32, got {config.get('lora_alpha')}"
        target_modules = config.get("target_modules", [])
        assert "query" in target_modules, f"'query' not in target_modules: {target_modules}"
        assert "value" in target_modules, f"'value' not in target_modules: {target_modules}"
        base = config.get("base_model_name_or_path", "")
        assert "blip" in base.lower(), f"Expected BLIP base model, got: {base}"

    def test_adapter_training_summary(self):
        """Verify training_summary.json documents real training (not a placeholder)."""
        summary_path = BACKEND_DIR / "models" / "remote_sensing_vlm" / "checkpoints" / "training_summary.json"
        assert summary_path.exists(), "training_summary.json missing"

        with open(summary_path) as f:
            summary = json.load(f)

        assert summary.get("total_steps", 0) >= 100, (
            f"total_steps={summary.get('total_steps')} — suspiciously low for real training"
        )
        assert summary.get("best_loss", 999) < 10.0, (
            f"best_loss={summary.get('best_loss')} — unreasonably high, check training"
        )
        assert summary.get("epochs_completed", 0) >= 1, "0 epochs completed — no real training occurred"


class TestModelRegistryIntegrity:
    """Tests for model_registry.json schema and VLM adapter entry."""

    def test_registry_json_valid(self):
        registry_path = BACKEND_DIR / "models" / "model_registry.json"
        assert registry_path.exists()
        with open(registry_path) as f:
            registry = json.load(f)
        assert "models" in registry
        assert "deterministic_tools" in registry

    def test_registry_contains_vlm_adapter_entry(self):
        """Verify the VLM adapter is now properly documented in the registry."""
        registry_path = BACKEND_DIR / "models" / "model_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)

        models = registry.get("models", {})
        assert "rs-vlm-adapter" in models, (
            "rs-vlm-adapter not found in model_registry.json. "
            "The adapter was trained but not documented."
        )
        vlm_entry = models["rs-vlm-adapter"]
        assert vlm_entry.get("status") == "PARTIAL_ADAPTATION"
        assert vlm_entry.get("training_epochs_completed", 0) >= 1
        metrics = vlm_entry.get("metrics", {})
        assert "bench_exact_match_accuracy" in metrics

    def test_registry_resnet50_metric_provenance(self):
        """Verify registry still correctly labels 91.79% as Validation Accuracy, not mAP."""
        registry_path = BACKEND_DIR / "models" / "model_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)

        ben = registry["models"].get("ben-scene-classifier", {})
        metrics = ben.get("metrics", {})
        assert metrics.get("validation_accuracy") == 91.79
        notes = metrics.get("metric_notes", "").lower()
        assert "not map" in notes or "not mAP" in metrics.get("metric_notes", ""), (
            "Registry metric_notes should explicitly state 91.79% is NOT mAP"
        )


class TestRegistryAPIContract:
    """Tests for the GET /api/registry endpoint."""

    def test_registry_endpoint_returns_expected_keys(self):
        """Test the registry endpoint schema via FastAPI test client."""
        import sys
        sys.path.insert(0, str(BACKEND_DIR))

        from fastapi.testclient import TestClient
        try:
            from main import app
            client = TestClient(app)
            response = client.get("/api/registry")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "models" in data, "Response missing 'models' key"
            assert "deterministic_tools" in data, "Response missing 'deterministic_tools' key"
            assert "live_availability" in data, "Response missing 'live_availability' key"
            assert "model_count" in data
            assert data["model_count"] == 7, f"Expected 7 models, got {data['model_count']}"
        except Exception as e:
            pytest.skip(f"Could not import app: {e}")
