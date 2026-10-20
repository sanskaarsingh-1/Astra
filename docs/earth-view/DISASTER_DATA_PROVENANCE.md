# Astra AI Earth View — Disaster Data Provenance & Telemetry Integrity
**Specification:** SIH26167 — Natural Disaster + Earth Observation + Precision Geolocation  
**Release:** v2.4 (September 2026)  
**Status:** In Production | Zero Synthetic Data Policy

---

## 1. Executive Summary

Astra Earth View (`/earth`) provides an operational Earth-observation and natural-disaster exploration interface tightly coupled with **SatQuery AI** multimodal vision-language analysis.

In accordance with SIH26167 specifications, Earth View eliminates general-purpose OSINT clutter (commercial aviation, CVE feeds, generic news, CCTV cameras, submarine cables, frontlines) and focuses exclusively on:
1. **Remote Sensing & Satellite Observation** (Sentinel, Landsat, MODIS, VIIRS)
2. **Natural Disasters & Geohazards** (Earthquakes, Wildfires, Floods, Cyclones, Volcanoes)
3. **Space Environment** (Geomagnetic Storms, Solar Flare Flux)
4. **Precision Geolocation** (Signed decimal degree coordinates, human-readable place resolution)
5. **Astra AI Specialist Integration** (Instant geographic context transfer to SatQuery AI)

---

## 2. Upstream Data Sources Provenance Register

| Attribute | USGS Earthquake Hazards | NASA EONET v3 | NASA FIRMS (Via EONET) | NOAA SWPC | OpenStreetMap Nominatim |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Provider** | U.S. Geological Survey (USGS) | NASA Goddard Space Flight Center | NASA / LANCE FIRMS | NOAA Space Weather Prediction Center | OpenStreetMap Foundation |
| **Category** | `EARTHQUAKE` | `WILDFIRE`, `CYCLONE`, `SEVERE_STORM`, `FLOOD`, `VOLCANO`, `LANDSLIDE`, `DROUGHT` | `WILDFIRE` thermal hotspots | `SPACE_WEATHER` (Kp Index) | Reverse Geocoding / Place Resolution |
| **Endpoint** | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson` | `https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=150` | Integrated via NASA EONET GeoJSON geometry | `https://services.swpc.noaa.gov/json/planetary_k_index_1m.json` | `https://nominatim.openstreetmap.org/reverse` |
| **Auth Requirement** | None (Public Keyless REST API) | None (Public Keyless REST API) | Keyless via EONET public proxy | None (Public Keyless JSON API) | None (Public with User-Agent header) |
| **Update Frequency** | Every 60 seconds (Live seismic events) | Every 5 to 15 minutes | Continuous satellite overpasses (VIIRS/MODIS) | Every 60 seconds | On-demand with client-side caching |
| **Coordinate System** | WGS 84 (EPSG:4326) [Longitude, Latitude, Depth km] | WGS 84 (EPSG:4326) [Longitude, Latitude] | WGS 84 (EPSG:4326) [Longitude, Latitude] | Non-spatial (Global Kp Index 0–9) | WGS 84 (EPSG:4326) |
| **Timestamp Format** | Epoch Milliseconds (ISO-8601 normalized) | ISO-8601 UTC string | ISO-8601 UTC string | UTC string (`YYYY-MM-DD HH:MM:SS`) | N/A |
| **Geometry Type** | `OFFICIAL_POINT` (Hypocenter coordinate) | `OFFICIAL_POINT`, `AFFECTED_POLYGON`, `STORM_TRACK` | `PIXEL_CENTER` (Satellite detection center) | Global parameter | Point centroid |
| **License / Terms** | U.S. Public Domain | Open Data (NASA Earth Science Data Policy) | Open Data (NASA ESDIS) | U.S. Public Domain | Open Database License (ODbL) |
| **Attribution** | USGS Earthquake Hazards Program | NASA EONET (GSFC) | NASA FIRMS / MODIS & VIIRS | NOAA SWPC | © OpenStreetMap contributors |

---

## 3. Spatial Meaning & Geometry Distinction Matrix

Per Phase 12 & Phase 13 of the SIH26167 Specification, Astra enforces a strict distinction between event coordinates:

| Event Type | Spatial Precision Tag | UI Label | Underlying Geographic Meaning |
| :--- | :--- | :--- | :--- |
| **Earthquake** | `OFFICIAL_POINT` | `Official Seismic Epicenter` | Instrumentally calculated epicenter/hypocenter from seismic array data. |
| **Wildfire** | `PIXEL_CENTER` | `Detected Location (Satellite Pixel Center)` | Thermal anomaly pixel center (~375m VIIRS or 1km MODIS). Not an exact perimeter boundary. |
| **Cyclone** | `STORM_TRACK` or `APPROXIMATE_CENTER` | `Observed Storm Center` | Eye / low-pressure vortex center at acquisition time. Trajectory lines represent recorded path. |
| **Volcano** | `OFFICIAL_POINT` | `Volcanic Vent / Crater` | Known active caldera or summit crater geographic position. |
| **Flood** | `AFFECTED_POLYGON` or `OFFICIAL_POINT` | `Flood Impact Footprint / Gauge Location` | Polygon represents inundated region if satellite flood map is available; point represents reference gauge. |
| **Landslide** | `OFFICIAL_POINT` | `Reported Slope Failure Point` | Centroid of reported mass-wasting event. |

> [!IMPORTANT]
> **Zero Artificial Polygon Fabrication:** Astra AI never synthesizes an artificial polygon around a point detection. If an affected area boundary is supplied by the official source, it is rendered; if not, it remains an exact pinpoint.

---

## 4. Place Name Resolution Architecture

Per Phase 10 & Phase 19:
- **USGS Earthquakes:** Uses the official USGS place string (e.g. `"24 km NE of Hualien City, Taiwan"`). This official text is never overwritten.
- **NASA EONET Events:** Uses the official EONET geographic event title (e.g. `"Wildfire - Western Victoria, Australia"`).
- **Secondary / Point Inquiries:** If an arbitrary map location is clicked, reverse geocoding is performed via OSM Nominatim and explicitly labeled:
  ```
  Derived: Nearest named place from geocoding service
  ```
- No city or country names are ever invented or guessed.

---

## 5. SatQuery AI Remote Sensing Context Transfer

When a user selects an event and clicks **`[ ✦ ANALYZE WITH ASTRA AI ]`**, the following structured payload is transmitted to the SatQuery AI engine:

```json
{
  "event_type": "earthquake",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "place_name": "Near Pune, Maharashtra, India",
  "timestamp": "2026-09-21T18:42:00Z",
  "source": "USGS Earthquake Hazards Program",
  "magnitude": 5.8,
  "depth_km": 12.0,
  "geometry_type": "OFFICIAL_POINT",
  "user_query": "Analyze remote-sensing land cover and satellite scene evidence around Near Pune, Maharashtra, India for earthquake impact."
}
```

This guarantees that the downstream Gemini 3.8 Flash / Antigravity vision-language specialist agents receive verified geographic coordinates and disaster classification for change detection and damage estimation.
