from app.core.config import settings
from app.modules.ai_engine.base import AIProvider
from app.modules.ai_engine.mock_provider import MockProvider
from app.modules.ai_engine.openai_provider import OpenAIProvider


def get_ai_provider() -> AIProvider:
    """
    Factory function selecting AIProvider implementation.
    If OPENAI_API_KEY is configured, returns OpenAIProvider.
    Otherwise, falls back to MockProvider for safe offline testing.
    """
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        return OpenAIProvider()
    return MockProvider()
