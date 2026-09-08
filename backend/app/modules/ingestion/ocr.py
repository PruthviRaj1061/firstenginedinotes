import io
import os
import logging
from typing import Optional
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_INSTALLED = True
except ImportError:
    pytesseract = None
    PYTESSERACT_INSTALLED = False

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Abstraction layer for OCR text extraction from images.
    Wraps PyTesseract with automatic binary location detection for Windows.
    """

    def __init__(self):
        self._available = False
        if PYTESSERACT_INSTALLED:
            # Check TESSERACT_CMD env var or standard Windows installation paths
            candidate_paths = []
            if "TESSERACT_CMD" in os.environ and os.environ["TESSERACT_CMD"].strip():
                candidate_paths.append(os.environ["TESSERACT_CMD"].strip())

            candidate_paths.extend([
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            ])

            for t_path in candidate_paths:
                if os.path.exists(t_path):
                    try:
                        pytesseract.pytesseract.tesseract_cmd = t_path
                        _ = pytesseract.get_tesseract_version()
                        self._available = True
                        logger.info(f"[OCR] Found Tesseract binary at '{t_path}'")
                        break
                    except Exception:
                        continue

            if not self._available:
                try:
                    _ = pytesseract.get_tesseract_version()
                    self._available = True
                except Exception as e:
                    logger.warning(f"[OCR] PyTesseract is installed but tesseract binary is unavailable: {e}")
                    self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def extract_text_from_image(self, image_input: bytes | Image.Image) -> str:
        """
        Extract text from raw image bytes or PIL Image object using PyTesseract.
        Returns extracted text, or empty string if unavailable or error occurs.
        """
        if not self._available:
            logger.debug("[OCR] Tesseract binary unavailable on host machine.")
            return ""

        try:
            if isinstance(image_input, bytes):
                image = Image.open(io.BytesIO(image_input))
            else:
                image = image_input

            # Convert to RGB if needed
            if image.mode not in ("L", "RGB"):
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image)
            return (text or "").strip()
        except Exception as e:
            logger.error(f"[OCR] Extraction error: {e}")
            return ""


ocr_engine = OCREngine()
