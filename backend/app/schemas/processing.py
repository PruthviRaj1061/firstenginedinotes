from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    STRICT = "strict"
    NON_STRICT = "non-strict"
    SCRATCH = "scratch"


class PipelineStep(str, Enum):
    INPUT = "input"
    EXTRACTION = "extraction"
    AI_ENGINE = "ai_engine"
    OUTPUT = "output"


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractionResult(BaseModel):
    filename: str
    file_type: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS
    error_message: Optional[str] = None


class ProcessResponse(BaseModel):
    success: bool
    mode: str
    content: Optional[str] = None
    error: Optional[str] = None
    pipeline_step: PipelineStep = PipelineStep.OUTPUT
    extracted_files: Optional[List[Dict[str, Any]]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    provider: str
    tesseract_available: bool
