# Phase 05 — Region Dossier & Astra AI Integration Bridge

**Target**: Implement OSIRIS-style Region Dossier aggregating all active spatial indicators around a selected point or bounding box, and the **"Analyze with Astra AI"** bridge connecting directly to the local RTX 5060 FastAPI backend.

---

## Capabilities Checklist

- [x] **Region Dossier Drawer**:
  - Activated by Right-Clicking anywhere on the map or selecting "Region Dossier"
  - Aggregates real-time situational awareness within configurable radius (e.g. 100km / 250km):
    - Country and territory identification
    - Real-time weather and temperature
    - Recent seismic activity
    - Thermal wildfire count
    - Air Quality Index (AQI)
    - Overhead satellites and next pass
    - Active flights in airspace
    - Nearby maritime vessels and ports
    - Strategic infrastructure within perimeter
    - Recent geocoded news / GDELT events

- [x] **"Analyze with Astra AI" Action Bridge**:
  - Primary button in Region Dossier: `Analyze with Astra AI`
  - Encapsulates target location, bounding box, and operational context
  - Bridges into the Astra AI investigation pipeline:
    - Pre-populates investigation query with geographic coordinates and detected entities
    - Direct integration with existing FastAPI endpoints (`/api/investigate`, `/api/specialists/*`)
    - Transitions to `/analyze` or opens in-place analysis modal
    - Enables single-click report generation using the existing Astra report synthesizer
