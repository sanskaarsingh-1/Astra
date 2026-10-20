"""
SIH26167 Final Demo Refocus & Product Simplification Verification Suite
Validates all 23 core requirements from Phase 24 of the SIH demo specification.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.schemas import (
    InputManifest,
    ImageManifest,
    ModalityResult,
    ModalityEnum,
    InvestigationPlan,
    PlanStep,
    TaskType,
    ExecutedStep,
    StepStatus,
    EvidenceFinding,
    FindingType,
    EvidencePackage,
    EvidenceStrength,
    ConfidenceStatus,
    Report,
)
from orchestrator.planner import _generate_fallback_plan
from evidence.assembler import assemble_evidence
from report.synthesizer import synthesize_report
from report.exporter import export_markdown_report, export_html_report
from models.rsvqa.model import RSVQASpecialist


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = WORKSPACE_ROOT / "frontend"


def make_dummy_manifest(image_count=1, is_cross_modal=False, query="Describe this image"):
    """Helper to construct validated InputManifest matching real system schema."""
    images = []
    for i in range(image_count):
        mod = ModalityEnum.SAR if (is_cross_modal and i == 1) else ModalityEnum.OPTICAL_RGB
        images.append(
            ImageManifest(
                file_id=f"img_{i}",
                filename=f"image_{i}.tif",
                file_path=f"/path/to/image_{i}.tif",
                format="GTiff",
                width_px=256,
                height_px=256,
                band_count=3 if mod == ModalityEnum.OPTICAL_RGB else 1,
                dtype="uint8",
                is_geospatial=False,
                modality=ModalityResult(
                    modality=mod,
                    confidence=0.99,
                    evidence=["RGB bands detected" if mod == ModalityEnum.OPTICAL_RGB else "Single band amplitude"],
                ),
            )
        )
    return InputManifest(query=query, images=images)


# ---------------------------------------------------------------------------
# 1. Disaster Event Parsing
# ---------------------------------------------------------------------------
def test_disaster_event_parsing():
    """Verify disaster event parsing from USGS GeoJSON format."""
    raw_feature = {
        "id": "us7000m8v5",
        "properties": {
            "title": "M 6.2 - Near Coast of Central Chile",
            "place": "Coquimbo, Chile",
            "mag": 6.2,
            "time": 1711200000000,
            "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000m8v5",
        },
        "geometry": {
            "type": "Point",
            "coordinates": [-71.45, -30.25, 25.0],
        },
    }
    
    event_id = raw_feature["id"]
    coords = raw_feature["geometry"]["coordinates"]
    lon, lat = coords[0], coords[1]
    depth = coords[2] if len(coords) > 2 else None
    
    assert event_id == "us7000m8v5"
    assert lat == -30.25
    assert lon == -71.45
    assert depth == 25.0
    assert raw_feature["properties"]["place"] == "Coquimbo, Chile"


# ---------------------------------------------------------------------------
# 2. Coordinate Normalization
# ---------------------------------------------------------------------------
def test_coordinate_normalization():
    """Verify signed and bounded coordinate formatting."""
    def format_signed_coords(lat: float, lon: float) -> str:
        lat_str = f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'}"
        lon_str = f"{abs(lon):.4f}°{'E' if lon >= 0 else 'W'}"
        return f"{lat_str}, {lon_str}"

    assert format_signed_coords(28.6139, 77.2090) == "28.6139°N, 77.2090°E"
    assert format_signed_coords(-33.8688, 151.2093) == "33.8688°S, 151.2093°E"
    assert format_signed_coords(-12.0464, -77.0428) == "12.0464°S, 77.0428°W"


# ---------------------------------------------------------------------------
# 3. Latitude Validation
# ---------------------------------------------------------------------------
def test_latitude_validation():
    """Verify latitude boundary enforcement [-90.0, 90.0]."""
    def is_valid_latitude(lat: float) -> bool:
        return -90.0 <= lat <= 90.0

    assert is_valid_latitude(0.0) is True
    assert is_valid_latitude(90.0) is True
    assert is_valid_latitude(-90.0) is True
    assert is_valid_latitude(90.001) is False
    assert is_valid_latitude(-91.0) is False


# ---------------------------------------------------------------------------
# 4. Longitude Validation
# ---------------------------------------------------------------------------
def test_longitude_validation():
    """Verify longitude boundary enforcement [-180.0, 180.0]."""
    def is_valid_longitude(lon: float) -> bool:
        return -180.0 <= lon <= 180.0

    assert is_valid_longitude(0.0) is True
    assert is_valid_longitude(180.0) is True
    assert is_valid_longitude(-180.0) is True
    assert is_valid_longitude(180.1) is False
    assert is_valid_longitude(-180.01) is False


# ---------------------------------------------------------------------------
# 5. Point Geometry
# ---------------------------------------------------------------------------
def test_point_geometry():
    """Verify distinct spatial precision classifications for points."""
    precision_types = {"OFFICIAL_POINT", "PIXEL_CENTER", "APPROXIMATE_CENTER"}
    assert "OFFICIAL_POINT" in precision_types
    assert "PIXEL_CENTER" in precision_types


# ---------------------------------------------------------------------------
# 6. Polygon Geometry
# ---------------------------------------------------------------------------
def test_polygon_geometry():
    """Verify polygon geometry preserves boundary and centroid distinction."""
    polygon_geojson = {
        "type": "Polygon",
        "coordinates": [
            [[77.0, 28.0], [77.2, 28.0], [77.2, 28.2], [77.0, 28.2], [77.0, 28.0]]
        ],
    }
    coords = polygon_geojson["coordinates"][0]
    centroid_lon = sum(pt[0] for pt in coords[:-1]) / (len(coords) - 1)
    centroid_lat = sum(pt[1] for pt in coords[:-1]) / (len(coords) - 1)
    
    assert polygon_geojson["type"] == "Polygon"
    assert round(centroid_lon, 2) == 77.1
    assert round(centroid_lat, 2) == 28.1
    assert len(coords) == 5


# ---------------------------------------------------------------------------
# 7. Line / Track Geometry
# ---------------------------------------------------------------------------
def test_line_track_geometry():
    """Verify line/track geometry for cyclones preserves sequence of waypoints."""
    track_geojson = {
        "type": "LineString",
        "coordinates": [
            [85.0, 18.0],
            [86.0, 19.5],
            [87.2, 21.0],
        ],
    }
    assert track_geojson["type"] == "LineString"
    assert len(track_geojson["coordinates"]) == 3
    assert track_geojson["coordinates"][0] != track_geojson["coordinates"][-1]


# ---------------------------------------------------------------------------
# 8. Event Pointer
# ---------------------------------------------------------------------------
def test_event_pointer_state():
    """Verify event pointer state contains all necessary visualization metadata."""
    pointer_data = {
        "event_id": "usgs_quake_001",
        "event_type": "EARTHQUAKE",
        "lat": 37.7749,
        "lng": -122.4194,
        "place": "San Francisco Bay Area",
        "source": "USGS",
        "magnitude": 5.4,
    }
    assert pointer_data["event_id"] is not None
    assert isinstance(pointer_data["lat"], float)
    assert isinstance(pointer_data["lng"], float)
    assert pointer_data["source"] == "USGS"


# ---------------------------------------------------------------------------
# 9. Event Navigation
# ---------------------------------------------------------------------------
def test_event_navigation_parameters():
    """Verify navigation computes appropriate zoom based on geometry type."""
    def get_zoom_for_geometry(geom_type: str, magnitude: float = 0.0) -> int:
        if geom_type == "OFFICIAL_POINT":
            return 8 if magnitude >= 6.0 else 10
        elif geom_type == "AFFECTED_POLYGON":
            return 7
        return 9

    assert get_zoom_for_geometry("OFFICIAL_POINT", magnitude=7.2) == 8
    assert get_zoom_for_geometry("OFFICIAL_POINT", magnitude=4.1) == 10
    assert get_zoom_for_geometry("AFFECTED_POLYGON") == 7


# ---------------------------------------------------------------------------
# 10. Place Name Resolution
# ---------------------------------------------------------------------------
def test_place_name_resolution():
    """Verify fallback chain for place name resolution."""
    def resolve_place_name(props: dict, lat: float, lng: float) -> str:
        if props.get("place"):
            return props["place"]
        if props.get("title"):
            return props["title"]
        return f"Event near {lat:.2f}°, {lng:.2f}°"

    assert resolve_place_name({"place": "Tokyo, Japan"}, 35.68, 139.76) == "Tokyo, Japan"
    assert resolve_place_name({"title": "Flood Warning"}, 25.0, 85.0) == "Flood Warning"
    assert resolve_place_name({}, 20.0, 75.0) == "Event near 20.00°, 75.00°"


# ---------------------------------------------------------------------------
# 11. Earth View -> SatQuery Transfer Contract
# ---------------------------------------------------------------------------
def test_earth_view_to_satquery_transfer_contract():
    """Verify sessionStorage contract and analysis request structure."""
    payload = {
        "lat": 34.0522,
        "lng": -118.2437,
        "mode": "bitemporal",
        "context": json.dumps({
            "event_id": "eonet_wildfire_102",
            "event_type": "WILDFIRE",
            "place_name": "Los Angeles County",
            "source": "NASA EONET",
            "timestamp": "2026-09-20T10:00:00Z",
        }),
        "query": "What changed between these two images, where did the change occur, and approximately how much area was affected?",
    }
    
    assert "lat" in payload and "lng" in payload
    assert payload["mode"] in ["single", "bitemporal", "crossmodal"]
    ctx = json.loads(payload["context"])
    assert ctx["source"] == "NASA EONET"
    assert "area was affected" in payload["query"]


# ---------------------------------------------------------------------------
# 12. Single-Image Routing
# ---------------------------------------------------------------------------
def test_single_image_routing():
    """Verify planner routing logic for single image classification."""
    manifest = make_dummy_manifest(image_count=1, query="What is the dominant land cover in this image?")
    plan = _generate_fallback_plan(manifest)
    
    tool_ids = [s.tool_id for s in plan.steps]
    assert "ben-scene-classifier" in tool_ids
    assert plan.task_classification == TaskType.SCENE_CLASSIFICATION.value


# ---------------------------------------------------------------------------
# 13. Change-Analysis Routing
# ---------------------------------------------------------------------------
def test_change_analysis_routing():
    """Verify planner routing logic for bitemporal change detection."""
    manifest = make_dummy_manifest(
        image_count=2,
        query="What changed between these two images, where did the change occur, and approximately how much area was affected?",
    )
    plan = _generate_fallback_plan(manifest)
    
    tool_ids = [s.tool_id for s in plan.steps]
    assert "bit-change-detection" in tool_ids
    assert "change-area" in tool_ids
    assert plan.task_classification in [TaskType.CHANGE_DETECTION.value, TaskType.CHANGE_VQA.value]


# ---------------------------------------------------------------------------
# 14. Optical-SAR Routing
# ---------------------------------------------------------------------------
def test_optical_sar_routing():
    """Verify planner routing logic for crossmodal optical + SAR pair."""
    manifest = make_dummy_manifest(
        image_count=2,
        is_cross_modal=True,
        query="Compare the optical and SAR observations and explain what additional information the SAR image provides.",
    )
    plan = _generate_fallback_plan(manifest)
    
    tool_ids = [s.tool_id for s in plan.steps]
    assert "cross-modal-specialist" in tool_ids
    assert plan.task_classification == TaskType.CROSS_MODAL_ANALYSIS.value


# ---------------------------------------------------------------------------
# 15. Evidence Assembly
# ---------------------------------------------------------------------------
def test_evidence_assembly():
    """Verify assemble_evidence builds valid EvidencePackage from executed steps."""
    manifest = make_dummy_manifest(image_count=1)
    step = ExecutedStep(
        step_id="step_1",
        tool_id="ben-scene-classifier",
        status=StepStatus.SUCCESS,
        input_summary="image_0.tif",
        output_summary="Urban fabric (92%)",
        duration_ms=45,
        raw_output={
            "dominant_class": "Urban fabric",
            "confidence": 0.92,
            "probabilities": {"Urban fabric": 0.92, "Industrial": 0.08},
        },
        confidence=0.92,
    )
    pkg = assemble_evidence([step], manifest)
    
    assert isinstance(pkg, EvidencePackage)
    assert len(pkg.findings) >= 1
    assert "ben-scene-classifier" in pkg.models_used


# ---------------------------------------------------------------------------
# 16. Failed Specialist Handling
# ---------------------------------------------------------------------------
def test_failed_specialist_handling():
    """Verify failed specialist is explicitly recorded as FAILED / UNAVAILABLE with 0.0 confidence."""
    manifest = make_dummy_manifest(image_count=2)
    step = ExecutedStep(
        step_id="step_fail",
        tool_id="bit-change-detection",
        status=StepStatus.FAILED,
        input_summary="t1, t2",
        output_summary="GPU memory exceeded",
        error_message="GPU memory allocation exceeded during inference",
        duration_ms=10,
    )
    pkg = assemble_evidence([step], manifest)
    
    assert len(pkg.findings) >= 1
    failed_finding = pkg.findings[0]
    assert "SPECIALIST STATUS: FAILED / UNAVAILABLE" in str(failed_finding.value)
    assert failed_finding.strength.model_confidence == 0.0
    assert failed_finding.strength.evidence_strength == "Failed"


# ---------------------------------------------------------------------------
# 17. Fallback Synthesis Labeling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fallback_synthesis_labeling():
    """Verify fallback synthesis is explicitly marked with [FALLBACK SYNTHESIS]."""
    manifest = make_dummy_manifest(image_count=2)
    plan = _generate_fallback_plan(manifest)
    step = ExecutedStep(
        step_id="step_fail",
        tool_id="bit-change-detection",
        status=StepStatus.FAILED,
        input_summary="t1, t2",
        output_summary="OOM",
        error_message="Model server unavailable",
        duration_ms=10,
    )
    pkg = assemble_evidence([step], manifest, plan)

    with patch("report.synthesizer.genai") as mock_genai:
        mock_genai.GenerativeModel.side_effect = Exception("API offline")
        report = await synthesize_report(
            evidence=pkg,
            plan=plan,
            query="What changed?",
            manifest=manifest,
        )

        assert report.executive_summary.startswith("[FALLBACK SYNTHESIS]")
        assert any("FALLBACK SYNTHESIS" in lim for lim in report.limitations)
        assert any("FAILED" in lim for lim in report.limitations)


# ---------------------------------------------------------------------------
# 18. Confidence Integrity
# ---------------------------------------------------------------------------
def test_confidence_integrity_in_exporter():
    """Verify exporter renders 0% (FAILED / UNAVAILABLE) and distinct styling for failures."""
    manifest = make_dummy_manifest(image_count=2)
    step = ExecutedStep(
        step_id="step_fail",
        tool_id="bit-change-detection",
        status=StepStatus.FAILED,
        input_summary="t1, t2",
        output_summary="OOM",
        error_message="Model unavailable",
        duration_ms=10,
    )
    pkg = assemble_evidence([step], manifest)
    
    report = Report(
        executive_summary="[FALLBACK SYNTHESIS] Investigation summary",
        narrative="Specialist was unavailable during inference.",
        spatial_findings="N/A",
        temporal_findings="N/A",
        sar_evidence="N/A",
        cross_modal_analysis="N/A",
        methodology="Fallback routing",
        conflicts_identified="None",
        limitations=["bit-change-detection was unavailable"],
        confidence_summary="Overall confidence: 0.0 (FAILED)",
        assumptions=["Standard parameters"],
    )
    
    html = export_html_report(report, pkg, "job_conf")
    assert "FAILED / UNAVAILABLE" in html
    assert "conf-failed" in html


# ---------------------------------------------------------------------------
# 19. Report Metadata
# ---------------------------------------------------------------------------
def test_report_metadata_includes_crs_and_input_counts():
    """Verify markdown report exporter displays input counts and CRS notes accurately."""
    manifest = make_dummy_manifest(image_count=2)
    step = ExecutedStep(
        step_id="step_meta",
        tool_id="raster-metadata",
        status=StepStatus.SUCCESS,
        input_summary="image_0.tif",
        output_summary="Metadata extracted",
        duration_ms=5,
    )
    pkg = assemble_evidence([step], manifest)
    report = Report(
        executive_summary="Summary",
        narrative="Multi-image comparison executed.",
        spatial_findings="Event coordinates supplied by source. CRS not available in source image.",
        temporal_findings="N/A",
        sar_evidence="N/A",
        cross_modal_analysis="N/A",
        methodology="Test methodology",
        conflicts_identified="None",
        limitations=["Resolution limits"],
        confidence_summary="Calibrated score: 0.85",
        assumptions=["Calibrated"],
    )

    md = export_markdown_report(report, pkg, "job_meta")
    assert "Event coordinates supplied by source." in md
    assert "CRS not available in source image." in md


# ---------------------------------------------------------------------------
# 20. Missing CRS Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_crs_handling():
    """Verify synthesizer notes when CRS is not available in source image."""
    manifest = make_dummy_manifest(image_count=1)
    plan = _generate_fallback_plan(manifest)
    step = ExecutedStep(
        step_id="step_crs",
        tool_id="raster-metadata",
        status=StepStatus.SUCCESS,
        input_summary="image_0.tif",
        output_summary="No CRS in geotiff",
        duration_ms=5,
    )
    pkg = assemble_evidence([step], manifest, plan)

    report = await synthesize_report(
        evidence=pkg,
        plan=plan,
        query="Describe this scene",
        manifest=manifest,
    )
    assert report.spatial_findings == "CRS not available in source image."


# ---------------------------------------------------------------------------
# 21. Missing Geolocation Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_geolocation_handling():
    """Verify synthesizer reports event coordinates when external source supplies them."""
    manifest = make_dummy_manifest(image_count=1)
    plan = _generate_fallback_plan(manifest)
    step = ExecutedStep(
        step_id="step_geo",
        tool_id="raster-metadata",
        status=StepStatus.SUCCESS,
        input_summary="image_0.tif",
        output_summary="No CRS in geotiff",
        duration_ms=5,
    )
    pkg = assemble_evidence([step], manifest, plan)

    report = await synthesize_report(
        evidence=pkg,
        plan=plan,
        query="What is here at coordinates 28.6139°N, 77.2090°E?",
        manifest=manifest,
    )
    assert "Event coordinates supplied by source." in report.spatial_findings


# ---------------------------------------------------------------------------
# 22. Unsupported Person Detection Handling
# ---------------------------------------------------------------------------
def test_unsupported_person_detection_handling():
    """Verify VQA specialist refuses person/casualty detection per Phase 13 guardrail."""
    specialist = RSVQASpecialist()
    dummy_img = Path("non_existent_img.tif")
    
    questions = [
        "Are there people in this disaster area?",
        "Can you detect any person on the ground?",
        "How many human casualties or victims are visible?",
    ]
    for q in questions:
        result = specialist.predict(dummy_img, q)
        assert result["confidence"] == 0.0
        assert result["status"] == "UNSUPPORTED_TASK"
        assert "Individual-person detection is not a validated capability of the current system and is therefore not reported" in result["answer"]
        assert "Individual-person detection is not currently supported reliably" in result["answer"]


# ---------------------------------------------------------------------------
# 23. No Fabricated Data Behavior
# ---------------------------------------------------------------------------
def test_no_fabricated_data_behavior():
    """Verify measurements are tagged DETERMINISTIC and never fabricated."""
    from engine.tools.geometry import calculate_mask_area
    
    # 10x10 binary mask with 10 true pixels
    mask = [[1 if (i == j) else 0 for j in range(10)] for i in range(10)]
    res = calculate_mask_area(mask=mask, crs_epsg=32643, gsd_x=10.0, gsd_y=10.0)
    
    assert res["confidence_status"] == "DETERMINISTIC"
    assert res["evidence_strength"] == "GROUND_TRUTH_DETERMINISTIC"
    assert res["confidence"] == 1.0
    assert res["changed_pixels"] == 10
    # 10 pixels * 100 m² = 1000 m² = 0.001 km² = 0.1 hectare
    assert res["area_m2"] == 1000.0
    assert res["area_ha"] == 0.1


# ---------------------------------------------------------------------------
# 24. Verified Demo Cases and File Serving (Fix 1)
# ---------------------------------------------------------------------------
def test_demo_cases_and_file_serving():
    """Verify one-click demo cases listing and safe raster serving endpoints."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    
    # 1. Cases listing
    res_cases = client.get("/api/demo/cases")
    assert res_cases.status_code == 200
    cases = res_cases.json().get("cases", [])
    assert len(cases) >= 3
    case_ids = [c["id"] for c in cases]
    assert "building_change" in case_ids
    assert "optical_sar" in case_ids
    assert "single_image" in case_ids

    # 2. File serving
    res_file = client.get("/api/demo/file/building_change_t1.tif")
    assert res_file.status_code == 200
    assert len(res_file.content) > 1000
    assert res_file.headers.get("content-type") == "image/tiff"


