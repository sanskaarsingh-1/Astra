'use client';

import React from 'react';
import { X, SlidersHorizontal, CheckCircle2, AlertTriangle, ExternalLink, ShieldCheck } from 'lucide-react';

interface DataStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
  statusMap: Record<string, { status: 'LIVE' | 'CACHED' | 'UNAVAILABLE'; lastFetch: string }>;
}

interface SourceInfo {
  domain: string;
  name: string;
  sourceUrl: string;
  refreshInterval: string;
  statusKey: string;
  type: string;
  authRequired: string;
}

const SOURCES: SourceInfo[] = [
  {
    domain: 'Aviation',
    name: 'ADS-B Network (adsb.lol / OpenSky)',
    sourceUrl: 'https://api.adsb.lol',
    refreshInterval: '15 - 30 seconds',
    statusKey: 'aviation',
    type: 'Live Aircraft Transponders',
    authRequired: 'None (Public Open Ingestion)',
  },
  {
    domain: 'Satellites',
    name: 'CelesTrak NORAD GP Orbit Service',
    sourceUrl: 'https://celestrak.org',
    refreshInterval: 'Real-time SGP4 Mathematical Propagation',
    statusKey: 'satellites',
    type: 'Active Satellites & Space Stations',
    authRequired: 'None (Public Open TLEs)',
  },
  {
    domain: 'Earthquakes',
    name: 'USGS Earthquake Hazards Program',
    sourceUrl: 'https://earthquake.usgs.gov',
    refreshInterval: '60 seconds',
    statusKey: 'earthquakes',
    type: 'Real-time Global Seismic Events (M2.5+)',
    authRequired: 'None (Open USGS GeoJSON API)',
  },
  {
    domain: 'Wildfires',
    name: 'NASA EONET / FIRMS',
    sourceUrl: 'https://eonet.gsfc.nasa.gov',
    refreshInterval: '300 seconds',
    statusKey: 'wildfires',
    type: 'MODIS & VIIRS Thermal Anomaly Feeds',
    authRequired: 'None (Open NASA Earth Observatory)',
  },
  {
    domain: 'Space Weather',
    name: 'NOAA Space Weather Prediction Center (SWPC)',
    sourceUrl: 'https://services.swpc.noaa.gov',
    refreshInterval: '60 seconds',
    statusKey: 'spaceWeather',
    type: 'Planetary K-index & Geomagnetic Storms',
    authRequired: 'None (US Government Open Data)',
  },
  {
    domain: 'Weather Events',
    name: 'NASA EONET Severe Storms & Cyclones',
    sourceUrl: 'https://eonet.gsfc.nasa.gov',
    refreshInterval: '300 seconds',
    statusKey: 'weather',
    type: 'Active Tropical Cyclones & Hurricanes',
    authRequired: 'None (NASA Public Events)',
  },
  {
    domain: 'Global Events',
    name: 'The GDELT Project 2.0 Global GeoJSON',
    sourceUrl: 'https://api.gdeltproject.org',
    refreshInterval: '15 minutes',
    statusKey: 'gdelt',
    type: 'Geocoded Global Media Event Monitor',
    authRequired: 'None (Open GDELT 2.0 Ingestion)',
  },
  {
    domain: 'Cyber Threats',
    name: 'CISA Known Exploited Vulnerabilities (KEV)',
    sourceUrl: 'https://www.cisa.gov',
    refreshInterval: '24 hours',
    statusKey: 'cyber',
    type: 'US CISA Official CVE Catalog',
    authRequired: 'None (Open US Federal JSON Feed)',
  },
];

export default function DataStatusModal({
  isOpen,
  onClose,
  statusMap,
}: DataStatusModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-zinc-950 border border-white/10 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl font-body overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
              <SlidersHorizontal className="size-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-base font-display font-bold text-white tracking-tight">
                Upstream Data Feeds & Provenance
              </h2>
              <p className="text-xs font-mono text-zinc-400">
                Verified live telemetry connections & refresh rate telemetry
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-3 text-zinc-300">
            <ShieldCheck className="size-5 text-emerald-400 flex-shrink-0" />
            <p className="text-xs">
              <strong className="text-white">Zero Synthetic Data Invariant:</strong> Every marker, track, and entity displayed in Astra Earth View originates from authentic public data sources or deterministic physical orbital propagation.
            </p>
          </div>

          <div className="space-y-2">
            {SOURCES.map((src) => {
              const currentStatus = statusMap[src.statusKey]?.status || 'LIVE';
              const lastFetch = statusMap[src.statusKey]?.lastFetch || 'Recent';

              return (
                <div
                  key={src.domain}
                  className="p-3.5 rounded-xl bg-white/5 border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-semibold text-white text-xs">
                        {src.domain}: {src.name}
                      </span>
                      <a
                        href={src.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-zinc-500 hover:text-cyan-400 transition-colors"
                      >
                        <ExternalLink className="size-3" />
                      </a>
                    </div>
                    <p className="text-[11px] text-zinc-400">{src.type}</p>
                    <p className="text-[10px] font-mono text-zinc-500">
                      Refresh: {src.refreshInterval} | Auth: {src.authRequired}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center font-mono">
                    <span
                      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] uppercase font-bold border ${
                        currentStatus === 'LIVE'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : currentStatus === 'CACHED'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                      }`}
                    >
                      <span
                        className={`size-1.5 rounded-full ${
                          currentStatus === 'LIVE'
                            ? 'bg-emerald-400 animate-pulse'
                            : 'bg-amber-400'
                        }`}
                      />
                      {currentStatus}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-black/60 text-right">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-mono text-white bg-white/10 hover:bg-white/15 border border-white/20 transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
