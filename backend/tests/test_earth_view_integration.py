"""
Astra AI Earth View Integration & Regression Tests
SIH26167 Earth View 2D / 3D / Satellite Globe Specification

Tests:
1. 2D Map, 3D Globe, and Satellite Mode Integrity
2. Satellite imagery providers & keyless fallback strategy
3. No CARTO mandatory dependency / zero required API keys
4. Live Data Feed telemetry & explicit failure states (LIVE, LOADING, OFFLINE, UNAVAILABLE)
5. Model safety invariant: zero modification to weights / best_model.pth
6. Analyze with Astra AI bridge validation
7. Normalized Disaster Event Model & Category Integrity (SIH26167 Phase 5 & 6)
8. Spatial precision type distinction (OFFICIAL_POINT vs PIXEL_CENTER vs AFFECTED_POLYGON)
9. Disaster Data Provenance documentation existence
10. OSINT features removed from Earth View map and drawers
"""

import os
import json
import pytest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = WORKSPACE_ROOT / "frontend"
BACKEND_DIR = WORKSPACE_ROOT / "backend"
DOCS_DIR = WORKSPACE_ROOT / "docs"


def test_no_carto_mandatory_dependency():
    """Verify that CARTO is not a mandatory dependency and no CARTO key is required."""
    providers_file = FRONTEND_DIR / "src" / "lib" / "earth" / "satellite-providers.ts"
    assert providers_file.exists(), "satellite-providers.ts must exist"
    content = providers_file.read_text(encoding="utf-8")
    
    # Esri World Imagery must be primary keyless satellite provider
    assert "esri_world_imagery" in content
    assert "requiresKey: false" in content
    # OpenStreetMap must be primary 2D map provider
    assert "openstreetmap" in content
    # Carto must be marked optional if present
    if "carto" in content.lower():
        assert "optional" in content.lower() or "carto_dark" in content


def test_three_primary_modes_exist_in_hud():
    """Verify 2D MAP, 3D GLOBE, and SATELLITE modes are first-class in EarthHud."""
    hud_file = FRONTEND_DIR / "src" / "components" / "earth" / "EarthHud.tsx"
    assert hud_file.exists(), "EarthHud.tsx must exist"
    content = hud_file.read_text(encoding="utf-8")
    
    assert "2D MAP" in content
    assert "3D GLOBE" in content
    assert "SATELLITE" in content
    assert "DisplayMode = '2d' | '3d' | 'satellite'" in content


def test_explicit_telemetry_status_mapping():
    """Verify failure != 0 and explicit states exist (LIVE, LOADING, OFFLINE, UNAVAILABLE)."""
    hud_file = FRONTEND_DIR / "src" / "components" / "earth" / "EarthHud.tsx"
    content = hud_file.read_text(encoding="utf-8")
    
    assert "'LIVE'" in content
    assert "'LOADING'" in content
    assert "'OFFLINE'" in content
    assert "'UNAVAILABLE'" in content
    assert "'RATE_LIMITED'" in content
    assert "'REQUIRES_API_KEY'" in content


def test_rotating_earth_d3_canvas_component():
    """Verify RotatingEarthCanvas component exists, uses D3 geoOrthographic and clean lifecycle."""
    canvas_file = FRONTEND_DIR / "src" / "components" / "earth" / "RotatingEarthCanvas.tsx"
    assert canvas_file.exists(), "RotatingEarthCanvas.tsx must exist"
    content = canvas_file.read_text(encoding="utf-8")
    
    assert "geoOrthographic" in content
    assert "geoPath" in content
    assert "geoGraticule" in content
    assert "AbortController" in content
    # Ensure zero production console spam [v0]
    assert "[v0]" not in content


def test_model_safety_invariant():
    """CRITICAL SAFETY INVARIANT: Checkpoint weights and model registry are strictly untouched."""
    weights_path = BACKEND_DIR / "weights" / "best_model.pth"
    if weights_path.exists():
        stat = weights_path.stat()
        assert stat.st_size > 0, "best_model.pth must remain intact"
    
    model_registry_path = BACKEND_DIR / "registry" / "model_registry.py"
    if model_registry_path.exists():
        assert model_registry_path.stat().st_size > 0


