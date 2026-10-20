"use client";

import * as React from "react";
import { AnimatedBackground } from "@/components/ui/AnimatedBackground";

// Product-First Page Sections
import HeroSection from "@/components/HeroSection";
import HowItWorksSection from "@/components/HowItWorksSection";
import CapabilitiesSection from "@/components/CapabilitiesSection";
import EarthViewSection from "@/components/EarthViewSection";
import Footer from "@/components/Footer";

export default function Home() {
  const videoRef = React.useRef<HTMLVideoElement | null>(null);

  // Robust auto-resume handler: keeps background video smooth and recovers from tab switches / sleep
  React.useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const playSafe = () => {
      if (video.paused) {
        const p = video.play();
        if (p !== undefined) {
          p.catch(() => {});
        }
      }
    };

    playSafe();

    const handleVisibility = () => {
      if (!document.hidden) {
        playSafe();
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("focus", handleVisibility);
    video.addEventListener("canplay", playSafe);
    video.addEventListener("loadeddata", playSafe);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("focus", handleVisibility);
      video.removeEventListener("canplay", playSafe);
      video.removeEventListener("loadeddata", playSafe);
    };
  }, []);

  return (
    <div className="min-h-screen w-full bg-transparent text-foreground flex flex-col selection:bg-cyan-500/30 selection:text-cyan-50 relative">
      {/* Earth From Space Video Background (Homepage Dedicated) */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-black [transform:translateZ(0)]">
        <video
          ref={videoRef}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          poster="/earth-poster.jpg"
          className="w-full h-full object-cover pointer-events-none opacity-90 [transform:translateZ(0)] will-change-transform"
        >
          <source src="/earth-from-space.3840x2160.mp4" type="video/mp4" />
          <source src="/videos/earth-from-space.3840x2160.mp4" type="video/mp4" />
        </video>
        {/* Deep Black Tint matching Section 2 across the entire homepage */}
        <div className="absolute inset-0 bg-zinc-950/75 pointer-events-none" />
      </div>

      {/* Ambient background particles & glows */}
      <AnimatedBackground />

      <main className="flex-1 w-full relative z-10">
        {/* 1. Hero / Home */}
        <HeroSection />

        {/* 2. How It Works */}
        <HowItWorksSection />

        {/* 3. Capabilities */}
        <CapabilitiesSection />

        {/* 4. Earth View (Real-World EO Context) */}
        <EarthViewSection />
      </main>

      {/* 10. Footer */}
      <Footer />
    </div>
  );
}
