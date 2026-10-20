'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { Map as MlMap, GeoJSONSource } from 'maplibre-gl';
import type { FeatureCollection, Feature } from 'geojson';
import 'maplibre-gl/dist/maplibre-gl.css';
import { SatelliteEntity } from '@/lib/earth/data-sources';
import { DisasterEvent } from '@/lib/earth/disaster-events';

export interface MapViewport {
  lat: number;
  lng: number;
  zoom: number;
}

export interface EarthMapProps {
  activeMode: '2d' | '3d' | 'satellite';
  activeLayers: Record<string, boolean>;
  flyToCoords?: { lat: number; lng: number; zoom?: number; key?: number } | null;
  onEntitySelect?: (entity: { type: string; data: any }) => void;
  onDisasterSelect?: (event: DisasterEvent) => void;
  selectedDisaster?: DisasterEvent | null;
  onSceneSelect?: (coords: { lat: number; lng: number; zoom: number }) => void;
  onRegionDossierRequest?: (coords: { lat: number; lng: number }) => void;
  onCoordsChange?: (coords: { lat: number; lng: number; zoom: number }) => void;
  isAutoRotating?: boolean;

  // Real-time Disaster & Earth Observation Data
  disasterEvents?: DisasterEvent[];
  satellites?: SatelliteEntity[];

  // Legacy/optional props for backward compatibility
  aircraft?: any[];
  earthquakes?: any[];
  wildfires?: any[];
  weatherEvents?: any[];
  ports?: any[];
  cctvs?: any[];
  news?: any[];
  conflicts?: any[];
  frontlines?: any[];
  infrastructure?: any[];
  cables?: any[];
}

const EMPTY_GEOJSON: FeatureCollection = {
  type: 'FeatureCollection',
  features: [],
};

// Compute Astronomical Solar Terminator (Night Hemisphere Polygon)
function computeSolarTerminator(): FeatureCollection {
  const now = new Date();
  const dayOfYear = Math.floor(
    (now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000
  );
  const declination = -23.44 * Math.cos(((2 * Math.PI) / 365) * (dayOfYear + 10));
  const decRad = (declination * Math.PI) / 180;
  const utcHours = now.getUTCHours() + now.getUTCMinutes() / 60 + now.getUTCSeconds() / 3600;
  const subsolarLng = (12 - utcHours) * 15;

  // Protect against division by zero at equinox
  const safeTanDec = Math.abs(Math.tan(decRad)) < 0.005 ? 0.005 * (declination >= 0 ? 1 : -1) : Math.tan(decRad);

  const points: [number, number][] = [];
  for (let lng = -180; lng <= 180; lng += 3) {
    const lngRad = ((lng - subsolarLng) * Math.PI) / 180;
    const tanLat = -Math.cos(lngRad) / safeTanDec;
    const lat = (Math.atan(tanLat) * 180) / Math.PI;
    points.push([lng, Math.max(-85, Math.min(85, lat))]);
  }

  // Close polygon over polar night hemisphere
  const southPolarNight = declination > 0;
  const edgeLat = southPolarNight ? -89.9 : 89.9;
  const ring: [number, number][] = [
    [-180, edgeLat],
    ...points,
    [180, edgeLat],
    [-180, edgeLat],
  ];

  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [ring],
        },
        properties: {},
      },
    ],
  };
}

