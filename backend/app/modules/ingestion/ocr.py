import io
import logging
from typing import Optional
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_INSTALLED = True
except ImportError:
    PYTESSERACT_INSTALLED = False

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Abstraction layer for OCR text extraction from images.
    Wraps PyTesseract with fallback handling if binary is missing.
    """

    def __init__(self):
        self._available = False
        if PYTESSERACT_INSTALLED:
            try:
                # Test pytesseract binary availability
                _ = pytesseract.get_tesseract_version()
                self._available = True
            except Exception as e:
                logger.warning(f"PyTesseract is installed but tesseract binary is unavailable: {e}")
                self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def extract_text_from_image(self, image_input: bytes | Image.Image) -> str:
        """
        Extract text from raw image bytes or PIL Image object.
        """
        if not self._available:
            logger.info("OCR requested but Tesseract binary is not installed on system.")
            return "[OCR Unavailable: Tesseract engine binary is not installed on host machine]"

        try:
            if isinstance(image_input, bytes):
                image = Image.open(io.BytesIO(image_input))
            else:
                image = image_input

            # Convert to RGB if needed
            if image.mode not in ("L", "RGB"):
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return f"[OCR Error: {str(e)}]"


ocr_engine = OCREngine()
