"""
Astra AI — Agentic End-to-End Workflow Verification Tests
SIH26167 | ISRO SAC

Validates all 9 primary agentic workflows through the complete pipeline:
QUERY -> GATEWAY -> PLANNER -> EXECUTOR -> EVIDENCE -> REPORT -> SSE:
1. LULC Scene Classification
2. Visual Question Answering (RSVQA + VLM fallback)
3. Narrative Scene Captioning (VRSBench)
4. Visual Grounding / Object Localization (VRSBench)
5. Bi-Temporal Change Detection (Siamese BIT)
6. Change-VQA (CDVQA)
7. Optical + SAR Cross-Modal Synthesis
8. Multi-Tool Composite Query (LULC + Area Quantification)
9. Error Handling / Invalid Input
"""

import asyncio
import io
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from starlette.testclient import TestClient

from backend.main import app, _run_investigation, _investigation_store
from backend.orchestrator.schemas import (
    ImageManifest, ModalityEnum, ModalityResult, InputManifest, StepStatus
)


@pytest.fixture
def optical_geotiff(tmp_path):
    """Create valid optical GeoTIFF in EPSG:3857."""
    p = tmp_path / "optical_test.tif"
    data = np.full((3, 128, 128), fill_value=120, dtype=np.uint8)
    transform = from_origin(100000.0, 200000.0, 10.0, 10.0)
    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        height=128,
        width=128,
        count=3,
        dtype="uint8",
        crs="EPSG:3857",
        transform=transform,
    ) as dst:
        dst.write(data)
    return p


@pytest.fixture
def sar_geotiff(tmp_path):
    """Create valid SAR GeoTIFF in EPSG:3857."""
    p = tmp_path / "sar_test.tif"
    data = np.full((2, 128, 128), fill_value=45, dtype=np.uint8)
    transform = from_origin(100000.0, 200000.0, 10.0, 10.0)
    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        height=128,
        width=128,
        count=2,
        dtype="uint8",
        crs="EPSG:3857",
        transform=transform,
    ) as dst:
        dst.write(data)
    return p


class TestAgenticWorkflows:
    """Complete 9-workflow verification suite."""

    @pytest.mark.asyncio
    async def test_workflow_1_lulc_classification(self, optical_geotiff):
        """Workflow 1: LULC scene classification query."""
        queue = asyncio.Queue()
        job_id = "test-job-wf1-lulc"
        await _run_investigation(
            job_id=job_id,
            query="Classify the land cover and categories in this scene",
            file_paths=[optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        assert evidence.trace.steps_succeeded >= 2
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "ben-scene-classifier" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_2_vqa_query(self, optical_geotiff):
        """Workflow 2: Remote sensing visual question answering."""
        queue = asyncio.Queue()
        job_id = "test-job-wf2-vqa"
        await _run_investigation(
            job_id=job_id,
            query="What type of landscape is present in this satellite image?",
            file_paths=[optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "rsvqa-specialist" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_3_caption_query(self, optical_geotiff):
        """Workflow 3: Scene captioning narrative description."""
        queue = asyncio.Queue()
        job_id = "test-job-wf3-caption"
        await _run_investigation(
            job_id=job_id,
            query="Describe this satellite scene in narrative detail",
            file_paths=[optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "vrsbench-caption" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_4_grounding_query(self, optical_geotiff):
        """Workflow 4: Referring expression visual grounding."""
        queue = asyncio.Queue()
        job_id = "test-job-wf4-grounding"
        await _run_investigation(
            job_id=job_id,
            query="Locate and ground the buildings and structures with bounding boxes",
            file_paths=[optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "vrsbench-grounding" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_5_change_detection_query(self, optical_geotiff):
        """Workflow 5: Bi-temporal change detection."""
        queue = asyncio.Queue()
        job_id = "test-job-wf5-change"
        await _run_investigation(
            job_id=job_id,
            query="Detect change between these two temporal scenes",
            file_paths=[optical_geotiff, optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "bit-change-detection" in tool_ids
        assert "change-area" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_6_change_vqa_query(self, optical_geotiff):
        """Workflow 6: Change visual question answering."""
        queue = asyncio.Queue()
        job_id = "test-job-wf6-cdvqa"
        await _run_investigation(
            job_id=job_id,
            query="What has changed between date 1 and date 2 in the residential area?",
            file_paths=[optical_geotiff, optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "bit-change-detection" in tool_ids
        assert "cdvqa-specialist" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_7_optical_sar_cross_modal(self, optical_geotiff, sar_geotiff):
        """Workflow 7: Optical + SAR multi-sensor cross-modal synthesis."""
        queue = asyncio.Queue()
        job_id = "test-job-wf7-crossmodal"
        await _run_investigation(
            job_id=job_id,
            query="Synthesize optical reflectance with SAR microwave backscatter",
            file_paths=[optical_geotiff, sar_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        tool_ids = [s.tool_id for s in evidence.trace.executed_steps]
        assert "cross-modal-specialist" in tool_ids

    @pytest.mark.asyncio
    async def test_workflow_8_multi_tool_composite(self, optical_geotiff):
        """
        Workflow 8: Multi-tool composite query:
        'What is the dominant land cover and approximately how much area does it cover?'
        """
        queue = asyncio.Queue()
        job_id = "test-job-wf8-composite"
        await _run_investigation(
            job_id=job_id,
            query="What is the dominant land cover and approximately how much area does it cover?",
            file_paths=[optical_geotiff],
            queue=queue,
        )
        assert job_id in _investigation_store
        report, evidence, _ = _investigation_store[job_id]
        assert len(evidence.findings) >= 1
        assert evidence.trace.steps_succeeded >= 2

    @pytest.mark.asyncio
    async def test_workflow_9_invalid_file_handling(self, tmp_path):
        """Workflow 9: Pipeline gracefully catches and emits error event for corrupted input."""
        corrupted_file = tmp_path / "corrupted.tif"
        corrupted_file.write_bytes(b"NOT_A_VALID_TIFF_HEADER")

        queue = asyncio.Queue()
        job_id = "test-job-wf9-corrupted"
        await _run_investigation(
            job_id=job_id,
            query="Analyze this scene",
            file_paths=[corrupted_file],
            queue=queue,
        )

        events = []
        while not queue.empty():
            events.append(await queue.get())

        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) >= 1, "Pipeline did not emit error event for corrupted input"
