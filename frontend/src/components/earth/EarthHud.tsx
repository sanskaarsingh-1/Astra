'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Satellite,
  Radio,
  Search,
  SlidersHorizontal,
  Zap,
  ArrowLeft,
} from 'lucide-react';
// Supported projection modes: 2D MAP | 3D GLOBE | SATELLITE
export type DisplayMode = '2d' | '3d' | 'satellite';
export type FeedStatusType =
  | 'LIVE'
  | 'LOADING'
  | 'OFFLINE'
  | 'UNAVAILABLE'
  | 'REQUIRES_API_KEY'
  | 'RATE_LIMITED'
  | 'ERROR';

export interface FeedStatusInfo {
  status: FeedStatusType;
  count: number;
}

export interface ViewPreset {
  name: string;
  lat: number;
  lng: number;
  zoom: number;
}

export const VIEW_PRESETS: ViewPreset[] = [
  { name: 'Indo-Pacific (ISRO)', lat: 20.59, lng: 78.96, zoom: 4.2 },
  { name: 'Global View', lat: 20.0, lng: 0.0, zoom: 2.0 },
  { name: 'Middle East', lat: 27.5, lng: 45.0, zoom: 4.5 },
  { name: 'Europe', lat: 50.0, lng: 15.0, zoom: 4.2 },
  { name: 'East Asia', lat: 32.0, lng: 120.0, zoom: 4.5 },
  { name: 'Americas', lat: 38.0, lng: -97.0, zoom: 3.8 },
];

export interface DisasterFeedStatuses {
  earthquakes: FeedStatusInfo;
  wildfires: FeedStatusInfo;
  storms?: FeedStatusInfo;
  volcanoes?: FeedStatusInfo;
  floods?: FeedStatusInfo;
  satellites?: FeedStatusInfo;
  // Backward compatibility
  weather?: FeedStatusInfo;
  aircraft?: FeedStatusInfo;
  cctvs?: FeedStatusInfo;
  conflicts?: FeedStatusInfo;
}

export interface EarthHudProps {
  activeMode?: DisplayMode;
  onModeChange?: (mode: DisplayMode) => void;
  feedStatuses: DisasterFeedStatuses;
  spaceWeatherKp: number;
  spaceWeatherStatus?: string;
  activeLayersCount?: number;
  mouseCoords: { lat: number; lng: number; zoom: number };
  isAutoRotating?: boolean;
  onToggleAutoRotate?: () => void;
  isD3GlobeActive?: boolean;
  onToggleD3Globe?: () => void;
  onAnalyzeSceneClick?: () => void;
  onOpenLayerManager?: () => void;
  onOpenIntelFeed: () => void;
  onOpenDataStatus?: () => void;
  onSelectPreset?: (preset: ViewPreset) => void;
  onSearchSubmit: (query: string) => void;
}

function renderStatusBadge(feed: FeedStatusInfo) {
  if (feed.status === 'LOADING') {
    return (
      <span className="text-[10px] text-zinc-400 font-mono animate-pulse tracking-wide font-medium">
        LOADING...
      </span>
    );
  }
  if (feed.status === 'OFFLINE') {
    return (
      <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 font-mono font-bold border border-red-500/30">
        OFFLINE
      </span>
    );
  }
  if (feed.status === 'UNAVAILABLE') {
    return (
      <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-mono font-bold border border-amber-500/30">
        UNAVAIL
      </span>
    );
  }
  if (feed.status === 'RATE_LIMITED') {
    return (
      <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-mono font-bold border border-amber-500/30">
        RATE LTD
      </span>
    );
  }
  if (feed.status === 'REQUIRES_API_KEY') {
    return (
      <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono font-bold border border-blue-500/30">
        KEY REQ
      </span>
    );
  }
  if (feed.status === 'ERROR') {
    return (
      <span className="text-[9px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono font-bold border border-rose-500/30">
        ERROR
      </span>
    );
  }
  // LIVE: display genuine count (even if 0)
  return <span className="font-semibold text-white font-mono">{feed.count.toLocaleString()}</span>;
}

