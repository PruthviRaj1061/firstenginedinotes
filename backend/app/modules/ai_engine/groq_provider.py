import logging
from app.core.config import settings
from app.modules.ai_engine.base import AIProvider

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq
    HAS_GROQ_PKG = True
except ImportError:
    AsyncGroq = None
    HAS_GROQ_PKG = False

from openai import AsyncOpenAI


class GroqProvider(AIProvider):
    """
    Groq LLM provider using official AsyncGroq or AsyncOpenAI client targeting Groq API.
    """

    def __init__(self, api_key: str = "", model_name: str = ""):
        self.api_key = (api_key or settings.GROQ_API_KEY).strip()
        self.model_name = model_name or settings.DEFAULT_MODEL or "openai/gpt-oss-120b"

        if self.api_key:
            if HAS_GROQ_PKG:
                self.client = AsyncGroq(api_key=self.api_key)
            else:
                self.client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return f"groq ({self.model_name})"

    @property
    def supports_vision(self) -> bool:
        if not self.client:
            return False
        return "vision" in self.model_name.lower() or "llama-3.2" in self.model_name.lower()

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise ValueError("Groq API key (GROQ_API_KEY) is not configured.")

        messages = []
        if system_instruction and system_instruction.strip():
            messages.append({"role": "system", "content": system_instruction.strip()})

        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
            )

            output_text = response.choices[0].message.content or ""
            return output_text.strip()

        except Exception as e:
            logger.error(f"Groq API call failed: {str(e)}")
            raise RuntimeError(f"AI Provider error: {str(e)}")

    async def generate_with_vision(
        self, image_bytes: bytes, prompt: str, system_instruction: str = ""
    ) -> str:
        if not self.supports_vision:
            raise NotImplementedError(f"Groq model '{self.model_name}' does not support vision analysis.")

        import base64
        base64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{base64_img}"

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ],
        })

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            output_text = response.choices[0].message.content or ""
            return output_text.strip()
        except Exception as e:
            logger.error(f"Groq Vision API call failed: {str(e)}")
            raise RuntimeError(f"Groq Vision error: {str(e)}")

