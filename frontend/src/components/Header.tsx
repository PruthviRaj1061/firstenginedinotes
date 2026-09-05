"use client";

import React from "react";
import { Cpu, CheckCircle2, XCircle, Sparkles } from "lucide-react";
import { HealthResponse } from "@/lib/api";

interface HeaderProps {
  healthInfo: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ healthInfo }) => {
  return (
    <header className="border-b border-surface-border bg-[#0d1322]/80 backdrop-blur-md px-6 py-4 sticky top-0 z-50 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-lg shadow-blue-500/20">
          <Cpu className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            AI Content Engine <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">v1.0 MVP</span>
          </h1>
          <p className="text-xs text-gray-400">
            Multi-Format Ingestion & Grounded Processing Pipeline
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {healthInfo ? (
          <div className="flex items-center space-x-3 text-xs">
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Backend Connected</span>
            </div>
            
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-surface border border-surface-border text-gray-300 font-mono">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              <span>Provider: {healthInfo.provider}</span>
            </div>

            {healthInfo.tesseract_available ? (
              <span className="hidden md:inline-block px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 text-[10px] font-mono border border-blue-500/20">
                OCR Enabled
              </span>
            ) : (
              <span className="hidden md:inline-block px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 text-[10px] font-mono border border-amber-500/20">
                OCR Standby
              </span>
            )}
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Backend Offline</span>
          </div>
        )}
      </div>
    </header>
  );
};
