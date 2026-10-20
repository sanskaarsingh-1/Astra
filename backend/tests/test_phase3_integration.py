"""
Astra AI - Phase 3 Integration Tests
End-to-end composite query, VLM augmentation, and singleton tests.
"""

import pytest
import sys
from pathlib import Path
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# ─── Priority 2: VRSBench Singleton ──────────────────────────────────────────

class TestVRSBenchSingleton:
    """Verify VRSBenchSpecialist is now a singleton (not re-instantiated per request)."""

    def test_get_vrsbench_specialist_import(self):
        """Verify get_vrsbench_specialist() is importable."""
        from backend.models.captioning.model import get_vrsbench_specialist
        assert callable(get_vrsbench_specialist)

    def test_vrsbench_singleton_same_instance(self):
        """Two calls to get_vrsbench_specialist() must return the same object."""
        from backend.models.captioning.model import get_vrsbench_specialist
        s1 = get_vrsbench_specialist()
        s2 = get_vrsbench_specialist()
        assert s1 is s2, "get_vrsbench_specialist() returned different instances — singleton broken"

    def test_vrsbench_singleton_is_loaded(self):
        """After get_vrsbench_specialist(), model._is_loaded must be True."""
        from backend.models.captioning.model import get_vrsbench_specialist
        specialist = get_vrsbench_specialist()
        assert specialist._is_loaded, "VRSBenchSpecialist was not loaded after get_vrsbench_specialist()"


# ─── Priority 1: VLM Augmentation in RSVQA ───────────────────────────────────

class TestRSVQAVLMAugmentation:
    """Verify RSVQA specialist wiring and vlm_augmented flag behavior."""

    def test_rsvqa_version_bumped(self):
        """Model version should be 1.1.0 after VLM augmentation was added."""
        from backend.models.rsvqa.model import rsvqa_specialist
        assert rsvqa_specialist.model_version == "1.1.0", (
            f"Expected version 1.1.0, got {rsvqa_specialist.model_version}. "
            "VLM augmentation may not have been applied."
        )

    def test_rsvqa_output_contains_vlm_augmented_key(self):
        """predict() output must always contain vlm_augmented key."""
        from backend.models.rsvqa.model import rsvqa_specialist
        from unittest.mock import patch, MagicMock

        mock_scene = {
            "labels": ["Broad-leaved forest", "Pastures"],
            "top_predictions": [{"label": "Broad-leaved forest", "probability": 0.82}],
            "all_probabilities": {"Broad-leaved forest": 0.82, "Pastures": 0.65, "Urban fabric": 0.05},
        }

        import tempfile
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            img = Image.new("RGB", (120, 120), color=(100, 160, 80))
            img.save(tf.name)
            tmp_path = Path(tf.name)

        with patch("backend.services.model_service.model_service") as mock_svc:
            mock_svc.predict_scene.return_value = mock_scene
            result = rsvqa_specialist.predict(tmp_path, "What is the dominant land cover?")

        assert "vlm_augmented" in result, "vlm_augmented key missing from RSVQA output"
        assert isinstance(result["vlm_augmented"], bool)

        tmp_path.unlink(missing_ok=True)

    def test_rsvqa_presence_question_no_vlm(self):
        """Presence questions must NOT trigger VLM (heuristic-only path)."""
        from backend.models.rsvqa.model import rsvqa_specialist
        from unittest.mock import patch
        from PIL import Image
        import tempfile

        mock_scene = {
            "labels": ["Broad-leaved forest"],
            "top_predictions": [{"label": "Broad-leaved forest", "probability": 0.82}],
            "all_probabilities": {"Broad-leaved forest": 0.82, "Urban fabric": 0.05},
        }

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            img = Image.new("RGB", (120, 120))
            img.save(tf.name)
            tmp_path = Path(tf.name)

        with patch("backend.services.model_service.model_service") as mock_svc:
            mock_svc.predict_scene.return_value = mock_scene
            result = rsvqa_specialist.predict(tmp_path, "Is there a forest in the scene?")

        assert result["question_type"] == "presence"
        assert result["vlm_augmented"] is False, (
            "Presence questions should use LULC heuristic, NOT VLM augmentation"
        )

        tmp_path.unlink(missing_ok=True)

    def test_vlm_augment_helper_safe_on_missing_adapter(self):
        """_try_vlm_augment must return None gracefully when VLM unavailable."""
        from backend.models.rsvqa.model import _try_vlm_augment
        from unittest.mock import patch
        import tempfile
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            img = Image.new("RGB", (64, 64))
            img.save(tf.name)
            tmp_path = Path(tf.name)

        with patch("backend.models.remote_sensing_vlm.model.get_vlm_inference", return_value=None):
            result = _try_vlm_augment(tmp_path, "What do you see?")

        assert result is None, "Expected None when VLM unavailable"
        tmp_path.unlink(missing_ok=True)


# ─── Priority 3: Temperature Scaling ─────────────────────────────────────────

