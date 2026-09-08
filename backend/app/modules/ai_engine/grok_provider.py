import logging
import base64
from openai import AsyncOpenAI
from app.core.config import settings
from app.modules.ai_engine.base import AIProvider

logger = logging.getLogger(__name__)

# Known Grok vision models
GROK_VISION_KEYWORDS = ["vision", "grok-2-vision", "grok-vision"]


class GrokProvider(AIProvider):
    """
    Dedicated Grok / xAI LLM provider using OpenAI-compatible AsyncOpenAI client
    targeting https://api.x.ai/v1.
    Supports multimodal vision requests when configured with a vision-capable Grok model.
    """

    XAI_BASE_URL = "https://api.x.ai/v1"

    def __init__(self, api_key: str = "", model_name: str = ""):
        # Precedence: explicit api_key -> GROK_API_KEY -> XAI_API_KEY
        resolved_key = (api_key or settings.GROK_API_KEY or settings.XAI_API_KEY or "").strip()
        self.api_key = resolved_key
        
        # Model precedence: explicit model_name -> DEFAULT_MODEL -> fallback default
        configured_model = model_name or settings.DEFAULT_MODEL or "grok-2-vision-1212"
        self.model_name = configured_model.strip()

        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.XAI_BASE_URL,
            )
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return f"grok ({self.model_name})"

    @property
    def supports_vision(self) -> bool:
        """
        Model-aware vision capability check. Returns True if client is initialized
        and configured model is vision-capable.
        """
        if not self.client:
            return False
        
        model_lower = self.model_name.lower()
        return any(keyword in model_lower for keyword in GROK_VISION_KEYWORDS)

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """
        Standard text generation endpoint.
        """
        if not self.client:
            raise ValueError("Grok/xAI API key (GROK_API_KEY or XAI_API_KEY) is not configured.")

        messages = []
        if system_instruction and system_instruction.strip():
            messages.append({"role": "system", "content": system_instruction.strip()})

        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(f"[GROK_PROVIDER] Sending text request to Grok model '{self.model_name}'")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
            )

            output_text = response.choices[0].message.content or ""
            return output_text.strip()

        except Exception as e:
            logger.error(f"[GROK_PROVIDER] Grok API call failed for model '{self.model_name}': {str(e)}")
            raise RuntimeError(f"Grok Provider error: {str(e)}")

    async def generate_with_vision(
        self, image_bytes: bytes, prompt: str, system_instruction: str = "", image_format: str = "png"
    ) -> str:
        """
        Multimodal image understanding request using base64 data URI format.
        """
        if not self.supports_vision:
            raise NotImplementedError(
                f"Configured Grok model '{self.model_name}' does not support vision analysis."
            )

        if not self.client:
            raise ValueError("Grok/xAI API key is not configured.")

        # Determine MIME type safely
        fmt_clean = (image_format or "png").lower().replace(".", "")
        mime = "image/png"
        if fmt_clean in ["jpg", "jpeg"]:
            mime = "image/jpeg"
        elif fmt_clean == "webp":
            mime = "image/webp"

        base64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{mime};base64,{base64_img}"

        messages = []
        if system_instruction and system_instruction.strip():
            messages.append({"role": "system", "content": system_instruction.strip()})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ],
        })

        try:
            logger.info(f"[GROK_PROVIDER] Invoking Grok Vision for model '{self.model_name}' (mime={mime})")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )

            output_text = response.choices[0].message.content or ""
            return output_text.strip()

        except Exception as e:
            logger.error(f"[GROK_PROVIDER] Grok Vision API call failed for model '{self.model_name}': {str(e)}")
            raise RuntimeError(f"Grok Vision error: {str(e)}")
