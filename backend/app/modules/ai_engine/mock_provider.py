from app.modules.ai_engine.base import AIProvider


class MockProvider(AIProvider):
    """
    Mock AI Provider used when no API key is configured or for local automated testing.
    Explicitly indicates that responses are simulated.
    """

    @property
    def provider_name(self) -> str:
        return "mock-provider"

    @property
    def supports_vision(self) -> bool:
        return True

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        # Detect mode from system instruction or prompt if present
        mode_str = "unknown"
        if "STRICT MODE" in system_instruction:
            mode_str = "strict"
        elif "NON-STRICT MODE" in system_instruction:
            mode_str = "non-strict"
        elif "SCRATCH MODE" in system_instruction:
            mode_str = "scratch"

        # Provide informative mock output preserving transparency
        mock_output = (
            "[MOCK AI OUTPUT]\n"
            "Processed request successfully using Mock AI Provider.\n"
            f"Detected Mode: {mode_str}\n\n"
            "System Instruction Summary:\n"
            f"{system_instruction[:150]}...\n\n"
            "Prompt Preview:\n"
            f"{prompt[:200]}...\n\n"
            "Note: To enable live AI generation, set 'GROQ_API_KEY', 'GOOGLE_API_KEY', 'OPENROUTER_API_KEY', or 'OPENAI_API_KEY' in your .env file."
        )

        return mock_output

    async def generate_with_vision(
        self, image_bytes: bytes, prompt: str, system_instruction: str = ""
    ) -> str:
        # Provide deterministic mock visual analysis content for test verification
        return (
            "The image is a visual document element (chart/diagram/figure). "
            "It displays a data trend with clearly visible headings, labels, and numbers. "
            "Values increase progressively across key categories."
        )

