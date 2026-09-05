"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { LeftPanel, ModeType } from "@/components/LeftPanel";
import { FlowVisualizer } from "@/components/FlowVisualizer";
import { OutputPanel } from "@/components/OutputPanel";
import { checkHealth, processContent, ProcessResponse, HealthResponse } from "@/lib/api";

export default function Home() {
  const [healthInfo, setHealthInfo] = useState<HealthResponse | null>(null);
  const [mode, setMode] = useState<ModeType>("strict");
  const [prompt, setPrompt] = useState<string>("Summarize the key information from the provided content.");
  const [files, setFiles] = useState<File[]>([]);
  
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<
    "idle" | "input" | "extraction" | "ai_engine" | "output" | "completed" | "failed"
  >("idle");
  const [lastResponse, setLastResponse] = useState<ProcessResponse | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      const data = await checkHealth();
      setHealthInfo(data);
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleProcess = async () => {
    if (!prompt.trim() && mode === "scratch") {
      alert("Prompt is required in Scratch mode.");
      return;
    }
    if (!prompt.trim() && (mode === "strict" || mode === "non-strict")) {
      alert(`Prompt is required in ${mode} mode.`);
      return;
    }

    setIsProcessing(true);
    setLastResponse(null);
    setCurrentStep("input");

    // Progressive step animation
    if (files.length > 0 && mode !== "scratch") {
      setTimeout(() => setCurrentStep("extraction"), 300);
      setTimeout(() => setCurrentStep("ai_engine"), 700);
    } else {
      setTimeout(() => setCurrentStep("ai_engine"), 300);
    }

    try {
      const res = await processContent(mode, prompt, files);
      setLastResponse(res);
      setIsProcessing(false);

      if (res.success) {
        setCurrentStep("completed");
      } else {
        setCurrentStep("failed");
      }
    } catch (e) {
      setIsProcessing(false);
      setCurrentStep("failed");
    }
  };

  const handleClearOutput = () => {
    setLastResponse(null);
    setCurrentStep("idle");
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#090d16]">
      {/* Header Bar */}
      <Header healthInfo={healthInfo} />

      {/* Main 3-Panel Grid Layout */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Panel: Input Section (4 cols) */}
        <div className="lg:col-span-4 h-full overflow-hidden">
          <LeftPanel
            mode={mode}
            setMode={setMode}
            prompt={prompt}
            setPrompt={setPrompt}
            files={files}
            setFiles={setFiles}
            onProcess={handleProcess}
            isProcessing={isProcessing}
          />
        </div>

        {/* Center Panel: Pipeline Flow Visualization (4 cols) */}
        <div className="lg:col-span-4 h-full overflow-hidden">
          <FlowVisualizer
            currentStep={currentStep}
            lastResponse={lastResponse}
            mode={mode}
            filesCount={files.length}
          />
        </div>

        {/* Right Panel: Text Output Panel (4 cols) */}
        <div className="lg:col-span-4 h-full overflow-hidden">
          <OutputPanel
            response={lastResponse}
            onClear={handleClearOutput}
            isProcessing={isProcessing}
          />
        </div>
      </main>
    </div>
  );
};
