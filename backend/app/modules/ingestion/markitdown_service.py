import os
import io
import tempfile
import asyncio
import logging
from typing import Optional

from markitdown import MarkItDown

from app.schemas.processing import ExtractionResult, ExtractionStatus

logger = logging.getLogger(__name__)


class MarkItDownService:
    """
    Dedicated service wrapping Microsoft's MarkItDown conversion engine.
    Safely handles byte streams via temporary files and executes CPU-bound
    conversions inside thread pools to prevent blocking the event loop.
    """

    def __init__(self):
        self._md = MarkItDown()

    def _convert_sync(self, temp_path: str) -> str:
        """
        Synchronous worker method executing MarkItDown conversion on file path.
        """
        result = self._md.convert(temp_path)
        return result.text_content if hasattr(result, "text_content") else str(result)

    async def convert(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        """
        Asynchronously converts binary file content to normalized Markdown.
        Manages temporary file lifecycle cleanly using try...finally.
        """
        ext = os.path.splitext(filename)[1].lower()
        clean_ext = ext.replace(".", "")

        if not file_bytes:
            return ExtractionResult(
                filename=filename,
                file_type=clean_ext,
                text="",
                metadata={},
                extraction_status=ExtractionStatus.FAILED,
                error_message="File content is empty.",
                extraction_method="markitdown",
                output_format="markdown",
                fallback_used=False,
            )

        temp_path = None
        try:
            # Create a secure temporary file with original extension for MarkItDown format detection
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name

            # Run synchronous MarkItDown conversion in thread pool to avoid blocking async loop
            converted_md = await asyncio.to_thread(self._convert_sync, temp_path)
            normalized_md = (converted_md or "").strip()

            if not normalized_md:
                return ExtractionResult(
                    filename=filename,
                    file_type=clean_ext,
                    text="",
                    metadata={},
                    extraction_status=ExtractionStatus.PARTIAL,
                    error_message="MarkItDown returned empty content.",
                    extraction_method="markitdown",
                    output_format="markdown",
                    fallback_used=False,
                )

            char_count = len(normalized_md)
            word_count = len(normalized_md.split())
            line_count = len(normalized_md.splitlines())

            return ExtractionResult(
                filename=filename,
                file_type=clean_ext,
                text=normalized_md,
                metadata={
                    "char_count": char_count,
                    "word_count": word_count,
                    "line_count": line_count,
                    "engine": "markitdown",
                },
                extraction_status=ExtractionStatus.SUCCESS,
                extraction_method="markitdown",
                output_format="markdown",
                fallback_used=False,
            )

        except Exception as e:
            logger.warning(f"MarkItDown conversion failed for file '{filename}': {e}")
            return ExtractionResult(
                filename=filename,
                file_type=clean_ext,
                text="",
                metadata={},
                extraction_status=ExtractionStatus.FAILED,
                error_message=f"MarkItDown error: {str(e)}",
                extraction_method="markitdown",
                output_format="markdown",
                fallback_used=False,
            )
        finally:
            # Secure temporary file cleanup
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_err:
                    logger.error(f"Failed to remove temp file '{temp_path}': {cleanup_err}")


markitdown_service = MarkItDownService()