export default function EarthMap({
  activeMode,
  activeLayers,
  flyToCoords,
  onEntitySelect,
  onDisasterSelect,
  selectedDisaster,
  onSceneSelect,
  onRegionDossierRequest,
  onCoordsChange,
  isAutoRotating = false,
  disasterEvents = [],
  satellites = [],
}: EarthMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize MapLibre GL
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // Basemaps: OSM (2D) + Esri Dark Gray (3D) + Cesium ion Satellite (Satellite)
    const cesiumToken = process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN || '';
    const cesiumImageryTiles = process.env.NEXT_PUBLIC_CESIUM_IMAGERY_URL
      ? [process.env.NEXT_PUBLIC_CESIUM_IMAGERY_URL]
      : [
          'https://ecn.t0.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1',
          'https://ecn.t1.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1',
          'https://ecn.t2.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1',
          'https://ecn.t3.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1',
        ];

    const baseStyle = {
      version: 8 as const,
      sources: {
        'osm-tiles': {
          type: 'raster' as const,
          tiles: [
            'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution: '© OpenStreetMap contributors',
        },
        'esri-dark-gray': {
          type: 'raster' as const,
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
          ],
          tileSize: 256,
          attribution: '© Esri, DeLorme, NAVTEQ',
        },
        // Cesium ion Global Satellite Imagery (Asset ID 2: Bing Maps Aerial)
        'cesium-satellite': {
          type: 'raster' as const,
          tiles: cesiumImageryTiles,
          tileSize: 256,
          attribution: '© Cesium ion (Asset 2: Bing Maps Aerial), Microsoft',
        },
      },
      layers: [
        {
          id: 'osm-layer',
          type: 'raster' as const,
          source: 'osm-tiles',
          minzoom: 0,
          maxzoom: 19,
          layout: {
            visibility: (activeMode === '2d' ? 'visible' : 'none') as 'visible' | 'none',
          },
        },
        {
          id: 'esri-dark-layer',
          type: 'raster' as const,
          source: 'esri-dark-gray',
          minzoom: 0,
          maxzoom: 18,
          layout: {
            visibility: (activeMode === '3d' ? 'visible' : 'none') as 'visible' | 'none',
          },
        },
        {
          id: 'cesium-satellite-layer',
          type: 'raster' as const,
          source: 'cesium-satellite',
          minzoom: 0,
          maxzoom: 19,
          layout: {
            visibility: (activeMode === 'satellite' ? 'visible' : 'none') as 'visible' | 'none',
          },
        },
      ],
    };

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: baseStyle,
      center: [78.9629, 20.5937], // Centered on India / Indo-Pacific
      zoom: activeMode === '2d' ? 3.5 : 2.5,
      minZoom: 1.5,
      maxZoom: 19,
      attributionControl: false,
      // @ts-ignore
      projection: activeMode === '2d' ? { type: 'mercator' } : { type: 'globe' },
    });

    mapRef.current = map;

    // Gracefully handle tile fetch errors without disrupting disaster layers or HUD
    map.on('error', (e) => {
      if (e?.error?.message?.includes('tile') || e?.error?.message?.includes('fetch')) {
        console.warn('EarthMap tile fetch notice:', e.error.message);
      }
    });

    map.on('load', () => {
      // ─── GEOJSON SOURCES SETUP ──────────────────────────────────────────────
      const sourceIds = [
        'day-night',
        'satellites',
        'satellite-tracks',
        'disasters-points',
        'disaster-selected',
        'target-location',
      ];

      sourceIds.forEach((id) => {
        if (!map.getSource(id)) {
          map.addSource(id, { type: 'geojson', data: EMPTY_GEOJSON });
        }
      });

      // ─── 0. SEARCHED TARGET LOCATION RETICLE (Phase 8 & 14) ────────────────
      map.addLayer({
        id: 'target-location-halo',
        type: 'circle',
        source: 'target-location',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            1, 8,
            6, 16,
            12, 26,
            16, 38,
          ],
          'circle-color': '#06B6D4',
          'circle-opacity': 0.3,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#22D3EE',
          'circle-stroke-opacity': 0.9,
        },
      });
      map.addLayer({
        id: 'target-location-point',
        type: 'circle',
        source: 'target-location',
        paint: {
          'circle-radius': 5,
          'circle-color': '#FFFFFF',
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#0891B2',
        },
      });

      // ─── 1. DAY / NIGHT TERMINATOR ─────────────────────────────────────────
      map.addLayer({
        id: 'day-night-layer',
        type: 'fill',
        source: 'day-night',
        paint: {
          'fill-color': '#020617',
          'fill-opacity': 0.38,
        },
      });

      // ─── 2. SATELLITE ORBIT TRACKS ─────────────────────────────────────────
      map.addLayer({
        id: 'satellite-tracks-line',
        type: 'line',
        source: 'satellite-tracks',
        paint: {
          'line-color': '#10B981',
          'line-width': 1.2,
          'line-opacity': 0.5,
          'line-dasharray': [3, 2],
        },
      });

      // ─── 3. SATELLITES PINS (Earth Observation) ────────────────────────────
      map.addLayer({
        id: 'satellites-circle',
        type: 'circle',
        source: 'satellites',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 3.5, 6, 6],
          'circle-color': '#10B981',
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#FFFFFF',
          'circle-opacity': 0.9,
        },
      });
      map.addLayer({
        id: 'satellites-label',
        type: 'symbol',
        source: 'satellites',
        layout: {
          'text-field': ['get', 'name'],
          'text-size': 9,
          'text-font': ['Open Sans Regular'],
          'text-offset': [0, 1.2],
          'text-allow-overlap': false,
        },
        paint: {
          'text-color': '#A7F3D0',
          'text-halo-color': '#000000',
          'text-halo-width': 1.5,
        },
      });

      // ─── 4. SELECTED DISASTER POINTER PULSE / RETICLE ───────────────────────
      // Outer Halo Ring (Phase 7 & Phase 32: Unmistakable Event Pointer)
      map.addLayer({
        id: 'disaster-selected-halo',
        type: 'circle',
        source: 'disaster-selected',
        paint: {
          'circle-radius': 24,
          'circle-color': '#06B6D4',
          'circle-opacity': 0.25,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#22D3EE',
          'circle-stroke-opacity': 0.9,
        },
      });
      // Inner Pinpoint Reticle
      map.addLayer({
        id: 'disaster-selected-point',
        type: 'circle',
        source: 'disaster-selected',
        paint: {
          'circle-radius': 6,
          'circle-color': '#FFFFFF',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#0891B2',
        },
      });

      // ─── 5. DISASTERS: EARTHQUAKES (Scaled by Magnitude) ───────────────────
      map.addLayer({
        id: 'disaster-earthquakes-circle',
        type: 'circle',
        source: 'disasters-points',
        filter: ['==', ['get', 'category'], 'EARTHQUAKE'],
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['coalesce', ['get', 'magnitude'], 3.0],
            2.5,
            4,
            5.0,
            10,
            7.0,
            24,
          ],
          'circle-color': [
            'interpolate',
            ['linear'],
            ['coalesce', ['get', 'magnitude'], 3.0],
            2.5,
            '#FBBF24',
            5.0,
            '#F97316',
            6.5,
            '#EF4444',
          ],
          'circle-opacity': 0.75,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#FFFFFF',
        },
      });
      map.addLayer({
        id: 'disaster-earthquakes-label',
        type: 'symbol',
        source: 'disasters-points',
        filter: [
          'all',
          ['==', ['get', 'category'], 'EARTHQUAKE'],
          ['>=', ['coalesce', ['get', 'magnitude'], 0], 4.5],
        ],
        layout: {
          'text-field': ['concat', 'M', ['to-string', ['get', 'magnitude']]],
          'text-size': 10,
          'text-font': ['Open Sans Bold'],
          'text-offset': [0, 1.3],
          'text-allow-overlap': false,
        },
        paint: {
          'text-color': '#F97316',
          'text-halo-color': '#000000',
          'text-halo-width': 1.5,
        },
      });

      // ─── 6. DISASTERS: WILDFIRES (NASA EONET / FIRMS Pixel Centers) ─────────
      map.addLayer({
        id: 'disaster-wildfires-circle',
        type: 'circle',
        source: 'disasters-points',
        filter: ['==', ['get', 'category'], 'WILDFIRE'],
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 1, 4, 6, 8, 12, 12],
          'circle-color': '#EA580C',
          'circle-opacity': 0.85,
          'circle-blur': 0.2,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#FEF08A',
        },
      });

      // ─── 7. DISASTERS: VOLCANIC ACTIVITY (Distinct Red/Purple Summit Point) ─
      map.addLayer({
        id: 'disaster-volcanoes-circle',
        type: 'circle',
        source: 'disasters-points',
        filter: ['==', ['get', 'category'], 'VOLCANO'],
        paint: {
          'circle-radius': 9,
          'circle-color': '#DC2626',
          'circle-opacity': 0.9,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#FCA5A5',
        },
      });
      map.addLayer({
        id: 'disaster-volcanoes-label',
        type: 'symbol',
        source: 'disasters-points',
        filter: ['==', ['get', 'category'], 'VOLCANO'],
        layout: {
          'text-field': ['get', 'title'],
          'text-size': 9,
          'text-font': ['Open Sans Bold'],
          'text-offset': [0, 1.3],
          'text-allow-overlap': false,
        },
        paint: {
          'text-color': '#FCA5A5',
          'text-halo-color': '#000000',
          'text-halo-width': 1.5,
        },
      });

      // ─── 8. DISASTERS: CYCLONES & SEVERE STORMS ────────────────────────────
      map.addLayer({
        id: 'disaster-storms-circle',
        type: 'circle',
        source: 'disasters-points',
        filter: [
          'any',
          ['==', ['get', 'category'], 'CYCLONE'],
          ['==', ['get', 'category'], 'SEVERE_STORM'],
        ],
        paint: {
          'circle-radius': 10,
          'circle-color': '#0284C7',
          'circle-opacity': 0.8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#BAE6FD',
        },
      });
      map.addLayer({
        id: 'disaster-storms-label',
        type: 'symbol',
        source: 'disasters-points',
        filter: [
          'any',
          ['==', ['get', 'category'], 'CYCLONE'],
          ['==', ['get', 'category'], 'SEVERE_STORM'],
        ],
        layout: {
          'text-field': ['get', 'title'],
          'text-size': 9,
          'text-font': ['Open Sans Bold'],
          'text-offset': [0, 1.4],
          'text-allow-overlap': false,
        },
        paint: {
          'text-color': '#BAE6FD',
          'text-halo-color': '#000000',
          'text-halo-width': 1.5,
        },
      });

      // ─── 9. DISASTERS: FLOODS & HYDROLOGICAL ───────────────────────────────
      map.addLayer({
        id: 'disaster-floods-circle',
        type: 'circle',
        source: 'disasters-points',
        filter: ['==', ['get', 'category'], 'FLOOD'],
        paint: {
          'circle-radius': 8,
          'circle-color': '#2563EB',
          'circle-opacity': 0.8,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#BFDBFE',
        },
      });

      // ─── 10. DISASTERS: LANDSLIDES, DROUGHT & OTHER ENVIRONMENTAL ───────────
      map.addLayer({
        id: 'disaster-other-circle',
        type: 'circle',
        source: 'disasters-points',
        filter: [
          'all',
          ['!=', ['get', 'category'], 'EARTHQUAKE'],
          ['!=', ['get', 'category'], 'WILDFIRE'],
          ['!=', ['get', 'category'], 'VOLCANO'],
          ['!=', ['get', 'category'], 'CYCLONE'],
          ['!=', ['get', 'category'], 'SEVERE_STORM'],
          ['!=', ['get', 'category'], 'FLOOD'],
        ],
        paint: {
          'circle-radius': 7,
          'circle-color': '#D97706',
          'circle-opacity': 0.8,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#FDE68A',
        },
      });

      // ─── CLICK HANDLERS FOR DISASTER SELECTION ─────────────────────────────
      const disasterLayers = [
        'disaster-earthquakes-circle',
        'disaster-wildfires-circle',
        'disaster-volcanoes-circle',
        'disaster-storms-circle',
        'disaster-floods-circle',
        'disaster-other-circle',
      ];

      disasterLayers.forEach((layerId) => {
        map.on('click', layerId, (e) => {
          if (!e.features || e.features.length === 0) return;
          const feat = e.features[0];
          const eventId = feat.properties?.id;

          const matchedEvent = disasterEvents.find((ev) => ev.id === eventId);
          if (matchedEvent && onDisasterSelect) {
            onDisasterSelect(matchedEvent);
          } else if (onEntitySelect) {
            onEntitySelect({
              type: feat.properties?.category || 'disaster',
              data: feat.properties,
            });
          }
        });

        map.on('mouseenter', layerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = '';
        });
      });

      // Satellite pin click
      map.on('click', 'satellites-circle', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        if (onEntitySelect) {
          onEntitySelect({ type: 'satellite', data: feat.properties });
        }
      });
      map.on('mouseenter', 'satellites-circle', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'satellites-circle', () => {
        map.getCanvas().style.cursor = '';
      });

      // Generic Map Click: Select satellite scene if no disaster was clicked
      map.on('click', (e) => {
        const activeInteractive = [...disasterLayers, 'satellites-circle'].filter((id) =>
          map.getLayer(id)
        );
        const features = map.queryRenderedFeatures(e.point, { layers: activeInteractive });
        if (features && features.length > 0) return; // Handled by disaster marker click

        if (onSceneSelect) {
          onSceneSelect({
            lat: e.lngLat.lat,
            lng: e.lngLat.lng,
            zoom: map.getZoom(),
          });
        }
      });

      // Context menu right-click for Region Dossier
      map.on('contextmenu', (e) => {
        if (onRegionDossierRequest) {
          onRegionDossierRequest({ lat: e.lngLat.lat, lng: e.lngLat.lng });
        }
      });

      // Live Mouse Coordinates Readout (Phase 33)
      map.on('mousemove', (e) => {
        if (onCoordsChange) {
          onCoordsChange({
            lat: e.lngLat.lat,
            lng: e.lngLat.lng,
            zoom: map.getZoom(),
          });
        }
      });

      setMapLoaded(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Guarantee canvas fills 100% of viewport without black letterboxing
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;

    const triggerResize = () => {
      try {
        map.resize();
      } catch {}
    };

    window.addEventListener('resize', triggerResize);

    let ro: ResizeObserver | null = null;
    if (containerRef.current && typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(() => {
        triggerResize();
      });
      ro.observe(containerRef.current);
    }

    const t1 = setTimeout(triggerResize, 50);
    const t2 = setTimeout(triggerResize, 250);

    return () => {
      window.removeEventListener('resize', triggerResize);
      if (ro) ro.disconnect();
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [mapLoaded]);

  // Update Solar Terminator
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const source = mapRef.current.getSource('day-night') as GeoJSONSource | undefined;
    if (source) {
      source.setData(computeSolarTerminator());
    }
  }, [mapLoaded]);

  // Handle Mode Switch: 2D MAP <-> 3D GLOBE <-> SATELLITE
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;

    // 1. Projection switch: 2D uses mercator; 3D and SATELLITE use globe
    try {
      if (activeMode === '2d') {
        // @ts-ignore
        if (typeof map.setProjection === 'function') {
          // @ts-ignore
          map.setProjection({ type: 'mercator' });
        }
      } else {
        // @ts-ignore
        if (typeof map.setProjection === 'function') {
          // @ts-ignore
          map.setProjection({ type: 'globe' });
        }
      }
    } catch {}

    // 2. Basemap layer visibility
    if (map.getLayer('osm-layer')) {
      map.setLayoutProperty(
        'osm-layer',
        'visibility',
        activeMode === '2d' ? 'visible' : 'none'
      );
    }
    if (map.getLayer('esri-dark-layer')) {
      map.setLayoutProperty(
        'esri-dark-layer',
        'visibility',
        activeMode === '3d' ? 'visible' : 'none'
      );
    }
    if (map.getLayer('cesium-satellite-layer')) {
      map.setLayoutProperty(
        'cesium-satellite-layer',
        'visibility',
        activeMode === 'satellite' ? 'visible' : 'none'
      );
    }
  }, [mapLoaded, activeMode]);

  // Auto-rotation in 3D / Globe mode
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;
    if (activeMode === '2d' || !isAutoRotating) return;

    let animFrame: number;
    let lastTime = performance.now();

    const rotate = (currentTime: number) => {
      const delta = (currentTime - lastTime) / 1000;
      lastTime = currentTime;

      // Only rotate when user is not actively dragging or animating
      if (!map.isMoving()) {
        const center = map.getCenter();
        center.lng = (center.lng + delta * 3) % 360;
        map.setCenter(center);
      }
      animFrame = requestAnimationFrame(rotate);
    };

    animFrame = requestAnimationFrame(rotate);
    return () => cancelAnimationFrame(animFrame);
  }, [mapLoaded, activeMode, isAutoRotating]);

  // Handle FlyTo Location Requests (Phase 8 & Phase 14)
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;
    const source = map.getSource('target-location') as any;

    if (!flyToCoords) {
      if (source && typeof source.setData === 'function') {
        source.setData(EMPTY_GEOJSON);
      }
      return;
    }

    const targetZoom = flyToCoords.zoom || 13.5;

    // Place tactical target reticle pin on searched coordinates
    if (source && typeof source.setData === 'function') {
      source.setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [flyToCoords.lng, flyToCoords.lat],
            },
            properties: {
              label: `Target (${flyToCoords.lat.toFixed(4)}, ${flyToCoords.lng.toFixed(4)})`,
            },
          },
        ],
      });
    }

    try {
      map.stop();
      map.flyTo({
        center: [flyToCoords.lng, flyToCoords.lat],
        zoom: targetZoom,
        essential: true,
        duration: 1800,
      });
    } catch {
      map.jumpTo({
        center: [flyToCoords.lng, flyToCoords.lat],
        zoom: targetZoom,
      });
    }
  }, [mapLoaded, flyToCoords]);

  // Update Layer Visibility Toggles (Disasters & Earth Observation only)
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;

    const layerMap: Record<string, string[]> = {
      earthquakes: ['disaster-earthquakes-circle', 'disaster-earthquakes-label'],
      wildfires: ['disaster-wildfires-circle'],
      volcanoes: ['disaster-volcanoes-circle', 'disaster-volcanoes-label'],
      storms: ['disaster-storms-circle', 'disaster-storms-label'],
      floods: ['disaster-floods-circle'],
      otherHazards: ['disaster-other-circle'],
      satellites: ['satellites-circle', 'satellites-label', 'satellite-tracks-line'],
      daynight: ['day-night-layer'],
    };

    Object.entries(layerMap).forEach(([toggleKey, layerIds]) => {
      const isVisible = activeLayers[toggleKey] !== false;
      layerIds.forEach((id) => {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, 'visibility', isVisible ? 'visible' : 'none');
        }
      });
    });
  }, [mapLoaded, activeLayers]);

  // ─── SYNC DISASTER EVENTS TO MAP ──────────────────────────────────────────
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const source = mapRef.current.getSource('disasters-points') as GeoJSONSource | undefined;
    if (!source) return;

    const features: Feature[] = disasterEvents.map((ev) => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [ev.longitude, ev.latitude],
      },
      properties: {
        id: ev.id,
        category: ev.category,
        title: ev.title,
        placeName: ev.placeName,
        magnitude: ev.magnitude,
        depthKm: ev.depthKm,
        severity: ev.severity,
        source: ev.source,
        timestamp: ev.timestamp,
        geometryType: ev.geometryType,
      },
    }));

    source.setData({
      type: 'FeatureCollection',
      features,
    });
  }, [mapLoaded, disasterEvents]);

  // ─── SYNC SELECTED DISASTER POINTER ───────────────────────────────────────
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const source = mapRef.current.getSource('disaster-selected') as GeoJSONSource | undefined;
    if (!source) return;

    if (!selectedDisaster) {
      source.setData(EMPTY_GEOJSON);
      return;
    }

    source.setData({
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [selectedDisaster.longitude, selectedDisaster.latitude],
          },
          properties: {
            id: selectedDisaster.id,
            title: selectedDisaster.title,
          },
        },
      ],
    });
  }, [mapLoaded, selectedDisaster]);

  // ─── SYNC SATELLITES (Sentinel, Landsat, ISS) ─────────────────────────────
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const satSource = mapRef.current.getSource('satellites') as GeoJSONSource | undefined;
    const trackSource = mapRef.current.getSource('satellite-tracks') as GeoJSONSource | undefined;

    if (satSource) {
      const fc: FeatureCollection = {
        type: 'FeatureCollection',
        features: satellites.map((sat) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [sat.lng, sat.lat] },
          properties: { ...sat },
        })),
      };
      satSource.setData(fc);
    }

    if (trackSource) {
      const trackFeatures: Feature[] = [];
      satellites.forEach((sat) => {
        if (sat.trajectory) {
          sat.trajectory.forEach((run) => {
            trackFeatures.push({
              type: 'Feature',
              geometry: { type: 'LineString', coordinates: run },
              properties: { name: sat.name },
            });
          });
        }
      });
      trackSource.setData({ type: 'FeatureCollection', features: trackFeatures });
    }
  }, [mapLoaded, satellites]);

  return (
    <div className="relative w-full h-full overflow-hidden bg-black">
      <div ref={containerRef} className="w-full h-full" />

      {/* Basemap Attribution Badge (Mandatory OSM / Data Provenance) */}
      <div className="absolute bottom-2 right-2 z-20 pointer-events-auto bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded text-[10px] text-slate-400 border border-slate-800/80 shadow-sm flex items-center gap-1.5 select-none font-mono">
        {activeMode === '2d' ? (
          <>
            <span>Basemap:</span>
            <a
              href="https://www.openstreetmap.org/copyright"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-0.5"
            >
              © OpenStreetMap contributors
            </a>
          </>
        ) : activeMode === 'satellite' ? (
          <>
            <span>Imagery:</span>
            <span className="text-slate-300">© Cesium ion (Asset 2: Bing Maps Aerial)</span>
          </>
        ) : (
          <>
            <span>Basemap:</span>
            <span className="text-slate-300">© Esri, DeLorme, NAVTEQ</span>
          </>
        )}
      </div>
    </div>
  );
}
