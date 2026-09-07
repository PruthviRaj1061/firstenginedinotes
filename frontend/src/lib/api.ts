const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ConversionItem {
  id: string;
  original_filename: string;
  markdown_filename: string;
  source_size_bytes: number;
  markdown_size_bytes: number;
  char_count: number;
  extraction_method: string;
  output_format: string;
  fallback_used: boolean;
  error_message?: string;
  created_at?: number;
  text?: string;
  image_count?: number;
  images_analyzed?: number;
  image_context_method?: string;
}

export interface ConvertResponse {
  success: boolean;
  conversions: ConversionItem[];
  download_available: boolean;
  combined_conversion_id?: string;
  error?: string;
}

export interface ProcessResponse {
  success: boolean;
  mode: string;
  content?: string;
  source_markdown?: string;
  error?: string;
  pipeline_step?: "input" | "conversion" | "image_context" | "markdown_ready" | "ai_engine" | "output";
  extracted_files?: Array<{
    filename: string;
    file_type: string;
    status: string;
    char_count: number;
    extraction_method?: string;
    output_format?: string;
    fallback_used?: boolean;
    text?: string;
    metadata: Record<string, any>;
  }>;
  conversions?: ConversionItem[];
}


export interface HealthResponse {
  status: string;
  version: string;
  provider: string;
  tesseract_available: boolean;
}

export async function checkHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("Health check error:", error);
    return null;
  }
}

export async function convertFiles(files: File[]): Promise<ConvertResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/convert`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errorText = await res.text();
      let errorMsg = `Conversion server error (${res.status})`;
      try {
        const errJson = JSON.parse(errorText);
        if (errJson.detail) errorMsg = errJson.detail;
        if (errJson.error) errorMsg = errJson.error;
      } catch (e) {
        if (errorText) errorMsg = errorText;
      }

      return {
        success: false,
        conversions: [],
        download_available: false,
        error: errorMsg,
      };
    }

    return await res.json();
  } catch (error: any) {
    console.error("Convert API error:", error);
    return {
      success: false,
      conversions: [],
      download_available: false,
      error: error.message || "Failed to communicate with conversion server.",
    };
  }
}

export function getDownloadUrl(conversionId: string): string {
  return `${API_BASE_URL}/api/v1/conversions/${encodeURIComponent(conversionId)}/download`;
}

export async function downloadMarkdownFile(conversionId: string, defaultFilename: string) {
  try {
    const url = getDownloadUrl(conversionId);
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to download artifact (${res.status})`);
    }
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = defaultFilename.endsWith(".md") ? defaultFilename : `${defaultFilename}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(blobUrl);
  } catch (err) {
    console.error("Download failed:", err);
    alert("Could not download Markdown file artifact.");
  }
}

export async function processContent(
  mode: "strict" | "non-strict" | "scratch",
  prompt: string,
  files?: File[],
  conversionIds?: string[]
): Promise<ProcessResponse> {
  const formData = new FormData();
  formData.append("mode", mode);
  formData.append("prompt", prompt);

  if (files && files.length > 0) {
    for (const file of files) {
      formData.append("files", file);
    }
  }

  if (conversionIds && conversionIds.length > 0) {
    for (const id of conversionIds) {
      formData.append("conversion_ids", id);
    }
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/process`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errorText = await res.text();
      let errorMsg = `Server error (${res.status})`;
      try {
        const errJson = JSON.parse(errorText);
        if (errJson.detail) errorMsg = errJson.detail;
        if (errJson.error) errorMsg = errJson.error;
      } catch (e) {
        if (errorText) errorMsg = errorText;
      }

      return {
        success: false,
        mode,
        error: errorMsg,
        pipeline_step: "input",
      };
    }

    return await res.json();
  } catch (error: any) {
    console.error("API call error:", error);
    return {
      success: false,
      mode,
      error: error.message || "Failed to communicate with backend server.",
      pipeline_step: "input",
    };
  }
}
