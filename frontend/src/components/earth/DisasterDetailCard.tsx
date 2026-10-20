'use client';

import React, { useState } from 'react';
import {
  X,
  Sparkles,
  ExternalLink,
  Copy,
  Check,
  MapPin,
  Activity,
  Flame,
  Waves,
  Wind,
  Mountain,
  AlertTriangle,
  Radio,
  Clock,
  Navigation,
  Globe2,
} from 'lucide-react';
import { DisasterEvent, formatSignedCoordinates } from '@/lib/earth/disaster-events';

interface DisasterDetailCardProps {
  event: DisasterEvent | null;
  onClose: () => void;
  onViewSatellite: (event: DisasterEvent) => void;
  onAnalyzeWithAi: (event: DisasterEvent) => void;
}

export default function DisasterDetailCard({
  event,
  onClose,
  onViewSatellite,
  onAnalyzeWithAi,
}: DisasterDetailCardProps) {
  const [copied, setCopied] = useState(false);

  if (!event) return null;

  const handleCopyCoords = () => {
    const text = formatSignedCoordinates(event.latitude, event.longitude);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Disaster Icon & Color mapping
  const getCategoryConfig = (cat: DisasterEvent['category']) => {
    switch (cat) {
      case 'EARTHQUAKE':
        return {
          icon: Activity,
          bg: 'bg-amber-500/10',
          text: 'text-amber-400',
          border: 'border-amber-500/30',
          label: 'EARTHQUAKE',
        };
      case 'WILDFIRE':
        return {
          icon: Flame,
          bg: 'bg-rose-500/10',
          text: 'text-rose-400',
          border: 'border-rose-500/30',
          label: 'WILDFIRE HOTSPOT',
        };
      case 'CYCLONE':
        return {
          icon: Wind,
          bg: 'bg-teal-500/10',
          text: 'text-teal-400',
          border: 'border-teal-500/30',
          label: 'TROPICAL CYCLONE',
        };
      case 'SEVERE_STORM':
        return {
          icon: Wind,
          bg: 'bg-sky-500/10',
          text: 'text-sky-400',
          border: 'border-sky-500/30',
          label: 'SEVERE STORM',
        };
      case 'FLOOD':
        return {
          icon: Waves,
          bg: 'bg-blue-500/10',
          text: 'text-blue-400',
          border: 'border-blue-500/30',
          label: 'FLOOD EVENT',
        };
      case 'VOLCANO':
        return {
          icon: Mountain,
          bg: 'bg-red-500/10',
          text: 'text-red-400',
          border: 'border-red-500/30',
          label: 'VOLCANIC ACTIVITY',
        };
      case 'TSUNAMI':
        return {
          icon: Waves,
          bg: 'bg-cyan-500/10',
          text: 'text-cyan-400',
          border: 'border-cyan-500/30',
          label: 'TSUNAMI WARNING',
        };
      case 'LANDSLIDE':
        return {
          icon: AlertTriangle,
          bg: 'bg-yellow-500/10',
          text: 'text-yellow-400',
          border: 'border-yellow-500/30',
          label: 'LANDSLIDE',
        };
      case 'DROUGHT':
        return {
          icon: AlertTriangle,
          bg: 'bg-orange-500/10',
          text: 'text-orange-400',
          border: 'border-orange-500/30',
          label: 'DROUGHT / VEGETATION',
        };
      default:
        return {
          icon: AlertTriangle,
          bg: 'bg-zinc-500/10',
          text: 'text-zinc-400',
          border: 'border-zinc-500/30',
          label: 'ENVIRONMENTAL EVENT',
        };
    }
  };

  const config = getCategoryConfig(event.category);
  const IconComponent = config.icon;
  const formattedCoords = formatSignedCoordinates(event.latitude, event.longitude);

  return (
    <aside className="absolute bottom-6 right-4 sm:right-6 z-40 w-full max-w-md bg-zinc-950/95 backdrop-blur-xl border border-white/15 rounded-2xl shadow-2xl p-4 sm:p-5 flex flex-col gap-4 text-white font-mono animate-in fade-in slide-in-from-bottom-4 duration-300">
      {/* 1. Header with Category & Close */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${config.bg} ${config.text} ${config.border}`}
          >
            <IconComponent className="size-3.5" />
            <span>{config.label}</span>
          </span>
          {event.severity && event.severity !== 'NOT_AVAILABLE' && (
            <span
              className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                event.severity === 'CRITICAL' || event.severity === 'EXTREME'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : 'bg-zinc-800 text-zinc-300 border border-zinc-700'
              }`}
            >
              {event.severity}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={onClose}
          className="size-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          title="Close Card"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* 2. Place Name & Title */}
      <div className="flex flex-col gap-1">
        <div className="flex items-start gap-2">
          <MapPin className="size-4 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div className="flex flex-col">
            <span className="font-display font-semibold text-base sm:text-lg text-white leading-tight">
              {event.placeName}
            </span>
            {event.isPlaceDerived && (
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
                Derived: Nearest named place from geocoding service
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 3. Machine-readable Signed Coordinates & Spatial Accuracy */}
      <div className="flex flex-col gap-1.5 bg-black/50 border border-white/10 rounded-xl p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <Navigation className="size-3 text-emerald-400" />
            <span className="text-zinc-200 font-semibold tracking-wider select-all">
              {formattedCoords}
            </span>
          </div>

          <button
            type="button"
            onClick={handleCopyCoords}
            className="flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-zinc-300 transition-colors uppercase tracking-wider"
            title="COPY COORDINATES"
            aria-label="COPY COORDINATES"
          >
            {copied ? (
              <>
                <Check className="size-3 text-emerald-400" />
                <span className="text-emerald-400">COPIED</span>
              </>
            ) : (
              <>
                <Copy className="size-3" />
                <span>COPY COORDINATES</span>
              </>
            )}
          </button>
        </div>

        {/* Spatial Accuracy Disclaimer */}
        <div className="text-[10px] text-zinc-500 flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-emerald-400" />
          {event.geometryType === 'PIXEL_CENTER' && (
            <span>Detected Location (Satellite Pixel Center)</span>
          )}
          {event.geometryType === 'OFFICIAL_POINT' && (
            <span>Official Event Coordinates</span>
          )}
          {event.geometryType === 'AFFECTED_POLYGON' && (
            <span>Official Affected Area Geometry</span>
          )}
          {event.geometryType === 'STORM_TRACK' && (
            <span>Official Observation / Track Line</span>
          )}
          {event.geometryType === 'APPROXIMATE_CENTER' && (
            <span>Approximate Event Centroid</span>
          )}
        </div>
      </div>

      {/* 4. Event-Specific Telemetry Attributes */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {event.magnitude !== null && event.magnitude !== undefined && (
          <div className="bg-white/5 border border-white/5 rounded-lg p-2 flex flex-col">
            <span className="text-[10px] text-zinc-500 uppercase">Magnitude</span>
            <span className="text-base font-bold text-amber-400">{event.magnitude.toFixed(1)}</span>
          </div>
        )}

        {event.depthKm !== null && event.depthKm !== undefined && (
          <div className="bg-white/5 border border-white/5 rounded-lg p-2 flex flex-col">
            <span className="text-[10px] text-zinc-500 uppercase">Focal Depth</span>
            <span className="text-base font-bold text-zinc-200">{event.depthKm} km</span>
          </div>
        )}

        {event.metadata?.tsunami !== undefined && (
          <div className="bg-white/5 border border-white/5 rounded-lg p-2 flex flex-col">
            <span className="text-[10px] text-zinc-500 uppercase">Tsunami Threat</span>
            <span className={`text-sm font-bold ${event.metadata.tsunami ? 'text-rose-400' : 'text-emerald-400'}`}>
              {event.metadata.tsunami ? 'WARNING ACTIVE' : 'NO THREAT'}
            </span>
          </div>
        )}

        <div className="bg-white/5 border border-white/5 rounded-lg p-2 flex flex-col">
          <span className="text-[10px] text-zinc-500 uppercase">Detected Time</span>
          <span className="text-zinc-300 font-mono text-[11px] truncate">
            {new Date(event.timestamp).toUTCString().replace('GMT', 'UTC')}
          </span>
        </div>
      </div>

      {/* 5. Provenance & Source */}
      <div className="flex items-center justify-between text-[11px] text-zinc-400 border-t border-white/10 pt-2.5">
        <span className="truncate">Source: <strong className="text-zinc-200">{event.source}</strong></span>
        {event.sourceUrl && (
          <a
            href={event.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-emerald-400 hover:underline flex-shrink-0"
          >
            <span>Official Report</span>
            <ExternalLink className="size-3" />
          </a>
        )}
      </div>

      {/* 6. Primary Action Buttons (Phase 9 & 34) */}
      <div className="flex items-center gap-2 pt-1">
        {/* Switch to Satellite Mode */}
        <button
          type="button"
          onClick={() => onViewSatellite(event)}
          className="flex-1 flex items-center justify-center gap-1.5 bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold py-2 rounded-xl text-xs transition-all active:scale-95 uppercase tracking-wider"
          title="VIEW SATELLITE"
        >
          <Globe2 className="size-3.5 text-cyan-400" />
          <span>VIEW SATELLITE</span>
        </button>

        {/* Analyze with SatQuery AI / Astra AI */}
        <button
          type="button"
          onClick={() => onAnalyzeWithAi(event)}
          className="flex-1 flex items-center justify-center gap-1.5 bg-gradient-to-r from-emerald-400 to-teal-300 text-zinc-950 font-bold py-2 rounded-xl text-xs hover:brightness-110 shadow-lg shadow-emerald-500/20 transition-all active:scale-95 uppercase tracking-wider"
          title="ANALYZE WITH SATQUERY AI"
          aria-label="ANALYZE WITH ASTRA AI"
        >
          <Sparkles className="size-3.5 fill-zinc-950 text-zinc-950" />
          <span>ANALYZE WITH SATQUERY AI</span>
        </button>
      </div>
    </aside>
  );
}
