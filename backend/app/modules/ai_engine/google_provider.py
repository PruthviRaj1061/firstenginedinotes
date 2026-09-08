import logging
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

from app.core.config import settings
from app.modules.ai_engine.base import AIProvider

logger = logging.getLogger(__name__)


class GoogleGeminiProvider(AIProvider):
    """
    Google Gemini LLM provider using google-generativeai SDK.
    """

    def __init__(self, api_key: str = "", model_name: str = ""):
        self.api_key = (api_key or settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY).strip()
        raw_model = (model_name or settings.DEFAULT_MODEL or "gemini-1.5-flash").strip()
        clean_model = raw_model.replace("models/", "")
        
        # If configured DEFAULT_MODEL belongs to another provider (e.g. openai/..., grok-..., etc.), fallback to gemini-1.5-flash
        if "gemini" not in clean_model.lower():
            clean_model = "gemini-1.5-flash"

        self.model_name = clean_model

        if self.api_key:
            if not GENAI_AVAILABLE:
                raise ImportError(
                    "google-generativeai package is not installed in the active environment. "
                    "Please activate .venv or run: pip install google-generativeai"
                )
            genai.configure(api_key=self.api_key)
            self._configured = True
        else:
            self._configured = False

    @property
    def provider_name(self) -> str:
        return f"google-gemini ({self.model_name})"

    @property
    def supports_vision(self) -> bool:
        return self._configured

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self._configured:
            raise ValueError("Google API key (GEMINI_API_KEY / GOOGLE_API_KEY) is not configured.")

        try:
            model_kwargs = {"model_name": self.model_name}
            if system_instruction and system_instruction.strip():
                model_kwargs["system_instruction"] = system_instruction.strip()

            model = genai.GenerativeModel(**model_kwargs)
            response = await model.generate_content_async(prompt)

            output_text = getattr(response, "text", "") or ""
            return output_text.strip()

        except Exception as e:
            logger.error(f"Google Gemini API call failed: {str(e)}")
            raise RuntimeError(f"AI Provider error: {str(e)}")

    async def generate_with_vision(
        self, image_bytes: bytes, prompt: str, system_instruction: str = "", image_format: str = "png"
    ) -> str:
        if not self._configured:
            raise ValueError("Google API key (GEMINI_API_KEY / GOOGLE_API_KEY) is not configured.")

        try:
            import io
            from PIL import Image

            pil_img = Image.open(io.BytesIO(image_bytes))
            model_kwargs = {"model_name": self.model_name}
            if system_instruction and system_instruction.strip():
                model_kwargs["system_instruction"] = system_instruction.strip()

            model = genai.GenerativeModel(**model_kwargs)
            response = await model.generate_content_async([pil_img, prompt])

            output_text = getattr(response, "text", "") or ""
            return output_text.strip()

        except Exception as e:
            logger.error(f"Google Gemini Vision call failed: {str(e)}")
            raise RuntimeError(f"AI Provider Vision error: {str(e)}")

