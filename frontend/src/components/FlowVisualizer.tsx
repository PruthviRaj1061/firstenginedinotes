"use client";

import React from "react";
import {
  FileCheck,
  Binary,
  BrainCircuit,
  CheckCircle2,
  AlertCircle,
  Clock,
  ChevronRight,
  Database,
  FileText,
} from "lucide-react";
import { ProcessResponse } from "@/lib/api";

interface FlowVisualizerProps {
  currentStep: "idle" | "input" | "extraction" | "ai_engine" | "output" | "completed" | "failed";
  lastResponse: ProcessResponse | null;
  mode: string;
  filesCount: number;
}

export const FlowVisualizer: React.FC<FlowVisualizerProps> = ({
  currentStep,
  lastResponse,
  mode,
  filesCount,
}) => {
  const steps = [
    {
      id: "input",
      label: "Input Ingestion",
      icon: FileCheck,
      desc: `${filesCount} file(s) attached (${mode} mode)`,
    },
    {
      id: "extraction",
      label: "Content Extraction",
      icon: Binary,
      desc: "PyMuPDF / DOCX / OCR Engine",
    },
    {
      id: "ai_engine",
      label: "AI Engine Processing",
      icon: BrainCircuit,
      desc: "PromptBuilder ➔ AIProvider",
    },
    {
      id: "output",
      label: "Text Output",
      icon: CheckCircle2,
      desc: "Grounded text response",
    },
  ];

  const getStepStatus = (stepId: string) => {
    const stepOrder = ["input", "extraction", "ai_engine", "output"];

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
          {["input", "extraction", "ai_engine", "output"].includes(currentStep) && (
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
      <div className="flex flex-col space-y-4 my-auto">
        {steps.map((step, idx) => {
          const status = getStepStatus(step.id);
          const StepIcon = step.icon;

          return (
            <React.Fragment key={step.id}>
              <div
                className={`p-4 rounded-xl border transition-all duration-300 flex items-center justify-between ${
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
                    <StepIcon className="w-5 h-5" />
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

      {/* Extracted Files Breakdown (if available) */}
      {lastResponse?.extracted_files && lastResponse.extracted_files.length > 0 && (
        <div className="p-4 rounded-xl bg-surface border border-surface-border space-y-2 mt-auto">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span>Extracted Source Metadata</span>
            </span>
            <span className="font-mono text-gray-500">
              {lastResponse.extracted_files.length} File(s)
            </span>
          </div>

          <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
            {lastResponse.extracted_files.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded-lg bg-[#0d1322] border border-surface-border text-xs"
              >
                <div className="flex items-center space-x-2 truncate">
                  <FileText className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                  <span className="text-gray-300 font-medium truncate">{file.filename}</span>
                </div>
                <div className="flex items-center space-x-2 font-mono text-[10px]">
                  <span className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
                    {file.file_type.toUpperCase()}
                  </span>
                  <span className="text-gray-400">{file.char_count} chars</span>
                  <span className="text-emerald-400">[{file.status}]</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