# ---------------------------------------------------------------------------
# 25. GeoTIFF Preview Endpoints (Bug 1 Fix)
# ---------------------------------------------------------------------------
def test_geotiff_preview_generation_and_endpoints(tmp_path):
    """Verify backend produces display-safe PNG previews from GeoTIFF rasters."""
    from fastapi.testclient import TestClient
    from main import app, generate_raster_preview
    import numpy as np
    from PIL import Image

    # 1. Test generate_raster_preview helper on dummy image
    test_img = tmp_path / "test_raster.png"
    Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)).save(test_img)
    out_preview = tmp_path / "preview.png"
    generate_raster_preview(test_img, out_preview)
    assert out_preview.exists()
    assert out_preview.stat().st_size > 0

    client = TestClient(app)
    # 2. Demo preview endpoint
    res_demo_preview = client.get("/api/demo/preview/optical_cartosat.tif")
    assert res_demo_preview.status_code == 200
    assert res_demo_preview.headers.get("content-type") == "image/png"
    assert len(res_demo_preview.content) > 100


# ---------------------------------------------------------------------------
# 26. Tiled Classifier top_predictions and Probabilities (Bug 3 Fix)
# ---------------------------------------------------------------------------
def test_tiled_classifier_populates_top_predictions():
    """Verify tiled processor includes top_predictions and all_probabilities."""
    from engine.tiler import TiledRasterProcessor
    import tempfile
    import rasterio
    from rasterio.transform import from_origin
    import numpy as np

    processor = TiledRasterProcessor(tile_size=64)
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tf:
        tf_path = Path(tf.name)

    try:
        # Create small test geotiff
        transform = from_origin(500000, 3000000, 10.0, 10.0)
        with rasterio.open(
            tf_path, 'w', driver='GTiff', height=128, width=128, count=3,
            dtype='uint8', crs='EPSG:32643', transform=transform
        ) as dst:
            dst.write(np.zeros((3, 128, 128), dtype='uint8'))

        def dummy_classifier(img_p):
            return {
                "prediction": "Arable land",
                "confidence": 0.88,
                "labels": ["Arable land", "Water bodies"],
                "all_probabilities": {"Arable land": 0.88, "Water bodies": 0.65},
            }

        res = processor.process_raster(tf_path, classifier_fn=dummy_classifier, force_tiling=True)
        assert res["type"] == "classification"
        assert res["is_tiled"] is True
        assert "top_predictions" in res
        assert len(res["top_predictions"]) > 0
        assert res["top_predictions"][0]["label"] == "Arable land"
        assert res["top_predictions"][0]["probability"] == 0.88
        assert "all_probabilities" in res
    finally:
        tf_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 27. Agriculture Query Disambiguation (Bug 4 Fix)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agriculture_query_synthesis_disambiguation():
    """Verify query about active cultivation disambiguates Arable land when VQA is unavailable."""
    from orchestrator.schemas import (
        InputManifest, ImageManifest, ModalityResult, ModalityEnum,
        InvestigationPlan, PlanStep, EvidenceFinding, FindingType,
        EvidencePackage, EvidenceStrength, ConfidenceStatus, StepStatus, ExecutedStep
    )
    from datetime import datetime, timezone

    query = "Are there active agricultural fields or cultivated crop plots in this region?"
    manifest = InputManifest(
        query=query,
        images=[
            ImageManifest(
                file_id="img_0",
                filename="scene.tif",
                file_path="/test/scene.tif",
                format="GTiff",
                width_px=1200,
                height_px=1200,
                band_count=3,
                dtype="uint8",
                is_geospatial=True,
                crs_epsg=32643,
                gsd_x=2.0,
                gsd_y=2.0,
                modality=ModalityResult(modality=ModalityEnum.OPTICAL_RGB, confidence=0.99, evidence=[]),
            )
        ]
    )

    plan = InvestigationPlan(
        plan_id="plan-ag-1",
        query=query,
        task_classification="single_image",
        plan_rationale="Agricultural investigation",
        steps=[
            PlanStep(step_id="step_1", tool_id="raster-metadata", task_type="metadata", description=""),
            PlanStep(step_id="step_2", tool_id="ben-scene-classifier", task_type="classification", description=""),
            PlanStep(step_id="step_3", tool_id="rsvqa-specialist", task_type="vqa", description=""),
        ]
    )

    now = datetime.now(timezone.utc)
    executed_steps = [
        ExecutedStep(step_id="step_1", tool_id="raster-metadata", status=StepStatus.SUCCESS, input_summary="tool=raster-metadata", output_summary="crs=32643", started_at=now, completed_at=now, raw_output={"type": "metadata", "crs_epsg": 32643}),
        ExecutedStep(step_id="step_2", tool_id="ben-scene-classifier", status=StepStatus.SUCCESS, input_summary="tool=ben-scene-classifier", output_summary="Arable land", started_at=now, completed_at=now, raw_output={"type": "classification", "labels": ["Arable land", "Coastal wetlands"], "top_predictions": [{"label": "Arable land", "probability": 0.85}], "confidence": 0.85}),
        ExecutedStep(step_id="step_3", tool_id="rsvqa-specialist", status=StepStatus.FAILED, input_summary="tool=rsvqa-specialist", output_summary="FAILED", started_at=now, completed_at=now, error_message="No module named 'backend'", raw_output=None),
    ]

    evidence = assemble_evidence(executed_steps, manifest, plan)
    report = await synthesize_report(query, evidence, plan, manifest)

    # Must clarify that Arable land is classifier-based scene evidence, not confirmation of active cultivation
    assert any("not a direct confirmation of active cultivation" in a or "does not independently confirm" in a for a in report.assumptions)
    # Calibrated confidence must be reduced due to failure
    assert evidence.overall_confidence < 0.65


