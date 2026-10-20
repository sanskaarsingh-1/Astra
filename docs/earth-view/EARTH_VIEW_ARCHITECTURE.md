# Astra Earth View Architecture

## 1. Architectural Philosophy

Astra Earth View is the **Global Passive Situational Awareness & Geospatial Intelligence Layer** of Astra. It complements the **Deep AI Remote Sensing Layer** (`/analyze`) by providing planetary-scale context, tracking real-world physical and geopolitical phenomena in real time.

```
                             ASTRA PLATFORM
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
        ASTRA EARTH VIEW                       ASTRA ANALYZE
             (/earth)                                (/analyze)
                 │                                       │
     Global Situational Awareness             Multi-Modal Earth Observation
  • Real-Time Aircraft & Transponders       • ResNet-50 LULC Classification
  • Orbital Satellite Tracking (SGP4)       • Siamese BIT Change Detection
  • USGS Earthquakes & Seismic Events       • RSVQA & CDVQA Reasoning
  • NASA EONET Wildfires & Hazards          • VRSBench Grounding & Captioning
  • NOAA SWPC Space Weather                 • Optical-SAR Cross-Modal Fusion
  • Geocoded Global News (GDELT)            • Multi-Agent Gemini Orchestration
  • Critical Infrastructure & Ports                      │
  • CISA Cyber Vulnerability Feed                        │
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                        ASTRA AI CORE PIPELINE
                       FastAPI + Local RTX 5060
                        + Gemini 2.5 Flash API
```

---

## 2. System Architecture & Component Breakdown

The Earth View subsystem is structured as a decoupled, reactive client-side geospatial application deployed within the Next.js static bundle (`output: "export"`) on Firebase Hosting.

### A. Component Hierarchy

```
frontend/src/app/earth/page.tsx (Page Controller & State Coordinator)
 ├── EarthMap (WebGL MapLibre Engine, GeoJSON Layers, SGP4 Propagator, Solar Terminator)
 ├── EarthHud (Top Bar, UTC Clock, Entity Counters, Quick Theater Nav, Search Input)
 ├── LayerManagerDrawer (Collapsible categorized layer controls, counts, active toggles)
 ├── EntityDetailDrawer (Right-side telemetry card, coordinates, metadata, AI Bridge button)
 ├── IntelFeedDrawer (Real-time chronological event stream, click-to-fly interaction)
 ├── RegionDossierModal (Geospatial radius aggregation, summary report export, AI Bridge button)
 └── DataStatusModal (Source health telemetry, refresh intervals, upstream endpoints)
```

### B. Data Flow & Normalization Pipeline

```
Upstream Public APIs
 (USGS, NASA, NOAA, CelesTrak, adsb.lol, GDELT, CISA, IAEA, Cables, Webcams)
         │
         ▼
[data-sources.ts] Data Adapters & Normalizers
 ├── In-Memory TTL Cache Check (prevents redundant fetches)
 ├── In-Flight Request Deduplication (prevents concurrent duplicate network calls)
 ├── Error Isolation Wrapper (try/catch with graceful degradation; upstream failure != crash)
 └── Normalization to Standard EarthEntity & GeoJSON Features
         │
         ▼
[React State in page.tsx]
 ├── activeLayers: Set<LayerId>
 ├── entityData: Record<LayerId, EarthEntity[]>
 ├── sourceHealth: Record<string, HealthStatus>
 └── intelFeed: IntelItem[]
         │
         ├────────────────────────────────┬───────────────────────────────┐
         ▼                                ▼                               ▼
[EarthMap.tsx]                   [EarthHud / Drawers]            [Region Dossier]
MapLibre GL GPU Rendering         Counters, Toggles, Feed         Haversine Spatial Query
(Clusters, Icons, Orbits)
```

---

## 3. Map Engine & WebGL Capabilities

