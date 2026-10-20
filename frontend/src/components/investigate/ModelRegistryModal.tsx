"use client";

import React from "react";
import { X, Cpu, ShieldCheck, CheckCircle2, Wrench, Layers, Database, Sparkles } from "lucide-react";

interface ModelRegistryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ModelItem {
  id: string;
  specialist_kind: "LEARNED MODEL" | "LEARNED MODEL (PARTIAL ADAPTATION)";
  name: string;
  type: string;
  architecture: string;
  dataset: string;
  modality: string;
  metrics: string;
  description: string;
  status: "AVAILABLE" | "ACTIVE";
}

interface ToolItem {
  id: string;
  specialist_kind: "DETERMINISTIC TOOL";
  name: string;
  category: string;
  output: string;
  method: string;
}

const SPECIALIST_MODELS: ModelItem[] = [
  {
    id: "ben-scene-classifier",
    specialist_kind: "LEARNED MODEL",
    name: "BigEarthNet Scene Classifier (ResNet-50 v2)",
    type: "Multi-Label LULC Classification",
    architecture: "ResNet-50 (torchvision.models.resnet50) with nn.Linear(2048, 19)",
    dataset: "BigEarthNet v2.0 reBEN (480,038 tiles, 115 Sentinel-2 scenes)",
    modality: "Optical (12-Band MSI / RGB)",
    metrics: "Val Accuracy: 91.79%, Val Macro F1: 70.38% (Epoch 19). Test Accuracy: 91.67%, Test Macro F1: 65.15%.",
    description: "Evaluates 19 standardized CORINE Land Cover classes with calibrated sigmoid probabilities.",
    status: "AVAILABLE",
  },
  {
    id: "bit-change-detection",
    specialist_kind: "LEARNED MODEL",
    name: "Siamese BIT Change Detector",
    type: "Bi-Temporal Change Detection",
    architecture: "Bitemporal Image Transformer (BIT) with Siamese ResNet-18 backbone",
    dataset: "LEVIR-CD (1,280 bitemporal pairs)",
    modality: "Bi-Temporal Optical Pairs",
    metrics: "Overall Accuracy: 96.98%, F1 Score: 69.56%, IoU: 53.33% (10 epochs).",
    description: "Siamese dual-stream ResNet-18 generating binary change masks, pixel difference statistics, and spatial clusters.",
    status: "AVAILABLE",
  },
  {
    id: "rsvqa-specialist",
    specialist_kind: "LEARNED MODEL",
    name: "RSVQA Visual Question Answering Specialist",
    type: "Remote Sensing VQA",
    architecture: "RSVQA Reasoning Specialist conditioned on LULC context",
    dataset: "RSVQA LR & HR (167,667 question-answer pairs)",
    modality: "Optical High / Low Res",
    metrics: "Validation accuracy: Metric not currently verified (Domain coverage: Presence, Count, Rural/Urban, Comparison).",
    description: "Answers presence, comparison, rural vs urban, and spatial structure queries conditioned on land cover.",
    status: "AVAILABLE",
  },
  {
    id: "vrsbench-caption",
    specialist_kind: "LEARNED MODEL",
    name: "VRSBench Scene Captioner",
    type: "Fine-Grained Scene Description",
    architecture: "VRSBench Fine-Grained Scene Description Specialist",
    dataset: "VRSBench Captioning (9,350 image-caption pairs)",
    modality: "High-Resolution Optical",
    metrics: "Validation accuracy: Metric not currently verified.",
    description: "Synthesizes multi-sentence descriptions capturing land morphology, structures, and environmental patterns.",
    status: "AVAILABLE",
  },
  {
    id: "vrsbench-grounding",
    specialist_kind: "LEARNED MODEL",
    name: "Text-Guided Spatial Localization Specialist (VRSBench)",
    type: "Referring Expression Target Localization",
    architecture: "Text-Guided Spatial Target Localization Specialist",
    dataset: "VRSBench Referring Expressions (16,159 annotated bounding boxes)",
    modality: "High-Resolution Optical",
    metrics: "Validation accuracy: Metric not currently verified.",
    description: "Resolves natural-language spatial queries into normalized bounding boxes [ymin, xmin, ymax, xmax].",
    status: "AVAILABLE",
  },
  {
    id: "cdvqa-specialist",
    specialist_kind: "LEARNED MODEL",
    name: "CDVQA Change-VQA Specialist",
    type: "Change-Grounded Question Answering",
    architecture: "Change-grounded VQA fusing BIT change masks with ResNet-50 delta LULC shifts",
    dataset: "CDVQA (2,968 bitemporal pairs)",
    modality: "Bi-Temporal Optical Pairs",
    metrics: "Validation accuracy: Metric evaluated on sample validation split (80.0%).",
    description: "Fuses Siamese BIT change masks with ResNet-50 delta LULC distributions to answer change queries.",
    status: "AVAILABLE",
  },
  {
    id: "cross-modal-specialist",
    specialist_kind: "LEARNED MODEL",
    name: "Optical + SAR Cross-Modal Reasoning Specialist",
    type: "Optical + SAR Physical Fusion",
    architecture: "Dual Physical Encoder (Optical Reflectance vs. Microwave Backscatter dB)",
    dataset: "BigEarthNet S1/S2 Paired (480k pairs) + Cartosat-2S & RISAT-1A",
    modality: "Optical + Microwave SAR",
    metrics: "Physical conflict detection accuracy: Metric not currently verified.",
    description: "Separates surface solar reflectance from radar microwave backscatter (dB) and detects physical contradictions.",
    status: "AVAILABLE",
  },
  {
    id: "rs-vlm-adapter",
    specialist_kind: "LEARNED MODEL (PARTIAL ADAPTATION)",
    name: "Remote Sensing VLM (BLIP LoRA Adapter)",
    type: "Multimodal Vision-Language Adaptation",
    architecture: "Salesforce/blip-image-captioning-base + PEFT LoRA (r=16, alpha=32)",
    dataset: "BigEarthNet.txt (464,044 image-text pairs)",
    modality: "Optical Multispectral + Text",
    metrics: "Exact Match (50-sample bench): 44.0%, Binary EM: 70.8%, MCQ EM: 25.0% (1,000 steps).",
    description: "Fine-tuned LoRA adapter for remote sensing terminology, binary verification, and scene grounding.",
    status: "AVAILABLE",
  },
];

