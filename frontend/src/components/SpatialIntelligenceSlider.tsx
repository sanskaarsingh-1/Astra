"use client";

import React, { useState, useEffect } from "react";
import {
  HelpCircle,
  BrainCircuit,
  Cpu,
  Layers,
  ShieldCheck,
  FileSearch,
} from "lucide-react";

export interface PipelineStep {
  id: number;
  stageNumber: string;
  name: string;
  subtitle: string;
  icon: React.ElementType;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 0,
    stageNumber: "01",
    name: "Query Ingest",
    subtitle: "Natural Language & Rasters",
    icon: HelpCircle,
  },
  {
    id: 1,
    stageNumber: "02",
    name: "Agentic Plan",
    subtitle: "Intent & DAG Routing",
    icon: BrainCircuit,
  },
  {
    id: 2,
    stageNumber: "03",
    name: "7 Specialists",
    subtitle: "Specialist CV Models",
    icon: Cpu,
  },
  {
    id: 3,
    stageNumber: "04",
    name: "Spatial Math",
    subtitle: "Deterministic Metrics",
    icon: Layers,
  },
  {
    id: 4,
    stageNumber: "05",
    name: "Evidence Audit",
    subtitle: "Physical Consistency",
    icon: ShieldCheck,
  },
  {
    id: 5,
    stageNumber: "06",
    name: "Tactical Report",
    subtitle: "Executive GIS Briefing",
    icon: FileSearch,
  },
];

interface SpatialIntelligenceSliderProps {
  autoPlayInterval?: number; // 2000ms = 2 seconds
  className?: string;
}

export default function SpatialIntelligenceSlider({
  autoPlayInterval = 2000,
  className = "",
}: SpatialIntelligenceSliderProps) {
  const [activeStep, setActiveStep] = useState<number>(0);

  // Advance by exactly 1 step sequentially every 2 seconds (1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 1)
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % PIPELINE_STEPS.length);
    }, autoPlayInterval);

    return () => clearInterval(timer);
  }, [autoPlayInterval, activeStep]);

  return (
    <div
      className={`w-full max-w-5xl mx-auto flex flex-col items-center select-none ${className}`}
    >
      {/* Title */}
      <p className="text-center text-xs font-mono font-medium text-zinc-400 uppercase tracking-widest mb-10">
        From raw satellite pixels to verified spatial intelligence.
      </p>

      {/* The 6 Small Cards with Glowing Subtle Blur Switching Animation */}
      <div className="w-full relative">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-3.5 relative z-10">
          {PIPELINE_STEPS.map((step, idx) => {
            const isActive = idx === activeStep;
            const Icon = step.icon;

            return (
              <button
                key={step.id}
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`relative overflow-hidden rounded-2xl border p-4 sm:p-5 text-left transition-all duration-300 ease-out cursor-pointer group flex flex-col justify-between min-h-[135px] sm:min-h-[145px] ${
                  isActive
                    ? "bg-zinc-900/95 border-white/30 shadow-xl scale-[1.02] opacity-100 z-20"
                    : "bg-zinc-950/40 border-white/10 text-zinc-400 opacity-60 hover:opacity-90 z-10 backdrop-blur-md"
                }`}
              >
                {/* Hairline top sheen */}
                {isActive && (
                  <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent pointer-events-none z-30" />
                )}

                {/* Sweeping Specular Shine when in preview */}
                {isActive && (
                  <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl z-20">
                    <div
                      className="absolute inset-y-0 w-3/4 bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none"
                      style={{ animation: "card-shine 2s cubic-bezier(0.4, 0, 0.2, 1) infinite" }}
                    />
                  </div>
                )}

                {/* Top Row: Stage Number & Icon */}
                <div className="flex items-center justify-between mb-3 w-full relative z-10">
                  <span
                    className={`text-[11px] font-mono font-medium tracking-wider transition-colors duration-300 ${
                      isActive ? "text-white" : "text-zinc-500"
                    }`}
                  >
                    {step.stageNumber}
                  </span>
                  <div
                    className={`size-8 rounded-xl flex items-center justify-center border transition-all duration-300 ${
                      isActive
                        ? "bg-white/10 border-white/25 text-white"
                        : "bg-white/5 border-white/10 text-zinc-500"
                    }`}
                  >
                    <Icon className="size-4" />
                  </div>
                </div>

                {/* Card Title & Subtitle */}
                <div className="w-full relative z-10">
                  <h4
                    className={`text-xs sm:text-[13px] font-mono font-bold tracking-tight transition-colors duration-300 leading-snug ${
                      isActive ? "text-white" : "text-zinc-400"
                    }`}
                  >
                    {step.name}
                  </h4>
                  <p
                    className={`text-[10px] font-mono mt-1 leading-tight truncate transition-colors duration-300 ${
                      isActive ? "text-zinc-300" : "text-zinc-600"
                    }`}
                  >
                    {step.subtitle}
                  </p>
                </div>

                {/* Short Centered Pill Progress Indicator */}
                {isActive && (
                  <div className="absolute inset-x-0 bottom-2 flex justify-center z-30 pointer-events-none">
                    <div className="w-9 h-[2px] rounded-full bg-white/20 overflow-hidden">
                      <div
                        key={`progress-${activeStep}`}
                        className="h-full bg-white rounded-full"
                        style={{
                          animation: `progress-linear ${autoPlayInterval}ms linear forwards`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