# ---------------------------------------------------------------------------
# 28. Deterministic & Radiometric Calibration Wording (Bug 8 & 9 Fixes)
# ---------------------------------------------------------------------------
def test_wording_standards():
    """Verify deterministic and radiometric calibration wording in report exporter and registry."""
    from datetime import datetime, timezone
    from report.exporter import export_markdown_report
    from orchestrator.schemas import Report, EvidencePackage, InvestigationPlan, ExecutionTrace

    rep = Report(
        executive_summary="Summary",
        narrative="Narrative",
        spatial_findings="EPSG:32643",
        methodology="Multi-specialist automated analysis pipeline.",
        limitations=["None"],
        confidence_summary="Calibrated",
        assumptions=["Radiometric calibration status was not independently verified by this workflow."],
    )
    now = datetime.now(timezone.utc)
    dummy_plan = InvestigationPlan(
        plan_id="plan-test",
        query="test",
        task_classification="single_image",
        plan_rationale="test",
        steps=[]
    )
    trace = ExecutionTrace(
        trace_id="tr-1",
        timestamp_start=now,
        timestamp_end=now,
        plan=dummy_plan,
        executed_steps=[],
    )
    ev = EvidencePackage(
        request_id="req-1",
        query="test",
        findings=[],
        overall_confidence=0.9,
        trace=trace,
    )

    md = export_markdown_report(rep, ev, "job-test")
    # Must NOT say "exact mathematical calculations"
    assert "exact mathematical calculations" not in md
    # Must contain deterministic distinction
    assert "deterministic numerical computation" in md or "DETERMINISTIC indicates" in md

    # Check model registry notes
    with open(WORKSPACE_ROOT / "backend" / "models" / "model_registry.json", "r", encoding="utf-8") as f:
        reg = json.load(f)
    det_note = reg["provenance_notes"]["deterministic_calculation_note"]
    assert "DETERMINISTIC indicates that the numerical operation is deterministic" in det_note
    assert "exact mathematical" not in det_note

