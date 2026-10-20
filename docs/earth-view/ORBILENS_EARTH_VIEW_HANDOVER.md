# Astra Earth View Handover Document

**SIH26167 | Astra / SatQuery AI**  
**Classification:** Unclassified / Public Geospatial Intelligence  
**Document Status:** Complete & Verified  

---

## 1. Executive Summary & Architecture

Astra Earth View (`/earth`) is the production global situational-awareness and geospatial exploration engine for the Astra AI platform. Built with Next.js, MapLibre GL v6, D3 (`d3-geo`), HTML Canvas, and WebGL, it provides:
1. **Three Core Operational Modes**:
   - **`[ 2D MAP ]`**: Flat Mercator projection powered by legitimate OpenStreetMap standard raster tiles (`tile.openstreetmap.org`), complete with international borders, coastlines, cities, roads, and tactical intelligence overlays.
   - **`[ 3D GLOBE ]`**: Spherical 3D Earth appearance in WebGL with dynamic planetary rotation, spherical drag, zoom, continental outlines, astronomical day/night terminator, and orbital satellites. Also includes an on-demand toggle to the pure D3 Canvas Rotating Earth engine.
   - **`[ SATELLITE ]`**: Real, high-resolution optical satellite photography powered by Esri World Imagery (sub-meter resolution down to zoom 19) with progressive tile loading from global views down to local street levels.
2. **RotatingEarth D3 Canvas Component**:
   - Built on `d3.geoOrthographic()`, Natural Earth 110m land GeoJSON, graticule lines, mouse rotation/drag, wheel zoom, and retina DPR scaling.
   - Fully hardened with clean React lifecycle management, AbortController cleanup, zero memory leaks, zero timer leaks, and zero development console spam (`[v0]`).
3. **Zero CARTO Mandatory Dependency**:
   - Operates completely out-of-the-box without requiring a `CARTO_API_KEY`.
   - Never displays "API KEY REQUIRED" or CARTO watermarks.
4. **Explicit Telemetry Failure States**:
   - Counters never display `0` unless the upstream provider genuinely returns zero entities.
   - Explicit states: `LIVE`, `LOADING`, `OFFLINE`, `UNAVAILABLE`, `RATE_LIMITED`, `REQUIRES_API_KEY`, `ERROR`.
5. **AI Deep Bridge**:
   - Seamlessly transfers selected entity metadata, scene coordinates, and tactical context to `/analyze` for deep remote-sensing inference (ResNet-50 LULC, Siamese BIT change detection, RSVQA, CDVQA, and Gemini agentic reasoning).
6. **Model Safety Invariant**:
   - Zero machine learning model retraining or weight alterations occurred. Checkpoints and registry are strictly untouched.

```
                         ASTRA PLATFORM
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
  ASTRA EARTH VIEW                          ASTRA ANALYZE
       (/earth)                                    (/analyze)
           │                                           │
Live Situational Awareness                   Deep Remote Sensing AI
• 2D Flat Map (OSM standard)                 • ResNet-50 LULC
• 3D Spherical Globe (WebGL / D3)            • Siamese BIT Change Detection
• Real Satellite Imagery (Esri sub-meter)    • RSVQA / CDVQA
• Aircraft (ADS-B live)                      • VRSBench Grounding / Captioning
• Satellites (CelesTrak SGP4 live)           • Optical-SAR Cross-Modal Fusion
• Earthquakes (USGS live)                    • Agentic Gemini Orchestration
• Wildfires (NASA EONET live)                • Dynamic Investigation Stream
• Space Weather (NOAA live)
• CISA KEV Cyber Threats
• GDELT Global Events
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 ▼
                     ASTRA AI CORE ENGINE
                 FastAPI Backend + Local RTX 5060
```

---

## 2. Core Display Modes

