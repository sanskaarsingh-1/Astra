"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Award, Database, Binary, ShieldAlert } from "lucide-react";
import Footer from "@/components/Footer";

export default function EthicsPage() {
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
          <Award className="size-3.5 text-cyan-400" />
          <span>AI Governance</span>
        </div>

        {/* Title */}
        <h1 className="font-display font-semibold text-3xl sm:text-5xl text-white tracking-tight mb-4">
          Sovereign Data Ethics
        </h1>
        <p className="text-zinc-400 font-mono text-xs mb-12">
          Smart India Hackathon 2026 • Sovereign AI Principles &amp; Geospatial Integrity
        </p>

        {/* Content Sections */}
        <div className="space-y-8 text-sm text-zinc-300 leading-relaxed">
          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <Database className="size-4 text-cyan-400" />
              1. Sovereign Compute &amp; Data Residency
            </h2>
            <p className="mb-3">
              Under SIH 2026 directives, Astra AI prioritizes domestic infrastructure hosting. Sensitive national boundary data, high-resolution domestic satellite captures, and defense-adjacent infrastructure queries never transit foreign clouds or unverified edge proxies.
            </p>
          </section>

          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <Binary className="size-4 text-emerald-400" />
              2. Algorithmic Transparency &amp; Anti-Hallucination
            </h2>
            <p className="mb-3">
              Large language models can hallucinate geographic observations. To counter this, Astra enforces a strict separation of powers: LLMs/VLMs are restricted to reasoning and translation, while spatial quantification (surface area, distance, delta NDVI) is performed strictly by deterministic math kernels outside the neural weights.
            </p>
            <p>
              Every finding must cite an authentic visual pixel coordinate or spectral band index to prevent fabricated spatial evidence.
            </p>
          </section>

          <section className="rounded-2xl border border-white/10 bg-zinc-950/70 p-6 sm:p-8 backdrop-blur-md">
            <h2 className="text-lg font-semibold text-white font-display flex items-center gap-2 mb-3">
              <ShieldAlert className="size-4 text-amber-400" />
              3. Conflict Detection in Specialist Consensus
            </h2>
            <p>
              Our 7 specialized vision models cross-audit findings. If Model A detects standing water but Model B’s SAR dielectric assessment indicates dry terrain, the conflicting evidence is surfaced explicitly in the final report rather than smoothed over or suppressed.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
