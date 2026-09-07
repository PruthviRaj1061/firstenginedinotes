import fitz  # PyMuPDF
from PIL import Image
import io
from app.modules.ingestion.extractors.base import BaseExtractor
from app.modules.ingestion.ocr import ocr_engine
from app.schemas.processing import ExtractionResult, ExtractionStatus


class PdfExtractor(BaseExtractor):
    """
    Extractor for PDF files using PyMuPDF (fitz) supporting text, embedded images,
    and scanned/image-heavy pages via OCREngine abstraction.
    """

    MIN_PAGE_TEXT_CHARS = 30  # Threshold under which page is assumed to be scanned/image-heavy

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(doc)

            page_contents = []
            ocr_pages_count = 0
            text_pages_count = 0

            for page_idx in range(total_pages):
                page = doc[page_idx]
                page_text = page.get_text("text").strip()

                if len(page_text) >= self.MIN_PAGE_TEXT_CHARS:
                    text_pages_count += 1
                    page_contents.append(f"[Page {page_idx + 1}]\n{page_text}")
                else:
                    # Low text count -> Attempt OCR on rendered page image
                    ocr_pages_count += 1
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    ocr_text = ocr_engine.extract_text_from_image(img_bytes)

                    combined_page_text = page_text
                    if ocr_text and not ocr_text.startswith("[OCR"):
                        combined_page_text = (page_text + "\n" + ocr_text).strip() if page_text else ocr_text

                    if combined_page_text:
                        page_contents.append(f"[Page {page_idx + 1} (OCR Applied)]\n{combined_page_text}")
                    else:
                        page_contents.append(f"[Page {page_idx + 1}]\n(No text or OCR content found)")

            full_text = "\n\n".join(page_contents).strip()

            method = "ocr" if ocr_pages_count > 0 else "pymupdf"
            return ExtractionResult(
                filename=filename,
                file_type="pdf",
                text=full_text,
                metadata={
                    "total_pages": total_pages,
                    "text_pages": text_pages_count,
                    "ocr_pages": ocr_pages_count,
                    "char_count": len(full_text),
                },
                extraction_status=ExtractionStatus.SUCCESS if full_text else ExtractionStatus.PARTIAL,
                extraction_method=method,
                output_format="markdown",
            )
        except Exception as e:
            return ExtractionResult(
                filename=filename,
                file_type="pdf",
                text="",
                metadata={},
                extraction_status=ExtractionStatus.FAILED,
                error_message=f"Failed to parse PDF: {str(e)}",
            )
