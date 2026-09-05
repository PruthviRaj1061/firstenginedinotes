from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.services.content_processor import content_processor
from app.modules.ai_engine import get_ai_provider
from app.modules.ingestion.ocr import ocr_engine
from app.schemas.processing import ProcessResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint returning system status, AI provider name, and OCR availability.
    """
    provider = get_ai_provider()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        provider=provider.provider_name,
        tesseract_available=ocr_engine.is_available,
    )


@router.post("/process", response_model=ProcessResponse)
async def process_content(
    mode: str = Form(...),
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):
    """
    Process content request across Strict, Non-Strict, and Scratch modes.
    Accepts multipart/form-data.
    """
    file_payloads = []
    if files:
        for f in files:
            if f.filename:
                content_bytes = await f.read()
                file_payloads.append((f.filename, content_bytes))

    response = await content_processor.process_request(
        mode_input=mode,
        prompt=prompt,
        files=file_payloads,
    )

    return response