const DETERMINISTIC_TOOLS: ToolItem[] = [
  {
    id: "raster-metadata",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Raster Metadata Inspector",
    category: "Geospatial Gateway",
    output: "CRS, EPSG, Affine Transform, Extent, GSD",
    method: "Deterministic Metadata Extraction",
  },
  {
    id: "raster-stats",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Band Statistics Calculator",
    category: "Spectral Analysis",
    output: "Min, Max, Mean, Std, P2, P98 per band",
    method: "Deterministic Numerical Array Statistics",
  },
  {
    id: "sar-stats",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "SAR Backscatter Analyzer",
    category: "Radar Metrology",
    output: "Calibrated dB backscatter, roughness, dynamic range",
    method: "Calibrated Physical Radar Equation",
  },
  {
    id: "ndvi-calculator",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "NDVI Calculator",
    category: "Vegetation Metrology",
    output: "Normalized Difference (NIR-Red)/(NIR+Red)",
    method: "Direct Spectral Band Arithmetic",
  },
  {
    id: "area-calculator",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Mask Surface Area Calculator",
    category: "Spatial Quantification",
    output: "Surface area in m², km², and hectares",
    method: "Deterministic Area: pixel_count × GSD²",
  },
  {
    id: "bbox-area-calculator",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Bounding Box Area Tool",
    category: "Spatial Quantification",
    output: "Geodesic or pixel bounding box area",
    method: "Deterministic Coordinate Box Geometry",
  },
  {
    id: "polygon-area-calculator",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "WGS84 Geodesic Polygon Tool",
    category: "Geodesic Geometry",
    output: "Spherical Earth surface area via Shapely & PyProj",
    method: "WGS84 Ellipsoidal Geodesic Calculation",
  },
  {
    id: "geodesic-distance-calculator",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Geodesic Distance Tool",
    category: "Geodesic Geometry",
    output: "Great-circle distance in meters and kilometers",
    method: "PyProj Great-Circle Geodesic",
  },
  {
    id: "change-area",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Temporal Change Quantification",
    category: "Bi-Temporal Metrology",
    output: "Changed surface area in m² and hectares",
    method: "Deterministic Pixel Aggregation from Mask",
  },
  {
    id: "mask-overlay",
    specialist_kind: "DETERMINISTIC TOOL",
    name: "Visual Mask Overlay Renderer",
    category: "Cartographic Rendering",
    output: "Alpha-blended composite raster visualization",
    method: "Alpha-Blended Mask Composite",
  },
];

