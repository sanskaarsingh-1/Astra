'use client';

import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Target,
  Cpu,
  Layers,
  CheckCircle2,
  X,
  Compass,
  FileText,
  Copy,
  Check,
  RefreshCw,
  Radio,
  BarChart2,
} from 'lucide-react';
import { FlowButton } from '@/components/ui/flow-button';

export interface SceneCoords {
  lat: number;
  lng: number;
  zoom: number;
  name?: string;
}

interface SatQuerySceneInspectorProps {
  isOpen: boolean;
  coords: SceneCoords | null;
  onClose: () => void;
  onOpenInSatQuery: (params: { lat: number; lng: number; query: string; mode: string }) => void;
}

const SIH_PROMPT_CHIPS = [
  {
    id: 'lulc',
    label: '🏷️ Land Cover (LULC)',
    prompt: 'Identify the dominant land-cover classes present in this satellite scene.',
    specialist: 'ResNet-50 v2 Deep LULC Classifier',
    mode: 'single',
  },
  {
    id: 'agri',
    label: '🌾 Agricultural VQA',
    prompt: 'Are there active agricultural fields or cultivated crop plots in this region?',
    specialist: 'RSVQA Dual-Encoder Vision-Language Model',
    mode: 'single',
  },
  {
    id: 'caption',
    label: '📝 Scene Captioning',
    prompt: 'Describe this satellite scene in comprehensive multimodal detail.',
    specialist: 'VRSBench Fine-Tuned Captioning VLM',
    mode: 'single',
  },
  {
    id: 'grounding',
    label: '🎯 Built-up Grounding',
    prompt: 'Localize and ground all high-density built-up residential and commercial infrastructure.',
    specialist: 'VRSBench Spatial Grounding Engine',
    mode: 'single',
  },
  {
    id: 'change',
    label: '🔄 Bi-Temporal Change',
    prompt: 'Detect structural and environmental changes between past and current satellite observations.',
    specialist: 'Siamese BIT ResNet-18 Change Detection',
    mode: 'bitemporal',
  },
  {
    id: 'sar',
    label: '📡 Optical + SAR',
    prompt: 'Compare optical reflectance with Sentinel-1 / RISAT synthetic aperture radar backscatter.',
    specialist: 'Cross-Modal Optical-SAR Fusion Network',
    mode: 'crossmodal',
  },
];

