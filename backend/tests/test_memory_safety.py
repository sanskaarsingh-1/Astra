"""
Astra AI — GPU Memory Safety & Model Residency Tests
SIH26167 | Target: NVIDIA RTX 5060 Laptop GPU (~8 GB VRAM)

Validates:
1. Model residency tracking across models.
2. Verification of torch.inference_mode() enforcement.
3. Verification that parameters have requires_grad=False (zero gradients).
4. Controlled offload to CPU and eviction.
5. Repeated inference execution memory stability (leak detection).
"""

import pytest
import torch
from backend.services.memory_manager import memory_manager, GPUMemoryManager


class TestGPUMemorySafety:
    """Test suite for memory safety and residency."""

    def test_vram_status_schema(self):
        """VRAM status returns valid dictionary with memory stats."""
        status = memory_manager.get_vram_status()
        assert isinstance(status, dict)
        assert "allocated_mb" in status
        assert "reserved_mb" in status
        assert "free_mb" in status
        assert "total_mb" in status

    def test_inference_mode_safety_and_no_gradients(self):
        """Verify models are configured safely without active gradient graphs."""
        audit = memory_manager.verify_inference_mode_safety()
        assert isinstance(audit, dict)
        assert "all_safe" in audit
        assert audit["all_safe"] is True, f"Unsafe model gradients detected: {audit}"

    def test_resident_models_query(self):
        """Querying resident models returns dict of loaded components."""
        resident = memory_manager.get_resident_models()
        assert isinstance(resident, dict)
        # Any resident model must have valid metadata
        for name, info in resident.items():
            assert "architecture" in info
            assert "parameters_count" in info
            assert info["parameters_count"] > 0
            assert info["requires_grad"] is False

    def test_controlled_offload_model_to_cpu(self):
        """Verify offloading a model to CPU changes device safely."""
        mgr = GPUMemoryManager()
        from backend.services.model_service import model_service
        # Reset and load
        model_service.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model = model_service.load_ben_classifier()
        if model_service.device.type == "cuda":
            model.to(model_service.device)

        # Offload to CPU
        success = mgr.offload_model("ben_classifier", to_cpu=True)
        assert success is True

        # Check parameter device
        m = model_service.models.get("ben_classifier")
        assert m is not None
        first_dev = next(m.parameters()).device
        assert first_dev.type == "cpu"

        # Restore back to default device for subsequent tests
        if torch.cuda.is_available():
            m.to("cuda:0")
            model_service.device = torch.device("cuda:0")

    def test_repeated_inference_memory_stability(self, tmp_path):
        """
        Run consecutive inference passes after warmup.
        Verify memory does not grow unbounded (no memory leak).
        """
        from PIL import Image
        from backend.services.model_service import model_service

        # Create dummy image
        img_path = tmp_path / "leak_test.png"
        img = Image.new("RGB", (224, 224), color=(100, 150, 200))
        img.save(img_path)

        # Warmup pass (initializes cuDNN convolution workspace buffers)
        model_service.load_ben_classifier()
        model_service.predict_scene(img_path)

        if torch.cuda.is_available():
            mem_initial = torch.cuda.memory_allocated()

        # 15 consecutive inferences
        for _ in range(15):
            res = model_service.predict_scene(img_path)
            assert "prediction" in res
            assert "confidence" in res

        if torch.cuda.is_available():
            mem_final = torch.cuda.memory_allocated()
            diff_mb = (mem_final - mem_initial) / (1024 ** 2)
            # Memory should remain flat after warmup (diff < 1.0 MB)
            assert diff_mb < 1.0, f"Memory leak detected! Grew by {diff_mb:.2f} MB after 15 passes."
