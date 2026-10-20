"use client";

import React, { useEffect, useRef, useState, type ReactNode } from "react";
import {
  AnimatePresence,
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  useVelocity,
  useReducedMotion,
} from "framer-motion";
import { cn } from "@/lib/utils";

const CARD_W = 248;
const GAP = 10;
const GUTTER = 8;
const EASE_OUT = [0.23, 1, 0.32, 1] as const;
// Loose enough that the card visibly trails the cursor, tight enough that it never feels like it is swimming.
const FOLLOW = { stiffness: 260, damping: 26, mass: 0.6 } as const;
// A card dragged sideways leans into the motion; 7deg at a brisk flick is noticeable without looking like it will fall off.
const MAX_TILT = 7;
const TILT_AT_SPEED = 1400;
// Holds the card up after a touch press ends, so it can actually be read.
const TOUCH_LINGER = 1400;

type Mode = "cursor" | "anchored";

export interface HoverPreviewLinkProps {
  href: string;
  title: string;
  domain: string;
  image: ReactNode;
  children: ReactNode;
  simulate?: { x: number; below?: boolean } | null;
  className?: string;
}

export function HoverPreviewLink({
  href,
  title,
  domain,
  image,
  children,
  simulate,
  className,
}: HoverPreviewLinkProps) {
  const reduceMotion = useReducedMotion();
  const wrap = useRef<HTMLSpanElement>(null);
  const [open, setOpen] = useState<Mode | null>(null);
  const [below, setBelow] = useState(false);
  const linger = useRef<ReturnType<typeof setTimeout>>(undefined);

  // x is the card's left edge relative to the link, raw from the pointer;
  // the spring gives it lag and its velocity drives the lean.
  const targetX = useMotionValue(0);
  const x = useSpring(targetX, FOLLOW);
  const speed = useVelocity(x);
  const tilt = useSpring(
    useTransform(speed, [-TILT_AT_SPEED, TILT_AT_SPEED], [MAX_TILT, -MAX_TILT], {
      clamp: true,
    }),
    { stiffness: 400, damping: 30 }
  );

  useEffect(() => () => clearTimeout(linger.current), []);

  // Screen pixels per layout pixel: not 1 when an ancestor is scaled
  const scaleOf = (el: HTMLElement, r: DOMRect) =>
    el.offsetWidth ? r.width / el.offsetWidth : 1;

  // Keeps the card inside the viewport so it can't widen a page
  const clampLeft = (left: number) => {
    const el = wrap.current;
    if (!el) return left;
    const r = el.getBoundingClientRect();
    const s = scaleOf(el, r);
    const vw = document.documentElement.clientWidth;
    const min = (GUTTER - r.left) / s;
    const max = (vw - GUTTER - r.left) / s - CARD_W;
    return Math.round(Math.min(Math.max(left, min), Math.max(min, max)));
  };

  const place = (mode: Mode, clientX?: number) => {
    const el = wrap.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const centre =
      mode === "cursor" && clientX !== undefined
        ? (clientX - r.left) / scaleOf(el, r)
        : el.offsetWidth / 2;
    return clampLeft(centre - CARD_W / 2);
  };

  const show = (mode: Mode, clientX?: number) => {
    const el = wrap.current;
    const left = place(mode, clientX);
    if (!el || left === undefined) return;
    clearTimeout(linger.current);
    // Flip below when there isn't room above in the viewport
    setBelow(el.getBoundingClientRect().top < 200);
    if (!open) {
      targetX.jump(left);
      x.jump(left);
      tilt.jump(0);
    } else {
      targetX.set(left);
    }
    setOpen(mode);
  };

  const hide = () => {
    clearTimeout(linger.current);
    setOpen(null);
  };

  // Simulated pointer support
  const simX = simulate?.x;
  const simBelow = simulate?.below ?? false;
  const simOpen = useRef(false);
  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    if (simX === undefined) {
      if (simOpen.current) setOpen(null);
      simOpen.current = false;
      return;
    }
    const left = clampLeft(simX * el.offsetWidth - CARD_W / 2);
    if (!simOpen.current) {
      targetX.jump(left);
      x.jump(left);
      tilt.jump(0);
      setBelow(simBelow);
      setOpen("cursor");
      simOpen.current = true;
    } else {
      targetX.set(left);
    }
  }, [simX, simBelow]);

  return (
    <span ref={wrap} className="relative inline-block">
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        onPointerEnter={(e) => {
          if (e.pointerType !== "touch") show("cursor", e.clientX);
        }}
        onPointerMove={(e) => {
          if (e.pointerType === "touch" || !open) return;
          if (reduceMotion) return;
          targetX.set(place("cursor", e.clientX) ?? 0);
        }}
        onPointerLeave={(e) => {
          if (e.pointerType !== "touch") hide();
        }}
        onPointerDown={(e) => {
          if (e.pointerType === "touch") show("anchored");
        }}
        onPointerUp={(e) => {
          if (e.pointerType !== "touch") return;
          clearTimeout(linger.current);
          linger.current = setTimeout(hide, TOUCH_LINGER);
        }}
        onPointerCancel={hide}
        onFocus={(e) => {
          if (e.currentTarget.matches(":focus-visible")) show("anchored");
        }}
        onBlur={hide}
        onKeyDown={(e) => {
          if (e.key === "Escape") hide();
        }}
        className={cn(
          "inline-block font-medium text-foreground underline decoration-border decoration-1 underline-offset-4 outline-none transition-[text-decoration-color] duration-150 ease-out hover:decoration-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white",
          className
        )}
      >
        {children}
      </a>

      <AnimatePresence>
        {open ? (
          <motion.span
            aria-hidden
            className={cn(
              "pointer-events-none absolute left-0 z-50 block",
              below ? "top-full" : "bottom-full"
            )}
            style={{
              x,
              rotate: reduceMotion ? 0 : tilt,
              width: CARD_W,
              paddingTop: below ? GAP : 0,
              paddingBottom: below ? 0 : GAP,
              transformOrigin: below ? "50% 0%" : "50% 100%",
            }}
          >
            <motion.span
              className="block overflow-hidden rounded-xl bg-zinc-900 border border-white/15 p-1 shadow-2xl backdrop-blur-xl"
              style={{ transformOrigin: below ? "50% 0%" : "50% 100%" }}
              initial={
                reduceMotion
                  ? { opacity: 0 }
                  : { opacity: 0, scale: 0.88, y: below ? -6 : 6, filter: "blur(4px)" }
              }
              animate={{
                opacity: 1,
                scale: 1,
                y: 0,
                filter: "blur(0px)",
                transition: { duration: 0.18, ease: EASE_OUT },
              }}
              exit={{
                opacity: 0,
                scale: reduceMotion ? 1 : 0.96,
                filter: reduceMotion ? "blur(0px)" : "blur(2px)",
                transition: { duration: 0.12, ease: EASE_OUT },
              }}
            >
              {/* Thumbnail Container */}
              <div className="relative block w-full h-[122px] overflow-hidden rounded-lg bg-zinc-950 border border-white/10">
                {image}
              </div>
              <span className="block px-2.5 pt-2 pb-1.5 text-left">
                <span className="block truncate text-[13px] font-medium text-white font-display">
                  {title}
                </span>
                <span className="block truncate text-xs text-zinc-400 font-mono">{domain}</span>
              </span>
            </motion.span>
          </motion.span>
        ) : null}
      </AnimatePresence>
    </span>
  );
}

/**
 * High fidelity preview thumbnail for Satyajit's portfolio at satydev.com
 * using the official satydev.png capture.
 */
export function SatyDevThumb() {
  return (
    <div className="relative w-full h-full min-h-[122px] bg-zinc-950 select-none overflow-hidden group">
      <img
        src="/images/satydev.png"
        onError={(e) => {
          const target = e.currentTarget as HTMLImageElement;
          if (!target.dataset.fallback) {
            target.dataset.fallback = "true";
            target.src = "/satydev.png";
          }
        }}
        alt="Satyajit — AI Product Engineer & Designer"
        className="w-full h-full object-cover object-top transition-transform duration-500 ease-out group-hover:scale-[1.03]"
        loading="eager"
      />
      {/* Subtle bottom vignette for text contrast and live pill */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent pointer-events-none" />

      {/* Floating status pill */}
      <div className="absolute bottom-2 left-2 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/80 backdrop-blur-md border border-white/15 text-[9.5px] font-mono text-zinc-300 shadow-md">
        <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span>satydev.com</span>
      </div>
    </div>
  );
}