export default function EarthHud({
  activeMode,
  onModeChange,
  feedStatuses,
  spaceWeatherKp,
  spaceWeatherStatus,
  activeLayersCount,
  mouseCoords,
  isAutoRotating = false,
  onToggleAutoRotate,
  isD3GlobeActive = false,
  onToggleD3Globe,
  onAnalyzeSceneClick,
  onOpenLayerManager,
  onOpenIntelFeed,
  onOpenDataStatus,
  onSelectPreset,
  onSearchSubmit,
}: EarthHudProps) {
  const [utcTime, setUtcTime] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(
        now.toISOString().substring(11, 19) + ' UTC'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSearchSubmit(searchQuery.trim());
    }
  };

  return (
    <>
      {/* ─── TOP STATUS & NAVIGATION BAR ────────────────────────────────────── */}
      {/* ─── TOP STATUS & NAVIGATION BAR ────────────────────────────────────── */}
      <header className="absolute top-0 left-0 right-0 z-30 pointer-events-none p-2 sm:p-3">
        <div className="max-w-[1920px] mx-auto w-full flex flex-col gap-2">
          {/* Main Top Header: Compact Single Row */}
          <div className="flex items-center justify-between gap-2.5 sm:gap-3 bg-zinc-950/90 backdrop-blur-md border border-white/10 rounded-2xl px-3 sm:px-4 py-2 shadow-2xl pointer-events-auto">
            {/* Left: Brand, Return Navigation, Search, and Live Disaster Statistics */}
            <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
              {/* Back to Home */}
              <Link
                href="/"
                className="size-8 sm:size-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-zinc-300 hover:text-white hover:bg-white/10 transition-colors flex-shrink-0"
                title="Back to Astra Home"
              >
                <ArrowLeft className="size-4" />
              </Link>

              {/* Astra AI Brand + EARTH Badge */}
              <Link href="/" className="flex items-center gap-2 group flex-shrink-0">
                <div className="size-8 sm:size-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:border-white/30 transition-colors flex-shrink-0">
                  <Satellite className="size-4 text-white" />
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="font-display font-semibold text-sm sm:text-base tracking-tight text-white whitespace-nowrap">
                    Astra AI
                  </span>
                  <span className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1 whitespace-nowrap">
                    <span className="size-1 rounded-full bg-emerald-400 animate-pulse" />
                    EARTH
                  </span>
                </div>
              </Link>

              {/* Global Search Bar */}
              <form
                onSubmit={handleSearch}
                className="relative flex items-center w-48 sm:w-60 md:w-68 lg:w-76 flex-shrink-0"
              >
                <Search className="absolute left-2.5 size-3.5 text-zinc-400 pointer-events-none" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search place, coords..."
                  className="w-full bg-black/60 border border-white/10 rounded-xl pl-8 pr-11 py-1.5 text-xs font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 transition-all shadow-inner"
                />
                <button
                  type="submit"
                  className="absolute right-1 px-2 py-0.5 rounded-lg text-[9px] font-mono font-bold uppercase tracking-wider bg-white/10 hover:bg-white/20 text-zinc-200 transition-colors"
                >
                  GO
                </button>
              </form>

              {/* Live Situational Disaster Statistics Ribbon */}
              <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-zinc-400 bg-black/40 border border-white/10 px-3 py-1.5 rounded-xl shadow-inner flex-shrink-0">
                <span className="text-[10px] uppercase text-zinc-500 font-semibold tracking-wider">
                  DISASTERS:
                </span>
                <div className="flex items-center gap-1">
                  <span className="text-zinc-500">Quakes</span>
                  {renderStatusBadge(feedStatuses.earthquakes)}
                </div>
                <span className="text-zinc-700">•</span>
                <div className="flex items-center gap-1">
                  <span className="text-zinc-500">Fires</span>
                  {renderStatusBadge(feedStatuses.wildfires)}
                </div>
                <span className="text-zinc-700">•</span>
                <div className="flex items-center gap-1">
                  <span className="text-zinc-500">Storms</span>
                  {renderStatusBadge(feedStatuses.storms || feedStatuses.weather || { status: 'LOADING', count: 0 })}
                </div>
                {feedStatuses.volcanoes && (
                  <>
                    <span className="text-zinc-700">•</span>
                    <div className="flex items-center gap-1">
                      <span className="text-zinc-500">Volcanoes</span>
                      {renderStatusBadge(feedStatuses.volcanoes)}
                    </div>
                  </>
                )}
                {feedStatuses.floods && (
                  <>
                    <span className="text-zinc-700">•</span>
                    <div className="flex items-center gap-1">
                      <span className="text-zinc-500">Floods</span>
                      {renderStatusBadge(feedStatuses.floods)}
                    </div>
                  </>
                )}
                <span className="text-zinc-700">•</span>
                <div className="flex items-center gap-1 text-cyan-300">
                  <Zap className="size-3" />
                  <span>Kp {spaceWeatherKp.toFixed(1)}</span>
                </div>
              </div>
            </div>

            {/* Right: Disasters Action Button */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                type="button"
                onClick={onOpenIntelFeed}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-medium text-rose-300 bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/15 hover:border-rose-500/30 hover:text-white transition-all whitespace-nowrap active:scale-95 shadow-sm"
                title="Live Natural Disasters & Planetary Hazards Feed"
              >
                <Radio className="size-3.5 text-rose-400 animate-pulse flex-shrink-0" />
                <span>Disasters</span>
              </button>

              {onOpenDataStatus && (
                <button
                  type="button"
                  onClick={onOpenDataStatus}
                  className="p-2 rounded-xl text-zinc-400 bg-white/5 border border-white/10 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all active:scale-95 flex-shrink-0"
                  title="Upstream Feeds & Data Provenance Status"
                >
                  <SlidersHorizontal className="size-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Coordinate & Zoom Status Pill — Below main header toward top-left */}
          <div className="flex items-center self-start pointer-events-auto">
            <div className="flex items-center gap-2 bg-zinc-950/85 backdrop-blur-md border border-white/10 rounded-xl px-2.5 py-1 text-xs font-mono text-zinc-300 shadow-xl whitespace-nowrap">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>
                {mouseCoords.lat >= 0
                  ? `${mouseCoords.lat.toFixed(4)}°N`
                  : `${Math.abs(mouseCoords.lat).toFixed(4)}°S`}
                ,{' '}
                {mouseCoords.lng >= 0
                  ? `${mouseCoords.lng.toFixed(4)}°E`
                  : `${Math.abs(mouseCoords.lng).toFixed(4)}°W`}
              </span>
              <span className="text-zinc-600">|</span>
              <span className="text-zinc-200 font-semibold">Z {mouseCoords.zoom.toFixed(1)}x</span>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
