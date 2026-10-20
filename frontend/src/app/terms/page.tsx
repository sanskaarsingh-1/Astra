"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, FileText, AlertTriangle, Cpu, Globe, Scale } from "lucide-react";
import Footer from "@/components/Footer";

export default function TermsPage() {
  return (
    <div className="min-h-screen w-full bg-black text-foreground flex flex-col selection:bg-cyan-500/30 selection:text-cyan-50 relative font-body">
      <main className="flex-1 w-full max-w-4xl mx-auto px-6 py-20 relative z-10">
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
          <FileText className="size-3.5 text-cyan-400" />
          <span>User Agreement</span>
        </div>

        {/* Title */}
        <h1 className="font-display font-semibold text-3xl sm:text-5xl text-white tracking-tight mb-4">
          Terms of Service
        </h1>
        <p className="text-zinc-400 font-mono text-xs mb-12">
          Last Updated: September 2026 • Astra AI Platform Terms
        </p>

        {/* Content Sections */}
        <div className="space-y-8 text-sm text-zinc-300 leading-relaxed">
          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <Scale className="size-4 text-cyan-400" />
              1. Scope &amp; Acceptance
            </h2>
            <p>
              By accessing Astra AI, Earth View, or the SatQuery AI investigation interface, you agree to comply with these Terms of Service. If you are accessing this platform on behalf of a government agency, research university, or commercial entity, you confirm you have appropriate authorization.
            </p>
          </section>

          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <Cpu className="size-4 text-emerald-400" />
              2. Nature of Automated AI Model Outputs
            </h2>
            <p className="mb-3">
              Astra AI employs deep learning segmentation, change-detection models, and Vision-Language Reasoning agents. While models are validated against authentic benchmarks (e.g. BigEarthNet, SpaceNet, and Sentinel-2 ground truth), outputs represent probabilistic classifications and algorithmic estimates.
            </p>
            <p>
              Automated reports are engineered to accelerate tactical disaster triage and situational assessment, but human operators should cross-verify mission-critical spatial conclusions against official state authority directives.
            </p>
          </section>

          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <Globe className="size-4 text-amber-400" />
              3. Permissible Geospatial Use
            </h2>
            <p className="mb-3">
              Users may ingest satellite rasters for scientific research, disaster relief, climate monitoring, urban analysis, and humanitarian logistics. Users must not use the platform for unauthorized surveillance of protected facilities or in violation of Indian National Geospatial guidelines.
            </p>
          </section>

          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <AlertTriangle className="size-4 text-rose-400" />
              4. API Rate Limits &amp; Service Availability
            </h2>
            <p>
              High-throughput batch inference and continuous multi-spectral pipeline tasking are subject to compute quota limits to maintain system stability across all concurrent operators.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