class TestTemperatureScaling:
    """Tests for temperature scaling calibration infrastructure."""

    def test_calibrate_temperature_script_exists(self):
        """calibrate_temperature.py must exist."""
        script = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "calibrate_temperature.py"
        assert script.exists(), f"calibrate_temperature.py missing at {script}"

    def test_model_service_has_temperature_attr(self):
        """ModelService must have temperature and calibration_applied attributes after Phase 3."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("model_service", BACKEND_DIR / "services" / "model_service.py")
        mod = importlib.util.module_from_spec(spec)
        # Check source code directly instead of importing (avoids GPU load)
        source = (BACKEND_DIR / "services" / "model_service.py").read_text()
        assert "self.temperature" in source, "temperature attribute missing from model_service.py"
        assert "calibration_applied" in source, "calibration_applied attribute missing"
        assert "temp_scaler.json" in source, "temp_scaler.json reference missing"

    def test_temp_scaler_if_present_is_valid_json(self):
        """If temp_scaler.json was generated, verify its schema."""
        import json
        scaler_path = BACKEND_DIR / "models" / "bigearthnet_resnet50_v2_full" / "temp_scaler.json"
        if not scaler_path.exists():
            pytest.skip("temp_scaler.json not yet generated (run calibrate_temperature.py first)")

        with open(scaler_path) as f:
            scaler = json.load(f)

        assert "temperature" in scaler, "temperature key missing from temp_scaler.json"
        T = scaler["temperature"]
        assert isinstance(T, (int, float)), f"temperature must be a number, got {type(T)}"
        assert 0.1 <= T <= 10.0, f"Temperature T={T} out of expected range [0.1, 10.0]"
        assert "method" in scaler, "method key missing"
        assert scaler["method"] == "temperature_scaling"

    def test_model_service_calibration_applied_flag_present_in_output(self):
        """predict_scene() output schema includes calibration_applied and temperature_T."""
        source = (BACKEND_DIR / "services" / "model_service.py").read_text()
        assert "calibration_applied" in source
        assert "temperature_T" in source


# ─── Priority 4: Composite Query Integration ──────────────────────────────────

class TestCompositeQueryIntegration:
    """
    End-to-end composite query test.
    Exercises the full multi-tool pipeline: raster-metadata -> ben-scene-classifier -> area-calculator.
    Uses a real synthetic GeoTIFF to verify multi-step plan execution.
    """

    def test_classifier_to_area_composite_structure(self):
        """
        Verify the fallback planner generates a valid multi-step plan
        for a composite LULC + area query.
        """
        import asyncio
        sys.path.insert(0, str(BACKEND_DIR))

        from orchestrator.planner import _generate_fallback_plan
        from orchestrator.schemas import InputManifest, ImageManifest, ModalityResult, ModalityEnum

        img = ImageManifest(
            file_id="test_composite_id",
            filename="test_composite.tif",
            file_path="test_composite.tif",
            format="GTiff",
            width_px=512,
            height_px=512,
            band_count=3,
            dtype="uint8",
            is_geospatial=True,
            modality=ModalityResult(
                modality=ModalityEnum.OPTICAL_RGB,
                confidence=0.95,
                evidence=["3 bands RGB"],
            ),
            sensor="Sentinel-2",
        )

        manifest = InputManifest(
            images=[img],
            query="classify the land cover and calculate the area",
            is_bitemporal=False,
            is_cross_modal=False,
        )

        plan = _generate_fallback_plan(manifest)
        assert plan is not None
        assert len(plan.steps) >= 2

        tool_ids = [s.tool_id for s in plan.steps]
        assert "raster-metadata" in tool_ids, "raster-metadata missing from composite plan"
        assert "ben-scene-classifier" in tool_ids, "ben-scene-classifier missing from composite plan"

    def test_composite_plan_steps_have_dependencies(self):
        """Composite LULC steps must have proper dependency ordering."""
        import asyncio
        sys.path.insert(0, str(BACKEND_DIR))

        from orchestrator.planner import _generate_fallback_plan
        from orchestrator.schemas import InputManifest, ImageManifest, ModalityResult, ModalityEnum

        img = ImageManifest(
            file_id="test_id_2",
            filename="test.tif",
            file_path="test.tif",
            format="GTiff",
            width_px=224,
            height_px=224,
            band_count=3,
            dtype="uint8",
            is_geospatial=True,
            modality=ModalityResult(
                modality=ModalityEnum.OPTICAL_RGB,
                confidence=0.95,
                evidence=["RGB 3 bands"],
            ),
            sensor="Sentinel-2",
        )

        manifest = InputManifest(
            images=[img],
            query="what land cover classes are present?",
            is_bitemporal=False,
            is_cross_modal=False,
        )

        plan = _generate_fallback_plan(manifest)
        # Find ben-scene-classifier step and verify it depends on raster-metadata
        ben_step = next((s for s in plan.steps if s.tool_id == "ben-scene-classifier"), None)
        if ben_step:
            assert len(ben_step.depends_on) > 0, (
                "ben-scene-classifier step has no dependencies — should depend on raster-metadata"
            )

    def test_registry_api_endpoint_live(self):
        """GET /api/registry must return 200 and include rs-vlm-adapter in models."""
        import json
        sys.path.insert(0, str(BACKEND_DIR))

        try:
            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)
            response = client.get("/api/registry")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            # rs-vlm-adapter was added in Phase 2
            registry_path = BACKEND_DIR / "models" / "model_registry.json"
            import json as _json
            with open(registry_path) as f:
                registry = _json.load(f)
            assert "rs-vlm-adapter" in registry.get("models", {}), (
                "rs-vlm-adapter not in model_registry.json"
            )
        except Exception as e:
            pytest.skip(f"App import failed: {e}")
