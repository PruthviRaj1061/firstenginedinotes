import os
import io
from PIL import Image
from app.modules.ingestion.extractors.base import BaseExtractor
from app.modules.ingestion.ocr import ocr_engine
from app.schemas.processing import ExtractionResult, ExtractionStatus


class ImageExtractor(BaseExtractor):
    """
    Extractor for image files (PNG, JPG, JPEG, WEBP) using OCREngine abstraction.
    """

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        try:
            pil_image = Image.open(io.BytesIO(file_bytes))
            width, height = pil_image.size
            format_name = pil_image.format

            extracted_text = ocr_engine.extract_text_from_image(pil_image)

            status = ExtractionStatus.SUCCESS
            if not extracted_text or extracted_text.startswith("[OCR"):
                status = ExtractionStatus.PARTIAL

            return ExtractionResult(
                filename=filename,
                file_type=ext,
                text=extracted_text,
                metadata={
                    "width": width,
                    "height": height,
                    "image_format": format_name,
                    "char_count": len(extracted_text),
                    "ocr_engine_available": ocr_engine.is_available,
                },
                extraction_status=status,
            )
        except Exception as e:
            return ExtractionResult(
                filename=filename,
                file_type=ext,
                text="",
                metadata={},
                extraction_status=ExtractionStatus.FAILED,
                error_message=f"Failed to read image: {str(e)}",
            )
