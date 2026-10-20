# Astra AI Earth View — OSIRIS Feature Parity Matrix

This document provides a forensic, item-by-item verification matrix comparing the capabilities of the upstream **OSIRIS** project with their implementation in **Astra AI Earth View** (`/earth`).

---

## 1. Feature Parity Audit Table

| OSIRIS Feature | Astra Status | Upstream Source | Mode | API Route / Endpoint | License | Notes |
|:---|:---|:---|:---|:---|:---|:---|
| **Commercial Aircraft Tracking** | `IMPLEMENTED` | ADS-B Network (`adsb.lol`) | LIVE | Public REST ADS-B Ingestion | CC-BY-SA 4.0 | Real-time position, altitude (ft/m), groundspeed, heading, ICAO24, callsign. |
| **Military & Special Airspace** | `IMPLEMENTED` | ADS-B Network (`adsb.lol`) | LIVE | Filtered ADS-B Stream | CC-BY-SA 4.0 | Identified via ICAO military type indicators (C17, C130, F16, F35, P8, etc.). |
| **Private Jet Fleet** | `IMPLEMENTED` | ADS-B Network (`adsb.lol`) | LIVE | Filtered ADS-B Stream | CC-BY-SA 4.0 | Categorized by executive typecodes (Gulfstream, Global Express, Citation, Learjet). |
| **Active Satellites Tracking** | `IMPLEMENTED` | CelesTrak NORAD GP | LIVE | `https://celestrak.org/NORAD/elements/gp.php` | Public Domain | True SGP4 orbital propagation via `satellite.js` with geodetic altitude. |
| **Space Stations (ISS/Tiangong)**| `IMPLEMENTED` | CelesTrak Space Stations | LIVE | CelesTrak Stations TLE feed | Public Domain | Real-time SGP4 propagation + complete ground track trajectory line. |
| **Real-time Earthquakes** | `IMPLEMENTED` | USGS Hazards Program | LIVE | `https://earthquake.usgs.gov/.../2.5_day.geojson` | Public Domain | M2.5+ past 24h, depth scaling, magnitude threat spectrum, tsunami flags. |
| **Active Wildfires & Hotspots** | `IMPLEMENTED` | NASA EONET / FIRMS | LIVE | `https://eonet.gsfc.nasa.gov/api/v3/events` | NASA Open Data | VIIRS/MODIS thermal anomalies, detection time, satellite instrument. |
| **Severe Storms & Cyclones** | `IMPLEMENTED` | NASA EONET Severe Storms | LIVE | `https://eonet.gsfc.nasa.gov/api/v3/categories/severeStorms` | NASA Open Data | Real-time tropical storm centroids and disaster event telemetry. |
| **Space Weather Telemetry** | `IMPLEMENTED` | NOAA SWPC | LIVE | `https://services.swpc.noaa.gov/.../noaa-planetary-k-index.json` | Public Domain | Real-time Planetary K-index, geomagnetic storm severity status, solar wind. |
| **Public CCTVs & Webcams** | `IMPLEMENTED` | Municipal DOT / EarthCam | LIVE | Verified Public Streaming Gateways | Public Terms | Real live snapshot viewer with manual refresh button and status badge. |
| **Global Events & Geonews** | `IMPLEMENTED` | The GDELT Project 2.0 | LIVE | `https://api.gdeltproject.org/api/v2/geo/geo` | Open Research | Geocoded strategic world events with title, source, publication date. |
| **Geopolitical Conflicts** | `IMPLEMENTED` | UN OCHA / ACLED / OSINT | LIVE | Verified Geopolitical Aggregates | Open Data | Real active theaters (Donbas, Red Sea, Gaza, Taiwan Strait, LAC Ladakh). |
| **Military Frontlines** | `IMPLEMENTED` | OSINT Combat Indicators | REFERENCE | Verified LineString Coordinates | Open Research | Donbas Line of Contact, LAC Ladakh, Korean 38th Parallel Demarcation. |
| **Strategic Ports & Chokepoints**| `IMPLEMENTED` | World Bank & Port Authorities | REFERENCE | Global Container Gateways Dataset | Open Data | Coordinates, UN/LOCODE, TEU volume, strategic chokepoint flags. |
| **Critical Nuclear Infrastructure**| `IMPLEMENTED` | IAEA PRIS Database | REFERENCE | IAEA Operational Reactors Dataset | Public Domain | Reactor type, MWe capacity, country, coordinates. |
| **Space Launch Centers** | `IMPLEMENTED` | ISRO, NASA, ESA, Roscosmos | REFERENCE | Major Spaceports Dataset | Public Domain | SDSC SHAR Sriharikota, Kennedy KSC, CSG Kourou, Baikonur. |
| **Undersea Submarine Cables** | `IMPLEMENTED` | Submarine Cable Map | REFERENCE | TeleGeography Open Geometry | CC-BY-SA 4.0 | Multi-segment subsea fiber optic routes and global landing stations. |
| **Passive Cyber Intelligence** | `IMPLEMENTED` | CISA Official Catalog | LIVE | `https://www.cisa.gov/.../known_exploited_vulnerabilities.json` | Public Domain | Known Exploited Vulnerabilities (KEV) with CVE IDs and vendor advisories. |
| **Defense & Commodity Markets** | `IMPLEMENTED` | Global Financial Feeds | LIVE | Standard Market Indices Ticker | Public Quotes | Brent Crude, Gold Spot, Lockheed Martin, RTX, Boeing, HAL, BEL. |
| **Astronomical Solar Terminator** | `IMPLEMENTED` | Keplerian / Solar Math | LIVE | Computed in-browser (`computeSolarTerminator`) | MIT (Derived) | Exact subsolar point & declination projecting night hemisphere polygon. |
| **MapLibre WebGL Engine** | `IMPLEMENTED` | MapLibre GL JS | CLIENT | Hardware-accelerated GPU canvas | BSD-3-Clause | 3D Globe & 2D Mercator projections, custom symbol rotation, zoom controls. |
| **Minimalist Dark Basemap** | `IMPLEMENTED` | Esri Dark Gray Canvas | LIVE | `https://server.arcgisonline.com/.../World_Dark_Gray_Base/...` | Esri MLA | Keyless minimalist dark aesthetic matching Astra black/zinc visual system. |
| **OpenStreetMap 2D Basemap** | `IMPLEMENTED` | OpenStreetMap Standard | LIVE | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | ODbL | Keyless high-detail political and topographic street map tiles for 2D mode. |
| **ESRI Satellite Imagery Base** | `IMPLEMENTED` | ESRI World Imagery | LIVE | `https://server.arcgisonline.com/.../tile/{z}/{y}/{x}` | Esri Terms | High-resolution satellite tiles toggled via single HUD button. |
| **Global Geosearch & FlyTo** | `IMPLEMENTED` | OpenStreetMap Nominatim | LIVE | `https://nominatim.openstreetmap.org/search` | ODbL | Search by city, country, coordinates, aircraft callsign, or satellite NORAD. |
| **Live Intelligence Feed Ticker** | `IMPLEMENTED` | Multi-source Event Stream | LIVE | Real-time Ingestion Pipeline | MIT (Derived) | Chronological event drawer with click-to-fly map centering. |
| **Contextual Region Dossier** | `IMPLEMENTED` | Astra Spatial Engine | LIVE | On Right-Click / Coordinate Selection | MIT (Derived) | Aggregates airspace, quakes, fires, and infrastructure within radius. |
| **Analyze with Astra AI** | `IMPLEMENTED` | Astra AI FastAPI Backend | LIVE | `POST /api/investigate` Bridge | Proprietary | Connects Earth View geographic envelope to local RTX 5060 AI specialists. |
| **Active Target Port Scanning** | `NOT INTEGRATED` | N/A (Excluded by Design) | N/A | Excluded per Security Specification | N/A | Excluded per Rule 20 & 29: Passive public intelligence only; no active probing. |

---

## 2. Summary Parity Score

- **Total Assessed Capabilities**: 28
- **Fully Implemented**: 27
- **Deliberately Excluded for Security (Active Scanning)**: 1
- **Feature Parity Compliance**: **100% of Permitted Passive Situational Awareness Features Implemented**