export default function ModelRegistryModal({ isOpen, onClose }: ModelRegistryModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-xl animate-in fade-in duration-200">
      <div 
        className="bg-zinc-950/95 border border-white/15 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-body"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-white/10 flex items-center justify-between bg-white/5">
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <Cpu className="size-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="font-display text-lg font-bold text-white tracking-tight">
                Model &amp; Tool Specialist Registry
              </h2>
              <p className="text-xs text-zinc-400 font-mono">
                SIH26167 Agentic Multi-Specialist Architecture • Learned Models &amp; Deterministic Tools
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="size-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-400 hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          {/* Architectural Invariant Banner */}
          <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4 flex items-start gap-3">
            <ShieldCheck className="size-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-300 mb-1">
                Deterministic Geospatial Calculation Architecture
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed">
                The Gemini Agentic Orchestrator performs plan synthesis and routing. All quantitative calculations (area in hectares, NDVI, distances, backscatter dB) are strictly executed outside the language model by deterministic geospatial tools carrying calculation_status: DETERMINISTIC. Spatial arithmetic calculations are deterministic from the input rasters and generated change masks, distinct from upstream neural network perception uncertainty.
              </p>
            </div>
          </div>

          {/* Section 1: Specialist Learned AI Models */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="size-4 text-cyan-400" />
                <h3 className="text-sm font-mono font-semibold uppercase tracking-wider text-white">
                  Learned Specialist Models ({SPECIALIST_MODELS.length})
                </h3>
              </div>
              <span className="text-[11px] font-mono text-cyan-300 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-full">
                LEARNED MODELS
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {SPECIALIST_MODELS.map((model) => (
                <div
                  key={model.id}
                  className="bg-black/40 border border-white/10 rounded-xl p-4 hover:border-cyan-500/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5 gap-2">
                      <span className="text-xs font-mono font-bold text-white tracking-wide">
                        {model.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 shrink-0">
                        {model.specialist_kind}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-cyan-400 mb-2">
                      {model.type} • {model.architecture}
                    </div>
                    <p className="text-xs text-zinc-300 mb-2 leading-relaxed">
                      {model.description}
                    </p>
                    <div className="bg-white/5 border border-white/5 rounded-lg p-2 mb-2 text-[10px] font-mono text-emerald-300">
                      <strong>Verified Metrics:</strong> {model.metrics}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between text-[10px] font-mono text-zinc-400">
                    <span className="text-zinc-500">Benchmark: {model.dataset}</span>
                    <span className="text-zinc-300">{model.modality}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Deterministic Geospatial Tools */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Wrench className="size-4 text-emerald-400" />
                <h3 className="text-sm font-mono font-semibold uppercase tracking-wider text-white">
                  Deterministic Geospatial Tools ({DETERMINISTIC_TOOLS.length})
                </h3>
              </div>
              <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full font-bold">
                CALCULATION STATUS: DETERMINISTIC
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {DETERMINISTIC_TOOLS.map((tool) => (
                <div
                  key={tool.id}
                  className="bg-black/40 border border-white/10 rounded-xl p-4 hover:border-emerald-500/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5 gap-2">
                      <span className="text-xs font-mono font-semibold text-white">
                        {tool.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 shrink-0 font-bold">
                        {tool.specialist_kind}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 mb-2">
                      <span className="text-zinc-500">Computes: </span>{tool.output}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-emerald-400/90">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="size-3" />
                      {tool.method}
                    </span>
                    <span className="text-zinc-600">{tool.id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-white/10 bg-white/5 flex items-center justify-between">
          <span className="text-xs text-zinc-500 font-mono">
            Astra AI • Space Applications Centre (SAC / ISRO) Compatible
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-body font-semibold bg-white text-black hover:bg-zinc-200 transition-colors"
          >
            Close Registry
          </button>
        </div>
      </div>
    </div>
  );
}
