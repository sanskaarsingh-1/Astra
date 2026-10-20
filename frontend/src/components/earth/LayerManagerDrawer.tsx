'use client';

import React from 'react';
import {
  X,
  Layers,
  Plane,
  Satellite,
  Activity,
  Flame,
  CloudLightning,
  Anchor,
  Camera,
  ShieldAlert,
  Zap,
  Cable,
  SunMoon,
  Check,
} from 'lucide-react';

interface LayerManagerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeLayers: Record<string, boolean>;
  onToggleLayer: (layerKey: string) => void;
  entityCounts: Record<string, number>;
}

interface LayerGroup {
  id: string;
  name: string;
  icon: React.ElementType;
  color: string;
  layers: {
    key: string;
    label: string;
    description: string;
    countKey?: string;
  }[];
}

const LAYER_GROUPS: LayerGroup[] = [
  {
    id: 'disasters',
    name: 'Natural Disasters & Hazards',
    icon: Activity,
    color: 'text-orange-400',
    layers: [
      {
        key: 'earthquakes',
        label: 'Earthquakes (M2.5+)',
        description: 'USGS real-time seismic feed with magnitude scaling',
        countKey: 'earthquakes',
      },
      {
        key: 'wildfires',
        label: 'Wildfires & Thermal Hotspots',
        description: 'NASA EONET / FIRMS satellite detection pixel centers',
        countKey: 'wildfires',
      },
      {
        key: 'storms',
        label: 'Cyclones & Severe Storms',
        description: 'NOAA / NASA active tropical storm tracking and centers',
        countKey: 'storms',
      },
      {
        key: 'volcanoes',
        label: 'Volcanic Activity',
        description: 'Global active summit eruptions & thermal anomalies',
        countKey: 'volcanoes',
      },
      {
        key: 'floods',
        label: 'Floods & Hydrological Events',
        description: 'Inundation and severe precipitation alerts',
        countKey: 'floods',
      },
      {
        key: 'otherHazards',
        label: 'Landslides & Drought',
        description: 'Geohazards and regional moisture deficits',
        countKey: 'otherHazards',
      },
    ],
  },
  {
    id: 'observation',
    name: 'Earth Observation & Satellites',
    icon: Satellite,
    color: 'text-emerald-400',
    layers: [
      {
        key: 'satellites',
        label: 'Earth Observation Satellites',
        description: 'Sentinel, Landsat, Terra, Aqua & ISS orbital tracks',
        countKey: 'satellites',
      },
      {
        key: 'daynight',
        label: 'Solar Terminator (Day / Night)',
        description: 'Real-time astronomical night hemisphere projection',
      },
    ],
  },
];

export default function LayerManagerDrawer({
  isOpen,
  onClose,
  activeLayers,
  onToggleLayer,
  entityCounts,
}: LayerManagerDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 left-0 z-40 w-full max-w-sm sm:max-w-md bg-zinc-950/95 backdrop-blur-2xl border-r border-white/10 shadow-2xl flex flex-col font-body animate-in slide-in-from-left duration-200">
      {/* Drawer Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="size-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
            <Layers className="size-4 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-display font-bold text-white uppercase tracking-wider">
              Layer Manager
            </h2>
            <p className="text-[11px] font-mono text-zinc-400">
              Toggle live geospatial feeds
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Layer Groups List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {LAYER_GROUPS.map((group) => {
          const GroupIcon = group.icon;
          return (
            <div key={group.id} className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400">
                <GroupIcon className={`size-3.5 ${group.color}`} />
                <span>{group.name}</span>
              </div>

              <div className="space-y-2">
                {group.layers.map((layer) => {
                  const isActive = activeLayers[layer.key] !== false;
                  const count =
                    layer.countKey && entityCounts[layer.countKey] !== undefined
                      ? entityCounts[layer.countKey]
                      : null;

                  return (
                    <div
                      key={layer.key}
                      onClick={() => onToggleLayer(layer.key)}
                      className={`flex items-start justify-between p-3 rounded-xl border transition-all cursor-pointer select-none ${
                        isActive
                          ? 'bg-white/5 border-white/20 hover:border-white/30'
                          : 'bg-transparent border-white/5 opacity-60 hover:opacity-80'
                      }`}
                    >
                      <div className="flex-1 pr-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-display font-medium text-white">
                            {layer.label}
                          </span>
                          {count !== null && (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/10 text-zinc-300 border border-white/10">
                              {count.toLocaleString()}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] font-body text-zinc-400 mt-0.5">
                          {layer.description}
                        </p>
                      </div>

                      {/* Custom Toggle Switch */}
                      <div
                        className={`size-5 rounded-md flex items-center justify-center border transition-all flex-shrink-0 mt-0.5 ${
                          isActive
                            ? 'bg-emerald-500 border-emerald-400 text-black'
                            : 'border-zinc-700 bg-zinc-900'
                        }`}
                      >
                        {isActive && <Check className="size-3 stroke-[3]" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-white/10 bg-black/40 text-[11px] font-mono text-zinc-500 flex items-center justify-between">
        <span>Progressive Viewport Ingestion</span>
        <span className="text-emerald-400">Verified Sensor Feeds</span>
      </div>
    </div>
  );
}
