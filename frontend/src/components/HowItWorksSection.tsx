"use client";

import React, { useRef, useState, useEffect } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useSpring,
  useMotionValueEvent,
  MotionValue,
} from "framer-motion";
import { HelpCircle, BrainCircuit, FileSearch, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  {
    step: "01",
    title: "Input & Ingest",
    desc: "Accepts multi-temporal satellite imagery (optical & SAR) along with user-specified areas of interest and natural language inquiries.",
    icon: HelpCircle,
  },
  {
    step: "02",
    title: "Geospatial Preprocessing",
    desc: "Performs orthorectification, cloud masking, band normalization, and temporal pixel alignment across timestamps.",
    icon: Layers,
  },
  {
    step: "03",
    title: "Multi-Model Intelligence",
    desc: "Dispatches aligned imagery to specialist computer vision models and vision-language reasoning engines for detection and validation.",
    icon: BrainCircuit,
  },
  {
    step: "04",
    title: "Explainable Output",
    desc: "Compiles segmented masks, quantified delta measurements, confidence metrics, and an interactive auditable report.",
    icon: FileSearch,
  },
];

function HowItWorksCard({
  step,
  index,
  stepProgress,
  activeIndex,
  onCardClick,
}: {
  step: (typeof STEPS)[0];
  index: number;
  stepProgress: MotionValue<number>;
  activeIndex: number;
  onCardClick: () => void;
}) {
  // Distance from center focus (0 = dead center, 1 = 1 card away, etc.)
  const dist = useTransform(stepProgress, (currentPos) => {
    return Math.abs(index - currentPos);
  });

  const scale = useTransform(dist, (d) => Math.max(0.88, 1 - d * 0.1));
  const opacity = useTransform(dist, (d) => (d > 2.0 ? 0.05 : Math.max(0.38, 1 - d * 0.45)));

  const isActive = index === activeIndex;

  return (
    <motion.div
      onClick={onCardClick}
      style={{
        scale,
        opacity,
        zIndex: isActive ? 20 : 10,
      }}
      className={cn(
        "relative rounded-3xl border p-7 sm:p-9 backdrop-blur-2xl transition-[border-color,box-shadow,background-color] duration-300 flex flex-col justify-between shadow-2xl shrink-0 cursor-pointer will-change-transform",
        "w-[300px] sm:w-[380px] lg:w-[440px] h-[320px] sm:h-[350px]",
        isActive
          ? "bg-zinc-950/95 border-white/35 shadow-[0_0_50px_-5px_rgba(255,255,255,0.16)] ring-1 ring-white/20"
          : "bg-zinc-950/70 border-white/10 hover:border-white/25 hover:bg-zinc-950/80"
      )}
    >
      {/* Specular hairline top accent for iPhone-like glass sheen */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent rounded-t-3xl pointer-events-none" />

      <div>
        {/* Step number badge & icon - JetBrains Mono 500 */}
        <div className="flex items-center justify-between mb-5">
          <span
            className={cn(
              "text-xs sm:text-sm font-mono font-semibold tracking-wider transition-colors duration-300",
              isActive ? "text-white" : "text-zinc-400"
            )}
          >
            STAGE {step.step}
          </span>
          <div
            className={cn(
              "size-10 sm:size-11 rounded-2xl flex items-center justify-center border transition-all duration-300",
              isActive
                ? "bg-white/10 border-white/25 text-white"
                : "bg-white/5 border-white/10 text-zinc-400"
            )}
          >
            <step.icon className="size-5" />
          </div>
        </div>

        {/* Title - Space Grotesk 600 */}
        <h3
          className={cn(
            "font-display font-semibold text-lg sm:text-xl lg:text-2xl mb-3 tracking-tight transition-colors duration-300",
            isActive ? "text-white" : "text-zinc-300"
          )}
        >
          {step.title}
        </h3>

        {/* Description - Inter 400 */}
        <p className="font-body text-xs sm:text-sm text-zinc-300 leading-relaxed font-normal">
          {step.desc}
        </p>
      </div>

      <div className="mt-5 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-zinc-500">
        <span className={cn("text-xs font-mono transition-colors", isActive ? "text-zinc-300" : "text-zinc-500")}>
          Step {step.step}
        </span>
        <span className="text-[11px] text-zinc-500 font-mono">
          0{index + 1}/04
        </span>
      </div>
    </motion.div>
  );
}

// Center targets for direct click navigation
const STEP_TARGET_PROGRESS = [0.05, 0.38, 0.70, 0.95];

export default function HowItWorksSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeCard, setActiveCard] = useState(0);

  // Native scroll progress through the container
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Spring-smoothed scroll progress for organic momentum
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 140,
    damping: 26,
    mass: 0.5,
    restDelta: 0.0005,
  });

  // Dedicated step progress mapping across 260vh
  const stepProgress = useTransform(
    smoothProgress,
    [0, 0.12, 0.34, 0.46, 0.66, 0.78, 0.95, 1.0],
    [0, 0.00, 1.00, 1.00, 2.00, 2.00, 3.00, 3.0]
  );

  useMotionValueEvent(stepProgress, "change", (latest) => {
    const current = Math.min(
      STEPS.length - 1,
      Math.max(0, Math.round(latest))
    );
    setActiveCard(current);
  });

  // Dynamic responsive padding so Card 00 starts dead center
  const [metrics, setMetrics] = useState({
    cardWidth: 440,
    gap: 36,
    paddingX: 500,
    totalDistance: 1500,
  });

  useEffect(() => {
    const updateMetrics = () => {
      const w = window.innerWidth;
      const cardWidth = w >= 1024 ? 440 : w >= 640 ? 380 : Math.min(300, w * 0.78);
      const gap = w >= 1024 ? 36 : 28;
      const paddingX = Math.max(20, (w - cardWidth) / 2);
      const totalDistance = (STEPS.length - 1) * (cardWidth + gap);
      setMetrics({ cardWidth, gap, paddingX, totalDistance });
    };
    updateMetrics();
    window.addEventListener("resize", updateMetrics);
    return () => window.removeEventListener("resize", updateMetrics);
  }, []);

  const x = useTransform(stepProgress, (sp) => -sp * (metrics.cardWidth + metrics.gap));

  const scrollToStep = (targetIdx: number) => {
    if (!containerRef.current) return;
    const scrollTop = window.scrollY + containerRef.current.getBoundingClientRect().top;
    const scrollRange = containerRef.current.offsetHeight - window.innerHeight;
    const targetProgress = STEP_TARGET_PROGRESS[targetIdx] ?? (targetIdx / (STEPS.length - 1));
    const target = scrollTop + targetProgress * scrollRange;
    window.scrollTo({ top: target, behavior: "smooth" });
  };

  // Sticky container remains visible, cleanly dissolves between 0.96 and 1.0 before unpinning
  const stickyOpacity = useTransform(scrollYProgress, [0, 0.02, 0.96, 1.0], [1, 1, 1, 0]);

  return (
    <section
      ref={containerRef}
      id="how-it-works"
      aria-label="How Astra Works"
      className="relative z-10 w-full h-[260vh] bg-transparent"
    >
      {/* Sticky Viewport Container - with pb-28 sm:pb-32 to clear floating dock */}
      <motion.div
        style={{ opacity: stickyOpacity }}
        className="sticky top-0 h-screen w-full flex flex-col justify-between pt-6 sm:pt-8 pb-28 sm:pb-32 overflow-hidden select-none"
      >
        {/* Top Header - space-grotesk heading & mono badge */}
        <div className="max-w-6xl mx-auto w-full px-6 z-10 shrink-0">
          <div className="flex justify-center mb-2 sm:mb-3">
            <span className="text-zinc-400 text-xs font-mono uppercase tracking-wider">
              System Workflow
            </span>
          </div>

          <h2 className="font-display font-semibold text-2xl sm:text-4xl lg:text-5xl text-white text-center tracking-tight max-w-3xl mx-auto mb-2">
            How Astra Coordinates Analysis
          </h2>

          <p className="font-body text-xs sm:text-sm lg:text-base text-zinc-300 font-normal text-center max-w-2xl mx-auto leading-relaxed">
            From raw multi-spectral data to decision-ready reports: a modular,
            verifiable pipeline designed for real-world reliability.
          </p>
        </div>

        {/* 3-Card Center-Focus Track Area */}
        <div className="relative w-full overflow-hidden my-auto py-2">
          <motion.div
            style={{
              x,
              paddingLeft: `${metrics.paddingX}px`,
              paddingRight: `${metrics.paddingX}px`,
            }}
            className="flex items-center gap-7 lg:gap-9 w-max relative z-10 will-change-transform"
          >
            {STEPS.map((step, idx) => (
              <HowItWorksCard
                key={step.step}
                step={step}
                index={idx}
                stepProgress={stepProgress}
                activeIndex={activeCard}
                onCardClick={() => scrollToStep(idx)}
              />
            ))}
          </motion.div>
        </div>

        {/* Bottom Progress Bar & Pipeline Note (elevated safely above dock) */}
        <div className="max-w-5xl mx-auto w-full px-6 z-10 shrink-0">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
              <span className="text-zinc-500">Stage</span>
              <span className="text-white font-medium">0{activeCard + 1} / 04</span>
              <span className="text-zinc-400 hidden sm:inline">
                — {STEPS[activeCard].title}
              </span>
            </div>

            {/* Scroll Progress Indicator & Step dots */}
            <div className="flex items-center gap-4 shrink-0">
              <div className="flex items-center gap-1.5">
                {STEPS.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => scrollToStep(i)}
                    aria-label={`Go to stage 0${i + 1}`}
                    className={cn(
                      "size-2 rounded-full transition-all duration-300 cursor-pointer",
                      i === activeCard
                        ? "bg-white scale-125 shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                        : "bg-zinc-600 hover:bg-zinc-400"
                    )}
                  />
                ))}
              </div>

              <div className="w-24 sm:w-32 h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-white rounded-full"
                  style={{
                    scaleX: smoothProgress,
                    transformOrigin: "left",
                  }}
                />
              </div>

              <span className="text-[11px] font-mono text-zinc-400 tabular-nums">
                {Math.round(((activeCard + 1) / STEPS.length) * 100)}%
              </span>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
