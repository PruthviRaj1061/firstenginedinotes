import os
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.modules.ingestion.service import ingestion_service
from app.services.conversion_storage import conversion_storage
from app.schemas.processing import ConvertResponse, ConversionItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/convert", response_model=ConvertResponse)
async def convert_files(
    files: List[UploadFile] = File(...),
):
    """
    Dedicated ingestion conversion endpoint.
    Converts uploaded original files (PDF, DOCX, TXT, images) into normalized
    Markdown (.md) artifacts using MarkItDown (with PyMuPDF/OCR fallback).
    Returns conversion metadata and download identifiers.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for conversion.",
        )

    try:
        file_payloads = []
        for f in files:
            if f.filename:
                content_bytes = await f.read()
                file_payloads.append((f.filename, content_bytes))

        if not file_payloads:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All provided files were empty or invalid.",
            )

        combined_text, extraction_results, combined_id = await ingestion_service.process_files_and_combine(
            file_payloads
        )

        conversion_items: List[ConversionItem] = []
        for (fname, fbytes), res in zip(file_payloads, extraction_results):
            source_size = len(fbytes)
            md_size = len(res.text.encode("utf-8")) if res.text else 0
            base_name = os.path.splitext(fname)[0]
            clean_base = base_name if base_name else "document"
            md_filename = f"{clean_base}.md"

            conversion_items.append(
                ConversionItem(
                    id=res.id or "",
                    original_filename=res.filename,
                    markdown_filename=md_filename,
                    source_size_bytes=source_size,
                    markdown_size_bytes=md_size,
                    char_count=len(res.text) if res.text else 0,
                    extraction_method=res.extraction_method,
                    output_format=res.output_format,
                    fallback_used=res.fallback_used,
                    error_message=res.error_message,
                    image_count=res.image_count,
                    images_filtered=res.images_filtered,
                    images_unique=res.images_unique,
                    images_analyzed=res.images_analyzed,
                    images_unavailable=res.images_unavailable,
                    image_context_method=res.image_context_method,
                    text=res.text if len(res.text) <= 2000 else None,  # Snippet preview if small
                )
            )


        return ConvertResponse(
            success=True,
            conversions=conversion_items,
            download_available=True,
            combined_conversion_id=combined_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during document conversion")
        return ConvertResponse(
            success=False,
            conversions=[],
            download_available=False,
            error=f"Conversion error: {str(e)}",
        )


@router.get("/conversions/{conversion_id}/download")
async def download_conversion_artifact(conversion_id: str):
    """
    Secure download endpoint for generated Markdown (.md) artifacts.
    Validates conversion_id strictly to prevent path traversal vulnerabilities.
    Returns Content-Type: text/markdown.
    """
    if not conversion_storage.is_valid_id(conversion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversion ID format.",
        )

    metadata = conversion_storage.get_metadata(conversion_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion artifact not found or expired.",
        )

    filepath = conversion_storage.get_markdown_filepath(conversion_id)
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Markdown artifact file missing from storage.",
        )

    markdown_filename = metadata.get("markdown_filename", "document.md")

    return FileResponse(
        path=filepath,
        media_type="text/markdown; charset=utf-8",
        filename=markdown_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{markdown_filename}"',
            "Cache-Control": "no-cache",
        },
    )
