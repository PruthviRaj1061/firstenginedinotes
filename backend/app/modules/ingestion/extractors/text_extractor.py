import os
from app.modules.ingestion.extractors.base import BaseExtractor
from app.schemas.processing import ExtractionResult, ExtractionStatus


class TextExtractor(BaseExtractor):
    """
    Extractor for plain text (.txt) and Markdown (.md) files.
    """

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        ext = os.path.splitext(filename)[1].lower()
        
        # Safe decoding try list
        text = ""
        decoding_error = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(encoding)
                decoding_error = None
                break
            except Exception as e:
                decoding_error = str(e)
                continue

        if text == "" and decoding_error:
            text = file_bytes.decode("utf-8", errors="replace")

        text = text.strip()
        line_count = len(text.splitlines()) if text else 0
        word_count = len(text.split()) if text else 0

        return ExtractionResult(
            filename=filename,
            file_type=ext.replace(".", ""),
            text=text,
            metadata={
                "char_count": len(text),
                "line_count": line_count,
                "word_count": word_count,
            },
            extraction_status=ExtractionStatus.SUCCESS if text else ExtractionStatus.PARTIAL,
        )
