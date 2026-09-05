import logging
from openai import AsyncOpenAI
from app.core.config import settings
from app.modules.ai_engine.base import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI LLM provider using official AsyncOpenAI client.
    """

    def __init__(self, api_key: str = "", model_name: str = ""):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name or settings.DEFAULT_MODEL
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    @property
    def provider_name(self) -> str:
        return f"openai ({self.model_name})"

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise ValueError("OpenAI API key is not configured.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
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
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise RuntimeError(f"AI Provider error: {str(e)}")
