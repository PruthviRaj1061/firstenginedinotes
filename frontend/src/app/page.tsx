"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { LeftPanel, ModeType } from "@/components/LeftPanel";
import { FlowVisualizer } from "@/components/FlowVisualizer";
import { OutputPanel } from "@/components/OutputPanel";
import {
  checkHealth,
  convertFiles,
  processContent,
  downloadMarkdownFile,
  ProcessResponse,
  HealthResponse,
  ConversionItem,
} from "@/lib/api";

export default function Home() {
  const [healthInfo, setHealthInfo] = useState<HealthResponse | null>(null);
  const [mode, setMode] = useState<ModeType>("strict");
  const [prompt, setPrompt] = useState<string>("Summarize the key information from the provided content.");
  const [files, setFiles] = useState<File[]>([]);
  const [conversions, setConversions] = useState<ConversionItem[]>([]);
  const [combinedConversionId, setCombinedConversionId] = useState<string | undefined>(undefined);

  const [isConverting, setIsConverting] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<
    "idle" | "input" | "conversion" | "image_context" | "markdown_ready" | "ai_engine" | "output" | "completed" | "failed"
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

  // Automatic file to Markdown conversion effect upon file upload
  useEffect(() => {
    if (mode === "scratch" || files.length === 0) {
      setConversions([]);
      setCombinedConversionId(undefined);
      if (currentStep !== "completed" && currentStep !== "failed" && !isProcessing) {
        setCurrentStep("idle");
      }
      return;
    }

    let isMounted = true;

    const performConversion = async () => {
      setIsConverting(true);
      setCurrentStep("conversion");

      try {
        const res = await convertFiles(files);
        if (!isMounted) return;

        setIsConverting(false);
        if (res.success) {
          setConversions(res.conversions);
          setCombinedConversionId(res.combined_conversion_id);
          setCurrentStep("markdown_ready");
        } else {
          setConversions([]);
          setCombinedConversionId(undefined);
          setCurrentStep("failed");
          setLastResponse({
            success: false,
            mode,
            error: res.error || "File conversion failed",
            pipeline_step: "conversion",
          });
        }
      } catch (err: any) {
        if (!isMounted) return;
        setIsConverting(false);
        setCurrentStep("failed");
        setLastResponse({
          success: false,
          mode,
          error: err.message || "File conversion request error",
          pipeline_step: "conversion",
        });
      }
    };

    performConversion();

    return () => {
      isMounted = false;
    };
  }, [files, mode]);

  const handleDownloadMarkdown = (conversionId: string, filename: string) => {
    downloadMarkdownFile(conversionId, filename);
  };

  const handleProcess = async () => {
    if (!prompt.trim() && mode === "scratch") {
      alert("Prompt is required in Scratch mode.");
      return;
    }
    if (!prompt.trim() && (mode === "strict" || mode === "non-strict")) {
      alert(`Prompt is required in ${mode} mode.`);
      return;
    }

    if (mode !== "scratch" && files.length > 0 && conversions.length === 0 && !isConverting) {
      // Trigger conversion first if needed
      setIsConverting(true);
      setCurrentStep("conversion");
      const convRes = await convertFiles(files);
      setIsConverting(false);
      if (convRes.success) {
        setConversions(convRes.conversions);
        setCombinedConversionId(convRes.combined_conversion_id);
        setCurrentStep("markdown_ready");
      } else {
        alert(`Conversion error: ${convRes.error}`);
        return;
      }
    }

    setIsProcessing(true);
    setLastResponse(null);
    setCurrentStep("ai_engine");

    try {
      const conversionIds = conversions.map((c) => c.id);
      const res = await processContent(
        mode,
        prompt,
        conversionIds.length > 0 ? undefined : files,
        conversionIds.length > 0 ? conversionIds : undefined
      );

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
    if (conversions.length > 0) {
      setCurrentStep("markdown_ready");
    } else {
      setCurrentStep("idle");
    }
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
            conversions={conversions}
            combinedConversionId={combinedConversionId}
            isConverting={isConverting}
            onProcess={handleProcess}
            isProcessing={isProcessing}
            onDownloadMarkdown={handleDownloadMarkdown}
          />
        </div>

        {/* Center Panel: Pipeline Flow Visualization (4 cols) */}
        <div className="lg:col-span-4 h-full overflow-hidden">
          <FlowVisualizer
            currentStep={currentStep}
            lastResponse={lastResponse}
            mode={mode}
            filesCount={files.length}
            isConverting={isConverting}
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
}
