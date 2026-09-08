from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    STRICT = "strict"
    NON_STRICT = "non-strict"
    SCRATCH = "scratch"


class PipelineStep(str, Enum):
    INPUT = "input"
    CONVERSION = "conversion"
    IMAGE_CONTEXT = "image_context"
    MARKDOWN_READY = "markdown_ready"
    AI_ENGINE = "ai_engine"
    OUTPUT = "output"


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractionResult(BaseModel):
    id: Optional[str] = None
    filename: str
    file_type: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS
    error_message: Optional[str] = None
    extraction_method: str = "markitdown"
    output_format: str = "markdown"
    fallback_used: bool = False
    image_count: int = 0
    images_filtered: int = 0
    images_unique: int = 0
    images_analyzed: int = 0
    images_unavailable: int = 0
    image_context_method: str = "none"


class ConversionItem(BaseModel):
    id: str
    original_filename: str
    markdown_filename: str
    source_size_bytes: int
    markdown_size_bytes: int
    char_count: int
    extraction_method: str = "markitdown"
    output_format: str = "markdown"
    fallback_used: bool = False
    error_message: Optional[str] = None
    created_at: Optional[float] = None
    text: Optional[str] = None
    image_count: int = 0
    images_filtered: int = 0
    images_unique: int = 0
    images_analyzed: int = 0
    images_unavailable: int = 0
    image_context_method: str = "none"



class ConvertResponse(BaseModel):
    success: bool
    conversions: List[ConversionItem] = Field(default_factory=list)
    download_available: bool = True
    combined_conversion_id: Optional[str] = None
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    success: bool
    mode: str
    content: Optional[str] = None
    source_markdown: Optional[str] = None
    error: Optional[str] = None
    pipeline_step: PipelineStep = PipelineStep.OUTPUT
    extracted_files: Optional[List[Dict[str, Any]]] = None
    conversions: Optional[List[ConversionItem]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    provider: str
    tesseract_available: bool

