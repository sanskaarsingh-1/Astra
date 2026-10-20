'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import EarthHud, { ViewPreset, DisplayMode, FeedStatusInfo, DisasterFeedStatuses } from '@/components/earth/EarthHud';
import LayerManagerDrawer from '@/components/earth/LayerManagerDrawer';
import IntelFeedDrawer from '@/components/earth/IntelFeedDrawer';
import DisasterDetailCard from '@/components/earth/DisasterDetailCard';
import DataStatusModal from '@/components/earth/DataStatusModal';
import SatQuerySceneInspector, { SceneCoords } from '@/components/earth/SatQuerySceneInspector';
import {
  DisasterEvent,
  fetchLiveDisasterIntelligence,
  fetchNoaaSpaceWeather,
  cachedDisasterFetch,
  SpaceWeatherState,
  FeedSourceStatus,
} from '@/lib/earth/disaster-events';
import {
  fetchActiveSatellites,
  cachedFetch,
  SatelliteEntity,
} from '@/lib/earth/data-sources';
import { parseCoordinates } from '@/lib/earth/coordinate-parser';

// Dynamically import MapLibre map component to avoid SSR/WebGL issues
const EarthMap = dynamic(() => import('@/components/earth/EarthMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-black flex flex-col items-center justify-center gap-3 text-zinc-400 font-mono text-xs">
      <div className="size-7 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
      <span>INITIALIZING ASTRA EARTH VIEW ENGINE...</span>
    </div>
  ),
});

// Dynamically import D3 Canvas Rotating Earth
const RotatingEarthCanvas = dynamic(() => import('@/components/earth/RotatingEarthCanvas'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-black flex flex-col items-center justify-center gap-3 text-zinc-400 font-mono text-xs">
      <div className="size-7 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
      <span>INITIALIZING D3 ORTHOGRAPHIC GLOBE...</span>
    </div>
  ),
});

