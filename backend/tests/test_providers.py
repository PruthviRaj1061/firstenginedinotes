import pytest
from app.modules.ai_engine.mock_provider import MockProvider
from app.modules.ai_engine import get_ai_provider


@pytest.mark.asyncio
async def test_mock_ai_provider():
    provider = MockProvider()
    assert provider.provider_name == "mock-provider"

    res = await provider.generate(
        prompt="Write a test prompt",
        system_instruction="STRICT MODE system instruction",
    )

    assert "[MOCK AI OUTPUT]" in res
    assert "Detected Mode: strict" in res
    assert "Write a test prompt" in res


def test_get_ai_provider_fallback():
    provider = get_ai_provider()
    assert hasattr(provider, "generate")


def test_openrouter_provider_initialization():
    from app.modules.ai_engine.openrouter_provider import OpenRouterProvider
    provider = OpenRouterProvider(api_key="test_key", model_name="nvidia/nemotron-3-super-120b-a12b:free")
    assert provider.provider_name == "openrouter (nvidia/nemotron-3-super-120b-a12b:free)"


def test_google_gemini_provider_initialization():
    from app.modules.ai_engine.google_provider import GoogleGeminiProvider
    provider = GoogleGeminiProvider(api_key="test_key", model_name="gemini-3.6-flash")
    assert provider.provider_name == "google-gemini (gemini-3.6-flash)"
    assert provider._configured is True


def test_groq_provider_initialization():
    from app.modules.ai_engine.groq_provider import GroqProvider
    provider = GroqProvider(api_key="test_key", model_name="openai/gpt-oss-120b")
    assert provider.provider_name == "groq (openai/gpt-oss-120b)"
    assert provider.client is not None



