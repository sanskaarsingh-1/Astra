# Third-Party Notice & Attribution: OSIRIS

This document documents third-party open-source components and architecture derived from or inspired by the **OSIRIS** project, integrated into the **Astra AI Earth View** module.

---

## 1. Upstream Project Details

- **Project Name**: OSIRIS (Open-Source Geospatial Situational Awareness System)
- **Primary Repository**: [https://github.com/simplifaisoul/osiris](https://github.com/simplifaisoul/osiris)
- **Official Website**: [https://www.osirisai.live/](https://www.osirisai.live/)
- **Documentation**: [https://www.osirisai.live/docs](https://www.osirisai.live/docs)
- **Author / Copyright Holder**: simplifaisoul (2026)
- **License**: MIT License

---

## 2. Original MIT License Notice

```text
MIT License

Copyright (c) 2026 simplifaisoul

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 3. Scope of OSIRIS-Derived Components in Astra Earth View

The following algorithms, interface concepts, and architectural patterns in Astra Earth View (`/earth`) are derived from or informed by OSIRIS:

1. **MapLibre GL & WebGL Layer Architecture**:
   - Dynamic GeoJSON source binding pattern with hardware-accelerated WebGL layers.
   - 2D Mercator and 3D Globe projection toggling.
   - Dynamic aircraft canvas icon generator (`createIcon`) with heading orientation.

2. **Astronomical Solar Terminator**:
   - Real-time subsolar point and declination mathematical model (`computeSolarTerminator`) projecting day/night hemispheres onto the MapLibre coordinate space.

3. **Data Normalization & Upstream Integration Concepts**:
   - ADS-B transponder decoding and airline fleet categorization (commercial, military, private jets).
   - Real-time SGP4 orbital propagation algorithms for active satellites via CelesTrak TLE datasets.
   - USGS seismic feed parsing, depth scaling, and magnitude threat-spectrum visualization.
   - NASA FIRMS thermal anomaly / active fire ingestion.
   - Public CCTV snapshot streaming integration.
   - Undersea submarine cable geometry rendering.

4. **Situational Awareness Interface Concepts**:
   - Grouped Layer Manager structure (Aviation, Maritime, Space, Earth, Geopolitical, Surveillance, Media, Infrastructure, Cyber).
   - Live entity counters based strictly on verified upstream data returns.
   - Live streaming intelligence ticker with click-to-fly interaction.
   - Region Dossier contextual spatial aggregation.

---

## 4. Distinctive Astra AI Integration & Differentiation

- **Astra Native Branding**: Completely aligned with Astra AI visual hierarchy (`Space_Grotesk`, `Inter`, `JetBrains_Mono`, dark minimalist theme).
- **Zero Fabrication Guarantee**: All entity layers display only authenticated, live or verified public data.
- **Deep AI Remote Sensing Bridge**: Direct integration between Earth View geographic coordinates and the local Astra AI FastAPI backend (`POST /api/investigate`), enabling on-demand deep VQA, LULC, Change Detection, and Optical-SAR analysis.
- **Exclusion of Active Reconnaissance**: No aggressive port scanning or vulnerability probing is exposed; all feeds operate strictly as passive public intelligence.
