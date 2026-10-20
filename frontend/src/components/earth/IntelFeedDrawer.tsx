'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Radio,
  Activity,
  Flame,
  Wind,
  Waves,
  Mountain,
  AlertTriangle,
  MapPin,
  ExternalLink,
  Compass,
} from 'lucide-react';
import {
  DisasterEvent,
  FeedSourceStatus,
  formatSignedCoordinates,
} from '@/lib/earth/disaster-events';

interface IntelFeedDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  disasterEvents?: DisasterEvent[];
  onFlyToDisaster: (event: DisasterEvent) => void;
  lastRefreshTimestamp?: number;
  sourceStatuses?: Record<string, FeedSourceStatus>;

  // Optional legacy props
  earthquakes?: any[];
  wildfires?: any[];
  weatherEvents?: any[];
  conflicts?: any[];
  news?: any[];
  onFlyToEvent?: (coords: { lat: number; lng: number; zoom?: number }) => void;
}

export default function IntelFeedDrawer({
  isOpen,
  onClose,
  disasterEvents = [],
  onFlyToDisaster,
  onFlyToEvent,
  lastRefreshTimestamp,
  sourceStatuses = {},
}: IntelFeedDrawerProps) {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [secondsAgo, setSecondsAgo] = useState(0);

  // Freshness timer
  useEffect(() => {
    const updateFreshness = () => {
      if (!lastRefreshTimestamp) {
        setSecondsAgo(0);
        return;
      }
      const diff = Math.max(0, Math.floor((Date.now() - lastRefreshTimestamp) / 1000));
      setSecondsAgo(diff);
    };

    updateFreshness();
    const interval = setInterval(updateFreshness, 1000);
    return () => clearInterval(interval);
  }, [lastRefreshTimestamp]);

  const freshnessLabel = useMemo(() => {
    if (secondsAgo < 5) return 'Just now';
    if (secondsAgo < 60) return `${secondsAgo}s ago`;
    const mins = Math.floor(secondsAgo / 60);
    if (mins === 1) return '1 min ago';
    return `${mins} mins ago`;
  }, [secondsAgo]);

  if (!isOpen) return null;

  // Filter disaster events
  const filteredEvents = disasterEvents.filter((ev) => {
    if (filterCategory === 'ALL') return true;
    if (filterCategory === 'CYCLONE') {
      return ev.category === 'CYCLONE' || ev.category === 'SEVERE_STORM';
    }
    return ev.category === filterCategory;
  });

  // Sort descending by timestamp (most recent live events first)
  const sortedEvents = [...filteredEvents].sort((a, b) => {
    const timeA = new Date(a.timestamp).getTime() || 0;
    const timeB = new Date(b.timestamp).getTime() || 0;
    return timeB - timeA;
  });

  const getCategoryConfig = (cat: DisasterEvent['category']) => {
    switch (cat) {
      case 'EARTHQUAKE':
        return {
          icon: Activity,
          color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
          label: 'Earthquake',
        };
      case 'WILDFIRE':
        return {
          icon: Flame,
          color: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
          label: 'Wildfire',
        };
      case 'CYCLONE':
      case 'SEVERE_STORM':
        return {
          icon: Wind,
          color: 'text-sky-400 bg-sky-500/10 border-sky-500/30',
          label: cat === 'CYCLONE' ? 'Cyclone' : 'Storm',
        };
      case 'VOLCANO':
        return {
          icon: Mountain,
          color: 'text-red-400 bg-red-500/10 border-red-500/30',
          label: 'Volcano',
        };
      case 'FLOOD':
        return {
          icon: Waves,
          color: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
          label: 'Flood',
        };
      default:
        return {
          icon: AlertTriangle,
          color: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
          label: 'Hazard',
        };
    }
  };

  const handleLocate = (ev: DisasterEvent) => {
    if (onFlyToDisaster) {
      onFlyToDisaster(ev);
    } else if (onFlyToEvent) {
      onFlyToEvent({ lat: ev.latitude, lng: ev.longitude, zoom: 8 });
    }
  };

  return (
    <aside className="fixed inset-y-0 right-0 z-40 w-full max-w-sm sm:max-w-md bg-zinc-950/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl flex flex-col font-body animate-in slide-in-from-right duration-200 select-none">
      {/* Drawer Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="size-8 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
            <Radio className="size-4 text-rose-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-display font-bold text-white uppercase tracking-wider">
              Disasters & Hazards Feed
            </h2>
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400 mt-0.5">
              <span className="flex items-center gap-1 text-emerald-400 font-bold">
                <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                LIVE
              </span>
              <span>·</span>
              <span>Updated {freshnessLabel}</span>
              <span>({sortedEvents.length} events)</span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          title="Close Feed"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-1.5 px-5 py-2.5 border-b border-white/5 overflow-x-auto text-[11px] font-mono scrollbar-none">
        {['ALL', 'EARTHQUAKE', 'WILDFIRE', 'CYCLONE', 'VOLCANO', 'FLOOD'].map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setFilterCategory(cat)}
            className={`px-2.5 py-1 rounded-lg uppercase tracking-wider transition-all whitespace-nowrap active:scale-95 ${
              filterCategory === cat
                ? 'bg-white text-zinc-950 font-bold shadow'
                : 'text-zinc-400 bg-white/5 hover:bg-white/10 hover:text-white'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Events Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sortedEvents.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 font-mono text-xs flex flex-col items-center gap-2">
            <Radio className="size-5 text-zinc-600 animate-pulse" />
            <span>No active events reported from official feeds for this category.</span>
          </div>
        ) : (
          sortedEvents.map((item) => {
            const config = getCategoryConfig(item.category);
            const Icon = config.icon;
            const signedCoords = formatSignedCoordinates(item.latitude, item.longitude);

            return (
              <div
                key={item.id}
                onClick={() => handleLocate(item)}
                className="p-3.5 rounded-xl bg-white/5 border border-white/10 hover:border-emerald-500/40 hover:bg-white/10 transition-all cursor-pointer space-y-2 group"
              >
                {/* Header row: Badge + UTC Time */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border flex items-center gap-1 ${config.color}`}
                    >
                      <Icon className="size-3" />
                      <span>{config.label}</span>
                    </span>
                    {item.magnitude !== null && item.magnitude !== undefined && (
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white/10 text-white border border-white/15">
                        {item.category === 'EARTHQUAKE' ? `M${item.magnitude.toFixed(1)}` : `${item.magnitude.toFixed(0)} kts`}
                      </span>
                    )}
                    {item.depthKm !== null && item.depthKm !== undefined && (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/10 text-zinc-300">
                        {item.depthKm} km
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400">
                    {item.timestamp ? new Date(item.timestamp).toISOString().substring(11, 16) : '--:--'} UTC
                  </span>
                </div>

                {/* Event Name & Place */}
                <div>
                  <h3 className="text-xs font-display font-semibold text-white group-hover:text-cyan-300 transition-colors line-clamp-1">
                    {item.placeName || item.title}
                  </h3>
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400/90 mt-1">
                    <Compass className="size-2.5 flex-shrink-0" />
                    <span>{signedCoords}</span>
                  </div>
                </div>

                {/* Footer row: Source & Action */}
                <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 pt-1.5 border-t border-white/5">
                  <div className="flex items-center gap-1 truncate max-w-[210px]">
                    <span className="truncate">Source: {item.source}</span>
                    {item.sourceUrl && (
                      <a
                        href={item.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-zinc-500 hover:text-white inline-flex items-center flex-shrink-0"
                        title="Open official event source"
                      >
                        <ExternalLink className="size-2.5 ml-0.5" />
                      </a>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLocate(item);
                    }}
                    className="text-cyan-400 hover:text-cyan-300 font-semibold group-hover:underline flex items-center gap-1 ml-auto flex-shrink-0"
                  >
                    Locate <MapPin className="size-2.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="p-3.5 border-t border-white/10 bg-black/40 text-[11px] font-mono text-zinc-500 flex items-center justify-between">
        <span className="truncate max-w-[180px]">
          {filterCategory === 'ALL' ? 'Multi-Agency Feeds' : `${filterCategory} Feed`}
        </span>
        <span className="text-emerald-400 flex items-center gap-1 flex-shrink-0">
          <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Verified Official Sources
        </span>
      </div>
    </aside>
  );
}
