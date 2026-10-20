# Astra AI Earth View — Upstream Data Sources & Provenance

This document provides a comprehensive inventory of all real, authentic upstream data sources integrated into the **Astra AI Earth View** situational awareness platform.

---

## 1. Zero Synthetic Data Invariant

Every marker, coordinate, polygon, and telemetry readout presented in Astra Earth View originates from:
1. Direct, real-time public REST/GeoJSON endpoints (e.g. USGS, NASA EONET, NOAA SWPC, CISA KEV, GDELT, adsb.lol).
2. Deterministic mathematical orbital mechanics (SGP4/SDP4 propagation via `satellite.js` using CelesTrak active TLEs).
3. Verified physical reference datasets (IAEA PRIS Nuclear Power Reactors, Submarine Cable Map, World Bank Container Ports).

**No mock, hardcoded synthetic entities, or fabricated aircraft/vessels exist in the production runtime.**

---

## 2. Upstream Data Source Inventory

| Domain | Source Provider | Endpoint / Upstream URL | Ingestion Type | Update / Refresh Interval | Auth / API Key | License / Terms | Attribution Notice |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **Aviation** | ADS-B Network (`adsb.lol`) | `https://api.adsb.lol/v2/` | Live REST | 20 seconds | None required (Open Access) | Open Data / CC-BY-SA | ADS-B Community Feeds |
| **Satellites** | CelesTrak NORAD GP Data | `https://celestrak.org/NORAD/elements/gp.php` | Live TLE + SGP4 Orbit Propagation | Real-time calculation | None required | Public Domain / US Space Force | CelesTrak & Dr. T.S. Kelso |
| **Earthquakes** | USGS Earthquake Hazards Program | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson` | Live GeoJSON | 60 seconds | None required | Public Domain (USGS) | U.S. Geological Survey |
| **Wildfires** | NASA EONET / FIRMS | `https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires` | Live REST / GeoJSON | 300 seconds | None required | NASA Open Data Policy | NASA Earth Observatory / EOSDIS |
| **Severe Storms** | NASA EONET Severe Storms | `https://eonet.gsfc.nasa.gov/api/v3/categories/severeStorms` | Live REST / GeoJSON | 300 seconds | None required | NASA Open Data Policy | NASA EONET / NOAA NHC |
| **Space Weather** | NOAA Space Weather Prediction Center | `https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json` | Live JSON | 60 seconds | None required | Public Domain (NOAA) | NOAA SWPC Boulder, CO |
| **Cyber Threats** | CISA Known Exploited Vulnerabilities | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | Live JSON Feed | 24 hours | None required | US Federal Public Domain | Cybersecurity & Infrastructure Security Agency |
| **Global Events** | The GDELT Project 2.0 | `https://api.gdeltproject.org/api/v2/geo/geo` | Live GeoJSON | 15 minutes | None required | Open Research / GDELT | The GDELT Project |
| **Basemap (Dark)** | CARTO Dark Matter | `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json` | Vector Tiles | Static / Cached | None required | CC-BY 4.0 | © CARTO, © OpenStreetMap contributors |
| **Basemap (Satellite)**| ESRI World Imagery | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | Raster XYZ Tiles | Static / Cached | None required | Esri Master Agreement | © Esri, Maxar, Earthstar Geographics |
| **Geosearch** | OpenStreetMap Nominatim | `https://nominatim.openstreetmap.org/search` | Live Geocoding | On Demand | None required (Fair Use) | ODbL / OpenStreetMap | © OpenStreetMap contributors |
| **Undersea Cables** | Submarine Cable Map | Curated Physical Geometries | Reference GeoJSON | 30 days | None required | CC-BY-SA 4.0 | TeleGeography Submarine Cable Map |
| **Nuclear Facilities**| IAEA PRIS Database | Curated Reference Records | Reference GeoJSON | Annual | None required | IAEA Public Information | International Atomic Energy Agency |
| **Public CCTVs** | Verified Public Municipal Webcams | Live Snapshot URLs (e.g. EarthCam, NASA HDEV) | Live Image Refresh | On Demand | None required | Public Broadcast Terms | Respective Municipal / Space Agencies |

---

## 3. Resilience, Caching & Failure Isolation

1. **Error Isolation**:
   - Every fetch call operates inside an isolated `try / catch` block with an `AbortSignal.timeout(12000)` watchdog.
   - If an upstream server experiences transient downtime, that specific layer transitions to `CACHED` (serving last-known validated data) or displays `UNAVAILABLE` without crashing any other layer.

2. **TTL In-Memory Caching**:
   - `cachedFetch()` prevents repeated HTTP calls during panning or tab switches.
   - Polling intervals respect upstream rate limits.
