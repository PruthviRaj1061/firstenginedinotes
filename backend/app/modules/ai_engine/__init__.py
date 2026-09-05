from app.core.config import settings
from app.modules.ai_engine.base import AIProvider
from app.modules.ai_engine.mock_provider import MockProvider
from app.modules.ai_engine.openai_provider import OpenAIProvider
from app.modules.ai_engine.openrouter_provider import OpenRouterProvider


def get_ai_provider() -> AIProvider:
    """
    Factory function selecting AIProvider implementation.
    1. If OPENROUTER_API_KEY is configured, returns OpenRouterProvider (e.g. Nvidia Nemotron).
    2. Else if OPENAI_API_KEY is configured, returns OpenAIProvider.
    3. Otherwise, falls back to MockProvider for safe offline testing.
    """
    if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip():
        return OpenRouterProvider()
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        return OpenAIProvider()
    return MockProvider()
