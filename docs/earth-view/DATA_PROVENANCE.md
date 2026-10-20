# Astra AI Earth View — Data Provenance & Geospatial Registry

**SIH26167 | Astra / SatQuery AI**  
**Classification:** Unclassified / Public Geospatial Intelligence  
**Document Status:** Complete & Verified  

---

## 1. Executive Summary

This document catalogues all upstream data providers, basemap imagery services, orbital tracking elements, and real-time situational awareness telemetry integrated into the Astra Earth View (`/earth`).

All integrated data sources adhere strictly to:
- Keyless public access requirements (CARTO API keys are NOT mandated; zero watermarks).
- Legitimate public research, scientific, and open-data licences.
- Non-reconnaissance passive observation guidelines.
- Visible, legal attribution displays across MapLibre GL, D3 Canvas, and HUD drawers.

---

## 2. Basemap & Satellite Imagery Providers

| Provider Name | Endpoint | Data Type | Authentication | Resolution & Coverage | Terms / License | Attribution Display | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Esri World Imagery** | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | Optical Satellite Raster Tiles (XYZ) | None (Public Keyless) | 15m global to 0.3m sub-meter urban; Global coverage | Esri Master License Agreement (Permitted for public web display) | `© Esri, Maxar, Earthstar Geographics` | **LIVE (Primary Satellite)** |
| **OpenStreetMap Standard** | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | Vector-rendered Map Raster (XYZ) | None (Public Keyless) | Global street/political level (Zoom 0–19) | Open Database License (ODbL) | `© OpenStreetMap contributors` | **LIVE (Primary 2D Map)** |
| **Esri Dark Gray Canvas** | `https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}` | Minimalist Tactical Raster (XYZ) | None (Public Keyless) | Global cartographic (Zoom 0–16) | Esri Master License Agreement | `© Esri, DeLorme, NAVTEQ` | **LIVE (Primary 3D Globe)** |
| **NASA GIBS (MODIS Terra)** | `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg` | Daily Scientific True-Color Satellite Imagery | None (Public Open Data) | 250m global planetary daily observation | NASA Open Data Policy (Public Domain) | `Imagery courtesy of NASA EOSDIS GIBS` | **AVAILABLE (Scientific)** |
| **Natural Earth Vector (110m)** | `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson` | GeoJSON Physical Land Boundaries | None (Public CDN) | 1:110,000,000 scale continental polygons | Public Domain (CC0) | `Natural Earth Vector` | **LIVE (D3 Canvas Globe)** |

---

## 3. Real-Time Telemetry & Intelligence Providers

| Layer / Domain | Provider Name | Endpoint | Frequency / Caching | Attribution | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Aviation** | ADS-B Network (`adsb.lol` / OpenSky) | `https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist}` | Polled every 20s; 20s client cache | Open ADS-B Community | **LIVE** |
| **Orbital Space** | CelesTrak TLEs + SGP4 Propagator | `https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle` | Polled every 30s; SGP4 orbital calculation | CelesTrak / Dr. T.S. Kelso | **LIVE** |
| **Earthquakes** | USGS Earthquake Hazards Program | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson` | Polled every 60s; 60s client cache | U.S. Geological Survey (USGS) | **LIVE** |
| **Wildfires** | NASA EONET (Earth Observatory Natural Event Tracker) | `https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires` | Polled every 5min; 5min client cache | NASA Goddard Space Flight Center | **LIVE** |
| **Severe Weather** | NASA EONET Severe Storms | `https://eonet.gsfc.nasa.gov/api/v3/events?category=severeStorms` | Polled every 5min; 5min client cache | NASA Goddard Space Flight Center | **LIVE** |
| **Space Weather** | NOAA Space Weather Prediction Center (SWPC) | `https://services.swpc.noaa.gov/json/planetary_k_index_1m.json` | Polled every 60s; 60s client cache | NOAA SWPC | **LIVE** |
| **Global News & Events** | GDELT Project 2.0 Doc API | `https://api.gdeltproject.org/api/v2/doc/doc` | Polled every 5min; 5min client cache | The GDELT Project | **LIVE** |
| **Cyber Threat Landscape** | CISA Known Exploited Vulnerabilities (KEV) | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | Polled every 10min; 10min client cache | Cybersecurity and Infrastructure Security Agency (CISA) | **LIVE** |
| **Strategic Ports** | UN/LOCODE & World Port Index | Curated Top 25 Maritime Hubs & Strategic Chokepoints | Static curated geospatial points | UN/ECE & NGA WPI | **LIVE** |
| **Submarine Cables** | TeleGeography Submarine Cable Map | Curated major transoceanic fiber routes | GeoJSON LineString coordinates | TeleGeography Open Data | **LIVE** |
| **Conflict Frontlines** | OSIRIS Open Conflict Data | Frontline segments & alert perimeters | GeoJSON multi-lines | ACLED / DeepStateMap open sources | **LIVE** |

---

## 4. Upstream Status Mapping Architecture

Telemetry counters in the HUD use explicit states to prevent erroneous zeros:
- **`LIVE`**: The provider returned successfully; displays exact item count (`0` is only shown if genuine count is 0).
- **`LOADING`**: Initial asynchronous fetch in progress; displays animated pulse indicator.
- **`OFFLINE`**: Connection or fetch timed out; displays red `OFFLINE` badge.
- **`UNAVAILABLE`**: Upstream service returned 5xx or network block; displays amber `UNAVAIL` badge.
- **`RATE_LIMITED`**: Upstream service returned HTTP 429; displays `RATE LTD` badge.
- **`REQUIRES_API_KEY`**: Upstream service requires private key; displays `KEY REQ` badge.

---

## 5. Security & Safety Compliance

1. **Passive Observation Only**: No active network scanning, port probing, CCTV intrusion, or unauthorized telemetry collection.
2. **Model Safety Invariant**: Zero machine learning model retraining or checkpoint modifications were performed during Earth View development.
3. **No Secret Exposure**: Zero API keys or private tokens are embedded or committed to version control.