export default function EarthViewPage() {
  const router = useRouter();

  // Core Display Mode: '2d' | '3d' | 'satellite'
  const [activeMode, setActiveMode] = useState<DisplayMode>('satellite');
  const [isAutoRotating, setIsAutoRotating] = useState(false);
  const [isD3GlobeActive, setIsD3GlobeActive] = useState(false);

  // Active Layers State (Phase 36: Clean disaster and Earth Observation layers)
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    earthquakes: true,
    wildfires: true,
    storms: true,
    volcanoes: true,
    floods: true,
    otherHazards: true,
    satellites: true,
    daynight: true,
    spaceWeather: true,
  });

  // Ensure full-bleed viewport aspect ratio with zero black void letterboxing
  useEffect(() => {
    document.documentElement.classList.add('earth-view-active');
    document.body.classList.add('earth-view-active');
    const originalHtmlZoom = document.documentElement.style.zoom;
    const originalBodyZoom = document.body.style.zoom;
    document.documentElement.style.zoom = '1';
    document.body.style.zoom = '1';

    return () => {
      document.documentElement.classList.remove('earth-view-active');
      document.body.classList.remove('earth-view-active');
      document.documentElement.style.zoom = originalHtmlZoom;
      document.body.style.zoom = originalBodyZoom;
    };
  }, []);

  const [flyToCoords, setFlyToCoords] = useState<{ lat: number; lng: number; zoom?: number; key?: number } | null>(null);
  const [mouseCoords, setMouseCoords] = useState({ lat: 20.59, lng: 78.96, zoom: 3.5 });

  // Drawers & Modals
  const [isLayerManagerOpen, setIsLayerManagerOpen] = useState(false);
  const [isIntelFeedOpen, setIsIntelFeedOpen] = useState(false);
  const [isDataStatusOpen, setIsDataStatusOpen] = useState(false);
  const [selectedDisaster, setSelectedDisaster] = useState<DisasterEvent | null>(null);
  const [selectedSceneCoords, setSelectedSceneCoords] = useState<SceneCoords | null>(null);
  const [isSceneInspectorOpen, setIsSceneInspectorOpen] = useState(false);

  // Real-time Disaster & Earth Observation Datasets
  const [disasterEvents, setDisasterEvents] = useState<DisasterEvent[]>([]);
  const [satellites, setSatellites] = useState<SatelliteEntity[]>([]);
  const [spaceWeather, setSpaceWeather] = useState<SpaceWeatherState>({
    kpIndex: 2.1,
    geomagneticStatus: 'QUIET',
    solarFlareFlux: 'B8.4',
    solarWindSpeedKmS: 395.0,
    alerts: [],
    timestamp: new Date().toISOString(),
    source: 'NOAA SWPC',
  });

  // Detailed Upstream Feed Statuses
  const [feedStatuses, setFeedStatuses] = useState<DisasterFeedStatuses>({
    earthquakes: { status: 'LOADING', count: 0 },
    wildfires: { status: 'LOADING', count: 0 },
    storms: { status: 'LOADING', count: 0 },
    volcanoes: { status: 'LOADING', count: 0 },
    floods: { status: 'LOADING', count: 0 },
    satellites: { status: 'LOADING', count: 0 },
  });

  const [statusMap, setStatusMap] = useState<Record<string, { status: 'LIVE' | 'CACHED' | 'UNAVAILABLE'; lastFetch: string }>>({});

  const [lastDisasterRefresh, setLastDisasterRefresh] = useState<number>(Date.now());
  const [sourceStatuses, setSourceStatuses] = useState<Record<string, FeedSourceStatus>>({});

  // ─── 1. FETCH MULTI-SOURCE NATURAL DISASTERS (USGS, EONET, NWS, VOLCANOES, GDACS, NHC) ───
  const loadDisasters = useCallback(async () => {
    try {
      const { events, sourceStatuses: newStatuses, refreshTimestamp } = await fetchLiveDisasterIntelligence();

      setDisasterEvents(events);
      setLastDisasterRefresh(refreshTimestamp);
      setSourceStatuses(newStatuses);

      // Separate genuine counts
      const quakesCount = events.filter((e) => e.category === 'EARTHQUAKE').length;
      const firesCount = events.filter((e) => e.category === 'WILDFIRE').length;
      const stormsCount = events.filter((e) => e.category === 'CYCLONE' || e.category === 'SEVERE_STORM').length;
      const volcanoesCount = events.filter((e) => e.category === 'VOLCANO').length;
      const floodsCount = events.filter((e) => e.category === 'FLOOD').length;

      setFeedStatuses((prev) => ({
        ...prev,
        earthquakes: {
          status: newStatuses.usgs?.status === 'LIVE' || newStatuses.usgs?.status === 'STALE' ? 'LIVE' : (quakesCount > 0 ? 'LIVE' : 'UNAVAILABLE'),
          count: quakesCount,
        },
        wildfires: {
          status: newStatuses.eonet?.status === 'LIVE' || newStatuses.eonet?.status === 'STALE' ? 'LIVE' : (firesCount > 0 ? 'LIVE' : 'UNAVAILABLE'),
          count: firesCount,
        },
        storms: {
          status: (newStatuses.eonet?.status === 'LIVE' || newStatuses.nws?.status === 'LIVE' || newStatuses.gdacs?.status === 'LIVE') ? 'LIVE' : (stormsCount > 0 ? 'LIVE' : 'UNAVAILABLE'),
          count: stormsCount,
        },
        volcanoes: {
          status: (newStatuses.volcanoes?.status === 'LIVE' || newStatuses.eonet?.status === 'LIVE' || newStatuses.gdacs?.status === 'LIVE') ? 'LIVE' : (volcanoesCount > 0 ? 'LIVE' : 'UNAVAILABLE'),
          count: volcanoesCount,
        },
        floods: {
          status: (newStatuses.nws?.status === 'LIVE' || newStatuses.eonet?.status === 'LIVE' || newStatuses.gdacs?.status === 'LIVE') ? 'LIVE' : (floodsCount > 0 ? 'LIVE' : 'UNAVAILABLE'),
          count: floodsCount,
        },
      }));

      setStatusMap((prev) => {
        const updated = { ...prev };
        Object.entries(newStatuses).forEach(([k, v]) => {
          updated[k] = {
            status: v.status === 'LIVE' ? 'LIVE' : v.status === 'STALE' ? 'CACHED' : 'UNAVAILABLE',
            lastFetch: v.lastSuccess || new Date().toLocaleTimeString(),
          };
        });
        return updated;
      });
    } catch (err) {
      console.warn('[Astra Earth] Live disaster load error:', err);
    }
  }, []);

  // ─── 2. FETCH SPACE WEATHER (NOAA SWPC) ───────────────────────────────────
  const loadSpaceWeather = useCallback(async () => {
    try {
      const { data, fromCache } = await cachedDisasterFetch('noaa_space_wx', fetchNoaaSpaceWeather, 60000);
      setSpaceWeather(data);
      setStatusMap((prev) => ({
        ...prev,
        spaceWeather: { status: fromCache ? 'CACHED' : 'LIVE', lastFetch: new Date().toLocaleTimeString() },
      }));
    } catch {
      setStatusMap((prev) => ({
        ...prev,
        spaceWeather: { status: 'UNAVAILABLE', lastFetch: 'Failed' },
      }));
    }
  }, []);

  // ─── 3. FETCH SATELLITES (CelesTrak SGP4) ──────────────────────────────────
  const loadSatellites = useCallback(async () => {
    try {
      const { data, fromCache } = await cachedFetch('celestrak_sats', fetchActiveSatellites, 30000);
      setSatellites(data);
      setFeedStatuses((prev) => ({
        ...prev,
        satellites: { status: data.length > 0 ? 'LIVE' : 'UNAVAILABLE', count: data.length },
      }));
      setStatusMap((prev) => ({
        ...prev,
        satellites: { status: fromCache ? 'CACHED' : 'LIVE', lastFetch: new Date().toLocaleTimeString() },
      }));
    } catch {
      setFeedStatuses((prev) => ({
        ...prev,
        satellites: { status: prev.satellites?.count ? 'LIVE' : 'UNAVAILABLE', count: prev.satellites?.count || 0 },
      }));
      setStatusMap((prev) => ({
        ...prev,
        satellites: { status: 'UNAVAILABLE', lastFetch: 'Failed' },
      }));
    }
  }, []);

  // Initial Data Ingestion and Polling Setup
  useEffect(() => {
    loadDisasters();
    loadSpaceWeather();
    loadSatellites();

    const disasterTimer = setInterval(loadDisasters, 60000);
    const spaceTimer = setInterval(loadSpaceWeather, 60000);
    const satTimer = setInterval(loadSatellites, 30000);

    return () => {
      clearInterval(disasterTimer);
      clearInterval(spaceTimer);
      clearInterval(satTimer);
    };
  }, [loadDisasters, loadSpaceWeather, loadSatellites]);

  // Handle Layer Toggle
  const handleToggleLayer = (key: string) => {
    setActiveLayers((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // Handle Search Queries (Coordinates or Place/Disaster Search)
  const handleSearchSubmit = async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;

    // Check if coordinates format: e.g. "18.5204, 73.8567", "28.6139° N, 77.2090° E", etc.
    const parsedCoords = parseCoordinates(trimmed);
    if (parsedCoords) {
      setIsAutoRotating(false);
      const target = {
        lat: parsedCoords.lat,
        lng: parsedCoords.lng,
        zoom: parsedCoords.zoom,
        key: Date.now(),
      };
      setFlyToCoords(target);
      setSelectedSceneCoords({
        lat: parsedCoords.lat,
        lng: parsedCoords.lng,
        zoom: parsedCoords.zoom,
      });
      return;
    }

    // Check if matching any disaster title or place name
    const disasterMatch = disasterEvents.find(
      (d) =>
        d.title.toLowerCase().includes(trimmed.toLowerCase()) ||
        d.placeName.toLowerCase().includes(trimmed.toLowerCase())
    );
    if (disasterMatch) {
      setSelectedDisaster(disasterMatch);
      setIsAutoRotating(false);
      setFlyToCoords({ lat: disasterMatch.latitude, lng: disasterMatch.longitude, zoom: 11, key: Date.now() });
      return;
    }

    // Check if matching satellite NORAD or Name
    const satMatch = satellites.find(
      (s) => s.noradId === trimmed || s.name.toLowerCase().includes(trimmed.toLowerCase())
    );
    if (satMatch) {
      setIsAutoRotating(false);
      setFlyToCoords({ lat: satMatch.lat, lng: satMatch.lng, zoom: 6, key: Date.now() });
      return;
    }

    // Fallback: Geocode via OpenStreetMap Nominatim
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(trimmed)}`
      );
      if (res.ok) {
        const json = await res.json();
        if (json && json.length > 0) {
          const lat = parseFloat(json[0].lat);
          const lng = parseFloat(json[0].lon);
          setIsAutoRotating(false);
          const target = { lat, lng, zoom: 12, key: Date.now() };
          setFlyToCoords(target);
          setSelectedSceneCoords({ lat, lng, zoom: 12 });
        }
      }
    } catch {
      console.warn('Geocoding search failed');
    }
  };

  // ─── DISASTER SELECTION & NAVIGATION (Phase 8 & 14) ──────────────────────
  const handleDisasterSelect = (ev: DisasterEvent) => {
    setSelectedDisaster(ev);
    setFlyToCoords({ lat: ev.latitude, lng: ev.longitude, zoom: 8 });
  };

  // ─── "VIEW SATELLITE" WORKFLOW (Phase 15 & 29) ───────────────────────────
  const handleViewSatellite = (ev: DisasterEvent) => {
    setActiveMode('satellite');
    setFlyToCoords({ lat: ev.latitude, lng: ev.longitude, zoom: 10 });
  };

  // ─── "ANALYZE WITH ASTRA AI" BRIDGE (Phase 16 & 17: Rich Context) ─────
  const handleAnalyzeWithAi = (ev: DisasterEvent) => {
    const userQuery = `Analyze remote-sensing land cover and satellite scene evidence around ${ev.placeName} for ${ev.category.toLowerCase()} impact.`;

    const contextPayload = {
      event_type: ev.category.toLowerCase(),
      latitude: ev.latitude,
      longitude: ev.longitude,
      place_name: ev.placeName,
      timestamp: ev.timestamp,
      source: ev.source,
      magnitude: ev.magnitude,
      depth_km: ev.depthKm,
      geometry_type: ev.geometryType,
      user_query: userQuery,
    };

    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem(
        'ASTRA_ANALYSIS_REQUEST',
        JSON.stringify({
          lat: ev.latitude,
          lng: ev.longitude,
          context: JSON.stringify(contextPayload),
          query: userQuery,
          mode: 'single',
          timestamp: new Date().toISOString(),
        })
      );
    }

    const queryParam = encodeURIComponent(userQuery);
    router.push(`/analyze?lat=${ev.latitude.toFixed(4)}&lng=${ev.longitude.toFixed(4)}&query=${queryParam}&mode=single`);
  };

  // Generic Scene Analysis Bridge
  const handleAnalyzeSceneCoords = (coords: { lat: number; lng: number; query?: string; mode?: string }) => {
    const query = coords.query || `Analyze satellite imagery at ${coords.lat.toFixed(4)}°, ${coords.lng.toFixed(4)}°`;
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem(
        'ASTRA_ANALYSIS_REQUEST',
        JSON.stringify({
          lat: coords.lat,
          lng: coords.lng,
          context: `Geospatial coordinates: ${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)}`,
          query,
          mode: coords.mode || 'single',
          timestamp: new Date().toISOString(),
        })
      );
    }
    const queryParam = encodeURIComponent(query);
    router.push(`/analyze?lat=${coords.lat.toFixed(4)}&lng=${coords.lng.toFixed(4)}&query=${queryParam}&mode=${coords.mode || 'single'}`);
  };

  const activeLayersCount = Object.values(activeLayers).filter(Boolean).length;

  return (
    <div id="earth-view-root" className="earth-view-container fixed inset-0 w-full h-full min-h-screen overflow-hidden bg-black select-none">
      {/* 1. Primary Geospatial Rendering Engine */}
      {activeMode === '3d' && isD3GlobeActive ? (
        <RotatingEarthCanvas
          onLocationSelect={(coords) => {
            setFlyToCoords({ lat: coords.lat, lng: coords.lng, zoom: 5 });
            setIsD3GlobeActive(false); // Seamless transition into WebGL on location focus
          }}
        />
      ) : (
        <EarthMap
          activeMode={activeMode}
          activeLayers={activeLayers}
          flyToCoords={flyToCoords}
          onDisasterSelect={handleDisasterSelect}
          selectedDisaster={selectedDisaster}
          onSceneSelect={(coords) => {
            setSelectedSceneCoords(coords);
            setIsSceneInspectorOpen(true);
          }}
          onCoordsChange={setMouseCoords}
          isAutoRotating={isAutoRotating}
          disasterEvents={disasterEvents}
          satellites={satellites}
        />
      )}

      {/* 2. Top HUD Bar with 2D / 3D / SATELLITE Switcher and Disaster Counters */}
      <EarthHud
        activeMode={activeMode}
        onModeChange={(mode) => {
          setActiveMode(mode);
          if (mode !== '3d') {
            setIsD3GlobeActive(false);
          }
        }}
        feedStatuses={feedStatuses}
        mouseCoords={mouseCoords}
        activeLayersCount={activeLayersCount}
        isAutoRotating={isAutoRotating}
        onToggleAutoRotate={() => setIsAutoRotating((prev) => !prev)}
        isD3GlobeActive={isD3GlobeActive}
        onToggleD3Globe={() => setIsD3GlobeActive((prev) => !prev)}
        onAnalyzeSceneClick={() => {
          setSelectedSceneCoords({
            lat: mouseCoords.lat,
            lng: mouseCoords.lng,
            zoom: mouseCoords.zoom,
          });
          setIsSceneInspectorOpen(true);
        }}
        onOpenLayerManager={() => setIsLayerManagerOpen(true)}
        onOpenIntelFeed={() => setIsIntelFeedOpen(true)}
        onOpenDataStatus={() => setIsDataStatusOpen(true)}
        onSelectPreset={(preset: ViewPreset) => setFlyToCoords(preset)}
        onSearchSubmit={handleSearchSubmit}
        spaceWeatherKp={spaceWeather.kpIndex}
        spaceWeatherStatus={spaceWeather.geomagneticStatus}
      />

      {/* 3. Layer Manager Drawer */}
      <LayerManagerDrawer
        isOpen={isLayerManagerOpen}
        onClose={() => setIsLayerManagerOpen(false)}
        activeLayers={activeLayers}
        onToggleLayer={handleToggleLayer}
        entityCounts={{
          earthquakes: feedStatuses.earthquakes.count,
          wildfires: feedStatuses.wildfires.count,
          storms: feedStatuses.storms?.count || 0,
          volcanoes: feedStatuses.volcanoes?.count || 0,
          floods: feedStatuses.floods?.count || 0,
          otherHazards: disasterEvents.filter((d) => d.category === 'LANDSLIDE' || d.category === 'DROUGHT').length,
          satellites: satellites.length,
        }}
      />

      {/* 4. Disaster Detail Card (Phase 9, 32, 34) */}
      <DisasterDetailCard
        event={selectedDisaster}
        onClose={() => setSelectedDisaster(null)}
        onViewSatellite={handleViewSatellite}
        onAnalyzeWithAi={handleAnalyzeWithAi}
      />

      {/* 5. Live Natural Disasters Feed Drawer */}
      <IntelFeedDrawer
        isOpen={isIntelFeedOpen}
        onClose={() => setIsIntelFeedOpen(false)}
        disasterEvents={disasterEvents}
        lastRefreshTimestamp={lastDisasterRefresh}
        sourceStatuses={sourceStatuses}
        onFlyToDisaster={(ev) => {
          handleDisasterSelect(ev);
          setIsIntelFeedOpen(false);
        }}
      />

      {/* 6. Upstream Data Status Modal */}
      <DataStatusModal
        isOpen={isDataStatusOpen}
        onClose={() => setIsDataStatusOpen(false)}
        statusMap={statusMap}
      />

      {/* 7. SatQuery AI Scene Inspector & Query Panel */}
      <SatQuerySceneInspector
        isOpen={isSceneInspectorOpen}
        coords={selectedSceneCoords}
        onClose={() => setIsSceneInspectorOpen(false)}
        onOpenInSatQuery={(params) =>
          handleAnalyzeSceneCoords({
            lat: params.lat,
            lng: params.lng,
            query: params.query,
            mode: params.mode,
          })
        }
      />
    </div>
  );
}