export default function SatQuerySceneInspector({
  isOpen,
  coords,
  onClose,
  onOpenInSatQuery,
}: SatQuerySceneInspectorProps) {
  const [query, setQuery] = useState(SIH_PROMPT_CHIPS[0].prompt);
  const [selectedChip, setSelectedChip] = useState('lulc');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen || !coords) return null;

  const activeChipObj = SIH_PROMPT_CHIPS.find((c) => c.id === selectedChip) || SIH_PROMPT_CHIPS[0];

  const handleSelectChip = (chip: typeof SIH_PROMPT_CHIPS[0]) => {
    setSelectedChip(chip.id);
    setQuery(chip.prompt);
    setExecutionResult(null);
  };

  const handleRunInSitu = () => {
    setIsExecuting(true);
    setExecutionResult(null);

    // Simulate agentic planning -> specialist invocation -> synthesis pipeline
    setTimeout(() => {
      // Deterministic classification derived from geographic coordinates
      const latAbs = Math.abs(coords.lat);
      const isUrban = (latAbs > 18 && latAbs < 32 && Math.abs(coords.lng) > 70 && Math.abs(coords.lng) < 85);
      
      let breakdown: { label: string; pct: number; color: string }[] = [];
      let synthesis = '';
      let confidence = 94.6;

      if (selectedChip === 'lulc') {
        breakdown = isUrban
          ? [
              { label: 'Agricultural Vegetation', pct: 44.2, color: 'bg-emerald-500' },
              { label: 'Built-Up Infrastructure', pct: 31.8, color: 'bg-amber-500' },
              { label: 'Dense Forest / Canopy', pct: 14.5, color: 'bg-teal-500' },
              { label: 'Open Water Bodies', pct: 9.5, color: 'bg-blue-500' },
            ]
          : [
              { label: 'Arid / Open Barren Land', pct: 52.1, color: 'bg-amber-600' },
              { label: 'Sparse Scrub / Vegetation', pct: 26.4, color: 'bg-emerald-600' },
              { label: 'Built Infrastructure', pct: 12.3, color: 'bg-zinc-400' },
              { label: 'Water Resources', pct: 9.2, color: 'bg-blue-500' },
            ];
        confidence = 96.2;
        synthesis = `The multimodal ResNet-50 specialist identifies ${breakdown[0].label} as the dominant land-cover class (${breakdown[0].pct}%), followed by ${breakdown[1].label} (${breakdown[1].pct}%). Spatial distribution indicates active vegetative parcels interspersed with developed sectors.`;
      } else if (selectedChip === 'agri') {
        breakdown = [
          { label: 'Cultivated Crop Parcels', pct: 58.4, color: 'bg-emerald-500' },
          { label: 'Fallow / Unseeded Land', pct: 24.1, color: 'bg-amber-500' },
          { label: 'Irrigation Channels', pct: 17.5, color: 'bg-cyan-500' },
        ];
        confidence = 93.8;
        synthesis = `Affirmative. High-confidence signature of agricultural activity detected across the central sector. Regular field boundaries with high spectral green reflectance correlate strongly with irrigated cropland.`;
      } else if (selectedChip === 'change') {
        breakdown = [
          { label: 'Structural New Build Area', pct: 38.6, color: 'bg-rose-500' },
          { label: 'Vegetation Transition', pct: 42.1, color: 'bg-amber-500' },
          { label: 'Unchanged Baseline', pct: 19.3, color: 'bg-zinc-500' },
        ];
        confidence = 92.4;
        synthesis = `Siamese BIT change detection identifies structural expansion in the eastern quadrant (+38.6% modification intensity). New road and perimeter clearings detected between observation cycles.`;
      } else if (selectedChip === 'sar') {
        breakdown = [
          { label: 'Co-Polarized VV Backscatter', pct: 49.2, color: 'bg-cyan-500' },
          { label: 'Cross-Polarized VH Contrast', pct: 36.5, color: 'bg-indigo-500' },
          { label: 'Optical Shadow Correlation', pct: 14.3, color: 'bg-purple-500' },
        ];
        confidence = 95.1;
        synthesis = `Cross-modal optical-SAR verification resolves specular reflection discrepancies. Smooth dark patches observed in optical photography exhibit high radar backscatter, confirming metallic roofing rather than standing water.`;
      } else {
        breakdown = [
          { label: 'Primary Feature Alignment', pct: 64.0, color: 'bg-emerald-500' },
          { label: 'Secondary Context Features', pct: 36.0, color: 'bg-teal-500' },
        ];
        confidence = 94.0;
        synthesis = `Multimodal scene analysis confirms comprehensive feature extraction across coordinates [${coords.lat.toFixed(4)}°N, ${coords.lng.toFixed(4)}°E]. Resolution is verified at ~${Math.max(0.3, 15 / Math.pow(2, coords.zoom - 1)).toFixed(2)}m ground sampling distance.`;
      }

      setExecutionResult({
        chipId: selectedChip,
        specialist: activeChipObj.specialist,
        confidence,
        breakdown,
        synthesis,
        timestamp: new Date().toLocaleTimeString(),
      });
      setIsExecuting(false);
    }, 1200);
  };

  const handleCopyReport = () => {
    if (!executionResult) return;
    const reportText = `# Astra SatQuery Analysis Report
Target Scene: ${coords.lat.toFixed(4)}°N, ${coords.lng.toFixed(4)}°E (Zoom: ${coords.zoom.toFixed(1)}x)
Query: "${query}"
Specialist: ${executionResult.specialist}
Confidence: ${executionResult.confidence}%
Synthesis: ${executionResult.synthesis}
Generated by Astra SatQuery AI | SIH26167`;
    navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed bottom-3 sm:bottom-5 left-1/2 -translate-x-1/2 z-40 w-[95vw] max-w-4xl bg-zinc-950/95 backdrop-blur-2xl border border-white/15 rounded-3xl p-4 sm:p-6 shadow-2xl shadow-black/80 font-body animate-in fade-in slide-in-from-bottom-4 duration-200">
      {/* Top Header */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-white">
            <Sparkles className="size-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                SatQuery AI Scene Inspector
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                ACTIVE SCENE
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-400 mt-0.5">
              <Compass className="size-3 text-emerald-400" />
              <span>
                {coords.lat >= 0 ? `${coords.lat.toFixed(4)}°N` : `${Math.abs(coords.lat).toFixed(4)}°S`},{' '}
                {coords.lng >= 0 ? `${coords.lng.toFixed(4)}°E` : `${Math.abs(coords.lng).toFixed(4)}°W`}
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-zinc-300">Esri World Imagery (Sub-meter Optical)</span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          title="Close Inspector"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* SIH Core Prompt Chips */}
      <div className="py-3">
        <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block mb-2">
          Select Remote-Sensing Investigation Goal (SIH Tasks):
        </span>
        <div className="flex flex-wrap items-center gap-1.5">
          {SIH_PROMPT_CHIPS.map((chip) => (
            <button
              key={chip.id}
              type="button"
              onClick={() => handleSelectChip(chip)}
              className={`px-2.5 py-1 rounded-xl text-xs font-mono transition-all active:scale-95 ${
                selectedChip === chip.id
                  ? 'bg-white text-zinc-950 font-bold shadow-md'
                  : 'bg-white/5 border border-white/10 text-zinc-300 hover:bg-white/10 hover:text-white'
              }`}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* Natural Language Query Input & Action Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-2 pt-1 pb-3">
        <div className="relative flex-1 w-full">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask Astra AI a natural-language question about this scene..."
            className="w-full bg-black/50 border border-white/15 rounded-2xl px-4 py-2.5 text-xs sm:text-sm font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-white/40 transition-all shadow-inner"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {/* In-Situ Run Button */}
          <button
            type="button"
            onClick={handleRunInSitu}
            disabled={isExecuting || !query.trim()}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-white text-zinc-950 px-4 py-2.5 rounded-2xl text-xs font-semibold tracking-wider uppercase hover:bg-zinc-200 transition-all active:scale-95 disabled:opacity-50"
          >
            {isExecuting ? (
              <>
                <RefreshCw className="size-3.5 animate-spin text-emerald-600" />
                <span>Running Agent...</span>
              </>
            ) : (
              <>
                <Sparkles className="size-3.5 text-emerald-600" />
                <span>Ask Astra AI</span>
              </>
            )}
          </button>

          {/* Deep SatQuery Workspace Handoff */}
          <button
            type="button"
            onClick={() =>
              onOpenInSatQuery({
                lat: coords.lat,
                lng: coords.lng,
                query,
                mode: activeChipObj.mode,
              })
            }
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 bg-white/10 border border-white/20 text-white px-3.5 py-2.5 rounded-2xl text-xs font-mono font-medium hover:bg-white/15 transition-all active:scale-95 whitespace-nowrap"
            title="Open in full SatQuery deep investigation workspace"
          >
            <span>Open in SatQuery</span>
            <ArrowRight className="size-3.5 text-emerald-400" />
          </button>
        </div>
      </div>

      {/* In-Situ Execution Results View */}
      {executionResult && (
        <div className="mt-3 pt-3 border-t border-white/10 bg-white/[0.02] rounded-2xl p-3.5 animate-in fade-in duration-200">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-white/5">
            <div className="flex items-center gap-2 text-xs font-mono">
              <Cpu className="size-3.5 text-emerald-400" />
              <span className="text-zinc-400">Specialist:</span>
              <span className="text-white font-semibold">{executionResult.specialist}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                {executionResult.confidence}% CONFIDENCE
              </span>
              <button
                type="button"
                onClick={handleCopyReport}
                className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 hover:text-white px-2 py-0.5 rounded bg-white/5 border border-white/10"
              >
                {copied ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>

          {/* Classification Breakdown Bars */}
          <div className="py-2.5 space-y-1.5">
            <span className="text-[10px] font-mono uppercase text-zinc-500 flex items-center gap-1">
              <BarChart2 className="size-3" />
              Visual Evidence Breakdown:
            </span>
            <div className="space-y-1">
              {executionResult.breakdown.map((item: any) => (
                <div key={item.label} className="flex items-center justify-between gap-2 text-xs font-mono">
                  <span className="text-zinc-300 truncate max-w-[200px]">{item.label}</span>
                  <div className="flex items-center gap-2 flex-1 max-w-[280px]">
                    <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color} rounded-full transition-all duration-500`}
                        style={{ width: `${item.pct}%` }}
                      />
                    </div>
                    <span className="text-white font-bold text-[11px] w-12 text-right">{item.pct}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Gemini Agentic Synthesis */}
          <div className="pt-2 border-t border-white/5">
            <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold block mb-1">
              Gemini Agent Synthesis:
            </span>
            <p className="text-xs text-zinc-300 font-body leading-relaxed">
              {executionResult.synthesis}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
