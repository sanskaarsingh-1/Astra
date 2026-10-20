# Phase 04 — Entity Cards, Details Panel & Global Search

**Target**: Provide detailed contextual entity drawers for every map feature and global geosearch with smooth camera flight.

---

## Capabilities Checklist

- [x] **Global Geosearch**:
  - Search cities, countries, coordinates (e.g. `28.61, 77.20`), airports, ICAO hex codes, satellite NORAD IDs.
  - Integration with OpenStreetMap Nominatim geocoding.
  - Keyboard navigation and instant flyTo with elevation/pitch.

- [x] **Entity Detail Card (Right Drawer)**:
  - **Aircraft Card**: Callsign, ICAO24 hex, registration, altitude (feet and meters), groundspeed (knots and km/h), true track heading, aircraft model/type, and origin/destination airports.
  - **Satellite Card**: Satellite name, NORAD ID, mission classification (Earth Observation, Comms, Military, Space Station), altitude (km), velocity, inclination, period, and ground track.
  - **Maritime Vessel Card**: Name, MMSI, vessel type (Cargo, Tanker, Military, Fishing), speed, course, destination, and status.
  - **Earthquake Card**: Magnitude, depth (km), exact location, timestamp, USGS link, and tsunami warning flag.
  - **Wildfire Card**: Satellite sensor, brightness temperature (Kelvin), confidence level, and acquisition date.
  - **CCTV Webcam Card**: Camera name, operator source, location, live snapshot preview, and refresh button.
  - **Infrastructure Card**: Facility name, type, capacity (MW if power plant), commissioning year, and country.
  - **Submarine Cable Card**: Cable name, landing points, owners/consortium, length (km), and ready-for-service date.
