import os
import logging
from typing import List, Tuple, Optional
from app.core.config import settings
from app.modules.ingestion.extractors.base import BaseExtractor
from app.modules.ingestion.extractors.text_extractor import TextExtractor
from app.modules.ingestion.extractors.docx_extractor import DocxExtractor
from app.modules.ingestion.extractors.pdf_extractor import PdfExtractor
from app.modules.ingestion.extractors.image_extractor import ImageExtractor
from app.modules.ingestion.markitdown_service import markitdown_service
from app.modules.ingestion.image_extractor_utils import (
    extract_images_from_pdf,
    extract_images_from_docx,
    extract_images_from_standalone_image,
    ExtractedImageItem,
)
from app.modules.ingestion.image_understanding import image_understanding_service
from app.services.conversion_storage import conversion_storage
from app.schemas.processing import ExtractionResult, ExtractionStatus

logger = logging.getLogger(__name__)


class ContentIngestionService:
    """
    Ingestion layer orchestrator using MarkItDown as the primary document
    normalization engine. Automatically falls back to specialized extractors
    (PyMuPDF, DOCX parser, PyTesseract OCR) if MarkItDown fails or yields empty content.
    Extracts embedded images and enriches Markdown text with semantic visual context.
    """

    FALLBACK_EXTRACTORS = {
        ".txt": TextExtractor(),
        ".md": TextExtractor(),
        ".docx": DocxExtractor(),
        ".pdf": PdfExtractor(),
        ".png": ImageExtractor(),
        ".jpg": ImageExtractor(),
        ".jpeg": ImageExtractor(),
        ".webp": ImageExtractor(),
    }

    @property
    def max_bytes(self) -> int:
        return settings.MAX_FILE_SIZE_MB * 1024 * 1024

    def validate_file(self, filename: str, file_bytes: bytes) -> Tuple[bool, str]:
        """
        Validate file extension and size.
        """
        if not filename:
            return False, "Filename cannot be empty"

        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.FALLBACK_EXTRACTORS:
            supported_str = ", ".join(sorted(self.FALLBACK_EXTRACTORS.keys()))
            return False, f"Unsupported file type '{ext}'. Supported extensions: {supported_str}"

        file_size_mb = len(file_bytes) / (1024 * 1024)
        if len(file_bytes) > self.max_bytes:
            return False, f"File '{filename}' ({file_size_mb:.1f}MB) exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"

        return True, ""

    async def process_file(self, filename: str, file_bytes: bytes) -> ExtractionResult:
        """
        Processes an uploaded file into normalized Markdown enriched with visual image context.
        Creates a downloadable .md artifact.
        """
        is_valid, err_msg = self.validate_file(filename, file_bytes)
        ext = os.path.splitext(filename)[1].lower()
        clean_ext = ext.replace(".", "")

        if not is_valid:
            return ExtractionResult(
                filename=filename,
                file_type=clean_ext,
                text="",
                metadata={},
                extraction_status=ExtractionStatus.FAILED,
                error_message=err_msg,
                extraction_method="none",
                output_format="markdown",
                fallback_used=False,
            )

        source_size = len(file_bytes)
        extraction_result: ExtractionResult

        # 1. Primary conversion attempt: MarkItDown Engine
        md_result = await markitdown_service.convert(file_bytes, filename)

        if md_result.extraction_status == ExtractionStatus.SUCCESS and md_result.text.strip():
            logger.info(
                f"[INGESTION] filename={filename} method=markitdown status=success char_count={len(md_result.text)}"
            )
            extraction_result = md_result
        else:
            # 2. Fallback execution path
            logger.info(
                f"[INGESTION] filename={filename} method=markitdown status=failed_or_empty fallback_triggered=true"
            )
            fallback_extractor: BaseExtractor = self.FALLBACK_EXTRACTORS[ext]
            fallback_result = fallback_extractor.extract(file_bytes, filename)
            fallback_result.fallback_used = True

            if fallback_result.extraction_method == "markitdown":
                fallback_result.extraction_method = clean_ext

            logger.info(
                f"[INGESTION] filename={filename} method={fallback_result.extraction_method} status={fallback_result.extraction_status.value} char_count={len(fallback_result.text)}"
            )
            extraction_result = fallback_result

        # 3. Embedded Image Extraction & Image Understanding Analysis
        image_items: List[ExtractedImageItem] = []
        if ext == ".pdf":
            image_items = extract_images_from_pdf(file_bytes)
        elif ext == ".docx":
            image_items = extract_images_from_docx(file_bytes)
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            image_items = extract_images_from_standalone_image(file_bytes, filename)

        if image_items and extraction_result.text:
            enriched_text, img_meta = await image_understanding_service.analyze_and_enrich_markdown(
                extraction_result.text, image_items
            )
            extraction_result.text = enriched_text
            extraction_result.image_count = img_meta["image_count"]
            extraction_result.images_analyzed = img_meta["images_analyzed"]
            extraction_result.image_context_method = img_meta["image_context_method"]

        # 4. Store converted Markdown artifact for user download
        if extraction_result.text and extraction_result.text.strip():
            meta = conversion_storage.save_conversion(
                original_filename=filename,
                markdown_text=extraction_result.text,
                source_size_bytes=source_size,
                extraction_method=extraction_result.extraction_method,
                fallback_used=extraction_result.fallback_used,
                error_message=extraction_result.error_message,
                image_count=extraction_result.image_count,
                images_analyzed=extraction_result.images_analyzed,
                image_context_method=extraction_result.image_context_method,
            )
            extraction_result.id = meta["id"]

        return extraction_result


    async def process_files_and_combine(
        self, files: List[Tuple[str, bytes]]
    ) -> Tuple[str, List[ExtractionResult], Optional[str]]:
        """
        Processes multiple uploaded files and combines their normalized Markdown text
        into a canonical source document with clear section headers. Also creates a combined .md artifact.
        Returns (combined_text, results_list, combined_conversion_id).
        """
        results: List[ExtractionResult] = []
        combined_blocks: List[str] = []
        total_source_size = 0

        for filename, content_bytes in files:
            total_source_size += len(content_bytes)
            res = await self.process_file(filename, content_bytes)
            results.append(res)

            if res.text and res.text.strip():
                # Escape hash tags in filename to prevent markdown injection
                safe_filename = filename.replace("#", "")
                combined_blocks.append(f"# Source: {safe_filename}\n\n{res.text.strip()}")

        combined_text = "\n\n---\n\n".join(combined_blocks).strip()
        combined_id: Optional[str] = None

        if combined_text:
            combined_meta = conversion_storage.save_conversion(
                original_filename="combined_source.md",
                markdown_text=combined_text,
                source_size_bytes=total_source_size,
                extraction_method="combined",
                fallback_used=any(r.fallback_used for r in results),
            )
            combined_id = combined_meta["id"]

        return combined_text, results, combined_id


ingestion_service = ContentIngestionService()