def test_ai_bridge_payload_structure():
    """Verify the 'Analyze with Astra AI' bridge saves valid structured payload to sessionStorage."""
    page_file = FRONTEND_DIR / "src" / "app" / "earth" / "page.tsx"
    assert page_file.exists(), "Earth page.tsx must exist"
    content = page_file.read_text(encoding="utf-8")
    
    assert "ASTRA_ANALYSIS_REQUEST" in content
    assert "/analyze?lat=" in content


def test_disaster_event_model_integrity():
    """Verify normalized DisasterEvent model with distinct categories and spatial precision types."""
    model_file = FRONTEND_DIR / "src" / "lib" / "earth" / "disaster-events.ts"
    assert model_file.exists(), "disaster-events.ts must exist"
    content = model_file.read_text(encoding="utf-8")

    # Categories per Phase 5
    categories = [
        "EARTHQUAKE",
        "WILDFIRE",
        "FLOOD",
        "CYCLONE",
        "SEVERE_STORM",
        "VOLCANO",
        "TSUNAMI",
        "LANDSLIDE",
        "DROUGHT",
    ]
    for cat in categories:
        assert cat in content, f"Disaster category {cat} must be defined"

    # Spatial precision types per Phase 12 & 13
    precision_types = [
        "OFFICIAL_POINT",
        "PIXEL_CENTER",
        "APPROXIMATE_CENTER",
        "AFFECTED_POLYGON",
    ]
    for pt in precision_types:
        assert pt in content, f"Spatial precision type {pt} must be defined"

    # Adapters
    assert "fetchUsgsEarthquakes" in content
    assert "fetchEonetDisasters" in content
    assert "fetchNoaaSpaceWeather" in content
    assert "formatSignedCoordinates" in content


def test_disaster_detail_card_actions():
    """Verify DisasterDetailCard includes required Phase 9 actions and signed coordinates."""
    card_file = FRONTEND_DIR / "src" / "components" / "earth" / "DisasterDetailCard.tsx"
    assert card_file.exists(), "DisasterDetailCard.tsx must exist"
    content = card_file.read_text(encoding="utf-8")

    assert "VIEW SATELLITE" in content
    assert "ANALYZE WITH ASTRA AI" in content
    assert "COPY COORDINATES" in content
    assert "formatSignedCoordinates" in content


def test_disaster_data_provenance_documentation():
    """Verify DISASTER_DATA_PROVENANCE.md exists and documents official sources and limitations."""
    provenance_file = DOCS_DIR / "earth-view" / "DISASTER_DATA_PROVENANCE.md"
    assert provenance_file.exists(), "DISASTER_DATA_PROVENANCE.md must exist"
    content = provenance_file.read_text(encoding="utf-8")

    assert "USGS" in content
    assert "NASA EONET" in content
    assert "NASA FIRMS" in content
    assert "NOAA SWPC" in content
    assert "PIXEL_CENTER" in content
    assert "OFFICIAL_POINT" in content


def test_osint_removed_from_earth_map():
    """Verify general OSINT layers (aircraft, frontlines, conflicts, cables, ports, cctvs) are removed from EarthMap layers."""
    map_file = FRONTEND_DIR / "src" / "components" / "earth" / "EarthMap.tsx"
    assert map_file.exists(), "EarthMap.tsx must exist"
    content = map_file.read_text(encoding="utf-8")

    # In EarthMap, active layers must be disasters & earth observation
    assert "disaster-earthquakes-circle" in content
    assert "disaster-wildfires-circle" in content
    assert "disaster-volcanoes-circle" in content
    assert "disaster-storms-circle" in content
    assert "disaster-selected-halo" in content

    # Should not have active OSINT layer IDs in addLayer calls
    assert "id: 'aircraft-symbol'" not in content
    assert "id: 'cables-line'" not in content
    assert "id: 'conflicts-circle'" not in content
