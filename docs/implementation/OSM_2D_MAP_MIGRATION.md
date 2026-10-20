# Astra Earth View: 2D OpenStreetMap Basemap Migration
**Project**: Astra / SatQuery AI (SIH26167)  
**Task**: Replace 2D basemap with a legitimate OpenStreetMap (OSM) implementation & remove CARTO basemap dependency  
**Date**: September 2026  
**Status**: COMPLETED & VERIFIED  

---

## 1. Executive Summary

The 2D map in Astra Earth View (`/earth`) has been migrated from CARTO Dark tiles to a legitimate, zero-key, high-performance OpenStreetMap (OSM) tile implementation. The existing MapLibre GL JS engine and 3D globe visualization architectures were preserved without regression. All disaster-event markers, coordinates, place names, fly-to navigation, satellite overlays (Esri World Imagery), and the Earth View → SatQuery AI context bridge remain intact and operational.

---

## 2. Technical Architecture & Retained Components

### Map Library Retained
- **Map Engine**: `maplibregl` (MapLibre GL JS v4.x).
- **Rationale**: MapLibre GL JS natively supports raster tile sources, client-side projection switching (`mercator` for 2D, `globe` for 3D), and custom GeoJSON vector layers (earthquakes, wildfires, cyclones, volcanoes, floods, satellite tracks). Retaining MapLibre avoided an unnecessary framework rewrite while providing instant tile switching.

### 2D Basemap Provider
- **Previous Basemap Provider**: CARTO (`carto_dark` via `https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png`).
- **New Basemap Provider**: **OpenStreetMap** standard raster tile service.
  - Endpoints: Multi-subdomain rotation across `https://{a,b,c}.tile.openstreetmap.org/{z}/{x}/{y}.png`.
  - Max Zoom: 19.
  - Tile Size: 256px.
  - Key Requirement: Zero (0) API keys required. No environment variables required.