1. **Dual Base Map Engine**:
   - **Carto Dark Matter**: Vector-rendered, minimalist dark basemap optimized for maximum contrast with tactical geospatial symbols.
   - **ESRI World Imagery**: High-resolution global satellite photography base for optical terrain and urban density assessment.
2. **Dynamic Astronomical Solar Terminator**:
   - Computes solar declination and Greenwich hour angle in real-time.
   - Generates a spherical polygon covering the night hemisphere and applies an atmospheric twilight gradient.
3. **GPU Clustering & Progressive Rendering**:
   - Earthquake, wildfire, CCTV, and infrastructure layers utilize MapLibre GL GeoJSON clustering (`cluster: true`, `clusterRadius: 50`).
   - Clusters expand dynamically on zoom; high-density nodes are rendered with graduated heat colors without exhausting DOM elements.
4. **Custom Canvas Entity Markers**:
   - Aircraft transponders render true heading rotations using procedural SVG-to-Canvas markers (`aircraft-marker`).
   - Satellites compute 90-minute orbital ground tracks with automatic antimeridian (+180° / -180°) line segment splitting to eliminate horizontal wrapping artifacts.

---

## 4. Real-Time Orbital Tracking (SGP4 Engine)

- Integrates `satellite.js@5.0.0` (pure JS, Zero-Node dependency) for Simplified General Perturbations-4 (SGP4) satellite propagation.
- Ingests Two-Line Element (TLE) sets from CelesTrak.
- Evaluates true anomalous geodetic coordinates (`latitude`, `longitude`, `altitude_km`) at millisecond precision based on the local client clock.
- Dynamically recalculates sub-satellite positions every 10 seconds for real-time drift.

---

## 5. Astra AI Bridge (`Earth View` ➔ `Analyze`)

Earth View integrates directly into the existing Astra AI analysis pipeline without creating duplicate backend architecture.

### Bridge Mechanisms:
1. **Entity Detail Card**:
   - User clicks any aircraft, vessel, wildfire, earthquake, or infrastructure node.
   - Clicking **"Analyze with Astra AI"** routes the user to `/analyze?lat=${lat}&lon=${lon}&target=${name}&source=earth_view`.
2. **Region Dossier**:
   - User right-clicks any planetary point or selects an entity to open a 300 km radius dossier.
   - Summarizes all colocated infrastructure, natural hazards, satellite passes, and transponders.
   - Clicking **"Deep AI Scan with Astra"** passes the bounding coordinates and threat context into the Astra FastAPI agentic workflow (`/api/v1/investigation/stream`).
3. **Report Integration**:
   - Users can export structured Markdown intelligence dossiers directly to the clipboard or disk for instant briefing generation.

---

## 6. Minimalist UI & Brand Integration

- **Typography**: Matches the existing Astra design system:
  - Headers: `Space Grotesk` (uppercase, tracked, clean lines)
  - Body: `Inter` (neutral, crisp, readable at small tactical scales)
  - Data / Telemetry: `JetBrains Mono` (monospace for coordinates, timestamps, altitudes, frequencies)
- **Palette**: Strict tactical dark theme (`bg-black`, `bg-zinc-950`, `border-zinc-800`, `text-zinc-100`, accents in emerald, cyan, and amber).
- **Zero AI Slop**: Clean borders, discrete badges, no excessive neon glows, no synthetic placeholding.

---

## 7. Security & Non-Reconnaissance Boundary

In accordance with strict security requirements:
- **No Active Reconnaissance**: Port scanning, target probing, WHOIS lookups, and vulnerability scanners are completely omitted from the public Earth View interface.
- **Passive Intelligence Only**: Displays publicly published, defense-in-depth telemetry (e.g., CISA KEV disclosures, USGS feeds, NASA FIRMS hotspots).
- **Zero Exposed Secrets**: All public API integrations use unrestricted endpoints; sensitive proxy tokens (e.g., FIRMS MAP_KEY) are configured server-side.
