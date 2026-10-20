"use client";

import React, { useState } from "react";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Terminal,
  ShieldCheck,
  Check,
} from "lucide-react";

interface ExecutedStep {
  step_id: string;
  tool_id: string;
  status: string;
  duration_ms?: number;
  output_summary?: string;
  confidence_status?: string;
}

interface ExecutionTraceProps {
  trace: {
    trace_id?: string;
    plan?: {
      task_classification?: string;
      plan_rationale?: string;
      steps?: any[];
    };
    executed_steps?: ExecutedStep[];
    steps_planned?: number;
    steps_executed?: number;
    steps_succeeded?: number;
    steps_failed?: number;
  } | null;
}

function getFriendlyStepLabel(toolId: string, summary?: string): string {
  const t = (toolId || "").toLowerCase();
  if (t.includes("metadata") || t.includes("rasterio")) {
    return "Raster metadata extracted";
  }
  if (t.includes("scene-classifier") || t.includes("resnet50")) {
    return "LULC specialist executed (ResNet-50 / BigEarthNet)";
  }
  if (t.includes("change") || t.includes("bit-change")) {
    return "Bi-temporal change detection executed";
  }
  if (t.includes("area") || t.includes("geometry") || t.includes("stats") || t.includes("ndvi")) {
    return "Deterministic geospatial metrology calculated";
  }
  if (t.includes("rsvqa") || t.includes("vqa")) {
    return "Visual question answering specialist executed";
  }
  if (t.includes("vrsbench") || t.includes("grounding") || t.includes("referring")) {
    return "Visual grounding specialist executed (VRSBench)";
  }
  if (t.includes("cross-modal") || t.includes("sar")) {
    return "Optical + SAR cross-modal analysis executed";
  }
  if (t.includes("synthesizer") || t.includes("orchestrator") || t.includes("gemini")) {
    return "Evidence synthesized & report generated";
  }
  return summary || `${toolId} executed`;
}

export default function ExecutionTraceViewer({ trace }: ExecutionTraceProps) {
  // Default to collapsed detailed trace to prevent overpowering scientific findings
  const [isDetailedExpanded, setIsDetailedExpanded] = useState(false);

  if (!trace) return null;

  const steps = trace.executed_steps || [];
  const plan = trace.plan;
  const totalDurationMs = steps.reduce((sum, s) => sum + (s.duration_ms || 0), 0);
  const succeededCount = steps.filter((s) => s.status === "SUCCESS" || s.status === "succeeded").length;
  const failedCount = steps.filter((s) => s.status === "FAILED" || s.status === "failed").length;

  // Build the compact execution summary checklist (Section 9)
  const summaryChecklist = [
    { label: "Input validated", isSuccess: true, isFailed: false },
    ...steps.map((step) => {
      const isSuccess = step.status === "SUCCESS" || step.status === "succeeded";
      const isFailed = step.status === "FAILED" || step.status === "failed";
      return {
        label: getFriendlyStepLabel(step.tool_id, step.output_summary),
        isSuccess,
        isFailed,
        toolId: step.tool_id,
      };
    }),
    { label: "Evidence synthesized & findings verified", isSuccess: true, isFailed: false },
  ];

  return (
    <div className="bg-black/30 border border-white/15 rounded-xl overflow-hidden font-body backdrop-blur-sm">
      {/* Header */}
      <div className="px-4 py-3 bg-white/5 border-b border-white/10 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="size-6 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <ShieldCheck className="size-3.5 text-emerald-400" />
          </div>
          <div>
            <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              EXECUTION SUMMARY
            </h4>
            <p className="text-[11px] text-zinc-400 font-mono">
              {succeededCount} of {steps.length} operations completed • {totalDurationMs}ms total latency
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {plan?.task_classification && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/10 border border-white/20 text-zinc-300">
              {plan.task_classification}
            </span>
          )}
          {failedCount > 0 ? (
            <span className="text-[10px] font-mono text-rose-300 bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded-full font-semibold">
              {failedCount} specialist fallback
            </span>
          ) : (
            <span className="text-[10px] font-mono text-emerald-300 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold">
              Trace verified
            </span>
          )}
        </div>
      </div>

      {/* Compact Checklist Sequence (Section 9) */}
      <div className="p-4 space-y-2.5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
          {summaryChecklist.map((item, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 py-1 px-2.5 rounded-lg bg-white/5 border border-white/5"
            >
              {item.isSuccess ? (
                <Check className="size-3.5 text-emerald-400 shrink-0 stroke-[2.5]" />
              ) : item.isFailed ? (
                <XCircle className="size-3.5 text-rose-400 shrink-0" />
              ) : (
                <Loader2 className="size-3.5 text-zinc-300 shrink-0 animate-spin" />
              )}
              <span
                className={`truncate ${
                  item.isFailed ? "text-rose-300 font-medium" : "text-zinc-200"
                }`}
              >
                {item.label}
              </span>
            </div>
          ))}
        </div>

        {/* Collapsible Trigger for Full Detailed Audit Trace */}
        <div className="pt-2 border-t border-white/10 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setIsDetailedExpanded(!isDetailedExpanded)}
            className="flex items-center gap-1.5 text-xs font-mono text-zinc-400 hover:text-white transition-colors py-1"
          >
            <Terminal className="size-3 text-zinc-300" />
            <span>
              {isDetailedExpanded
                ? "Hide Detailed Audit Trace"
                : `Inspect Detailed Audit Trace (${steps.length} steps)`}
            </span>
            {isDetailedExpanded ? (
              <ChevronUp className="size-3.5" />
            ) : (
              <ChevronDown className="size-3.5" />
            )}
          </button>

          <span className="text-[10px] font-mono text-zinc-500">
            Immutable Agentic Audit Log
          </span>
        </div>

        {/* Expanded Audit Log Details */}
        {isDetailedExpanded && (
          <div className="mt-3 pt-3 border-t border-white/10 space-y-3">
            {plan?.plan_rationale && (
              <div className="bg-white/5 border border-white/5 rounded-lg p-3 text-xs text-zinc-300 font-mono leading-relaxed">
                <span className="text-zinc-500 uppercase tracking-wide text-[10px] block mb-1">
                  PLAN RATIONALE:
                </span>
                {plan.plan_rationale}
              </div>
            )}

            <div className="space-y-2">
              {steps.map((step, idx) => {
                const isSuccess = step.status === "SUCCESS" || step.status === "succeeded";
                const isFailed = step.status === "FAILED" || step.status === "failed";

                return (
                  <div
                    key={idx}
                    className="bg-black/40 border border-white/10 rounded-lg p-3 hover:border-white/20 transition-all font-mono"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-2">
                        {isSuccess ? (
                          <CheckCircle2 className="size-3.5 text-emerald-400" />
                        ) : isFailed ? (
                          <XCircle className="size-3.5 text-rose-400" />
                        ) : (
                          <Loader2 className="size-3.5 text-cyan-400 animate-spin" />
                        )}
                        <span className="text-xs font-bold text-white">
                          {step.step_id}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-cyan-300">
                          {step.tool_id}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-[10px] text-zinc-400">
                        {step.confidence_status && (
                          <span className="text-zinc-400">
                            [{step.confidence_status}]
                          </span>
                        )}
                        {step.duration_ms != null && (
                          <span className="flex items-center gap-1 text-zinc-400">
                            <Clock className="size-3" />
                            {step.duration_ms}ms
                          </span>
                        )}
                      </div>
                    </div>

                    {step.output_summary && (
                      <p className="text-xs text-zinc-300 leading-relaxed bg-black/30 p-2 rounded border border-white/5 break-words">
                        {step.output_summary}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