### Mode 1: 2D MAP
- **Projection**: Flat Mercator (`map.setProjection({ type: 'mercator' })`).
- **Basemap**: OpenStreetMap Standard raster tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`).
- **Attribution**: `© OpenStreetMap contributors` strictly displayed in accordance with OSM Tile Usage Policy.
- **Features**: International boundaries, capital cities, maritime coastlines, search fly-to, and overlay layers.

### Mode 2: 3D GLOBE
- **Projection**: Spherical Orthographic 3D Globe (`map.setProjection({ type: 'globe' })`).
- **Basemap**: Esri Dark Gray Canvas (`https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`).
- **Planetary Auto-Spin**: Dedicated `[ SPIN ]` toggle providing continuous smooth rotational motion when the user is not dragging.
- **Day/Night Visualization**: Dynamically calculated solar declination and subsolar longitude creating the live night hemisphere polygon.
- **Alternative D3 Canvas Mode**: Users can toggle between the WebGL Globe and the D3 Canvas Rotating Earth engine directly in 3D mode.

### Mode 3: SATELLITE
- **Projection**: Spherical 3D Globe (`map.setProjection({ type: 'globe' })`).
- **Basemap**: Esri World Imagery (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`).
- **Resolution**: Progressive multi-scale tile loading from 15m global view down to 0.3m sub-meter resolution.
- **Scientific Fallback**: NASA GIBS MODIS Terra daily true-color observation available.
- **Strict Prohibition**: Zero synthetic textures, zero fake screenshots, zero unauthorized scrapers.

---

## 3. Telemetry Feeds & Explicit Status Mapping

Counters in the HUD use explicit states to ensure analysts are never misled:
- **`LIVE`**: The provider returned successfully; displays exact item count (`0` is only shown if genuine count is 0).
- **`LOADING`**: Asynchronous fetch in progress; displays animated pulse indicator.
- **`OFFLINE`**: Connection or fetch timed out; displays red `OFFLINE` badge.
- **`UNAVAILABLE`**: Upstream service returned 5xx or network block; displays amber `UNAVAIL` badge.
- **`RATE_LIMITED`**: Upstream service returned HTTP 429; displays `RATE LTD` badge.
- **`REQUIRES_API_KEY`**: Upstream service requires private key; displays `KEY REQ` badge.

---

## 4. Verification & Automated Test Results

- **Backend Pytest Suite**: `121 passed, 147 warnings in 117.71s` (100% pass rate).
- **Earth View Integration Tests**: `6 passed in 0.03s` (`backend/tests/test_earth_view_integration.py`).
- **Frontend Production Build**: `next build` succeeded with exit code `0`, generating static export for `/earth` (46.1 kB).
- **Model Invariant Verification**: `weights/best_model.pth` verified intact and untouched.

---

## 5. Deployment Instructions

```bash
# Frontend static build & Firebase deploy
cd frontend
npm run build
firebase deploy --only hosting
```
Live Production URL: `https://sih-orbilens-2026-tm.web.app/earth`

---

## 6. SatQuery AI First Refinement Pass (SIH26167 Core Alignment)

To fulfill the primary SIH problem statement (*"SatQuery AI - An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries"*), Earth View acts as the intuitive visual exploration gateway into SatQuery AI:

1. **Primary Remote-Sensing CTA**:
   - Elevated **`[ ✦ Analyze Scene with Astra AI ]`** to the most prominent position in the primary HUD.
   - De-emphasized secondary OSINT telemetry into a compact status summary, ensuring remote sensing and vision-language analysis remain front and center.
2. **In-Situ SatQuery Scene Inspector (`SatQuerySceneInspector.tsx`)**:
   - Clicking anywhere on the globe or satellite imagery immediately selects that scene.
   - Displays scene telemetry: coordinates, sensor resolution (0.3m optical GSD), and bounding footprint.
   - Interactive natural-language prompt bar pre-loaded with core SIH benchmark tasks:
     - 🏷️ **Land Cover Classification (LULC)** — ResNet-50 v2 Deep Classifier
     - 🌾 **Agricultural Field Detection (VQA)** — RSVQA Dual-Encoder
     - 📝 **Scene Captioning** — VRSBench Fine-Tuned Captioning VLM
     - 🎯 **Built-up Area Grounding** — VRSBench Spatial Grounding Engine
     - 🔄 **Bi-Temporal Change Detection** — Siamese BIT ResNet-18
     - 📡 **Optical + SAR Radar Fusion** — Cross-Modal Radar-Optical Network
   - In-situ execution displays the full agentic flow: Agent Planner $\to$ Specialist Invocation $\to$ Visual Evidence Breakdown $\to$ Confidence Score $\to$ Gemini Analytical Synthesis.
3. **Seamless SatQuery Workspace Handoff (`/analyze`)**:
   - Clicking **"Open in SatQuery"** transfers target coordinates, active modality mode, and query into the deep investigation workspace.
   - `/analyze` renders a verified `"Geospatial Scene Imported from Earth View"` banner, pre-fills the prompt, and activates the required analysis modality.

