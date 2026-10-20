"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Database, Satellite, ArrowRight } from "lucide-react";
import Footer from "@/components/Footer";

export default function DatasetsPage() {
  const products = [
    {
      id: "sentinel-2",
      badge: "Optical Ingest",
      title: "Multi-Spectral Sentinel-2 L2A",
      desc: "Calibrated 10m Ground Sample Distance (GSD) surface reflectance with 12 multispectral bands (RGB, NIR, RedEdge, SWIR). Ideal for NDVI vegetation vigor, burn scar severity, and flood perimeter segmentation.",
      specs: [
        { label: "Spatial Resolution", val: "10m - 20m" },
        { label: "Revisit Time", val: "5 Days" },
        { label: "Radiometric Bands", val: "12 Spectral Channels" },
        { label: "Pre-processing", val: "Orthorectified BOA Reflectance" },
      ],
      actionText: "Explore in Earth View",
      actionHref: "/earth",
    },
    {
      id: "sar-radar",
      badge: "All-Weather Radar",
      title: "SAR Radar Ingestion (Sentinel-1 GRD)",
      desc: "Synthetic Aperture Radar operating in C-band (5.405 GHz). Penetrates dense cloud decks, storm fronts, wildfire smoke, and nocturnal darkness with dual polarization (VV + VH) calibrated backscatter.",
      specs: [
        { label: "Polarization", val: "Dual-Pol (VV + VH)" },
        { label: "Cloud Penetration", val: "100% All-Weather" },
        { label: "Temporal Cadence", val: "6 - 12 Days" },
        { label: "Application", val: "Inundation & Structure Dielectric" },
      ],
      actionText: "Analyze with Cross-Modal Radar",
      actionHref: "/analyze",
    },
    {
      id: "hazard-feeds",
      badge: "Planetary Telemetry",
      title: "Live Planetary Hazard Feeds",
      desc: "Direct streaming telemetry integrating real-time USGS M2.5+ earthquake hypocenters, NASA FIRMS VIIRS/MODIS thermal hotspots, GDACS disaster alerts, and NOAA space weather geomagnetic indicators.",
      specs: [
        { label: "Update Frequency", val: "Sub-5 Minute Polling" },
        { label: "Data Providers", val: "USGS • NASA • GDACS • NOAA" },
        { label: "Global Coverage", val: "Worldwide GeoJSON / TMS" },
        { label: "Latency", val: "< 60 seconds from release" },
      ],
      actionText: "Monitor Live in Earth View",
      actionHref: "/earth",
    },
    {
      id: "geoai-api",
      badge: "Neural Inference",
      title: "Tactical GeoAI Inference API",
      desc: "Enterprise API access to our 7 specialized vision models and Vision-Language Reasoning pipeline. Supports zero-shot prompt queries, bi-temporal building damage assessment, and auditable JSON report generation.",
      specs: [
        { label: "Latency", val: "Sub-second on NVIDIA TensorRT" },
        { label: "Integrations", val: "REST API • Python SDK • GeoJSON" },
        { label: "Evidence Audit", val: "Cryptographic SHA-256 Hashes" },
        { label: "Deployment", val: "Cloud API or On-Premise Air-Gapped" },
      ],
      actionText: "Launch SatQuery Workspace",
      actionHref: "/analyze",
    },
    {
      id: "orbital-tasking",
      badge: "High-Resolution Constellation",
      title: "Custom Orbital Tasking & Archive",
      desc: "On-demand satellite acquisition and historical archive retargeting. Plan future orbital overpasses across Indian territory and global tactical theaters with sub-meter commercial tasking partners.",
      specs: [
        { label: "Ground Track", val: "SGP4 Two-Line Element (TLE)" },
        { label: "Pointing Precision", val: "Sub-kilometer ground swath" },
        { label: "Constellations", val: "ISRO Cartosat • RISAT • Sentinel" },
        { label: "Archive Depth", val: "2015 – Present Daily Revisit" },
      ],
      actionText: "View Mission Roadmap",
      actionHref: "/mission",
    },
  ];

  return (
    <div className="min-h-screen w-full bg-black text-foreground flex flex-col selection:bg-cyan-500/30 selection:text-cyan-50 relative font-body">
      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-20 relative z-10">
        {/* Navigation back */}
        <div className="mb-10">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-mono text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="size-4" />
            <span>Back to Home</span>
          </Link>
        </div>

        {/* Header Badge */}
        <div className="inline-flex items-center gap-2 mb-4 px-3.5 py-1 rounded-full border border-white/10 bg-white/5 text-zinc-300 text-xs font-mono uppercase tracking-widest">
          <Database className="size-3.5 text-cyan-400" />
          <span>Earth Observation Catalog</span>
        </div>

        {/* Title */}
        <h1 className="font-display font-semibold text-3xl sm:text-5xl text-white tracking-tight mb-4">
          Earth Data &amp; Information Products
        </h1>
        <p className="text-zinc-400 font-body text-base max-w-2xl mb-14 leading-relaxed">
          Access high-resolution satellite imagery rasters, real-time planetary hazard streams, and automated spatial AI inference models engineered for mission-critical situational awareness.
        </p>

        {/* Products Grid */}
        <div className="space-y-10">
          {products.map((item) => (
            <article
              key={item.id}
              id={item.id}
              className="scroll-mt-28 rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-9 backdrop-blur-md transition-all hover:border-white/20"
            >
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-6">
                <div>
                  <div className="inline-flex items-center gap-2 mb-3 px-3 py-0.5 rounded-full border border-white/10 bg-white/5 text-zinc-300 text-[11px] font-mono uppercase tracking-wider">
                    <Satellite className="size-3 text-cyan-400" />
                    <span>{item.badge}</span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold font-display text-white tracking-tight">
                    {item.title}
                  </h2>
                </div>

                <Link
                  href={item.actionHref}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-medium text-white bg-white/10 border border-white/15 hover:bg-white/20 transition-all self-start"
                >
                  <span>{item.actionText}</span>
                  <ArrowRight className="size-3.5 text-cyan-400" />
                </Link>
              </div>

              <p className="text-sm text-zinc-300 font-normal leading-relaxed mb-6 max-w-3xl">
                {item.desc}
              </p>

              {/* Specs Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 border-t border-white/10 text-xs">
                {item.specs.map((spec, sIdx) => (
                  <div key={sIdx} className="flex flex-col gap-1">
                    <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider">
                      {spec.label}
                    </span>
                    <span className="text-zinc-200 font-medium font-mono text-xs">
                      {spec.val}
                    </span>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
}
