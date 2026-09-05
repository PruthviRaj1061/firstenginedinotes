from app.modules.ai_engine.base import AIProvider


class MockProvider(AIProvider):
    """
    Mock AI Provider used when no API key is configured or for local automated testing.
    Explicitly indicates that responses are simulated.
    """

    @property
    def provider_name(self) -> str:
        return "mock-provider"

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
            "Note: To enable live generation using GPT models, set 'OPENAI_API_KEY' in your .env file."
        )

        return mock_output
