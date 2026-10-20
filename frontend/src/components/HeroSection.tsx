"use client";

import React from "react";
import Link from "next/link";
import { Satellite, ShieldCheck, Cpu } from "lucide-react";
import { Highlighter } from "@/registry/magicui/highlighter";

export default function HeroSection() {
  return (
    <section
      id="home"
      aria-label="Astra AI Hero"
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-transparent pt-28 pb-16 px-6"
    >
      <div className="relative z-10 max-w-4xl w-full mx-auto flex flex-col items-center text-center">
        {/* Minimalist SIH Label */}
        <div className="inline-flex items-center gap-2 mb-6 text-zinc-400 text-xs font-body">
          <Satellite className="size-3.5 text-zinc-400" />
          <span>Smart India Hackathon 2026</span>
        </div>

        {/* Headline - Space Grotesk 700 */}
        <h1 className="font-display font-bold text-4xl sm:text-6xl lg:text-7xl xl:text-[5rem] text-white leading-[1.04] tracking-tight mb-6 max-w-4xl">
          Turn Satellite Data into Actionable Insights.
        </h1>

        {/* Subheading - Inter 400 */}
        <p className="font-body text-base sm:text-lg lg:text-xl text-zinc-300 font-normal leading-relaxed mb-6 max-w-2xl">
          Astra is an agentic remote-sensing intelligence system that converts
          natural-language questions into specialized image analysis.
        </p>

        {/* Single Hero CTA - Handwritten Note (Caveat) with Doodle Underline */}
        <Link
          href="/analyze"
          aria-label="Ask satellites what changed - Launch SatQuery AI Investigation"
          className="mb-6 flex items-center justify-center gap-2 font-handwritten text-zinc-200 hover:text-white text-2xl sm:text-3xl -rotate-2 select-none cursor-pointer transition-colors duration-200 focus:outline-none focus-visible:ring-1 focus-visible:ring-white/40 rounded translate-y-[3px] group"
        >
          <Highlighter
            action="underline"
            color="#FFFFFF"
            strokeWidth={2.5}
            iterations={2}
            padding={3}
          >
            <span>ask it anything</span>
          </Highlighter>
          <span className="inline-block transition-transform duration-200 group-hover:translate-x-1">
            &rarr;
          </span>
        </Link>

        {/* Clean Metadata Line */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3 text-xs text-zinc-400 font-body">
          <span>Optical & SAR Ingest</span>
          <span className="text-zinc-600">&bull;</span>
          <span>Traceable Evidence</span>
          <span className="text-zinc-600">&bull;</span>
          <span>Multi-Model Routing</span>
        </div>
      </div>
    </section>
  );
}
