"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Loader2, ShieldCheck, RefreshCw, Compass } from "lucide-react";

interface PreFlightValidationBadgeProps {
  files: File[];
  validation: any;
  isValidating: boolean;
  onValidate: () => void;
}

export default function PreFlightValidationBadge({
  files,
  validation,
  isValidating,
  onValidate,
}: PreFlightValidationBadgeProps) {
  if (files.length === 0) return null;

  return (
    <div className="bg-black/30 border border-white/10 rounded-xl p-4 font-body backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Compass className="size-4 text-zinc-400" />
          <span className="text-xs font-medium text-white">
            Spatial Validation
          </span>
        </div>
        <button
          onClick={onValidate}
          disabled={isValidating}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-xs text-zinc-300 hover:text-white transition-colors disabled:opacity-50"
        >
          {isValidating ? (
            <>
              <Loader2 className="size-3 animate-spin text-zinc-300" />
              <span>Checking...</span>
            </>
          ) : (
            <>
              <RefreshCw className="size-3 text-zinc-400" />
              <span>Verify Geometry</span>
            </>
          )}
        </button>
      </div>

      {/* When validating */}
      {isValidating && !validation && (
        <div className="flex items-center gap-2 text-xs text-zinc-400 py-2">
          <Loader2 className="size-3.5 animate-spin text-zinc-400" />
          <span>Verifying GeoTIFF tags, CRS definition, and GSD resolution...</span>
        </div>
      )}

      {/* Validation Result */}
      {validation && (
        <div className="space-y-3">
          {/* Status Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {validation.is_valid ? (
                <div className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
                  <CheckCircle2 className="size-3.5" />
                  <span>Geometry and spatial tags verified</span>
                </div>
              ) : (
                <div className="inline-flex items-center gap-1.5 text-xs text-rose-400">
                  <XCircle className="size-3.5" />
                  <span>Validation Warning / Error</span>
                </div>
              )}
            </div>

            {validation.compatibility?.overlap_percentage != null && (
              <span className="text-xs text-zinc-400 font-mono">
                Overlap: {Math.round(validation.compatibility.overlap_percentage)}%
              </span>
            )}
          </div>

          {/* Raster manifests info */}
          {validation.manifests && validation.manifests.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
              {validation.manifests.map((m: any, idx: number) => (
                <div
                  key={idx}
                  className="bg-white/5 border border-white/5 rounded-lg p-2.5 text-[11px] font-mono space-y-1"
                >
                  <div className="flex items-center justify-between text-zinc-300 font-semibold truncate">
                    <span className="truncate">{m.filename || `Raster ${idx + 1}`}</span>
                    <span className="text-cyan-400 shrink-0 ml-1">
                      {m.modality?.modality || "OPTICAL"}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-3 text-zinc-400 text-[10px]">
                    <span>
                      CRS: <strong className="text-zinc-200">{m.crs_epsg ? `EPSG:${m.crs_epsg}` : (m.crs && m.crs !== "Local/Pixel" ? m.crs : "Unavailable")}</strong>
                    </span>
                    <span>
                      GSD: <strong className="text-zinc-200">{m.gsd_x != null && m.gsd_y != null ? `${m.gsd_x}m × ${m.gsd_y}m` : (m.gsd != null ? `${m.gsd}m` : "Unavailable")}</strong>
                    </span>
                    <span>
                      Size: <strong className="text-zinc-200">{m.width_px ?? "??"}×{m.height_px ?? "??"}</strong>
                    </span>
                    <span>
                      Bands: <strong className="text-zinc-200">{m.band_count ?? "?"}</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Warnings */}
          {validation.warnings && validation.warnings.length > 0 && (
            <div className="bg-amber-950/20 border border-amber-500/30 rounded-lg p-2.5 flex items-start gap-2">
              <AlertTriangle className="size-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="text-[11px] font-mono text-amber-200 space-y-0.5">
                {validation.warnings.map((w: string, i: number) => (
                  <p key={i}>• {w}</p>
                ))}
              </div>
            </div>
          )}

          {/* Errors */}
          {validation.errors && validation.errors.length > 0 && (
            <div className="bg-red-950/20 border border-red-500/30 rounded-lg p-2.5 flex items-start gap-2">
              <XCircle className="size-4 text-red-400 shrink-0 mt-0.5" />
              <div className="text-[11px] font-mono text-red-300 space-y-0.5">
                {validation.errors.map((err: string, i: number) => (
                  <p key={i}>• {err}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
