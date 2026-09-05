const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ProcessResponse {
  success: boolean;
  mode: string;
  content?: string;
  error?: string;
  pipeline_step?: "input" | "extraction" | "ai_engine" | "output";
  extracted_files?: Array<{
    filename: string;
    file_type: string;
    status: string;
    char_count: number;
    metadata: Record<string, any>;
  }>;
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

export async function processContent(
  mode: "strict" | "non-strict" | "scratch",
  prompt: string,
  files: File[]
): Promise<ProcessResponse> {
  const formData = new FormData();
  formData.append("mode", mode);
  formData.append("prompt", prompt);

  for (const file of files) {
    formData.append("files", file);
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
