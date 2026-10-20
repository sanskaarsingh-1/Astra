"use client";

import React, { useEffect } from "react";
import { motion, useSpring, useTransform, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

const DIGITS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
// The tens column starts blank, so 7% never reads as 07%.
const TENS = [" ", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
const EASE_OUT = "[transition-timing-function:cubic-bezier(0.23,1,0.32,1)]";

function Roll({ strip, index }: { strip: string[]; index: number }) {
  return (
    <span className="relative inline-block h-[1.5em] w-[1ch] overflow-hidden align-middle">
      <span
        className={cn(
          "absolute inset-x-0 top-0 flex flex-col transition-[translate] duration-300 motion-reduce:transition-none",
          EASE_OUT
        )}
        style={{ translate: `0 ${-index * 10}%` }}
      >
        {strip.map((d, i) => (
          <span key={i} className="h-[1.5em] flex items-center justify-center">
            {d}
          </span>
        ))}
      </span>
    </span>
  );
}

export interface TextProgressProps {
  /** 0 to 100 */
  value: number;
  label: string;
  doneLabel?: string;
  className?: string;
}

export function TextProgress({
  value,
  label,
  doneLabel = "Done",
  className,
}: TextProgressProps) {
  const reduceMotion = useReducedMotion();
  const clamped = Math.min(100, Math.max(0, value));
  const percent = Math.round(clamped);
  const done = percent >= 100;

  // Progress arrives in uneven jumps; a spring turns them into one steady
  // pour of ink and keeps its speed when the next jump lands mid-glide.
  const ink = useSpring(clamped, { stiffness: 90, damping: 20 });

  useEffect(() => {
    if (reduceMotion) {
      ink.jump(clamped);
    } else {
      ink.set(clamped);
    }
  }, [clamped, ink, reduceMotion]);

  const clip = useTransform(ink, (v) => `inset(0 ${Math.max(0, 100 - v).toFixed(2)}% 0 0)`);

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      aria-valuetext={done ? doneLabel : `${percent}%`}
      className={cn(
        "relative inline-flex items-center gap-2.5 text-sm sm:text-base leading-6 font-medium text-white select-none",
        className
      )}
    >
      <span aria-hidden className="grid">
        {/* Progressing label filling with ink */}
        <span
          className={cn(
            "relative col-start-1 row-start-1 whitespace-nowrap transition-[opacity,filter,translate]",
            EASE_OUT,
            done
              ? "-translate-y-1 opacity-0 blur-[4px] duration-200 motion-reduce:translate-y-0"
              : "opacity-100 duration-300"
          )}
        >
          <span className="text-white/20">{label}</span>
          {/* The same words, stacked and clipped: ink fills the letters themselves rather than a bar beside them */}
          <motion.span
            className="absolute inset-0 text-white"
            style={{ clipPath: clip }}
          >
            {label}
          </motion.span>
        </span>

        {/* Done label with animated checkmark */}
        <span
          className={cn(
            "col-start-1 row-start-1 flex items-center gap-1.5 whitespace-nowrap text-emerald-400 transition-[opacity,filter,translate]",
            EASE_OUT,
            done
              ? "translate-y-0 opacity-100 filter-none delay-100 duration-300"
              : "pointer-events-none translate-y-1 opacity-0 blur-[4px] duration-150 motion-reduce:translate-y-0"
          )}
        >
          <svg viewBox="0 0 16 16" fill="none" className="size-4 shrink-0 text-emerald-400">
            <path
              d="m3.5 8.5 3 3 6-7"
              pathLength={1}
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={1}
              className={cn(
                "transition-[stroke-dashoffset] [transition-timing-function:cubic-bezier(0.65,0,0.35,1)] motion-reduce:transition-none",
                done
                  ? "[stroke-dashoffset:0] delay-150 duration-300"
                  : "[stroke-dashoffset:1] delay-150 duration-0"
              )}
            />
          </svg>
          <span className="text-white font-medium">{doneLabel}</span>
        </span>
      </span>

      {/* Odometer percentage digits */}
      <span
        aria-hidden
        className={cn(
          "flex items-center text-zinc-400 font-mono text-xs sm:text-sm tabular-nums transition-[opacity,filter]",
          EASE_OUT,
          done ? "opacity-0 blur-[4px] duration-200" : "opacity-100 duration-300"
        )}
      >
        <Roll strip={TENS} index={Math.floor((percent % 100) / 10)} />
        <Roll strip={DIGITS} index={percent % 10} />
        <span>%</span>
      </span>

      <span className="sr-only" aria-live="polite">
        {done ? doneLabel : `${percent}%`}
      </span>
    </div>
  );
}

export default TextProgress;
