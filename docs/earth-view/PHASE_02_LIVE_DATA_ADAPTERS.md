# Phase 02 — Live Data Adapters & Real-Time Normalization

**Target**: Implement live, real upstream data adapters for all OSIRIS domains with zero data fabrication, intelligent caching, and graceful failure isolation.

---

## Data Domain Coverage Checklist

- [x] **Aviation**: Real-time ADS-B aircraft positions (`https://api.adsb.lol/v2/` & OpenSky) with heading, altitude, speed, ICAO24, callsign, and category.
- [x] **Satellites**: Real-time active orbital objects from CelesTrak TLE feeds, calculated using `satellite.js` SGP4 propagation (ISS, Starlink, Earth Observation, Military Recon, GPS, Weather).
- [x] **Maritime**: Real-time AIS vessel locations, world ports, and strategic maritime chokepoints (Malacca, Hormuz, Suez, Panama, Bosphorus).
- [x] **Earthquakes**: USGS real-time seismic feed (last 24h M2.5+, magnitude, depth, place, timestamp).
- [x] **Wildfires**: NASA FIRMS thermal anomaly / active fire hotspots (VIIRS/MODIS open data).
- [x] **Weather & Natural Events**: Severe storm tracking, global temperature, and weather alerts via Open-Meteo & NOAA.
- [x] **Space Weather**: NOAA Space Weather Prediction Center (Planetary K-index, Solar Flare X-ray flux, Geomagnetic alerts).
- [x] **Air Quality**: Global air quality monitoring stations & AQI indices via OpenAQ public API.
- [x] **Public CCTVs & Webcams**: Verified live public traffic, harbor, and city webcams with real image snapshots.
- [x] **Global News & GDELT**: GDELT Project 2.0 real-time geocoded global event streams and world news.
- [x] **Conflicts & Frontlines**: Verified geopolitical conflict incident records, conflict zones, and frontlines.
- [x] **Critical Infrastructure**: World nuclear power facilities, strategic electrical grids, and undersea submarine communication cables.
- [x] **Passive Cyber Threat Feeds**: Real-time CISA Known Exploited Vulnerabilities (KEV) and threat telemetry.
- [x] **Defense & Commodity Markets**: Real-time defense equities, Brent crude, gold, and key commodities.

---

## Technical Specifications

1. **Error Isolation**:
   - Every fetch is wrapped in a dedicated try/catch with timeout (`AbortSignal.timeout(10000)`).
   - A failure in one source (e.g. USGS or ADS-B) will NEVER crash the Earth View or prevent other layers from loading.

2. **In-Memory Caching & Rate Limiting**:
   - Each layer maintains a TTL-based cache to prevent hammering upstream APIs.
   - Dynamic polling intervals:
     - Aircraft: 15–30s
     - Vessels: 60s
     - Satellites: 10s (recomputed via SGP4 propagation)
     - Earthquakes: 120s
     - Fires: 300s
     - Weather / Air Quality: 300s
     - Infrastructure / Cables: 24 hours (static reference)

3. **Progressive Loading**:
   - Data is fetched ONLY when the respective layer is toggled ON by the operator.
