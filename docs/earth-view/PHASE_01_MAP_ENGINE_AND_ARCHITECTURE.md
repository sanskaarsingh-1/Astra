# Phase 01 — Map Engine & Architecture Implementation

**Target**: Stand up `/earth` route, MapLibre GL WebGL engine, 2D/3D projections, Day/Night terminator, base styles, and navigation links.

---

## Objectives & Invariants

- [x] Add `/earth` route in Next.js App Router (`frontend/src/app/earth/page.tsx`)
- [x] Add "Earth View" link to `Navbar.tsx` and homepage sections
- [x] Implement MapLibre GL wrapper component (`frontend/src/components/earth/EarthMap.tsx`) with dynamic SSR-safe import
- [x] Implement Carto Dark Matter base tiles and ESRI World Imagery satellite tiles
- [x] Implement mathematical astronomical solar terminator (`computeSolarTerminator`)
- [x] Support 3D Globe and 2D Mercator projections
- [x] Include compass, pitch, bearing, zoom, and live mouse coordinate readout
- [x] Preserve existing styling, font family (`Space_Grotesk`, `Inter`, `JetBrains_Mono`), and dark minimalism

---

## Step-by-Step Execution Plan

1. **Navigation Update**:
   - Update `frontend/src/components/Navbar.tsx` to include `Earth View` (`/earth`) in desktop LimelightNav and mobile drawer.
   - Update `NAV_LINKS` and activeTab synchronization.

2. **MapLibre Component**:
   - Create `frontend/src/components/earth/EarthMap.tsx`
   - Handle WebGL context, resize observer, and smooth flyTo interactions
   - Setup canvas aircraft symbol generator and marker icons

3. **Solar Terminator Layer**:
   - Calculate UTC solar position, declination, and generate GeoJSON polygon covering night hemisphere
   - Add fill layer with smooth transition and opacity

4. **Earth View Page**:
   - Create `frontend/src/app/earth/page.tsx`
   - Client component with dynamic import of `EarthMap` to avoid SSR issues
   - Minimalist top bar, sidebar hooks, and full viewport sizing
