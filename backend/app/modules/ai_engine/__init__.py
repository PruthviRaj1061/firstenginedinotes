from app.core.config import settings
from app.modules.ai_engine.base import AIProvider
from app.modules.ai_engine.google_provider import GoogleGeminiProvider
from app.modules.ai_engine.groq_provider import GroqProvider
from app.modules.ai_engine.mock_provider import MockProvider
from app.modules.ai_engine.openai_provider import OpenAIProvider
from app.modules.ai_engine.openrouter_provider import OpenRouterProvider


def get_ai_provider() -> AIProvider:
    """
    Factory function selecting AIProvider implementation.
    1. If GROQ_API_KEY is configured, returns GroqProvider.
    2. Else if GOOGLE_API_KEY or GEMINI_API_KEY is configured, returns GoogleGeminiProvider.
    3. Else if OPENROUTER_API_KEY is configured, returns OpenRouterProvider.
    4. Else if OPENAI_API_KEY is configured, returns OpenAIProvider.
    5. Otherwise, falls back to MockProvider for safe offline testing.
    """
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
        return GroqProvider()
    if (settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY.strip()) or (
        settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()
    ):
        return GoogleGeminiProvider()
    if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip():
        return OpenRouterProvider()
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        return OpenAIProvider()
    return MockProvider()

