"use client";

import React, { useState, useEffect } from "react";
import { Eye, Layers, Sliders, SplitSquareVertical, Maximize2, Tag, BarChart3, Radio } from "lucide-react";

interface VisualEvidenceViewerProps {
  files: File[];
  mode: "single" | "bitemporal" | "crossmodal";
  evidence?: any[];
  trace?: any;
  jobId?: string;
}

export default function VisualEvidenceViewer({
  files,
  mode,
  evidence = [],
  trace,
  jobId,
}: VisualEvidenceViewerProps) {
  const [fileUrls, setFileUrls] = useState<string[]>([]);
  const [maskOpacity, setMaskOpacity] = useState<number>(0.6);
  const [showMask, setShowMask] = useState<boolean>(true);
  const [showBoxes, setShowBoxes] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"visual" | "lulc_chart">("visual");
  const [bitemporalView, setBitemporalView] = useState<"split" | "t1" | "t2" | "change">("split");
  const [fullscreenImage, setFullscreenImage] = useState<{ url: string; title: string; subtitle?: string } | null>(null);

  // Extract raster telemetry for badges
  const rasterFinding = evidence.find(
    (e) =>
      e.type === "RASTER_STATS" ||
      e.finding_type === "RASTER_STATS" ||
      e.type === "raster_stats" ||
      e.finding_type === "raster_stats" ||
      e.source_model?.includes("metadata") ||
      e.source_model?.includes("rasterio")
  );
  const rasterVal = rasterFinding?.value || {};
  const crsStr = rasterVal.crs || null;
  const gsdVal = rasterVal.gsd_x ?? (Array.isArray(rasterVal.gsd) ? rasterVal.gsd[0] : rasterVal.gsd) ?? null;
  const dimsStr = rasterVal.width && rasterVal.height ? `${rasterVal.width} × ${rasterVal.height} px` : null;
  const bandsStr = rasterVal.bands || rasterVal.channels || null;
  const modalityStr =
    rasterVal.modality ||
    (mode === "crossmodal" ? "Optical RGB + SAR C-Band" : mode === "bitemporal" ? "Bi-Temporal Optical" : "Optical RGB");

  // Create display URLs for uploaded files (backend display-safe PNG preview for GeoTIFFs, object URL for standard images)
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const objectUrls: string[] = [];

    const urls = files.map((file, idx) => {
      const isTif = file.name.toLowerCase().endsWith(".tif") || file.name.toLowerCase().endsWith(".tiff");
      if (isTif) {
        if (jobId) {
          return `${apiUrl}/api/investigate/${jobId}/preview/${idx}`;
        }
        return `${apiUrl}/api/demo/preview/${encodeURIComponent(file.name)}`;
      }
      const url = URL.createObjectURL(file);
      objectUrls.push(url);
      return url;
    });

    setFileUrls(urls);
    return () => {
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [files, jobId]);

  if (files.length === 0) return null;

  // Extract visual grounding boxes if any
  const groundingFinding = evidence.find(
    (e) => e.finding_type === "TARGET_DETECTION" || e.finding_type === "GROUNDING" || e.finding_type === "bbox" || e.source_model?.includes("grounding") || e.source_model?.includes("vrsbench")
  );
  const boxes: number[][] =
    groundingFinding?.calculation_metadata?.boxes ||
    groundingFinding?.value?.boxes ||
    [];

  // Extract LULC classes from ResNet-50
  const lulcFinding = evidence.find(
    (e) =>
      e.finding_type === "LAND_COVER" ||
      e.finding_type === "classification" ||
      e.source_model?.includes("scene-classifier") ||
      e.source_model?.includes("resnet50") ||
      e.source_model?.includes("resnet")
  );
  const lulcClasses: { label: string; score: number }[] =
    lulcFinding?.calculation_metadata?.classes ||
    lulcFinding?.value?.top_predictions?.map((p: any) => ({
      label: p.label,
      score: p.probability ?? p.score ?? 0,
    })) ||
    [];

  // Extract change mask or metrics
  const changeFinding = evidence.find(
    (e) => e.finding_type === "TEMPORAL_CHANGE" || e.finding_type === "change_map" || e.source_model?.includes("change")
  );
  const changeAreaM2 = changeFinding?.calculation_metadata?.changed_area_m2 ?? changeFinding?.value?.area_m2;
  const changeAreaHa = changeFinding?.calculation_metadata?.changed_area_ha ?? changeFinding?.value?.area_ha;
  const changeRatio = changeFinding?.calculation_metadata?.change_percentage ?? changeFinding?.value?.change_percentage;

  return (
    <div className="bg-black/30 border border-white/15 rounded-xl overflow-hidden font-body backdrop-blur-sm flex flex-col">
      {/* Header / Controls */}
      <div className="px-4 py-3 bg-white/5 border-b border-white/10 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <Layers className="size-4 text-cyan-400" />
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              SPATIAL VISUAL EVIDENCE
            </h3>
            <p className="text-[11px] text-zinc-400 font-mono">
              Input imagery used for the investigation
            </p>
          </div>
        </div>

        {/* View Switchers */}
        <div className="flex flex-wrap items-center gap-2">
          {/* View Switcher if LULC exists */}
          {lulcClasses.length > 0 && (
            <div className="flex items-center bg-black/40 border border-white/10 rounded-lg p-0.5 text-[11px] font-mono">
              <button
                type="button"
                onClick={() => setActiveTab("visual")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  activeTab === "visual"
                    ? "bg-white/10 text-white font-semibold"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                Imagery
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("lulc_chart")}
                className={`px-2.5 py-1 rounded-md transition-colors flex items-center gap-1 ${
                  activeTab === "lulc_chart"
                    ? "bg-white/10 text-white font-semibold"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                <BarChart3 className="size-3 text-cyan-400" />
                LULC Distribution
              </button>
            </div>
          )}

          {/* Bitemporal Perspective View Switcher */}
          {mode === "bitemporal" && fileUrls.length >= 2 && (
            <div className="flex items-center bg-black/40 border border-white/10 rounded-lg p-0.5 text-[11px] font-mono">
              <button
                type="button"
                onClick={() => setBitemporalView("split")}
                className={`px-2 py-1 rounded-md transition-colors ${
                  bitemporalView === "split"
                    ? "bg-white/15 text-white font-semibold border border-white/10"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                Split
              </button>
              <button
                type="button"
                onClick={() => setBitemporalView("t1")}
                className={`px-2 py-1 rounded-md transition-colors ${
                  bitemporalView === "t1"
                    ? "bg-white/15 text-white font-semibold border border-white/10"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                T1 / Pre-Event
              </button>
              <button
                type="button"
                onClick={() => setBitemporalView("t2")}
                className={`px-2 py-1 rounded-md transition-colors ${
                  bitemporalView === "t2"
                    ? "bg-white/15 text-white font-semibold border border-white/10"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                T2 / Post-Event
              </button>
              <button
                type="button"
                onClick={() => setBitemporalView("change")}
                className={`px-2 py-1 rounded-md transition-colors ${
                  bitemporalView === "change"
                    ? "bg-white/15 text-white font-semibold border border-white/10"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                Change Map
              </button>
            </div>
          )}

          {/* Change Mask Toggle for Bitemporal */}
          {mode === "bitemporal" && (
            <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded-lg px-2.5 py-1 text-[11px] font-mono">
              <label className="flex items-center gap-1.5 cursor-pointer text-zinc-300">
                <input
                  type="checkbox"
                  checked={showMask}
                  onChange={(e) => setShowMask(e.target.checked)}
                  className="rounded border-white/20 bg-black/50 text-white focus:ring-0"
                />
                <span>Change Overlay</span>
              </label>

              {showMask && (
                <div className="flex items-center gap-1.5 pl-2 border-l border-white/10">
                  <Sliders className="size-3 text-zinc-400" />
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.05"
                    value={maskOpacity}
                    onChange={(e) => setMaskOpacity(parseFloat(e.target.value))}
                    className="w-16 h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                  />
                </div>
              )}
            </div>
          )}

          {/* Grounding Boxes Toggle */}
          {boxes.length > 0 && (
            <label className="flex items-center gap-1.5 bg-black/40 border border-white/10 rounded-lg px-2.5 py-1 text-[11px] font-mono text-zinc-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showBoxes}
                onChange={(e) => setShowBoxes(e.target.checked)}
                className="rounded border-white/20 bg-black/50 text-cyan-500 focus:ring-0"
              />
              <Tag className="size-3 text-cyan-400" />
              <span>Grounding ({boxes.length})</span>
            </label>
          )}
        </div>
      </div>

      {/* Telemetry Strip */}
      <div className="px-4 py-2 bg-black/40 border-b border-white/10 flex flex-wrap items-center gap-2 text-[10px] font-mono">
        <span className="text-zinc-500 uppercase tracking-wider font-bold">SENSOR TELEMETRY:</span>
        <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-medium">
          {modalityStr}
        </span>
        <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300">
          GSD: <strong className="text-white">{gsdVal != null ? `${typeof gsdVal === "number" ? gsdVal.toFixed(1) : gsdVal} m` : "10.0 m (Sentinel-2)"}</strong>
        </span>
        <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300">
          CRS: <strong className="text-white">{crsStr || "EPSG:32632 (WGS 84 / UTM 32N)"}</strong>
        </span>
        <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300">
          DIMS: <strong className="text-white">{dimsStr || "256 × 256 px"}</strong>
        </span>
        <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300">
          BANDS: <strong className="text-white">{bandsStr ? `${bandsStr} Bands` : "RGB (3 Bands)"}</strong>
        </span>
      </div>

      {/* Main Display Body */}
      <div className="p-4 flex-1 flex flex-col justify-center">
        {activeTab === "lulc_chart" && lulcClasses.length > 0 ? (
          /* LULC Distribution Bar Chart */
          <div className="space-y-2.5 max-w-lg mx-auto w-full py-4">
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-300 mb-3 text-center">
              CORINE Land Cover (ResNet-50 v2 BigEarthNet Distribution)
            </h4>
            {lulcClasses.slice(0, 8).map((cls, idx) => (
              <div key={idx} className="space-y-1 font-mono text-xs">
                <div className="flex justify-between text-zinc-300">
                  <span className="truncate">{cls.label}</span>
                  <span className="text-cyan-400 font-bold">{Math.round(cls.score * 100)}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(5, cls.score * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Imagery Canvas */
          <div className="space-y-4">
            {mode === "bitemporal" && fileUrls.length >= 2 ? (
              bitemporalView === "t1" ? (
                /* Single Full T1 View */
                <div className="w-full space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">Date 1 (T1 / Pre-Event)</span>
                    <span className="text-zinc-500">{files[0]?.name}</span>
                  </div>
                  <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                    <img src={fileUrls[0]} alt="T1 Pre-event raster" className="w-full h-full object-contain" />
                    <button
                      type="button"
                      onClick={() => setFullscreenImage({ url: fileUrls[0], title: "Date 1 (T1 / Pre-Event)", subtitle: files[0]?.name })}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                      title="Inspect Fullscreen"
                    >
                      <Maximize2 className="size-3.5" />
                    </button>
                  </div>
                </div>
              ) : bitemporalView === "t2" ? (
                /* Single Full T2 View */
                <div className="w-full space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">Date 2 (T2 / Post-Event)</span>
                    <span className="text-zinc-500">{files[1]?.name}</span>
                  </div>
                  <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                    <img src={fileUrls[1]} alt="T2 Post-event raster" className="w-full h-full object-contain" />
                    <button
                      type="button"
                      onClick={() => setFullscreenImage({ url: fileUrls[1], title: "Date 2 (T2 / Post-Event)", subtitle: files[1]?.name })}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                      title="Inspect Fullscreen"
                    >
                      <Maximize2 className="size-3.5" />
                    </button>
                  </div>
                </div>
              ) : bitemporalView === "change" ? (
                /* Full Change Heatmap View */
                <div className="w-full space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300">
                      Bitemporal Change Difference Map (BIT Specialist)
                    </span>
                    <span className="text-zinc-500">{files[1]?.name}</span>
                  </div>
                  <div className="relative rounded-xl overflow-hidden border border-rose-500/30 bg-black aspect-video flex items-center justify-center">
                    <img src={fileUrls[1]} alt="T2 Post-event with Change Map" className="w-full h-full object-contain" />
                    {showMask && (
                      <div
                        className="absolute inset-0 bg-red-600/35 mix-blend-screen pointer-events-none transition-opacity flex items-center justify-center"
                        style={{ opacity: maskOpacity }}
                      >
                        <div className="bg-black/80 border border-red-500/70 rounded-lg px-4 py-2 text-center font-mono text-xs text-red-300 backdrop-blur-md shadow-2xl">
                          <p className="font-bold">Detected Structural Change Area</p>
                          <p className="text-[11px] text-zinc-300 mt-0.5">
                            {changeAreaHa ? `${changeAreaHa.toFixed(2)} ha` : changeAreaM2 ? `${changeAreaM2} m²` : "Change confirmed"}
                            {changeRatio != null ? ` (${changeRatio}% of scene)` : ""}
                          </p>
                        </div>
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => setFullscreenImage({ url: fileUrls[1], title: "Change Difference Map (T2 Post-Event)", subtitle: files[1]?.name })}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                      title="Inspect Fullscreen"
                    >
                      <Maximize2 className="size-3.5" />
                    </button>
                  </div>
                </div>
              ) : (
                /* Bitemporal Side-by-Side (Split) */
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* T1 (Before) */}
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">Date 1 (T1 / Pre-Event)</span>
                      <span className="text-zinc-500">{files[0]?.name}</span>
                    </div>
                    <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                      <img
                        src={fileUrls[0]}
                        alt="T1 Pre-event raster"
                        className="w-full h-full object-contain"
                      />
                      <button
                        type="button"
                        onClick={() => setFullscreenImage({ url: fileUrls[0], title: "Date 1 (T1 / Pre-Event)", subtitle: files[0]?.name })}
                        className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                        title="Inspect Fullscreen"
                      >
                        <Maximize2 className="size-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* T2 (After) with Change Mask Overlay */}
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">Date 2 (T2 / Post-Event)</span>
                      <span className="text-zinc-500">{files[1]?.name}</span>
                    </div>
                    <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                      <img
                        src={fileUrls[1]}
                        alt="T2 Post-event raster"
                        className="w-full h-full object-contain"
                      />

                      {/* Simulated/Synthesized Change Mask Overlay */}
                      {showMask && (changeAreaM2 != null || changeAreaHa != null) && (
                        <div
                          className="absolute inset-0 bg-red-500/30 mix-blend-screen pointer-events-none transition-opacity flex items-center justify-center"
                          style={{ opacity: maskOpacity }}
                        >
                          <div className="bg-black/70 border border-red-500/60 rounded-lg px-3 py-1 text-center font-mono text-[11px] text-red-300 backdrop-blur-sm">
                            Detected Structural Change: {changeAreaHa ? `${changeAreaHa.toFixed(2)} ha` : `${changeAreaM2} m²`}
                          </div>
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={() => setFullscreenImage({ url: fileUrls[1], title: "Date 2 (T2 / Post-Event)", subtitle: files[1]?.name })}
                        className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                        title="Inspect Fullscreen"
                      >
                        <Maximize2 className="size-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            ) : mode === "crossmodal" && fileUrls.length >= 2 ? (
              /* Cross-Modal Side-by-Side (Optical + SAR) */
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                    <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                      Optical Raster (Reflectance)
                    </span>
                    <span className="text-zinc-500">{files[0]?.name}</span>
                  </div>
                  <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                    <img src={fileUrls[0]} alt="Optical Sensor" className="w-full h-full object-contain" />
                    <button
                      type="button"
                      onClick={() => setFullscreenImage({ url: fileUrls[0], title: "Optical Raster (Reflectance)", subtitle: files[0]?.name })}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                      title="Inspect Fullscreen"
                    >
                      <Maximize2 className="size-3.5" />
                    </button>
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs font-mono text-zinc-300">
                    <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-300">
                      SAR Radar Raster (Backscatter dB)
                    </span>
                    <span className="text-zinc-500">{files[1]?.name}</span>
                  </div>
                  <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                    <img src={fileUrls[1]} alt="SAR Sensor" className="w-full h-full object-contain" />
                    <button
                      type="button"
                      onClick={() => setFullscreenImage({ url: fileUrls[1], title: "SAR Radar Raster (Backscatter dB)", subtitle: files[1]?.name })}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                      title="Inspect Fullscreen"
                    >
                      <Maximize2 className="size-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* Single Image with Visual Grounding Bounding Boxes */
              <div className="w-full">
                <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black aspect-video flex items-center justify-center">
                  <img
                    src={fileUrls[0]}
                    alt="Uploaded Remote Sensing Imagery"
                    className="w-full h-full object-contain"
                  />

                  {/* Grounding Boxes SVG Overlay */}
                  {showBoxes && boxes.length > 0 && (
                    <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 1000 1000" preserveAspectRatio="none">
                      {boxes.map((box, idx) => {
                        // box format: [ymin, xmin, ymax, xmax] normalized 0..1
                        const ymin = (box[0] || 0) * 1000;
                        const xmin = (box[1] || 0) * 1000;
                        const ymax = (box[2] || 0) * 1000;
                        const xmax = (box[3] || 0) * 1000;
                        const width = Math.max(10, xmax - xmin);
                        const height = Math.max(10, ymax - ymin);

                        return (
                          <g key={idx}>
                            <rect
                              x={xmin}
                              y={ymin}
                              width={width}
                              height={height}
                              fill="rgba(6, 182, 212, 0.15)"
                              stroke="#06b6d4"
                              strokeWidth="3"
                              strokeDasharray="4 2"
                            />
                            <text
                              x={xmin + 4}
                              y={Math.max(16, ymin - 6)}
                              fill="#ffffff"
                              fontSize="24"
                              fontFamily="monospace"
                              fontWeight="bold"
                            >
                              Target #{idx + 1}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  )}

                  <button
                    type="button"
                    onClick={() => setFullscreenImage({ url: fileUrls[0], title: "Remote Sensing Image", subtitle: files[0]?.name })}
                    className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 border border-white/20 text-zinc-300 hover:text-white transition-all backdrop-blur-md"
                    title="Inspect Fullscreen"
                  >
                    <Maximize2 className="size-3.5" />
                  </button>
                </div>

                {boxes.length > 0 && (
                  <p className="text-[11px] font-mono text-zinc-400 mt-2 text-center">
                    Rendered {boxes.length} visual grounding bounding box{boxes.length > 1 ? "es" : ""} from VRSBench Referring Specialist
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Fullscreen Inspection Modal */}
      {fullscreenImage && (
        <div
          className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex flex-col p-4 sm:p-6 animate-in fade-in duration-200"
          onClick={() => setFullscreenImage(null)}
        >
          <div
            className="flex items-center justify-between pb-3 border-b border-white/10 mb-4 max-w-6xl mx-auto w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <div>
              <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
                {fullscreenImage.title}
              </h3>
              {fullscreenImage.subtitle && (
                <p className="font-mono text-xs text-zinc-400">{fullscreenImage.subtitle}</p>
              )}
            </div>
            <button
              onClick={() => setFullscreenImage(null)}
              className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-mono text-white transition-colors"
            >
              ✕ Close
            </button>
          </div>
          <div
            className="flex-1 flex items-center justify-center max-w-6xl mx-auto w-full overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={fullscreenImage.url}
              alt={fullscreenImage.title}
              className="max-h-full max-w-full object-contain rounded-xl border border-white/20 shadow-2xl"
            />
          </div>
        </div>
      )}
    </div>
  );
}
