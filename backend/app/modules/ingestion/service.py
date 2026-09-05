import os
from typing import List, Tuple
from app.core.config import settings
from app.modules.ingestion.extractors.base import BaseExtractor
from app.modules.ingestion.extractors.text_extractor import TextExtractor
from app.modules.ingestion.extractors.docx_extractor import DocxExtractor
from app.modules.ingestion.extractors.pdf_extractor import PdfExtractor
from app.modules.ingestion.extractors.image_extractor import ImageExtractor
from app.schemas.processing import ExtractionResult, ExtractionStatus


class ContentIngestionService:
    """
    Ingestion layer orchestrator for file validation, extension routing,
    extraction execution, and combining multi-file contexts.
    """

    SUPPORTED_EXTENSIONS = {
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
        if ext not in self.SUPPORTED_EXTENSIONS:
            supported_str = ", ".join(sorted(self.SUPPORTED_EXTENSIONS.keys()))
            return False, f"Unsupported file type '{ext}'. Supported extensions: {supported_str}"

        file_size_mb = len(file_bytes) / (1024 * 1024)
        if len(file_bytes) > self.max_bytes:
            return False, f"File '{filename}' ({file_size_mb:.1f}MB) exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"

        return True, ""

    def process_file(self, filename: str, file_bytes: bytes) -> ExtractionResult:
        """
        Validate and extract single file.
        """
        is_valid, err_msg = self.validate_file(filename, file_bytes)
        if not is_valid:
            ext = os.path.splitext(filename)[1].lower().replace(".", "")
            return ExtractionResult(
                filename=filename,
                file_type=ext,
                text="",
                metadata={},
                extraction_status=ExtractionStatus.FAILED,
                error_message=err_msg,
            )

        ext = os.path.splitext(filename)[1].lower()
        extractor: BaseExtractor = self.SUPPORTED_EXTENSIONS[ext]
        return extractor.extract(file_bytes, filename)

    def process_files_and_combine(self, files: List[Tuple[str, bytes]]) -> Tuple[str, List[ExtractionResult]]:
        """
        Process multiple files and combine extracted texts into normalized context string.
        """
        results: List[ExtractionResult] = []
        combined_blocks: List[str] = []

        for filename, content_bytes in files:
            res = self.process_file(filename, content_bytes)
            results.append(res)

            if res.text:
                combined_blocks.append(f"--- FILE: {filename} ---\n{res.text}")

        combined_text = "\n\n".join(combined_blocks).strip()
        return combined_text, results


ingestion_service = ContentIngestionService()