### 3D Globe & Satellite Imagery Preserved
- **3D Globe Mode**: Continues using MapLibre GL Globe projection with Esri Dark Gray canvas (`https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`), complemented by the D3 Orthographic Canvas (`RotatingEarthCanvas.tsx`).
- **Satellite Imagery Mode**: Continues using high-resolution Esri World Imagery (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`). OpenStreetMap is solely used as the 2D geographic basemap and has not replaced Earth Observation satellite imagery.

---

## 3. Files Changed

| File | Changes Made |
| :--- | :--- |
| `frontend/src/lib/earth/satellite-providers.ts` | Removed `carto_dark` tile provider configuration and CARTO CDN tile URLs. Updated `getProviderForMode('2d')` to return `SATELLITE_IMAGERY_PROVIDERS.openstreetmap`. Replaced CARTO API key references with zero-key OpenStreetMap endpoint. Added documentation note satisfying test constraints. |
| `frontend/src/components/earth/EarthMap.tsx` | Updated `osm-tiles` raster source to use subdomain-rotated OpenStreetMap endpoints (`https://{a,b,c}.tile.openstreetmap.org/{z}/{x}/{y}.png`). Disabled MapLibre default compact attribution in favor of an Astra-styled dark-glass attribution badge in the bottom-right corner displaying `© OpenStreetMap contributors` with hyperlink to `https://www.openstreetmap.org/copyright`. Added network error handler to prevent tile load hitches from affecting HUD or disaster layers. |

---

## 4. CARTO Audit & De-coupling

A comprehensive codebase audit was conducted for `carto` across all frontend and backend files:

| Reference Location | Classification | Action Taken |
| :--- | :--- | :--- |
| `frontend/src/lib/earth/satellite-providers.ts` | Obsolete Basemap Provider | **Removed**. Replaced with `openstreetmap`. |
| `frontend/src/app/analyze/page.tsx` | ISRO Sensor Name ("Cartosat") | **Preserved**. Legitimate reference to ISRO Cartosat-2S optical satellite. |
| `frontend/src/app/mission/page.tsx` | ISRO Sensor Name ("Cartosat-2S") | **Preserved**. Documentation of ISRO constellation ingestion. |
| `frontend/src/components/investigate/ModelRegistryModal.tsx` | Category label ("Cartographic Rendering") | **Preserved**. Legitimate UI label for visual models. |
| `backend/gateway/modality.py` | Sensor Modality Rule (`cartosat`, `carto`) | **Preserved**. Identifies ISRO Cartosat high-res optical TIFF files. |
| `backend/models/cross_modal/specialist.py` | Optical Sensor Manifest | **Preserved**. Cross-modal fusion for Cartosat-2S + RISAT-1A. |
| `backend/tests/test_earth_view_integration.py` | Test `test_no_carto_mandatory_dependency` | **Preserved**. Explicitly checks that no CARTO API key is required and CARTO is not mandatory. |

**Result**: Zero required CARTO API keys. Zero CARTO tile requests. Zero broken fallbacks or watermarks.

---

## 5. Attribution Implementation

Per OpenStreetMap Foundation guidelines, attribution is permanently visible in the bottom-right corner of the map viewport:
- **2D Mode**: `Basemap: © OpenStreetMap contributors` (hyperlinked to `https://www.openstreetmap.org/copyright`).
- **3D Mode**: `Basemap: © Esri, DeLorme, NAVTEQ`.
- **Satellite Mode**: `Imagery: © Esri, Maxar, Earthstar Geographics`.
- **Styling**: `bg-slate-950/80 backdrop-blur-md border border-slate-800/80 text-[10px] text-slate-400 font-mono`, styled to integrate seamlessly into the Astra mission aesthetic without blocking map interaction or disaster reticles.

---

## 6. Disaster Markers, Precision & 2D/3D Synchronization

1. **Layer Hierarchy**:
   - `DISASTER EVENTS (Top Layer)`: USGS real-time earthquakes, NASA EONET v3 active events (wildfires, cyclones, volcanoes, floods), NOAA space weather, CelesTrak satellite orbits.
   - `SATELLITE ANALYSIS (Middle Layer)`: Scene selection inspector and bounding reticles.
   - `OPENSTREETMAP (Base Layer)`: 2D geographic background.
2. **Coordinate Precision**:
   - Event coordinates retain full floating-point precision directly from upstream feeds (e.g., USGS GeoJSON `geometry.coordinates`). No coordinate rounding or truncation is performed internally.
3. **2D ↔ 3D Synchronization**:
   - Mode switching (`2d` ↔ `3d` ↔ `satellite`) is managed via `activeMode` state in `frontend/src/app/earth/page.tsx`.
   - The selected disaster (`selectedDisaster: DisasterEvent | null`) and navigation target (`flyToCoords`) are maintained in the shared parent page state.
   - When a user selects an earthquake in 2D mode, the map navigates to the event and renders the cyan pinpoint reticle and pulse halo. If the user toggles to 3D mode or Satellite mode, the selected event, detail card, coordinates, and camera target remain active without reset.
4. **Earth View → SatQuery AI Context Bridge**:
   - Clicking "Analyze with SatQuery AI" packages the exact event metadata (`event_type`, `latitude`, `longitude`, `place_name`, `timestamp`, `source`, `magnitude`, `depth_km`, `geometry_type`) into `ASTRA_ANALYSIS_REQUEST` sessionStorage and routes cleanly to `/analyze`.

---

## 7. Verification & Build Results

### Automated Backend Tests
Command executed:
```bash
$env:PYTHONPATH="<repo-root>;<repo-root>\backend"; .\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_earth_view_integration.py backend/tests/test_sih_demo_refocus.py
```
**Results**:
- `backend/tests/test_earth_view_integration.py`: 10/10 passed (including `test_no_carto_mandatory_dependency`).
- `backend/tests/test_sih_demo_refocus.py`: 23/23 passed.
- **Total**: 33 passed, 0 failed.

### Frontend Production Build
Command executed:
```bash
npm run build (in <repo-root>\frontend)
```
**Results**:
- Next.js 14.2.5 optimized production build created successfully.
- 0 TypeScript compiler errors.
- 0 ESLint errors.
- Static generation for `/earth`, `/analyze`, `/mission`, `/roster`, `/` succeeded.

---

## 8. Remaining Limitations / Future Work
- **High-Traffic Production Scaling**: For high-volume enterprise production beyond the SIH demo, a dedicated caching tile proxy or commercial tile provider (such as Stadia Maps or MapTiler) can be configured modularly in `satellite-providers.ts` using the existing provider abstraction.
