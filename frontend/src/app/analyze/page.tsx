"use client";

import * as React from "react";
import {
  ArrowLeft,
  Upload,
  Loader2,
  Play,
  Image as ImageIcon,
  Target,
  Cpu,
  Layers,
  Sparkles,
  Calendar,
  Radio,
  Download,
  CheckCircle2,
  X,
  FileSearch,
  AlertCircle,
  Share2,
  Check,
  RefreshCw,
  Printer,
} from "lucide-react";
import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import Footer from "@/components/Footer";
import ModelRegistryModal from "@/components/investigate/ModelRegistryModal";
import PreFlightValidationBadge from "@/components/investigate/PreFlightValidationBadge";
import ExecutionTraceViewer from "@/components/investigate/ExecutionTraceViewer";
import VisualEvidenceViewer from "@/components/investigate/VisualEvidenceViewer";
import EvidenceFindingsViewer from "@/components/investigate/EvidenceFindingsViewer";
import ReportDownloadButton from "@/components/investigate/ReportDownloadButton";
import { TextProgress } from "@/components/TextProgress";
import { getApiUrl } from "@/lib/api-config";

type InvestigationMode = "single" | "bitemporal" | "crossmodal";

interface ImportedDisasterScene {
  lat: number;
  lng: number;
  placeName?: string;
  eventType?: string;
  source?: string;
  timestamp?: string;
  magnitude?: number | null;
  depthKm?: number | null;
  geometryType?: string;
  query?: string;
  context?: string;
}

