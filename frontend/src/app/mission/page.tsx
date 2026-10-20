"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Satellite, ShieldCheck, Radio } from "lucide-react";
import { FlowButton } from "@/components/ui/flow-button";
import Footer from "@/components/Footer";
import SpatialIntelligenceSlider from "@/components/SpatialIntelligenceSlider";

// Helper for highlighting specific words
const Highlight = ({ children }: { children: React.ReactNode }) => (
  <span className="text-white font-medium underline underline-offset-4 decoration-white/30">
    {children}
  </span>
);

export default function MissionPage() {
  const videoRef = React.useRef<HTMLVideoElement | null>(null);

  React.useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let isMounted = true;
    const playSafe = () => {
      if (video && video.paused && isMounted) {
        video.play().catch(() => {});
      }
    };

    // Stagger playback using requestAnimationFrame to prevent main-thread stutter during page hydrate
    const rafId = requestAnimationFrame(() => {
      playSafe();
    });

    const handleVisibility = () => {
      if (!document.hidden) {
        playSafe();
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("focus", handleVisibility);
    video.addEventListener("canplay", playSafe);

    return () => {
      isMounted = false;
      cancelAnimationFrame(rafId);
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("focus", handleVisibility);
      video.removeEventListener("canplay", playSafe);
    };
  }, []);

  return (
    <div className="min-h-screen w-full bg-black text-foreground flex flex-col selection:bg-white selection:text-black relative overflow-hidden font-body">
      {/* Background Moon Video (Optimized 1080p Web Stream with Faststart & Hardware Acceleration) */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-black [transform:translateZ(0)]">
        <video
          ref={videoRef}
          autoPlay
          loop
          muted
          playsInline
          preload="metadata"
          poster="/moonmoon-poster.jpg"
          className="w-full h-full object-cover pointer-events-none opacity-90 [transform:translateZ(0)] [backface-visibility:hidden] will-change-transform"
        >
          <source src="/moonmoon.mp4" type="video/mp4" />
          <source src="/videos/moonmoon.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/40 pointer-events-none" />
      </div>

      {/* Navigation */}
      <header className="fixed top-0 w-full z-50 p-6 bg-black/40 backdrop-blur-md border-b border-white/10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="size-9 rounded-xl bg-white/5 border border-white/10 text-zinc-300 hover:text-white flex items-center justify-center transition-colors"
            >
              <ArrowLeft className="size-4" />
            </Link>
            <div>
              <span className="font-display font-bold text-white tracking-tight text-base">
                Astra AI / SatQuery AI
              </span>
              <p className="text-[10px] font-mono text-zinc-400">SIH26167 • ISRO Space Applications Centre</p>
            </div>
          </div>

          <FlowButton
            href="/analyze"
            variant="primary"
            text="Launch SatQuery AI"
            className="px-4 py-2 rounded-xl text-xs font-body font-semibold backdrop-blur-md"
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full pt-32 pb-24 px-6 flex flex-col items-center justify-center relative z-10">
        <div className="max-w-5xl mx-auto w-full space-y-16">
          
          {/* Section Header */}
          <div className="text-left">
            <h1 className="font-display font-bold text-3xl sm:text-4xl md:text-[44px] lg:text-[54px] text-white tracking-tight leading-[1.14] max-w-[760px] mb-6 sm:mb-8">
              Multimodal Vision-Language Assistant for Satellite Intelligence
            </h1>
            
            <div className="space-y-6 text-base sm:text-lg text-zinc-300 font-body font-normal leading-relaxed max-w-3xl">
              <p>
                Under the mandate of <strong>Smart India Hackathon 2026 (Problem Statement SIH26167)</strong>, Astra AI / SatQuery AI is engineered to bridge the gap between petabyte-scale raw satellite imagery and actionable tactical intelligence for the Indian Space Research Organisation (ISRO) and Space Applications Centre (SAC).
              </p>
              <p>
                Rather than deploying an unreliable black-box LLM, Astra AI establishes an <Highlight>Observable Agentic Architecture</Highlight>. The Gemini orchestrator parses natural language questions, classifies operational intent, and routes tasks to 7 specialist vision models while delegating all quantitative measurements to deterministic geospatial algorithms.
              </p>
            </div>
          </div>

          {/* 3 Pillars of Architecture */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="group relative bg-zinc-950/60 border border-white/10 rounded-2xl p-6 backdrop-blur-xl transition-all duration-300 hover:border-white/25 hover:bg-zinc-950/80">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-t-2xl pointer-events-none" />
              <div className="size-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 transition-all duration-300 group-hover:bg-white/10 group-hover:border-white/20">
                <Satellite className="size-5 text-white transition-colors" />
              </div>
              <h3 className="font-display font-medium text-base text-white mb-2">
                Multi-Sensor Ingest
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed font-body">
                Natively ingests ISRO Cartosat-2S Panchromatic (0.65m GSD), RISAT-1A / EOS-04 C-band SAR, and Sentinel-1/2 constellations with automatic CRS detection, affine transforms, and GSD resolution ratio enforcement.
              </p>
            </div>

            <div className="group relative bg-zinc-950/60 border border-white/10 rounded-2xl p-6 backdrop-blur-xl transition-all duration-300 hover:border-white/25 hover:bg-zinc-950/80">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-t-2xl pointer-events-none" />
              <div className="size-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 transition-all duration-300 group-hover:bg-white/10 group-hover:border-white/20">
                <ShieldCheck className="size-5 text-white transition-colors" />
              </div>
              <h3 className="font-display font-medium text-base text-white mb-2">
                Deterministic Accuracy
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed font-body">
                Zero hallucinated measurements. Surface area (m² and hectares), geodesic distances, NDVI vegetation indices, and SAR backscatter dB are strictly computed by deterministic mathematical tools carrying calculation_status: DETERMINISTIC.
              </p>
            </div>

            <div className="group relative bg-zinc-950/60 border border-white/10 rounded-2xl p-6 backdrop-blur-xl transition-all duration-300 hover:border-white/25 hover:bg-zinc-950/80">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-t-2xl pointer-events-none" />
              <div className="size-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 transition-all duration-300 group-hover:bg-white/10 group-hover:border-white/20">
                <Radio className="size-5 text-white transition-colors" />
              </div>
              <h3 className="font-display font-medium text-base text-white mb-2">
                Optical + SAR Fusion
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed font-body">
                Separates solar surface reflectance from microwave dielectric backscatter. Automatically detects physical contradictions (e.g. water vs asphalt, urban double-bounce) with structured conflict records.
              </p>
            </div>
          </div>

          {/* Visual Flow / Architecture Diagram with Automatic 5-Second Blooming Slider */}
          <div className="pt-8">
            <SpatialIntelligenceSlider />
          </div>
          
        </div>
      </main>
      <Footer />
    </div>
  );
}
