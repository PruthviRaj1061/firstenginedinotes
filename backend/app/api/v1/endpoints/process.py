import json
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
    conversion_ids: Optional[List[str]] = Form(None),
):
    """
    Process content request across Strict, Non-Strict, and Scratch modes.
    Accepts multipart/form-data with either uploaded files or pre-converted conversion_ids.
    """
    file_payloads = []
    if files:
        for f in files:
            if f.filename:
                content_bytes = await f.read()
                file_payloads.append((f.filename, content_bytes))

    parsed_ids: List[str] = []
    if conversion_ids:
        for cid in conversion_ids:
            cid_str = cid.strip()
            if not cid_str:
                continue
            if cid_str.startswith("[") and cid_str.endswith("]"):
                try:
                    loaded = json.loads(cid_str)
                    if isinstance(loaded, list):
                        parsed_ids.extend([str(item).strip() for item in loaded])
                    else:
                        parsed_ids.append(cid_str)
                except Exception:
                    parsed_ids.append(cid_str)
            elif "," in cid_str:
                parsed_ids.extend([item.strip() for item in cid_str.split(",") if item.strip()])
            else:
                parsed_ids.append(cid_str)

    response = await content_processor.process_request(
        mode_input=mode,
        prompt=prompt,
        files=file_payloads if file_payloads else None,
        conversion_ids=parsed_ids if parsed_ids else None,
    )

    return response

