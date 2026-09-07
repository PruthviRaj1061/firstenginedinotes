import logging
from openai import AsyncOpenAI
from app.core.config import settings
from app.modules.ai_engine.base import AIProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(AIProvider):
    """
    OpenRouter AI Provider integration supporting models such as
    Nvidia Nemotron (nvidia/nemotron-3-super-120b-a12b:free) and other OpenRouter models.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str = "", model_name: str = ""):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model_name = model_name or settings.DEFAULT_MODEL or "nvidia/nemotron-3-super-120b-a12b:free"

        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "AI Content Engine MVP",
                },
            )
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return f"openrouter ({self.model_name})"

    @property
    def supports_vision(self) -> bool:
        return self.client is not None

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise ValueError("OpenRouter API key is not configured.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(f"Sending request to OpenRouter model '{self.model_name}'")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
            )

            output_text = response.choices[0].message.content or ""
            return output_text.strip()

        except Exception as e:
            logger.error(f"OpenRouter API call failed: {str(e)}")
            raise RuntimeError(f"OpenRouter Provider error: {str(e)}")

    async def generate_with_vision(
        self, image_bytes: bytes, prompt: str, system_instruction: str = ""
    ) -> str:
        if not self.client:
            raise ValueError("OpenRouter API key is not configured.")

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
            logger.error(f"OpenRouter Vision API call failed: {str(e)}")
            raise RuntimeError(f"OpenRouter Vision error: {str(e)}")

