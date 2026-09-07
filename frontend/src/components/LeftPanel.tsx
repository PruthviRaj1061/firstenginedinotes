"use client";

import React, { useRef } from "react";
import {
  ShieldAlert,
  Sparkles,
  FileText,
  UploadCloud,
  File,
  X,
  Play,
  Download,
  CheckCircle2,
  Loader2,
  Image as ImageIcon,
} from "lucide-react";
import { ConversionItem } from "@/lib/api";

export type ModeType = "strict" | "non-strict" | "scratch";

interface LeftPanelProps {
  mode: ModeType;
  setMode: (m: ModeType) => void;
  prompt: string;
  setPrompt: (p: string) => void;
  files: File[];
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
  conversions: ConversionItem[];
  combinedConversionId?: string;
  isConverting: boolean;
  onProcess: () => void;
  isProcessing: boolean;
  onDownloadMarkdown: (conversionId: string, filename: string) => void;
}

const SUPPORTED_EXTS = [".txt", ".md", ".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp"];

export const LeftPanel: React.FC<LeftPanelProps> = ({
  mode,
  setMode,
  prompt,
  setPrompt,
  files,
  setFiles,
  conversions,
  combinedConversionId,
  isConverting,
  onProcess,
  isProcessing,
  onDownloadMarkdown,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      addFiles(selected);
    }
  };

  const addFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter((file) => {
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      return SUPPORTED_EXTS.includes(ext);
    });

    setFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const filtered = validFiles.filter((f) => !existingNames.has(f.name));
      return [...prev, ...filtered];
    });
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const dropped = Array.from(e.dataTransfer.files);
      addFiles(dropped);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes <= 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1322] border-r border-surface-border p-5 space-y-5 overflow-y-auto">
      {/* 1. Mode Selector */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center justify-between">
          <span>Processing Mode</span>
          <span className="text-[10px] text-gray-500 font-mono">V1 Spec</span>
        </label>
        <div className="grid grid-cols-3 gap-2">
          {/* Strict Button */}
          <button
            type="button"
            onClick={() => setMode("strict")}
            className={`flex flex-col items-center justify-center p-3 rounded-xl border text-xs font-medium transition-all ${
              mode === "strict"
                ? "bg-blue-600/15 border-blue-500 text-blue-300 shadow-md shadow-blue-500/10"
                : "bg-surface/50 border-surface-border text-gray-400 hover:border-gray-600 hover:text-gray-200"
            }`}
          >
            <ShieldAlert className="w-4 h-4 mb-1.5 text-blue-400" />
            <span>Strict</span>
          </button>

          {/* Non-Strict Button */}
          <button
            type="button"
            onClick={() => setMode("non-strict")}
            className={`flex flex-col items-center justify-center p-3 rounded-xl border text-xs font-medium transition-all ${
              mode === "non-strict"
                ? "bg-purple-600/15 border-purple-500 text-purple-300 shadow-md shadow-purple-500/10"
                : "bg-surface/50 border-surface-border text-gray-400 hover:border-gray-600 hover:text-gray-200"
            }`}
          >
            <Sparkles className="w-4 h-4 mb-1.5 text-purple-400" />
            <span>Non-Strict</span>
          </button>

          {/* Scratch Button */}
          <button
            type="button"
            onClick={() => setMode("scratch")}
            className={`flex flex-col items-center justify-center p-3 rounded-xl border text-xs font-medium transition-all ${
              mode === "scratch"
                ? "bg-emerald-600/15 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-500/10"
                : "bg-surface/50 border-surface-border text-gray-400 hover:border-gray-600 hover:text-gray-200"
            }`}
          >
            <FileText className="w-4 h-4 mb-1.5 text-emerald-400" />
            <span>Scratch</span>
          </button>
        </div>

        {/* Mode Descriptions */}
        <div className="p-3 rounded-xl bg-surface border border-surface-border text-xs text-gray-300">
          {mode === "strict" && (
            <p className="leading-relaxed">
              <strong className="text-blue-400">Strict Mode:</strong> AI output is strictly grounded <em>only</em> in uploaded content. Zero external knowledge or assumptions allowed.
            </p>
          )}
          {mode === "non-strict" && (
            <p className="leading-relaxed">
              <strong className="text-purple-400">Non-Strict Mode:</strong> Content is primary context. AI analyzes, interprets, and expands while remaining centered on source material.
            </p>
          )}
          {mode === "scratch" && (
            <p className="leading-relaxed">
              <strong className="text-emerald-400">Scratch Mode:</strong> Direct prompt generation. File uploads are optional/bypassed.
            </p>
          )}
        </div>
      </div>

      {/* 2. File Upload Area */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Source Material {mode === "scratch" ? "(Optional)" : "(Required)"}
          </label>
          <span className="text-[10px] text-gray-500 font-mono">
            PDF, DOCX, TXT, PNG, JPG, WEBP
          </span>
        </div>

        {mode !== "scratch" ? (
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-surface-border hover:border-blue-500/50 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition-colors bg-surface/30 group"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.md,.pdf,.docx,.png,.jpg,.jpeg,.webp"
              onChange={handleFileChange}
              className="hidden"
            />
            <UploadCloud className="w-8 h-8 text-gray-400 group-hover:text-blue-400 transition-colors mb-2" />
            <p className="text-xs text-gray-300 font-medium">
              Drop files here or <span className="text-blue-400">browse</span>
            </p>
            <p className="text-[10px] text-gray-500 mt-1">Converts automatically to Markdown (.md)</p>
          </div>
        ) : (
          <div className="p-3 rounded-xl bg-surface/30 border border-surface-border text-center text-xs text-gray-500 italic">
            File upload is bypassed in Scratch Mode.
          </div>
        )}

        {/* Conversion Progress & Converted File Cards */}
        {files.length > 0 && mode !== "scratch" && (
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {files.map((file, idx) => {
              // Find matching conversion artifact for this file
              const item = conversions.find((c) => c.original_filename === file.name);

              return (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#090d16] border border-surface-border space-y-2 text-xs transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 truncate">
                      <File className="w-4 h-4 text-blue-400 shrink-0" />
                      <span className="truncate font-medium text-gray-200">{file.name}</span>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <span className="text-[10px] text-gray-500 font-mono">
                        {formatFileSize(file.size)}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeFile(idx)}
                        className="text-gray-500 hover:text-rose-400 p-0.5 rounded transition-colors"
                        title="Remove file"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Status Indicator & Conversion Metrics */}
                  {isConverting && !item ? (
                    <div className="flex items-center space-x-2 text-blue-400 text-[11px] font-mono bg-blue-500/10 p-2 rounded-lg border border-blue-500/20">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Converting to Markdown...</span>
                    </div>
                  ) : item ? (
                    <div className="space-y-2 pt-1 border-t border-surface-border/60">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Converted to Markdown</span>
                        </span>
                        <span className="text-gray-400 font-mono text-[10px]">
                          Markdown: <strong className="text-gray-200">{formatFileSize(item.markdown_size_bytes)}</strong>
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono">
                        <span>
                          Method: <strong className="text-blue-300 uppercase">{item.extraction_method}</strong>
                          {item.fallback_used && <span className="text-amber-400 ml-1">(Fallback)</span>}
                        </span>
                        <span>{item.char_count.toLocaleString()} chars</span>
                      </div>

                      {item.image_count !== undefined && item.image_count > 0 && (
                        <div className="flex items-center justify-between text-[10px] bg-purple-950/30 border border-purple-500/20 px-2 py-1 rounded text-purple-300 font-mono">
                          <span className="flex items-center gap-1">
                            <ImageIcon className="w-3 h-3 text-purple-400" />
                            <span>Images: {item.images_analyzed ?? 0}/{item.image_count} analyzed</span>
                          </span>
                          <span className="text-purple-400 font-semibold">{item.image_context_method || "Vision"}</span>
                        </div>
                      )}

                      {/* Download .md Button */}
                      <button
                        type="button"
                        onClick={() => onDownloadMarkdown(item.id, item.markdown_filename)}
                        className="w-full py-1.5 px-3 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 font-medium text-[11px] flex items-center justify-center space-x-1.5 transition-all shadow-sm"
                      >
                        <Download className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Download {item.markdown_filename}</span>
                      </button>
                    </div>
                  ) : (
                    <div className="text-[11px] text-gray-500 italic">
                      Ready for conversion
                    </div>
                  )}
                </div>
              );
            })}

            {/* Combined Download Button if multiple converted files */}
            {conversions.length > 1 && combinedConversionId && (
              <button
                type="button"
                onClick={() => onDownloadMarkdown(combinedConversionId, "combined_source.md")}
                className="w-full py-2 px-3 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-purple-300 font-medium text-xs flex items-center justify-center space-x-2 transition-all mt-2"
              >
                <Download className="w-4 h-4 text-purple-400" />
                <span>Download Combined Markdown (.md)</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* 3. Prompt Input Textarea */}
      <div className="flex-1 flex flex-col space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Instruction / Task Prompt
          </label>
          <button
            type="button"
            onClick={() => setPrompt("")}
            className="text-[11px] text-gray-500 hover:text-gray-300"
          >
            Clear
          </button>
        </div>

        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            mode === "strict"
              ? "e.g., Summarize key takeaways using ONLY the uploaded content..."
              : mode === "non-strict"
              ? "e.g., Analyze the document and expand on practical applications..."
              : "e.g., Write a concise release announcement for AI Content Engine V1..."
          }
          className="flex-1 min-h-[120px] w-full p-3 rounded-xl bg-surface border border-surface-border text-xs text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none font-sans"
        />
      </div>

      {/* 4. Action Process Button */}
      <button
        type="button"
        onClick={onProcess}
        disabled={isProcessing || isConverting}
        className={`w-full py-3 px-4 rounded-xl font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-lg ${
          isProcessing || isConverting
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/20 active:scale-[0.99]"
        }`}
      >
        {isProcessing ? (
          <>
            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            <span>Running AI Engine...</span>
          </>
        ) : isConverting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
            <span>Converting Files to Markdown...</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4 fill-white" />
            <span>Process Content Engine</span>
          </>
        )}
      </button>
    </div>
  );
};
