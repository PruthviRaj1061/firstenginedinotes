"use client";

import React, { useState } from "react";
import {
  Copy,
  Check,
  Trash2,
  Download,
  FileText,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { ProcessResponse } from "@/lib/api";

interface OutputPanelProps {
  response: ProcessResponse | null;
  onClear: () => void;
  isProcessing: boolean;
}

export const OutputPanel: React.FC<OutputPanelProps> = ({
  response,
  onClear,
  isProcessing,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (response?.content) {
      navigator.clipboard.writeText(response.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = (ext: "md" | "txt" = "md") => {
    if (response?.content) {
      const mime = ext === "md" ? "text/markdown;charset=utf-8" : "text/plain;charset=utf-8";
      const blob = new Blob([response.content], { type: mime });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ai-content-output-${Date.now()}.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  const textContent = response?.content || "";
  const charCount = textContent.length;
  const wordCount = textContent.trim() ? textContent.trim().split(/\s+/).length : 0;

  return (
    <div className="flex flex-col h-full bg-[#0d1322] border-l border-surface-border p-5 space-y-4">
      {/* Header & Controls */}
      <div className="flex items-center justify-between border-b border-surface-border pb-3">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-300">
            Generated Text Output
          </h2>
        </div>

        {/* Action Toolbar */}
        <div className="flex items-center space-x-1.5">
          <button
            type="button"
            onClick={handleCopy}
            disabled={!textContent}
            title="Copy to clipboard"
            className="p-2 rounded-lg bg-surface border border-surface-border text-gray-400 hover:text-white hover:border-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-xs flex items-center gap-1.5 font-medium"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Copy</span>
              </>
            )}
          </button>

          {/* Download .md Button */}
          <button
            type="button"
            onClick={() => handleDownload("md")}
            disabled={!textContent}
            title="Download output as Markdown file"
            className="p-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-xs flex items-center gap-1.5 font-medium"
          >
            <Download className="w-3.5 h-3.5" />
            <span>.md</span>
          </button>

          {/* Download .txt Button */}
          <button
            type="button"
            onClick={() => handleDownload("txt")}
            disabled={!textContent}
            title="Download output as text file"
            className="p-2 rounded-lg bg-surface border border-surface-border text-gray-400 hover:text-white hover:border-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-xs flex items-center gap-1.5 font-medium"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">.txt</span>
          </button>

          <button
            type="button"
            onClick={onClear}
            disabled={!textContent && !response?.error}
            title="Clear output"
            className="p-2 rounded-lg bg-surface border border-surface-border text-gray-400 hover:text-rose-400 hover:border-rose-500/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-xs flex items-center gap-1.5 font-medium"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        </div>
      </div>

      {/* Output Content Display Container */}
      <div className="flex-1 flex flex-col relative rounded-xl bg-[#090d16] border border-surface-border p-4 overflow-hidden">
        {isProcessing ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-3 text-gray-400">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs font-mono animate-pulse">Running AI Content Engine...</p>
          </div>
        ) : response?.error ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-3">
            <div className="p-3 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wide">
              Processing Failure
            </h3>
            <p className="text-xs text-gray-300 font-mono max-w-sm bg-rose-950/20 border border-rose-500/20 p-3 rounded-lg">
              {response.error}
            </p>
          </div>
        ) : textContent ? (
          <div className="flex-1 overflow-y-auto whitespace-pre-wrap font-mono text-xs text-gray-200 leading-relaxed pr-2">
            {textContent}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center space-y-2 text-gray-500">
            <Sparkles className="w-8 h-8 text-gray-600 mb-1" />
            <p className="text-xs font-medium">No output generated yet.</p>
            <p className="text-[11px] text-gray-600 max-w-xs">
              Select a mode, enter your prompt, attach content files, and click Process to run the pipeline.
            </p>
          </div>
        )}
      </div>

      {/* Footer Metrics */}
      <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 pt-1">
        <div className="flex items-center space-x-3">
          <span>Words: <strong className="text-gray-200">{wordCount}</strong></span>
          <span>Chars: <strong className="text-gray-200">{charCount}</strong></span>
        </div>

        {response?.mode && (
          <span className="px-2 py-0.5 rounded bg-surface border border-surface-border text-gray-300 uppercase text-[10px]">
            Mode: {response.mode}
          </span>
        )}
      </div>
    </div>
  );
};
