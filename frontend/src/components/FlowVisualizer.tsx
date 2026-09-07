"use client";

import React, { useState } from "react";
import {
  FileCheck,
  Binary,
  BrainCircuit,
  CheckCircle2,
  AlertCircle,
  Clock,
  ChevronRight,
  FileText,
  Download,
  Eye,
  EyeOff,
  FileCode,
  Sparkles,
  Image as ImageIcon,
} from "lucide-react";
import { ProcessResponse, downloadMarkdownFile } from "@/lib/api";

interface FlowVisualizerProps {
  currentStep:
    | "idle"
    | "input"
    | "conversion"
    | "image_context"
    | "markdown_ready"
    | "ai_engine"
    | "output"
    | "completed"
    | "failed";
  lastResponse: ProcessResponse | null;
  mode: string;
  filesCount: number;
  isConverting?: boolean;
}

export const FlowVisualizer: React.FC<FlowVisualizerProps> = ({
  currentStep,
  lastResponse,
  mode,
  filesCount,
  isConverting = false,
}) => {
  const [expandedFileIdx, setExpandedFileIdx] = useState<number | null>(null);

  const steps = [
    {
      id: "input",
      label: "1. Input Ingestion",
      icon: FileCheck,
      desc: `${filesCount} file(s) attached (${mode} mode)`,
    },
    {
      id: "conversion",
      label: "2. Document Conversion",
      icon: Binary,
      desc: "Microsoft MarkItDown / Fallback",
    },
    {
      id: "image_context",
      label: "3. Image Context Analysis",
      icon: ImageIcon,
      desc: "Vision AI / PyTesseract OCR",
    },
    {
      id: "markdown_ready",
      label: "4. Canonical Markdown Ready",
      icon: FileCode,
      desc: ".md artifact with image context",
    },
    {
      id: "ai_engine",
      label: "5. AI Engine Processing",
      icon: BrainCircuit,
      desc: "PromptBuilder ➔ AIProvider",
    },
    {
      id: "output",
      label: "6. Text Output",
      icon: CheckCircle2,
      desc: "Grounded text response",
    },
  ];

  const stepOrder = ["input", "conversion", "image_context", "markdown_ready", "ai_engine", "output"];

  const getStepStatus = (stepId: string) => {
    if (currentStep === "failed") {
      const failedStep = lastResponse?.pipeline_step || "input";
      const failedIndex = stepOrder.indexOf(failedStep);
      const stepIndex = stepOrder.indexOf(stepId);

      if (stepIndex < failedIndex) return "completed";
      if (stepIndex === failedIndex) return "failed";
      return "idle";
    }

    if (currentStep === "idle") return "idle";
    if (currentStep === "completed") return "completed";

    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(stepId);

    if (stepIndex < currentIndex) return "completed";
    if (stepIndex === currentIndex) return "active";
    return "idle";
  };

  const handleDownloadItem = (conversionId?: string, fallbackFilename?: string, rawText?: string) => {
    if (conversionId) {
      downloadMarkdownFile(conversionId, fallbackFilename || "document.md");
    } else if (rawText) {
      const baseName = (fallbackFilename || "document.md").replace(/\.[^/.]+$/, "");
      const mdFilename = `${baseName}.md`;
      const blob = new Blob([rawText], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = mdFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#090d16] p-6 space-y-6 overflow-y-auto">
      <div className="flex items-center justify-between border-b border-surface-border pb-4">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-wide uppercase flex items-center gap-2">
            <span>Pipeline Flow Visualization</span>
          </h2>
          <p className="text-xs text-gray-400">
            Real-time execution state tracking for V1 engine
          </p>
        </div>

        {/* Status Chip */}
        <div className="flex items-center space-x-2">
          {currentStep === "idle" && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-gray-800 border border-gray-700 text-gray-400 text-xs font-mono">
              <Clock className="w-3.5 h-3.5" />
              <span>Pipeline Idle</span>
            </span>
          )}
          {stepOrder.includes(currentStep) && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-mono animate-pulse">
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              <span>Processing: {currentStep.toUpperCase()}</span>
            </span>
          )}
          {currentStep === "completed" && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Completed</span>
            </span>
          )}
          {currentStep === "failed" && (
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Execution Failed</span>
            </span>
          )}
        </div>
      </div>

      {/* Pipeline Flowchart Nodes */}
      <div className="flex flex-col space-y-3 my-auto">
        {steps.map((step, idx) => {
          const status = getStepStatus(step.id);
          const StepIcon = step.icon;

          return (
            <React.Fragment key={step.id}>
              <div
                className={`p-3.5 rounded-xl border transition-all duration-300 flex items-center justify-between ${
                  status === "active"
                    ? "bg-blue-950/40 border-blue-500/60 shadow-lg shadow-blue-500/10 translate-x-1"
                    : status === "completed"
                    ? "bg-surface border-emerald-500/30 text-gray-200"
                    : status === "failed"
                    ? "bg-rose-950/30 border-rose-500/50 text-rose-200"
                    : "bg-surface/40 border-surface-border text-gray-500 opacity-60"
                }`}
              >
                <div className="flex items-center space-x-3.5">
                  <div
                    className={`p-2.5 rounded-lg ${
                      status === "active"
                        ? "bg-blue-600 text-white animate-pulse"
                        : status === "completed"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : status === "failed"
                        ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        : "bg-gray-800 text-gray-400"
                    }`}
                  >
                    <StepIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold tracking-wide flex items-center gap-2">
                      <span>{step.label}</span>
                      {status === "completed" && (
                        <span className="text-[10px] text-emerald-400 font-mono">[Done]</span>
                      )}
                      {status === "active" && (
                        <span className="text-[10px] text-blue-400 font-mono animate-pulse">[Active]</span>
                      )}
                    </h3>
                    <p className="text-[11px] text-gray-400">{step.desc}</p>
                  </div>
                </div>

                <div className="text-xs font-mono">
                  {status === "completed" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {status === "active" && (
                    <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                  )}
                  {status === "failed" && <AlertCircle className="w-4 h-4 text-rose-400" />}
                </div>
              </div>

              {idx < steps.length - 1 && (
                <div className="flex justify-center my-0">
                  <ChevronRight className="w-4 h-4 text-gray-600 rotate-90" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Converted Markdown Download Section */}
      {((lastResponse?.conversions && lastResponse.conversions.length > 0) ||
        (lastResponse?.extracted_files && lastResponse.extracted_files.length > 0)) && (
        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-3 mt-auto">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <span className="flex items-center gap-1.5">
              <FileCode className="w-4 h-4 text-emerald-400" />
              <span>Generated Markdown Artifacts</span>
            </span>
            {lastResponse.source_markdown && (
              <button
                type="button"
                onClick={() => handleDownloadItem(undefined, "combined_source.md", lastResponse.source_markdown)}
                className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 px-2 py-1 rounded transition-colors"
                title="Download combined Markdown"
              >
                <Download className="w-3 h-3" />
                <span>Combined .md</span>
              </button>
            )}
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {(lastResponse.conversions || []).map((item, idx) => {
              const isExpanded = expandedFileIdx === idx;
              return (
                <div
                  key={idx}
                  className="rounded-lg bg-[#0d1322] border border-surface-border text-xs overflow-hidden"
                >
                  <div className="flex items-center justify-between p-2">
                    <div className="flex items-center space-x-2 truncate">
                      <FileText className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                      <span className="text-gray-300 font-medium truncate">{item.original_filename}</span>
                    </div>

                    <div className="flex items-center space-x-1.5 font-mono text-[10px]">
                      <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase font-semibold">
                        {item.extraction_method || "markitdown"}
                      </span>
                      {item.image_count !== undefined && item.image_count > 0 && (
                        <span className="px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30 text-[9px] flex items-center gap-1">
                          <ImageIcon className="w-2.5 h-2.5" />
                          <span>{item.images_analyzed ?? 0}/{item.image_count} imgs</span>
                        </span>
                      )}
                      {item.fallback_used && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px]">
                          FALLBACK
                        </span>
                      )}

                      {/* Download .md Button */}
                      <button
                        type="button"
                        onClick={() => handleDownloadItem(item.id, item.markdown_filename, item.text)}
                        className="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 transition-all"
                        title={`Download ${item.markdown_filename}`}
                      >
                        <Download className="w-3 h-3" />
                        <span>.md</span>
                      </button>

                      {/* Toggle Preview Button */}
                      {item.text && (
                        <button
                          type="button"
                          onClick={() => setExpandedFileIdx(isExpanded ? null : idx)}
                          className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
                          title={isExpanded ? "Hide Markdown preview" : "Preview Markdown content"}
                        >
                          {isExpanded ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Collapsible Markdown Preview */}
                  {isExpanded && item.text && (
                    <div className="p-3 bg-[#060911] border-t border-surface-border/50 text-[11px] font-mono text-gray-300 whitespace-pre-wrap max-h-40 overflow-y-auto leading-relaxed">
                      <div className="text-[10px] text-gray-500 mb-1 border-b border-gray-800 pb-1 font-semibold flex items-center justify-between">
                        <span>MARKDOWN CONTENT PREVIEW</span>
                        <span>{item.char_count} chars</span>
                      </div>
                      {item.text}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
