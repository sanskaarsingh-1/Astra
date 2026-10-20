"use client";

import React, { useRef, useState } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useMotionValueEvent,
  MotionValue,
} from "framer-motion";
import {
  Globe,
  Layers,
  Search,
  Map,
  ShieldCheck,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const CAPABILITIES = [
  {
    icon: Activity,
    title: "Multi-Temporal Change Detection",
    desc: "Tracks surface variations between baseline and target timestamps, segmenting changes in infrastructure, water bodies, and vegetation.",
    tag: "Temporal Analytics",
  },
  {
    icon: Search,
    title: "Natural Language Spatial Queries",
    desc: "Enables operators to query scenes using plain English (e.g., 'Identify flooded access routes near sector B') powered by Vision-Language Models.",
    tag: "Multimodal VLM",
  },
  {
    icon: Layers,
    title: "Optical & SAR Fusion",
    desc: "Fuses high-resolution optical imagery with Synthetic Aperture Radar data, overcoming cloud obstruction and nocturnal observation constraints.",
    tag: "Multi-Sensor",
  },
  {
    icon: Map,
    title: "Automated Segmentation Masks",
    desc: "Generates precise polygon and raster masks for detected anomalies, allowing seamless export into standard GIS workflows.",
    tag: "Geospatial GIS",
  },
  {
    icon: Globe,
    title: "Deterministic Area Metrics",
    desc: "Deterministic area and distance calculation outside the LLM from generated masks and calibrated pixel GSD dimensions.",
    tag: "Spatial Math",
  },
  {
    icon: ShieldCheck,
    title: "Auditable Decision Reports",
    desc: "Produces traceable, evidence-backed reports with model confidence ratings, sensor metadata, and verifiable observation logs.",
    tag: "Explainable AI",
  },
];

// Timings for each card's entrance and landing across 600vh of scroll:
// Card 0: Base card, initially on top, readable from 0.00 -> 0.12
// Card 1: enters 0.12 -> 0.18, hold 0.18 -> 0.27
// Card 2: enters 0.27 -> 0.33, hold 0.33 -> 0.42
// Card 3: enters 0.42 -> 0.48, hold 0.48 -> 0.57
// Card 4: enters 0.57 -> 0.63, hold 0.63 -> 0.72
// Card 5 ("Auditable Decision Reports" - 6th card): enters 0.72 -> 0.78, GENEROUS HOLD 0.78 -> 0.96 while sticky!
const CARD_TIMINGS = [
  { start: 0.0, end: 0.0 },
  { start: 0.12, end: 0.18 },
  { start: 0.27, end: 0.33 },
  { start: 0.42, end: 0.48 },
  { start: 0.57, end: 0.63 },
  { start: 0.72, end: 0.78 },
];

function getBlurForOffset(offset: number) {
  if (offset <= 0) return 0;
  if (offset === 1) return 2.0;
  if (offset === 2) return 4.0;
  if (offset === 3) return 6.0;
  return 8.0;
}

function sanitizeKeyframes(data: {
  inputs: number[];
  y: number[];
  scale: number[];
  opacity: number[];
  blur: number[];
}) {
  const cleanInputs: number[] = [];
  const cleanY: number[] = [];
  const cleanScale: number[] = [];
  const cleanOpacity: number[] = [];
  const cleanBlur: number[] = [];

  for (let i = 0; i < data.inputs.length; i++) {
    const val = Number(data.inputs[i].toFixed(4));
    if (i === 0) {
      cleanInputs.push(val);
      cleanY.push(data.y[i]);
      cleanScale.push(data.scale[i]);
      cleanOpacity.push(data.opacity[i]);
      cleanBlur.push(data.blur[i]);
    } else {
      const prev = cleanInputs[cleanInputs.length - 1];
      if (val > prev + 0.0001) {
        cleanInputs.push(val);
        cleanY.push(data.y[i]);
        cleanScale.push(data.scale[i]);
        cleanOpacity.push(data.opacity[i]);
        cleanBlur.push(data.blur[i]);
      }
    }
  }
  return {
    inputs: cleanInputs,
    y: cleanY,
    scale: cleanScale,
    opacity: cleanOpacity,
    blur: cleanBlur,
  };
}

/**
 * Computes strictly monotonic keyframe arrays for each card.
 * Entering cards smoothly fade up from a gentle y=70px offset, never hanging below the container.
 */
function getCardKeyframes(index: number) {
  if (index === 0) {
    const inputs: number[] = [0, CARD_TIMINGS[1].start];
    const y: number[] = [0, 0];
    const scale: number[] = [1, 1];
    const opacity: number[] = [1, 1];
    const blur: number[] = [0, 0];

    for (let k = 1; k <= 5; k++) {
      const kStart = CARD_TIMINGS[k].start;
      const kEnd = CARD_TIMINGS[k].end;
      const prevOffset = k - 1;
      const nextOffset = k;

      inputs.push(kStart);
      y.push(-12 * prevOffset);
      scale.push(1 - 0.035 * prevOffset);
      opacity.push(Math.max(0.18, 1 - 0.22 * prevOffset));
      blur.push(getBlurForOffset(prevOffset));

      inputs.push(kEnd);
      y.push(-12 * nextOffset);
      scale.push(1 - 0.035 * nextOffset);
      opacity.push(Math.max(0.18, 1 - 0.22 * nextOffset));
      blur.push(getBlurForOffset(nextOffset));
    }

    inputs.push(1.0);
    y.push(-12 * 5);
    scale.push(1 - 0.035 * 5);
    opacity.push(Math.max(0.18, 1 - 0.22 * 5));
    blur.push(getBlurForOffset(5));

    return sanitizeKeyframes({ inputs, y, scale, opacity, blur });
  }

  const enterStart = CARD_TIMINGS[index].start;
  const enterEnd = CARD_TIMINGS[index].end;

  // Gentle 70px entrance offset (stays completely inside container bounds)
  const inputs: number[] = [0];
  const y: number[] = [70];
  const scale: number[] = [0.96];
  const opacity: number[] = [0];
  const blur: number[] = [0];

  if (enterStart > 0.02) {
    inputs.push(enterStart - 0.02);
    y.push(70);
    scale.push(0.96);
    opacity.push(0);
    blur.push(0);
  }

  // Entrance start: 0% opacity, 70px down
  inputs.push(enterStart);
  y.push(70);
  scale.push(0.96);
  opacity.push(0);
  blur.push(0);

  // Entrance complete: landed on top of stack, 100% sharp and visible!
  inputs.push(enterEnd);
  y.push(0);
  scale.push(1);
  opacity.push(1);
  blur.push(0);

  // Subsequent cards landing on top of this one (only for k > index)
  for (let k = index + 1; k <= 5; k++) {
    const kStart = CARD_TIMINGS[k].start;
    const kEnd = CARD_TIMINGS[k].end;
    const offset = k - index;

    inputs.push(kStart);
    y.push(-12 * (offset - 1));
    scale.push(1 - 0.035 * (offset - 1));
    opacity.push(Math.max(0.18, 1 - 0.22 * (offset - 1)));
    blur.push(getBlurForOffset(offset - 1));

    inputs.push(kEnd);
    y.push(-12 * offset);
    scale.push(1 - 0.035 * offset);
    opacity.push(Math.max(0.22, 1 - 0.22 * offset));
    blur.push(getBlurForOffset(offset));
  }

  // Hold at final offset until end of section
  const finalOffset = 5 - index;
  inputs.push(1.0);
  y.push(-12 * finalOffset);
  scale.push(1 - 0.035 * finalOffset);
  opacity.push(Math.max(0.22, 1 - 0.22 * finalOffset));
  blur.push(getBlurForOffset(finalOffset));

  return sanitizeKeyframes({ inputs, y, scale, opacity, blur });
}

function CapabilityCard({
  card,
  index,
  scrollYProgress,
  isActive,
}: {
  card: (typeof CAPABILITIES)[0];
  index: number;
  scrollYProgress: MotionValue<number>;
  isActive: boolean;
}) {
  const { inputs, y: yVals, scale: scaleVals, opacity: opacityVals, blur: blurVals } = React.useMemo(
    () => getCardKeyframes(index),
    [index]
  );

  const y = useTransform(scrollYProgress, inputs, yVals);
  const scale = useTransform(scrollYProgress, inputs, scaleVals);
  const opacity = useTransform(scrollYProgress, inputs, opacityVals);
  const blurPx = useTransform(scrollYProgress, inputs, blurVals);
  const filter = useTransform(blurPx, (b) => (b <= 0.1 ? "none" : `blur(${b.toFixed(1)}px)`));

  return (
    <motion.div
      style={{
        y,
        scale,
        opacity,
        filter,
        zIndex: 10 + index * 5,
        pointerEvents: isActive ? "auto" : "none",
      }}
      className={cn(
        "absolute inset-0 w-full h-full rounded-2xl border border-white/15 bg-zinc-950/95 p-6 sm:p-8 backdrop-blur-xl shadow-2xl flex flex-col justify-between transition-colors duration-200 select-none",
        "will-change-[transform,opacity,filter] [transform:translateZ(0)] [backface-visibility:hidden]",
        "hover:border-white/25"
      )}
    >
      <div>
        {/* Top Header: Icon + Step number + Category tag */}
        <div className="flex items-center justify-between mb-4 sm:mb-5">
          <div className="flex items-center gap-3">
            <div className="size-10 sm:size-11 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
              <card.icon className="size-5 text-white" />
            </div>
            <span className="text-xs sm:text-sm font-mono text-zinc-400 font-semibold tracking-wider">
              0{index + 1} / 06
            </span>
          </div>
          <span className="text-xs text-zinc-400 font-mono">
            {card.tag}
          </span>
        </div>

        {/* Title & Description */}
        <h3 className="font-display font-medium text-lg sm:text-2xl text-white mb-2 tracking-tight">
          {card.title}
        </h3>
        <p className="font-body text-xs sm:text-sm text-zinc-300 font-normal leading-relaxed">
          {card.desc}
        </p>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono text-zinc-500">
        <span className="text-zinc-400 text-xs">Capability</span>
        <span className="text-zinc-500 text-[11px]">
          0{index + 1} of 06
        </span>
      </div>
    </motion.div>
  );
}

// Center targets for clicking on capability indicator dots
const CARD_TARGET_PROGRESS = [0.06, 0.22, 0.37, 0.52, 0.67, 0.85];

export default function CapabilitiesSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeCard, setActiveCard] = useState(0);

  // Scroll linked animation with Framer Motion over a comfortable responsive distance
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Smooth fade-out at the very end of the section (0.97 to 1.0) after 6th card is fully read
  const stickyOpacity = useTransform(scrollYProgress, [0, 0.02, 0.97, 1.0], [1, 1, 1, 0]);

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    let current = 0;
    if (latest >= 0.72) {
      current = 5;
    } else if (latest >= 0.57) {
      current = 4;
    } else if (latest >= 0.42) {
      current = 3;
    } else if (latest >= 0.27) {
      current = 2;
    } else if (latest >= 0.12) {
      current = 1;
    } else {
      current = 0;
    }
    setActiveCard(current);
  });

  const scrollToCard = (targetIdx: number) => {
    if (!containerRef.current) return;
    const scrollTop = window.scrollY + containerRef.current.getBoundingClientRect().top;
    const scrollRange = containerRef.current.offsetHeight - window.innerHeight;
    const targetProgress = CARD_TARGET_PROGRESS[targetIdx] ?? 0;
    const target = scrollTop + targetProgress * scrollRange;
    window.scrollTo({ top: target, behavior: "smooth" });
  };

  return (
    <section
      ref={containerRef}
      id="capabilities"
      aria-label="Capabilities"
      className="relative z-20 w-full h-[600vh] bg-transparent"
    >
      {/* Sticky Viewport Container - with generous pb-28 to clear floating dock */}
      <motion.div
        style={{ opacity: stickyOpacity }}
        className="sticky top-0 h-screen w-full flex flex-col justify-between pt-6 sm:pt-8 pb-28 sm:pb-32 px-6 overflow-hidden"
      >
        {/* Soft entrance heading */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="max-w-4xl mx-auto w-full text-center shrink-0 z-10"
        >
          {/* Section Label */}
          <div className="flex justify-center mb-2 sm:mb-3">
            <span className="text-zinc-400 text-xs font-mono uppercase tracking-wider">
              Core Capabilities
            </span>
          </div>

          <h2 className="font-display font-semibold text-2xl sm:text-4xl lg:text-5xl text-white tracking-tight mb-2 sm:mb-3">
            Engineered for Planetary Scale Observation
          </h2>

          <p className="font-body text-xs sm:text-sm lg:text-base text-zinc-300 font-normal text-center max-w-2xl mx-auto leading-relaxed">
            Comprehensive tools built to assist emergency response teams, environmental
            analysts, and infrastructure agencies with verified geospatial intelligence.
          </p>
        </motion.div>

        {/* Stacked Cards Deck Area */}
        <div className="relative w-full max-w-xl sm:max-w-2xl lg:max-w-3xl h-[310px] sm:h-[340px] mx-auto my-auto flex items-center justify-center">
          {CAPABILITIES.map((cap, idx) => (
            <CapabilityCard
              key={cap.title}
              card={cap}
              index={idx}
              scrollYProgress={scrollYProgress}
              isActive={idx === activeCard}
            />
          ))}
        </div>

        {/* Bottom Sequence Bar & Feature Title Indicator (elevated above dock) */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 max-w-xl sm:max-w-2xl lg:max-w-3xl mx-auto w-full pt-2 shrink-0 z-10 text-xs font-mono text-zinc-400">
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Capability</span>
            <span className="text-white font-medium">0{activeCard + 1} / 06</span>
            <span className="text-zinc-400 hidden sm:inline">
              — {CAPABILITIES[activeCard].title}
            </span>
          </div>

          {/* Deck dots indicator */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-zinc-500 font-mono hidden md:inline">
              Scroll to stack
            </span>
            <div className="flex items-center gap-1.5">
              {CAPABILITIES.map((_, i) => (
                <button
                  key={i}
                  onClick={() => scrollToCard(i)}
                  aria-label={`Jump to capability 0${i + 1}`}
                  className={cn(
                    "size-2 rounded-full transition-all duration-300 cursor-pointer",
                    i === activeCard
                      ? "bg-white scale-125 shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                      : i < activeCard
                      ? "bg-zinc-400 hover:bg-zinc-300"
                      : "bg-zinc-700 hover:bg-zinc-500"
                  )}
                />
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