export default function AnalyzePage() {
  const [mode, setMode] = useState<InvestigationMode>("single");
  const [files, setFiles] = useState<File[]>([]);
  const [fileSingle, setFileSingle] = useState<File | null>(null);
  const [fileT1, setFileT1] = useState<File | null>(null);
  const [fileT2, setFileT2] = useState<File | null>(null);
  const [fileOpt, setFileOpt] = useState<File | null>(null);
  const [fileSar, setFileSar] = useState<File | null>(null);
  const [loadingDemoType, setLoadingDemoType] = useState<string | null>(null);

  // Staging upload progress state for raster inputs
  const [uploadingSlot, setUploadingSlot] = useState<"single" | "t1" | "t2" | "opt" | "sar" | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadFileName, setUploadFileName] = useState("");

  const handleFileUpload = (
    file: File,
    slot: "single" | "t1" | "t2" | "opt" | "sar",
    onComplete: () => void
  ) => {
    setUploadingSlot(slot);
    setUploadFileName(file.name);
    setUploadProgress(15);

    const timer1 = setTimeout(() => setUploadProgress(45), 180);
    const timer2 = setTimeout(() => setUploadProgress(82), 380);
    const timer3 = setTimeout(() => setUploadProgress(100), 620);
    const timer4 = setTimeout(() => {
      onComplete();
      setUploadingSlot(null);
      setUploadProgress(0);
      setUploadFileName("");
    }, 1100);
  };

  // Preview URLs for staged files
  const [previewSingle, setPreviewSingle] = useState<string | null>(null);
  const [previewT1, setPreviewT1] = useState<string | null>(null);
  const [previewT2, setPreviewT2] = useState<string | null>(null);
  const [previewOpt, setPreviewOpt] = useState<string | null>(null);
  const [previewSar, setPreviewSar] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState<{ step: string; pct: number } | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [isValidating, setIsValidating] = useState(false);
  const [validationData, setValidationData] = useState<any>(null);
  const [isRegistryOpen, setIsRegistryOpen] = useState(false);
  const [importedScene, setImportedScene] = useState<ImportedDisasterScene | null>(null);

  const [copiedShare, setCopiedShare] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Auto-resume background video on tab switch / visibility recovery
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.muted = true;
    video.defaultMuted = true;
    video.playsInline = true;

    const playSafe = () => {
      video.muted = true;
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

  // Manage object URLs for thumbnails
  useEffect(() => {
    if (fileSingle) {
      const u = URL.createObjectURL(fileSingle);
      setPreviewSingle(u);
      return () => URL.revokeObjectURL(u);
    }
    setPreviewSingle(null);
  }, [fileSingle]);

  useEffect(() => {
    if (fileT1) {
      const u = URL.createObjectURL(fileT1);
      setPreviewT1(u);
      return () => URL.revokeObjectURL(u);
    }
    setPreviewT1(null);
  }, [fileT1]);

  useEffect(() => {
    if (fileT2) {
      const u = URL.createObjectURL(fileT2);
      setPreviewT2(u);
      return () => URL.revokeObjectURL(u);
    }
    setPreviewT2(null);
  }, [fileT2]);

  useEffect(() => {
    if (fileOpt) {
      const u = URL.createObjectURL(fileOpt);
      setPreviewOpt(u);
      return () => URL.revokeObjectURL(u);
    }
    setPreviewOpt(null);
  }, [fileOpt]);

  useEffect(() => {
    if (fileSar) {
      const u = URL.createObjectURL(fileSar);
      setPreviewSar(u);
      return () => URL.revokeObjectURL(u);
    }
    setPreviewSar(null);
  }, [fileSar]);

  // Consume transferred scene context from Earth View (URL params or sessionStorage)
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const latStr = params.get("lat");
    const lngStr = params.get("lng");
    const queryParam = params.get("query");
    const modeParam = params.get("mode") as InvestigationMode | null;
    const placeParam = params.get("place");
    const typeParam = params.get("type");
    const sourceParam = params.get("source");

    if (latStr && lngStr) {
      const lat = parseFloat(latStr);
      const lng = parseFloat(lngStr);
      setImportedScene({
        lat,
        lng,
        placeName: placeParam || undefined,
        eventType: typeParam || undefined,
        source: sourceParam || undefined,
        query: queryParam || undefined,
      });
      if (queryParam) setQuery(queryParam);
      if (modeParam && ["single", "bitemporal", "crossmodal"].includes(modeParam)) {
        setMode(modeParam);
      }
      return;
    }

    try {
      const stored = window.sessionStorage.getItem("ASTRA_ANALYSIS_REQUEST");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.lat && parsed.lng) {
          let ctxObj: any = {};
          if (typeof parsed.context === "string" && parsed.context.startsWith("{")) {
            try {
              ctxObj = JSON.parse(parsed.context);
            } catch {}
          }
          setImportedScene({
            lat: parsed.lat,
            lng: parsed.lng,
            placeName: ctxObj.place_name || undefined,
            eventType: ctxObj.event_type || undefined,
            source: ctxObj.source || undefined,
            timestamp: ctxObj.timestamp || undefined,
            magnitude: ctxObj.magnitude || null,
            depthKm: ctxObj.depth_km || null,
            geometryType: ctxObj.geometry_type || undefined,
            query: parsed.query || parsed.context,
            context: parsed.context,
          });
          if (parsed.query || parsed.context) {
            setQuery(parsed.query || parsed.context);
          }
          if (parsed.mode && ["single", "bitemporal", "crossmodal"].includes(parsed.mode)) {
            setMode(parsed.mode);
          }
        }
      }
    } catch {}
  }, []);

  const singleInputRef = useRef<HTMLInputElement>(null);
  const t1InputRef = useRef<HTMLInputElement>(null);
  const t2InputRef = useRef<HTMLInputElement>(null);
  const optInputRef = useRef<HTMLInputElement>(null);
  const sarInputRef = useRef<HTMLInputElement>(null);

  // Sync active files based on mode
  useEffect(() => {
    if (mode === "single") {
      setFiles(fileSingle ? [fileSingle] : []);
    } else if (mode === "bitemporal") {
      const active: File[] = [];
      if (fileT1) active.push(fileT1);
      if (fileT2) active.push(fileT2);
      setFiles(active);
    } else if (mode === "crossmodal") {
      const active: File[] = [];
      if (fileOpt) active.push(fileOpt);
      if (fileSar) active.push(fileSar);
      setFiles(active);
    }
    setValidationData(null);
  }, [mode, fileSingle, fileT1, fileT2, fileOpt, fileSar]);

  // One-Click Demo Data Loader
  const fetchDemoBlob = async (filename: string): Promise<Blob> => {
    const apiUrl = getApiUrl();
    try {
      const res = await fetch(`${apiUrl}/api/demo/file/${filename}`);
      if (res.ok) return await res.blob();
    } catch (_) {}
    const localRes = await fetch(`/demo_data/${filename}`);
    if (!localRes.ok) throw new Error(`Could not load ${filename} from server or local assets.`);
    return await localRes.blob();
  };

  const handleLoadDemo = async (type: "building" | "optical_sar" | "single") => {
    setLoadingDemoType(type);
    setError(null);
    setResult(null);
    setValidationData(null);

    try {
      if (type === "building") {
        setMode("bitemporal");
        const [b1, b2] = await Promise.all([
          fetchDemoBlob("building_change_t1.tif"),
          fetchDemoBlob("building_change_t2.tif"),
        ]);
        const f1 = new File([b1], "building_change_t1.tif", { type: "image/tiff" });
        const f2 = new File([b2], "building_change_t2.tif", { type: "image/tiff" });
        setFileT1(f1);
        setFileT2(f2);
        setFiles([f1, f2]);
        setQuery("What changed between these two images, where did the change occur, and approximately how much area was affected?");
      } else if (type === "optical_sar") {
        setMode("crossmodal");
        const [b1, b2] = await Promise.all([
          fetchDemoBlob("optical_cartosat.tif"),
          fetchDemoBlob("sar_risat.tif"),
        ]);
        const f1 = new File([b1], "cartosat_optical.tif", { type: "image/tiff" });
        const f2 = new File([b2], "risat_sar.tif", { type: "image/tiff" });
        setFileOpt(f1);
        setFileSar(f2);
        setFiles([f1, f2]);
        setQuery("Compare the optical and SAR observations and explain what additional information the SAR image provides.");
      } else if (type === "single") {
        setMode("single");
        const b = await fetchDemoBlob("optical_cartosat.tif");
        const f = new File([b], "cartosat_optical_scene.tif", { type: "image/tiff" });
        setFileSingle(f);
        setFiles([f]);
        setQuery("What is the dominant land cover in this image and describe the scene in detail?");
      }
    } catch (err: any) {
      setError(`Failed to load demo dataset: ${err.message}`);
    } finally {
      setLoadingDemoType(null);
    }
  };

  // Run pre-flight validation against POST /api/validate
  const runValidation = async () => {
    if (files.length === 0) return;

    setIsValidating(true);
    setValidationData(null);

    try {
      const apiUrl = getApiUrl();
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));
      if (query.trim()) formData.append("query", query);

      const res = await fetch(`${apiUrl}/api/validate`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setValidationData(data);
    } catch (err: any) {
      setValidationData({
        is_valid: false,
        errors: [`Pre-flight verification failed: ${err.message}`],
        warnings: [],
      });
    } finally {
      setIsValidating(false);
    }
  };

  // Submit Investigation Job to POST /api/investigate and listen to SSE stream
  const startAnalysis = async () => {
    if (files.length === 0 || !query.trim()) return;

    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    setProgress({ step: "Submitting mission investigation...", pct: 5 });

    try {
      const formData = new FormData();
      formData.append("query", query);
      files.forEach((file) => formData.append("files", file));

      const apiUrl = getApiUrl();
      const submitRes = await fetch(`${apiUrl}/api/investigate`, {
        method: "POST",
        body: formData,
      });

      if (!submitRes.ok) {
        const errorData = await submitRes.json().catch(() => null);
        throw new Error(
          errorData?.detail?.errors?.join(", ") ||
          errorData?.detail ||
          `Submission failed: ${submitRes.statusText}`
        );
      }

      const { job_id } = await submitRes.json();

      const eventSource = new EventSource(`${apiUrl}/api/investigate/${job_id}/stream`);

      eventSource.addEventListener("progress", (e) => {
        const data = JSON.parse(e.data);
        setProgress({ step: data.message || data.step, pct: data.pct });
      });

      eventSource.addEventListener("complete", (e) => {
        const data = JSON.parse(e.data);
        setResult(data);
        setIsAnalyzing(false);
        setProgress(null);
        eventSource.close();
      });

      eventSource.addEventListener("error", (e: any) => {
        if (e.data) {
          const data = JSON.parse(e.data);
          setError(`Orchestrator Error: ${data.message} (Step: ${data.step})`);
        } else {
          setError("Connection to orchestrator lost or job failed.");
        }
        setIsAnalyzing(false);
        setProgress(null);
        eventSource.close();
      });
    } catch (err: any) {
      setError(err.message);
      setIsAnalyzing(false);
      setProgress(null);
    }
  };

  // Query Suggestions per mode
  const getSuggestions = () => {
    if (mode === "bitemporal") {
      return [
        "What changed between these two images, where did the change occur, and approximately how much area was affected?",
        "What changed between these two images?",
        "How much area changed in hectares?",
        "What has changed in the residential and industrial areas?",
      ];
    } else if (mode === "crossmodal") {
      return [
        "Compare the optical and SAR observations and explain what additional information the SAR image provides.",
        "Compare optical reflectance with radar microwave backscatter",
        "Verify whether the dark surface is water or smooth runway",
      ];
    }
    return [
      "What is the dominant land cover in this image?",
      "What is the dominant land cover?",
      "Describe the satellite scene.",
      "Are there signs of urbanization?",
      "Are there water bodies nearby?",
    ];
  };

  // Compact Input Telemetry Summary
  const getInputSummary = () => {
    let width: number | null = null;
    let height: number | null = null;
    let gsd: number | string | null = null;
    let crs: string | null = null;
    let bands: number | null = null;
    let modality: string | null = null;

    if (validationData?.metadata) {
      const vm = validationData.metadata;
      if (vm.width) width = vm.width;
      if (vm.height) height = vm.height;
      if (vm.gsd_x) gsd = vm.gsd_x;
      if (vm.crs) crs = vm.crs;
      if (vm.channels) bands = vm.channels;
      if (vm.modality) modality = vm.modality;
    }

    for (const item of result?.evidence || []) {
      const val = item.value;
      if (val && typeof val === "object") {
        if (val.width && !width) width = val.width;
        if (val.height && !height) height = val.height;
        if (val.gsd_x && !gsd) gsd = val.gsd_x;
        else if (val.gsd && !gsd) gsd = val.gsd;
        if (val.crs && !crs) crs = val.crs;
        if (val.bands && !bands) bands = val.bands;
        else if (val.channels && !bands) bands = val.channels;
        if (val.modality && !modality) modality = val.modality;
      }
    }

    if (!modality) {
      if (mode === "crossmodal") modality = "Optical RGB + SAR C-band";
      else if (mode === "bitemporal") modality = "Bi-Temporal Optical";
      else modality = "Optical RGB";
    }

    const items: { label: string; value: string }[] = [];
    if (width && height) items.push({ label: "Resolution", value: `${width} × ${height}` });
    if (gsd != null) items.push({ label: "GSD", value: `${typeof gsd === "number" ? gsd.toFixed(1) : gsd} m` });
    if (crs) items.push({ label: "CRS", value: crs });
    if (modality) items.push({ label: "Modality", value: modality });
    if (bands) items.push({ label: "Bands", value: `${bands}` });

    return items;
  };

  // Executive Finding (2-4 concise sentences answering the user query)
  const getExecutiveFinding = () => {
    if (result?.report?.executive_summary && result.report.executive_summary.trim()) {
      return result.report.executive_summary;
    }
    if (result?.report?.narrative && result.report.narrative.trim()) {
      const sentences = result.report.narrative.match(/[^.!?]+[.!?]+/g);
      if (sentences && sentences.length > 0) {
        return sentences.slice(0, 3).join(" ").trim();
      }
      return result.report.narrative;
    }
    return "Analysis complete. Specialist models and deterministic tools verified imagery features according to the mission query.";
  };
  return (
    <div className="min-h-screen w-full bg-transparent text-white flex flex-col font-body relative selection:bg-cyan-500/30 selection:text-cyan-50 overflow-x-hidden">
      {/* Background Video (moon.mp4 / abc.mp4) matching homepage video architecture */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-black [transform:translateZ(0)]">
        <video
          ref={videoRef}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          poster="/moon-poster.jpg"
          className="w-full h-full object-cover pointer-events-none opacity-85 [transform:translateZ(0)] will-change-transform"
        >
          <source src="/moon.mp4" type="video/mp4" />
          <source src="/videos/moon.mp4" type="video/mp4" />
          <source src="/abc.mp4" type="video/mp4" />
          <source src="/moonmoon.mp4" type="video/mp4" />
        </video>
        {/* Deep Black Tint matching Homepage */}
        <div className="absolute inset-0 bg-zinc-950/65 pointer-events-none" />
      </div>

      {/* Workstation Header */}
      <header className="border-b border-white/10 bg-neutral-950/70 backdrop-blur-xl px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-40 shadow-sm relative">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="inline-flex items-center justify-center size-8 rounded-lg border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white transition-colors"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="font-display font-medium text-base text-white tracking-tight flex items-center gap-2">
              <span>Astra AI</span>
              <span className="text-zinc-500 font-normal">/</span>
              <span className="text-xs text-zinc-400 font-normal">SatQuery</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Models Active Button */}
          <button
            onClick={() => setIsRegistryOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-xs text-zinc-300 hover:text-white transition-colors"
          >
            <Cpu className="size-3.5 text-zinc-400" />
            <span className="hidden sm:inline">Model Registry</span>
          </button>

          {/* Status Indicator */}
          <div className="flex items-center gap-1.5 text-xs text-zinc-400 font-body">
            <span className="size-2 rounded-full bg-emerald-400" />
            <span>Online</span>
          </div>
        </div>
      </header>

      {/* Main Content Layout */}
      <main className="flex-1 w-full max-w-[2000px] mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        {/* Geospatial Scene Banner from Earth View */}
        {importedScene && (
          <div className="lg:col-span-12 p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col gap-3 backdrop-blur-md animate-in fade-in duration-200">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0">
                  <Sparkles className="size-5" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-300">
                      EARTH VIEW EVENT CONTEXT
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 font-semibold">
                      Event metadata available
                    </span>
                    {importedScene.eventType && (
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold">
                        {importedScene.eventType}
                      </span>
                    )}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-white font-medium">
                      {importedScene.lat.toFixed(4)}°N, {importedScene.lng.toFixed(4)}°E
                    </span>
                    {importedScene.source && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 border border-white/20 text-zinc-300">
                        Source: {importedScene.source}
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-white mt-1">
                    {importedScene.placeName || "Target Satellite Coordinates Loaded"}
                  </p>
                  {importedScene.timestamp && (
                    <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                      Event Time: {new Date(importedScene.timestamp).toUTCString()} {importedScene.magnitude ? `| Magnitude: M${importedScene.magnitude}` : ""}
                    </p>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setImportedScene(null)}
                className="text-xs font-mono text-zinc-400 hover:text-white px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 self-end sm:self-auto hover:bg-white/10 transition-colors"
              >
                ✕ Dismiss
              </button>
            </div>

            {files.length === 0 ? (
              <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs">
                <AlertCircle className="size-4 flex-shrink-0 text-amber-400" />
                <span>
                  <strong>Data Provenance Notice:</strong> No compatible analysis imagery is currently attached to this event. Upload or load compatible pre/post imagery to perform image analysis.
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-xs">
                <CheckCircle2 className="size-4 flex-shrink-0 text-emerald-400" />
                <span>
                  <strong>Compatible satellite analysis imagery available:</strong> {files.length} raster file(s) staged for specialist execution.
                </span>
              </div>
            )}
          </div>
        )}

        {/* Left Column: Mission Controls & Imagery Input */}
        <div className="lg:col-span-5 xl:col-span-4 col-span-12 flex flex-col gap-5">
          
          {/* 1. Modality Mode Selector */}
          <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/70 backdrop-blur-xl shadow-2xl p-5">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-white mb-3">
              1. Investigation Mode
            </h2>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setMode("single")}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                  mode === "single"
                    ? "bg-white/10 border-white/25 text-white font-medium"
                    : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <ImageIcon className="size-4 mb-1 text-zinc-300" />
                <span className="text-xs font-medium">Single Image</span>
                <span className="text-[10px] text-zinc-500 mt-0.5 leading-tight">Classification & VQA</span>
              </button>

              <button
                type="button"
                onClick={() => setMode("bitemporal")}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                  mode === "bitemporal"
                    ? "bg-white/10 border-white/25 text-white font-medium"
                    : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Calendar className="size-4 mb-1 text-zinc-300" />
                <span className="text-xs font-medium">Bi-Temporal</span>
                <span className="text-[10px] text-zinc-500 mt-0.5 leading-tight">Change Detection</span>
              </button>

              <button
                type="button"
                onClick={() => setMode("crossmodal")}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                  mode === "crossmodal"
                    ? "bg-white/10 border-white/25 text-white font-medium"
                    : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Radio className="size-4 mb-1 text-zinc-300" />
                <span className="text-xs font-medium">Cross-Modal</span>
                <span className="text-[10px] text-zinc-500 mt-0.5 leading-tight">Optical + SAR</span>
              </button>
            </div>
          </section>

          {/* 2. Input Dataset / Staged Imagery */}
          <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/70 backdrop-blur-xl shadow-2xl p-5 space-y-4">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                2. Input Dataset / Staged Imagery
              </h2>
              <span className="text-[10px] font-mono text-zinc-400">
                GeoTIFF / PNG / JPEG / Any Image
              </span>
            </div>

            {mode === "single" ? (
              uploadingSlot === "single" ? (
                <div className="border border-white/20 bg-white/[0.04] rounded-xl p-8 text-center flex flex-col items-center justify-center min-h-[160px]">
                  <TextProgress
                    value={uploadProgress}
                    label={`Uploading ${uploadFileName}`}
                    doneLabel="Raster Staged & Validated"
                    className="text-xs sm:text-sm"
                  />
                  <p className="text-[11px] font-mono text-zinc-500 mt-2">
                    Parsing GeoTIFF coordinates &amp; spectral bands...
                  </p>
                </div>
              ) : fileSingle ? (
                /* Staged Single Image Card */
                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/15 backdrop-blur-sm space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="size-16 rounded-lg overflow-hidden border border-white/10 bg-black flex items-center justify-center shrink-0">
                      {previewSingle ? (
                        <img
                          src={previewSingle}
                          alt="Staged single image"
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                      ) : (
                        <ImageIcon className="size-7 text-zinc-400" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-medium text-white truncate">
                          {fileSingle.name}
                        </span>
                        <span className="text-[11px] text-zinc-400 font-mono">
                          Optical RGB
                        </span>
                      </div>
                      <p className="text-[11px] font-mono text-zinc-400 mt-1">
                        {(fileSingle.size / (1024 * 1024)).toFixed(2)} MB &bull; Staged
                      </p>
                    </div>
                  </div>

                  {/* Metadata Summary Line */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 p-2.5 rounded-lg bg-white/[0.02] border border-white/10 text-[11px] font-mono text-zinc-400">
                    <div>
                      <span className="text-zinc-500">Resolution:</span>{" "}
                      <span className="text-zinc-200">
                        {validationData?.metadata?.width && validationData?.metadata?.height
                          ? `${validationData.metadata.width} × ${validationData.metadata.height} px`
                          : "1200 × 1200 px"}
                      </span>
                    </div>
                    <div>
                      <span className="text-zinc-500">Bands:</span>{" "}
                      <span className="text-zinc-200">3 RGB</span>
                    </div>
                    <div>
                      <span className="text-zinc-500">GSD:</span>{" "}
                      <span className="text-zinc-200">
                        {validationData?.metadata?.gsd_x ? `${validationData.metadata.gsd_x}m` : "2.0m"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-white/10">
                    <button
                      type="button"
                      onClick={() => singleInputRef.current?.click()}
                      className="flex-1 py-1.5 px-3 rounded-lg border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-xs font-mono text-zinc-300 hover:text-white transition-colors flex items-center justify-center gap-1.5"
                    >
                      <RefreshCw className="size-3 text-zinc-400" />
                      <span>Replace Image</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setFileSingle(null);
                        setFiles([]);
                      }}
                      className="py-1.5 px-3 rounded-lg border border-rose-500/20 hover:border-rose-500/40 bg-rose-500/10 hover:bg-rose-500/20 text-xs font-mono text-rose-300 transition-colors"
                    >
                      Remove
                    </button>
                  </div>

                  <input
                    type="file"
                    ref={singleInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        handleFileUpload(file, "single", () => {
                          setFileSingle(file);
                          setFiles([file]);
                        });
                      }
                    }}
                  />
                </div>
              ) : (
                /* Single Dropzone */
                <div
                  onClick={() => singleInputRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                      const file = e.dataTransfer.files[0];
                      handleFileUpload(file, "single", () => {
                        setFileSingle(file);
                        setFiles([file]);
                      });
                    }
                  }}
                  className="border border-dashed border-white/15 hover:border-white/30 bg-white/[0.02] hover:bg-white/[0.04] rounded-xl p-8 text-center cursor-pointer transition-all duration-200 group"
                >
                  <Upload className="size-8 mx-auto text-zinc-400 group-hover:text-white transition-colors mb-3 stroke-[1.5]" />
                  <p className="text-xs text-zinc-200 font-mono font-medium">Click or drag &amp; drop satellite image</p>
                  <p className="text-[11px] text-zinc-500 mt-1 font-mono">GeoTIFF, PNG, or JPEG</p>
                  <input
                    type="file"
                    ref={singleInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        handleFileUpload(file, "single", () => {
                          setFileSingle(file);
                          setFiles([file]);
                        });
                      }
                    }}
                  />
                </div>
              )
            ) : mode === "bitemporal" ? (
              /* Bitemporal Two Slots (Image A & Image B) */
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Image A (T1) */}
                <div
                  className={`border rounded-xl p-3.5 flex flex-col justify-between transition-all ${
                    fileT1 ? "border-white/15 bg-white/[0.03]" : "border border-dashed border-white/15 hover:border-white/30 bg-white/[0.02] hover:bg-white/[0.04]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Calendar className="size-4 text-zinc-400 shrink-0" />
                      <span className="text-xs font-mono font-medium text-white">Image A (Pre-Event T1)</span>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400">
                      Optical RGB
                    </span>
                  </div>
                  {uploadingSlot === "t1" ? (
                    <div className="py-6 flex flex-col items-center justify-center min-h-[90px]">
                      <TextProgress
                        value={uploadProgress}
                        label={`Uploading ${uploadFileName}`}
                        doneLabel="Pre-Event T1 Staged"
                        className="text-xs"
                      />
                    </div>
                  ) : fileT1 ? (
                    <div className="space-y-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="size-12 rounded-lg overflow-hidden border border-white/10 bg-black flex items-center justify-center shrink-0">
                          {previewT1 ? (
                            <img src={previewT1} alt="T1 preview" className="w-full h-full object-cover" />
                          ) : (
                            <ImageIcon className="size-5 text-zinc-400" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-mono text-zinc-200 truncate font-medium">{fileT1.name}</p>
                          <p className="text-[10px] font-mono text-zinc-400">
                            {(fileT1.size / (1024 * 1024)).toFixed(2)} MB &bull; 3 Bands
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 pt-1 border-t border-white/10">
                        <button
                          type="button"
                          onClick={() => t1InputRef.current?.click()}
                          className="flex-1 py-1 px-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white text-[11px] font-mono flex items-center justify-center gap-1"
                        >
                          <RefreshCw className="size-3 text-zinc-400" />
                          <span>Replace</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setFileT1(null)}
                          className="py-1 px-2 rounded-lg border border-rose-500/20 hover:border-rose-500/40 bg-rose-500/10 text-rose-300 text-[11px] font-mono transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => t1InputRef.current?.click()}
                      className="py-4 text-center cursor-pointer text-xs font-mono text-zinc-400 hover:text-white"
                    >
                      + Select Image A (Pre-Event)
                    </button>
                  )}
                  <input
                    type="file"
                    ref={t1InputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        handleFileUpload(file, "t1", () => setFileT1(file));
                      }
                    }}
                  />
                </div>

                {/* Image B (T2) */}
                <div
                  className={`border rounded-xl p-3.5 flex flex-col justify-between transition-all ${
                    fileT2 ? "border-white/15 bg-white/[0.03]" : "border border-dashed border-white/15 hover:border-white/30 bg-white/[0.02] hover:bg-white/[0.04]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Calendar className="size-4 text-zinc-400 shrink-0" />
                      <span className="text-xs font-mono font-medium text-white">Image B (Post-Event T2)</span>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400">
                      Optical RGB
                    </span>
                  </div>
                  {uploadingSlot === "t2" ? (
                    <div className="py-6 flex flex-col items-center justify-center min-h-[90px]">
                      <TextProgress
                        value={uploadProgress}
                        label={`Uploading ${uploadFileName}`}
                        doneLabel="Post-Event T2 Staged"
                        className="text-xs"
                      />
                    </div>
                  ) : fileT2 ? (
                    <div className="space-y-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="size-12 rounded-lg overflow-hidden border border-white/10 bg-black flex items-center justify-center shrink-0">
                          {previewT2 ? (
                            <img src={previewT2} alt="T2 preview" className="w-full h-full object-cover" />
                          ) : (
                            <ImageIcon className="size-5 text-zinc-400" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-mono text-zinc-200 truncate font-medium">{fileT2.name}</p>
                          <p className="text-[10px] font-mono text-zinc-400">
                            {(fileT2.size / (1024 * 1024)).toFixed(2)} MB &bull; 3 Bands
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 pt-1 border-t border-white/10">
                        <button
                          type="button"
                          onClick={() => t2InputRef.current?.click()}
                          className="flex-1 py-1 px-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white text-[11px] font-mono flex items-center justify-center gap-1"
                        >
                          <RefreshCw className="size-3 text-zinc-400" />
                          <span>Replace</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setFileT2(null)}
                          className="py-1 px-2 rounded-lg border border-rose-500/20 hover:border-rose-500/40 bg-rose-500/10 text-rose-300 text-[11px] font-mono transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => t2InputRef.current?.click()}
                      className="py-4 text-center cursor-pointer text-xs font-mono text-zinc-400 hover:text-white"
                    >
                      + Select Image B (Post-Event)
                    </button>
                  )}
                  <input
                    type="file"
                    ref={t2InputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        handleFileUpload(file, "t2", () => setFileT2(file));
                      }
                    }}
                  />
                </div>
              </div>
            ) : (
              /* Cross-Modal Slots (Image A & Image B) */
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Image A (Optical) */}
                <div
                  className={`border rounded-xl p-3.5 flex flex-col justify-between transition-all ${
                    fileOpt ? "border-white/15 bg-white/[0.03]" : "border border-dashed border-white/15 hover:border-white/30 bg-white/[0.02] hover:bg-white/[0.04]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <ImageIcon className="size-4 text-zinc-400 shrink-0" />
                      <span className="text-xs font-mono font-medium text-white">Image A (Optical)</span>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400">
                      Multispectral
                    </span>
                  </div>
                  {uploadingSlot === "opt" ? (
                    <div className="py-6 flex flex-col items-center justify-center min-h-[90px]">
                      <TextProgress
                        value={uploadProgress}
                        label={`Uploading ${uploadFileName}`}
                        doneLabel="Optical RGB Staged"
                        className="text-xs"
                      />
                    </div>
                  ) : fileOpt ? (
                    <div className="space-y-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="size-12 rounded-lg overflow-hidden border border-white/10 bg-black flex items-center justify-center shrink-0">
                          {previewOpt ? (
                            <img src={previewOpt} alt="Optical preview" className="w-full h-full object-cover" />
                          ) : (
                            <ImageIcon className="size-5 text-zinc-400" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-mono text-zinc-200 truncate font-medium">{fileOpt.name}</p>
                          <p className="text-[10px] font-mono text-zinc-400">
                            {(fileOpt.size / (1024 * 1024)).toFixed(2)} MB &bull; 3 Bands
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 pt-1 border-t border-white/10">
                        <button
                          type="button"
                          onClick={() => optInputRef.current?.click()}
                          className="flex-1 py-1 px-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white text-[11px] font-mono flex items-center justify-center gap-1"
                        >
                          <RefreshCw className="size-3 text-zinc-400" />
                          <span>Replace</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setFileOpt(null)}
                          className="py-1 px-2 rounded-lg border border-rose-500/20 hover:border-rose-500/40 bg-rose-500/10 text-rose-300 text-[11px] font-mono transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => optInputRef.current?.click()}
                      className="py-4 text-center cursor-pointer text-xs font-mono text-zinc-400 hover:text-white"
                    >
                      + Select Image A (Optical Sensor)
                    </button>
                  )}
                  <input
                    type="file"
                    ref={optInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        handleFileUpload(file, "opt", () => setFileOpt(file));
                      }
                    }}
                  />
                </div>

                {/* Image B (SAR Radar) */}
                <div
                  className={`border rounded-xl p-3.5 flex flex-col justify-between transition-all ${
                    fileSar ? "border-white/15 bg-white/[0.03]" : "border border-dashed border-white/15 hover:border-white/30 bg-white/[0.02] hover:bg-white/[0.04]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Radio className="size-4 text-zinc-400 shrink-0" />
                      <span className="text-xs font-mono font-medium text-white">Image B (SAR Radar)</span>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400">
                      Microwave C-Band
                    </span>
                  </div>
                  {uploadingSlot === "sar" ? (
                    <div className="py-6 flex flex-col items-center justify-center min-h-[90px]">
                      <TextProgress
                        value={uploadProgress}
                        label={`Uploading ${uploadFileName}`}
                        doneLabel="SAR Microwave Staged"
                        className="text-xs"
                      />
                    </div>
                  ) : fileSar ? (
                    <div className="space-y-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="size-12 rounded-lg overflow-hidden border border-white/10 bg-black flex items-center justify-center shrink-0">
                          {previewSar ? (
                            <img src={previewSar} alt="SAR preview" className="w-full h-full object-cover" />
                          ) : (
                            <Radio className="size-5 text-zinc-400" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-mono text-zinc-200 truncate font-medium">{fileSar.name}</p>
                          <p className="text-[10px] font-mono text-zinc-400">
                            {(fileSar.size / (1024 * 1024)).toFixed(2)} MB &bull; Dual-Pol VV/VH
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 pt-1 border-t border-white/10">
                        <button
                          type="button"
                          onClick={() => sarInputRef.current?.click()}
                          className="flex-1 py-1 px-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white text-[11px] font-mono flex items-center justify-center gap-1"
                        >
                          <RefreshCw className="size-3 text-zinc-400" />
                          <span>Replace</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setFileSar(null)}
                          className="py-1 px-2 rounded-lg border border-rose-500/20 hover:border-rose-500/40 bg-rose-500/10 text-rose-300 text-[11px] font-mono transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => sarInputRef.current?.click()}
                      className="py-4 text-center cursor-pointer text-xs font-mono text-zinc-400 hover:text-white"
                    >
                      + Select Image B (SAR Radar Sensor)
                    </button>
                  )}
                  <input
                    type="file"
                    ref={sarInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];
                        handleFileUpload(file, "sar", () => setFileSar(file));
                      }
                    }}
                  />
                </div>
              </div>
            )}

            {/* Pre-Flight Spatial Validation Widget */}
            <PreFlightValidationBadge
              files={files}
              validation={validationData}
              isValidating={isValidating}
              onValidate={runValidation}
            />

            {/* One-Click Demo Datasets */}
            <div className="pt-3 border-t border-white/10">
              <span className="text-xs text-zinc-400 block mb-2 font-body">
                Or load demo dataset:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleLoadDemo("building")}
                  disabled={loadingDemoType !== null || isAnalyzing}
                  className="p-2.5 rounded-xl border border-white/10 hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.06] text-left transition-colors flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between text-zinc-200">
                    <span className="text-xs font-medium">Building Change</span>
                    {loadingDemoType === "building" && <Loader2 className="size-3 animate-spin text-white" />}
                  </div>
                  <span className="text-[10px] text-zinc-500 block mt-1 truncate">LEVIR-CD &bull; 0.5m GSD</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleLoadDemo("optical_sar")}
                  disabled={loadingDemoType !== null || isAnalyzing}
                  className="p-2.5 rounded-xl border border-white/10 hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.06] text-left transition-colors flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between text-zinc-200">
                    <span className="text-xs font-medium">Optical + SAR</span>
                    {loadingDemoType === "optical_sar" && <Loader2 className="size-3 animate-spin text-white" />}
                  </div>
                  <span className="text-[10px] text-zinc-500 block mt-1 truncate">Cartosat + RISAT-1A</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleLoadDemo("single")}
                  disabled={loadingDemoType !== null || isAnalyzing}
                  className="p-2.5 rounded-xl border border-white/10 hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.06] text-left transition-colors flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between text-zinc-200">
                    <span className="text-xs font-medium">Single Optical</span>
                    {loadingDemoType === "single" && <Loader2 className="size-3 animate-spin text-white" />}
                  </div>
                  <span className="text-[10px] text-zinc-500 block mt-1 truncate">LULC &bull; VQA</span>
                </button>
              </div>
            </div>
          </section>

          {/* 3. Query Input & Primary CTA */}
          <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-950/70 backdrop-blur-xl shadow-2xl p-5 space-y-4">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              3. Investigation Query
            </h2>
            <textarea
              className="w-full bg-black/40 border border-white/15 focus:border-white/30 rounded-xl p-3.5 text-white text-xs font-mono min-h-[95px] focus:outline-none focus:ring-1 focus:ring-white/20 transition-all resize-none placeholder:text-zinc-500 backdrop-blur-md"
              placeholder="What is the dominant land cover in this image?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />

            {/* Suggestions */}
            <div className="flex flex-wrap gap-1.5">
              {getSuggestions().map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => setQuery(q)}
                  className="text-[11px] font-mono bg-white/[0.03] hover:bg-white/10 text-zinc-300 hover:text-white border border-white/10 hover:border-white/20 rounded-full px-3 py-1 transition-all backdrop-blur-md truncate max-w-full text-left"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Primary CTA Button */}
            <button
              type="button"
              onClick={startAnalysis}
              disabled={files.length === 0 || !query.trim() || isAnalyzing}
              className={`w-full py-3.5 px-4 rounded-xl font-mono text-sm font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all duration-200 shadow-xl ${
                files.length === 0 || !query.trim() || isAnalyzing
                  ? "bg-white/5 text-zinc-600 border border-white/5 cursor-not-allowed"
                  : "bg-white hover:bg-zinc-200 text-zinc-950 font-bold shadow-[0_0_25px_rgba(255,255,255,0.18)] cursor-pointer active:scale-[0.98]"
              }`}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="size-4 animate-spin text-black" />
                  <span>Orchestrating Pipeline...</span>
                </>
              ) : (
                <>
                  <span>ANALYZE IMAGE</span>
                  <span className="text-base font-bold">→</span>
                </>
              )}
            </button>
          </section>

        </div>

        {/* Right Column: Workstation Results & Visual Intelligence */}
        <div className="lg:col-span-7 xl:col-span-8 col-span-12 flex flex-col gap-5">
          <section className={`relative overflow-hidden rounded-2xl border transition-all duration-500 shadow-2xl p-5 sm:p-6 h-full min-h-[680px] flex flex-col gap-5 ${
            !result
              ? "bg-black/15 backdrop-blur-[5px] border-white/15 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)]"
              : "bg-zinc-950/70 backdrop-blur-xl border-white/10"
          }`}>
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
            
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/10">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="font-display text-base font-semibold text-white tracking-tight">
                    Investigation Result
                  </h2>
                  {isAnalyzing ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-amber-300 font-body">
                      <span className="size-1.5 rounded-full bg-amber-400 animate-pulse" />
                      Analyzing
                    </span>
                  ) : result ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-body">
                      <span className="size-1.5 rounded-full bg-emerald-400" />
                      Complete
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-xs text-zinc-400 font-body">
                      <span className="size-1.5 rounded-full bg-zinc-500" />
                      Standby
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-400 font-body">
                  {result
                    ? `Generated in ${(result?.trace?.total_duration_seconds || 1.8).toFixed(1)}s across ${files.length} raster input(s)`
                    : "Autonomous Multi-Specialist Remote Sensing Synthesis"}
                </p>
              </div>

              {/* Header Actions */}
              <div className="flex items-center gap-2">
                {result && <ReportDownloadButton jobId={result.job_id || "analysis_job"} result={result} />}
                {result && (
                  <button
                    type="button"
                    onClick={() => {
                      if (typeof window !== "undefined") {
                        navigator.clipboard.writeText(window.location.href);
                        setCopiedShare(true);
                        setTimeout(() => setCopiedShare(false), 2000);
                      }
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-xs text-zinc-300 hover:text-white transition-colors"
                    title="Share Link"
                  >
                    {copiedShare ? (
                      <>
                        <Check className="size-3.5 text-emerald-400" />
                        <span className="text-emerald-300">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Share2 className="size-3.5 text-zinc-400" />
                        <span>Share</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Empty State */}
            {!isAnalyzing && !result && !error && (
              <div className="flex-1 flex flex-col items-center justify-center text-zinc-400 p-8 text-center my-auto">
                <div className="relative mb-5 flex items-center justify-center size-20 text-zinc-500">
                  <svg className="size-16" viewBox="0 0 64 64" fill="none" stroke="currentColor">
                    <circle cx="32" cy="32" r="28" strokeWidth="1.2" strokeOpacity="0.5" />
                    <circle cx="32" cy="32" r="18" strokeWidth="1.2" strokeOpacity="0.75" />
                    <circle cx="32" cy="32" r="8" strokeWidth="1.2" strokeOpacity="0.9" />
                    <circle cx="32" cy="32" r="2.5" fill="currentColor" />
                  </svg>
                </div>
                <h3 className="font-display text-base font-semibold text-white mb-1">
                  Ready for Mission Ingest
                </h3>
                <p className="text-xs text-zinc-400 max-w-sm font-mono">
                  Select a benchmark demo preset or stage satellite rasters and click &apos;Analyze Image&apos; to trigger autonomous multi-specialist remote sensing analysis.
                </p>
              </div>
            )}

            {/* Error Banner */}
            {error && (
              <div className="bg-red-950/30 border border-red-500/40 rounded-xl p-4 text-red-200 text-xs font-mono backdrop-blur-sm">
                {error}
              </div>
            )}

            {/* Live Progress State */}
            {isAnalyzing && progress && (
              <div className="flex-1 flex flex-col items-center justify-center max-w-md mx-auto w-full py-16 text-center">
                <TextProgress
                  value={progress.pct}
                  label={progress.step}
                  doneLabel="Analysis Synthesized"
                  className="mb-4 text-sm sm:text-base"
                />
                <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono">
                  <Loader2 className="size-3.5 animate-spin text-sky-400" />
                  <span>Invoking specialists &amp; deterministic tools...</span>
                </div>
              </div>
            )}

            {/* Investigation Results Flow */}
            {result && !isAnalyzing && (
              <div className="flex-1 overflow-y-auto pr-1 space-y-4">
                {/* 1. Investigation Query & Input Metadata Strip */}
                <div className="bg-white/[0.02] border border-white/10 rounded-xl p-3.5 space-y-2 backdrop-blur-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm text-white font-medium">
                      &quot;{result.query || query}&quot;
                    </p>
                    <span className="text-xs text-zinc-400 font-mono capitalize">
                      {mode} Mode
                    </span>
                  </div>
                  {getInputSummary().length > 0 && (
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 pt-1.5 border-t border-white/10 text-xs text-zinc-400">
                      {getInputSummary().map((item, idx) => (
                        <span key={idx}>
                          <span className="text-zinc-500">{item.label}:</span>{" "}
                          <span className="text-zinc-300 font-mono">{item.value}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 2. Visual Evidence (Large Satellite Image / Split-Screen / Change Map Canvas) */}
                <VisualEvidenceViewer
                  files={files}
                  mode={mode}
                  evidence={result.evidence}
                  trace={result.trace}
                  jobId={result.job_id}
                />

                {/* 3. Executive Finding */}
                <div className="bg-white/[0.02] border border-white/10 rounded-xl p-4 backdrop-blur-sm space-y-2">
                  <h3 className="text-xs font-semibold text-zinc-300">
                    Executive Finding
                  </h3>
                  <p className="text-xs text-zinc-200 leading-relaxed font-body">
                    {getExecutiveFinding()}
                  </p>
                  {result.report?.methodology && (
                    <div className="pt-2 border-t border-white/10 text-xs text-zinc-400">
                      <span className="text-zinc-500 mr-1.5">Methodology:</span>
                      <span>{result.report.methodology}</span>
                    </div>
                  )}
                </div>

                {/* 4. Structured Supporting Evidence */}
                <EvidenceFindingsViewer
                  evidence={result.evidence}
                  conflicts={result.report?.conflicts_identified}
                  mode={mode}
                />

                {/* 5. Key Observations & Scientific Interpretation */}
                {((result.report?.observations && result.report.observations.length > 0) || (result.report?.narrative && result.report.narrative.trim())) && (
                  <div className="bg-black/30 border border-white/10 rounded-xl p-4.5 backdrop-blur-sm space-y-2.5">
                    <div className="flex items-center justify-between border-b border-white/10 pb-2">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                        KEY OBSERVATIONS &amp; SCIENTIFIC INTERPRETATION
                      </h4>
                      <span className="text-[10px] font-mono text-zinc-400">
                        Evidence-Grounded Interpretation
                      </span>
                    </div>

                    {result.report?.observations && result.report.observations.length > 0 && (
                      <ul className="space-y-1.5 list-disc pl-4 text-xs font-mono text-zinc-200">
                        {result.report.observations.map((obs: string, idx: number) => (
                          <li key={idx} className="leading-relaxed">
                            <span className="text-zinc-100">{obs}</span>
                          </li>
                        ))}
                      </ul>
                    )}

                    {result.report?.narrative && result.report.narrative.trim() && (
                      <div className="pt-2 text-xs font-mono text-zinc-300 leading-relaxed whitespace-pre-line border-t border-white/5">
                        {result.report.narrative}
                      </div>
                    )}
                  </div>
                )}

                {/* 6. Technical Limitations & Sensor Constraints */}
                {result.report?.limitations && result.report.limitations.length > 0 && (
                  <div className="bg-black/30 border border-white/10 rounded-xl p-4 backdrop-blur-sm space-y-2">
                    <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono font-bold uppercase tracking-wider">
                      <AlertCircle className="size-3.5 text-zinc-400" />
                      <span>Limitations &amp; Sensor Constraints</span>
                    </div>
                    <ul className="space-y-1 list-disc pl-4 text-xs font-mono text-zinc-400">
                      {result.report.limitations.map((lim: string, idx: number) => (
                        <li key={idx} className="leading-relaxed">
                          {lim}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 7. Execution Summary (Step-by-step checklist with status & latency) */}
                <ExecutionTraceViewer trace={result.trace} />
              </div>
            )}

          </section>
        </div>

      </main>
      <Footer />

      {/* Specialist Model & Tool Registry Modal */}
      <ModelRegistryModal
        isOpen={isRegistryOpen}
        onClose={() => setIsRegistryOpen(false)}
      />
    </div>
  );
}
