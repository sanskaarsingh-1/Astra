"use client";

import React from "react";
import Link from "next/link";
import { Globe, Satellite, Flame, Layers, ArrowRight, ShieldCheck, Activity, Compass } from "lucide-react";
import { FlowButton } from "@/components/ui/flow-button";

const DISCOVERY_CARDS = [
  {
    step: "01",
    tag: "Orbit Physics",
    title: "Live Satellite Constellation Passes",
    desc: "Propagates real-time SGP4 orbital mechanics for Cartosat-2S, RISAT-1A, and Sentinel constellations, displaying ground tracks, swaths, and sensor capture geometries.",
    icon: Satellite,
    badge: "SGP4 Propagation",
  },
  {
    step: "02",
    tag: "Live Telemetry",
    title: "Global Hazard & Disaster Telemetry",
    desc: "Aggregates authentic planetary feeds from USGS earthquakes (M2.5+), NASA FIRMS thermal hotspots, and GDACS flood and cyclone alerts with sub-meter spatial coordinates.",
    icon: Flame,
    badge: "USGS • NASA • GDACS",
  },
  {
    step: "03",
    tag: "Context Transfer",
    title: "Discovery-to-Analyze Pipeline",
    desc: "Inspect any planetary event or tactical coordinate in Earth View, then transfer authentic raster scene metadata directly into SatQuery AI with calibrated CRS projections intact.",
    icon: Layers,
    badge: "1-Click Handover",
  },
];

export default function EarthViewSection() {
  return (
    <section
      id="earth-view"
      aria-label="Earth View Discovery Layer"
      className="relative z-30 w-full bg-transparent py-24 sm:py-32 px-6 overflow-hidden"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section Label */}
        <div className="flex justify-center mb-6">
          <span className="text-zinc-400 text-xs font-mono uppercase tracking-wider">
            Earth View Discovery Layer
          </span>
        </div>

        {/* Heading - Space Grotesk 600 */}
        <h2 className="font-display font-semibold text-3xl sm:text-5xl text-white text-center tracking-tight max-w-3xl mx-auto mb-6">
          Earth View: Real-World Planetary Observation
        </h2>

        {/* Subtitle - Inter 400 */}
        <p className="font-body text-base sm:text-lg text-zinc-300 font-normal text-center max-w-2xl mx-auto mb-16 leading-relaxed">
          The situational awareness layer of Astra AI. Explore active satellite constellations,
          monitor real-time natural hazards worldwide, and pinpoint ground targets before launching deep AI analysis.
        </p>

        {/* 3 Column Preview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {DISCOVERY_CARDS.map((card) => (
            <div
              key={card.step}
              className="relative rounded-2xl border border-white/10 bg-zinc-950/70 p-7 backdrop-blur-md transition-all duration-300 hover:border-white/25 hover:bg-zinc-950/85 hover:-translate-y-1 hover:shadow-[0_12px_40px_-10px_rgba(0,0,0,0.8)] flex flex-col justify-between group"
            >
              {/* Specular hairline top accent */}
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-t-2xl pointer-events-none" />
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="size-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                    <card.icon className="size-5 text-white" />
                  </div>
                  <span className="text-xs font-mono text-zinc-400">
                    {card.badge}
                  </span>
                </div>

                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-mono text-zinc-500 font-medium">{card.step} /</span>
                  <span className="text-xs font-mono text-zinc-400 uppercase tracking-wider font-medium">{card.tag}</span>
                </div>

                <h3 className="font-display font-medium text-base sm:text-lg text-white mb-2">
                  {card.title}
                </h3>
                <p className="font-body text-xs sm:text-sm text-zinc-400 font-normal leading-relaxed">
                  {card.desc}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-zinc-500 font-mono">
                <span>0{card.step} of 03</span>
              </div>
            </div>
          ))}
        </div>

        {/* Tactical Handover Callout */}
        <div className="rounded-2xl border border-white/10 bg-zinc-950/80 p-6 sm:p-8 backdrop-blur-xl flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="size-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0">
              <Compass className="size-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-display font-medium text-white text-sm sm:text-base">
                  Ready for Global Exploration
                </span>
                <span className="text-xs text-zinc-500 font-body">
                  2D / 3D Globe
                </span>
              </div>
              <p className="font-body text-xs text-zinc-400 font-normal">
                Inspect events on the interactive map, select any region, and proceed directly to SatQuery AI.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <FlowButton
              href="/earth"
              variant="outline"
              text="Explore Earth View"
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl font-body font-medium text-xs uppercase tracking-wider"
            />
            <FlowButton
              href="/analyze"
              variant="primary"
              text="Analyze in SatQuery AI"
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl font-body font-semibold text-xs uppercase tracking-wider"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
