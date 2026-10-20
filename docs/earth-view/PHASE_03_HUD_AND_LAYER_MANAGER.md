# Phase 03 — Minimalist Astra HUD & Layer Management

**Target**: Build an Astra-native, minimalist Heads-Up Display (HUD) with collapsible grouped layer controls, verified real entity counters, live event feed, and source health indicators.

---

## HUD Architecture Checklist

- [x] **Top Bar**:
  - Astra Earth View brand with Live indicator badge
  - Status ticker with verified live entity counts (e.g. `AIRCRAFT: 8,421 | SATELLITES: 1,840 | QUAKES: 45 | FIRES: 1,210`)
  - Global View Presets: World, Indo-Pacific (ISRO focus), Europe/Middle East, Americas, Polar
  - Map style toggles (Dark Matter / Satellite Imagery / 3D Globe / 2D Mercator / Day-Night)

- [x] **Left Layer Panel**:
  - Minimalist glassmorphic drawer with categorized checkboxes:
    - **Aviation**: Commercial, Military, Private Jets
    - **Maritime**: AIS Vessels, Ports, Strategic Chokepoints
    - **Space**: Satellites (SGP4), ISS, Space Weather
    - **Earth Hazards**: Earthquakes (USGS), Thermal Wildfires (FIRMS), Weather, Air Quality
    - **Geopolitical**: Conflicts, Frontlines, GDELT Global Events
    - **Surveillance**: Public CCTV Webcams
    - **Infrastructure**: Nuclear Plants, Power Grids, Undersea Cables
    - **Cyber**: CISA KEV Vulnerabilities, Threat Feeds
    - **Markets**: Defense & Commodity Tickers
    - **Visual**: Solar Terminator, Graticule, Labels

- [x] **Live Intelligence Feed**:
  - Chronological stream of incoming world events
  - Click on any feed item to smoothly fly the camera to that exact geographic coordinate
  - Category badges, timestamps, and verified source attribution

- [x] **Source Health Panel**:
  - Visual status pill for every active upstream provider:
    - `● LIVE` (data retrieved successfully)
    - `● CACHED` (serving from validated TTL cache)
    - `○ UNAVAILABLE / ERROR` (with retry action)
