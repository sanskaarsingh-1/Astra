"use client";

import React from "react";
import Link from "next/link";
import { Satellite } from "lucide-react";

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer aria-label="Site Footer" className="relative z-30 pt-16 pb-28 px-4 md:px-8 bg-neutral-950 text-neutral-300 font-body">
      <div className="container max-w-7xl mx-auto">
        <div className="flex flex-col lg:flex-row justify-between gap-10">
          {/* Brand & Attribution */}
          <div className="mb-8 lg:mb-0 max-w-sm">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="size-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:border-white/30 transition-colors">
                <Satellite className="size-4 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold font-display text-white tracking-tight">
                  Astra AI
                </h2>
                <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/5 text-zinc-400 border border-white/10">
                  SIH 2026
                </span>
              </div>
            </Link>

            <div className="mt-4">
              <Link
                href="https://x.com/compose/tweet?text=Exploring%20Earth%20from%20space%20with%20%23AstraAI%20%F0%9F%9B%B0%EF%B8%8F%20Autonomous%20Satellite%20Intelligence"
                target="_blank"
                rel="noopener noreferrer"
              >
                <button
                  type="button"
                  className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-xs font-medium text-zinc-200 transition-all active:scale-95 shadow-sm"
                >
                  <span>Share Your Thoughts On</span>
                  {/* Twitter / X icon */}
                  <svg className="size-3.5 fill-current text-zinc-300" viewBox="0 0 24 24">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </button>
              </Link>
            </div>

            <p className="text-xs text-zinc-500 mt-5">
              © {currentYear} Astra AI. All rights reserved.
            </p>
          </div>

          {/* 4 Navigation Columns */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 flex-1 max-w-3xl">
            {/* 1. Pages */}
            <div>
              <h3 className="font-semibold text-xs font-mono tracking-wider uppercase text-zinc-200 mb-4">
                Pages
              </h3>
              <ul className="space-y-2.5 text-xs">
                <li>
                  <Link href="/" className="text-zinc-400 hover:text-white transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <Link href="/earth" className="text-zinc-400 hover:text-white transition-colors">
                    Earth View (3D)
                  </Link>
                </li>
                <li>
                  <Link href="/analyze" className="text-zinc-400 hover:text-white transition-colors">
                    SatQuery AI
                  </Link>
                </li>
                <li>
                  <Link href="/mission" className="text-zinc-400 hover:text-white transition-colors">
                    SIH Mission
                  </Link>
                </li>
              </ul>
            </div>

            {/* 2. Buy Our Information */}
            <div>
              <h3 className="font-semibold text-xs font-mono tracking-wider uppercase text-zinc-200 mb-4">
                Buy Our Information
              </h3>
              <ul className="space-y-2.5 text-xs">
                <li>
                  <Link href="/datasets#sentinel-2" className="text-zinc-400 hover:text-white transition-colors">
                    Multi-Spectral Sentinel-2
                  </Link>
                </li>
                <li>
                  <Link href="/datasets#sar-radar" className="text-zinc-400 hover:text-white transition-colors">
                    SAR Radar Ingestion
                  </Link>
                </li>
                <li>
                  <Link href="/datasets#hazard-feeds" className="text-zinc-400 hover:text-white transition-colors">
                    Live Planetary Hazards
                  </Link>
                </li>
                <li>
                  <Link href="/datasets#geoai-api" className="text-zinc-400 hover:text-white transition-colors">
                    Tactical GeoAI API
                  </Link>
                </li>
                <li>
                  <Link href="/datasets#orbital-tasking" className="text-zinc-400 hover:text-white transition-colors">
                    Orbital Tasking Archive
                  </Link>
                </li>
              </ul>
            </div>

            {/* 3. Socials */}
            <div>
              <h3 className="font-semibold text-xs font-mono tracking-wider uppercase text-zinc-200 mb-4">
                Socials
              </h3>
              <ul className="space-y-2.5 text-xs">
                <li>
                  <Link
                    href="https://github.com/Tushar-Mali/orbilens-ai"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    GitHub
                  </Link>
                </li>
                <li>
                  <Link
                    href="https://linkedin.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    LinkedIn
                  </Link>
                </li>
                <li>
                  <Link
                    href="https://x.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    X (Twitter)
                  </Link>
                </li>
                <li>
                  <Link
                    href="https://youtube.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    YouTube
                  </Link>
                </li>
              </ul>
            </div>

            {/* 4. Legal */}
            <div>
              <h3 className="font-semibold text-xs font-mono tracking-wider uppercase text-zinc-200 mb-4">
                Legal
              </h3>
              <ul className="space-y-2.5 text-xs">
                <li>
                  <Link href="/privacy" className="text-zinc-400 hover:text-white transition-colors">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="text-zinc-400 hover:text-white transition-colors">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link href="/ethics" className="text-zinc-400 hover:text-white transition-colors">
                    Sovereign Data Ethics
                  </Link>
                </li>
                <li>
                  <Link href="/security" className="text-zinc-400 hover:text-white transition-colors">
                    Security Architecture
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="w-full flex mt-12 md:mt-16 items-center justify-center select-none overflow-hidden">
          <h1 className="inline-block text-center text-4xl sm:text-6xl md:text-8xl lg:text-[10rem] font-bold select-none tracking-tight animate-text-shine leading-none pb-2">
            Astra AI
          </h1>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
export { Footer };
