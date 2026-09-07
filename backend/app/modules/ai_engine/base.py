from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Abstract AIProvider interface for LLM integrations.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name/Identifier of the AI provider."""
        pass

    @property
    def supports_vision(self) -> bool:
        """
        Indicates whether this provider/model configuration supports vision analysis.
        Defaults to False unless overridden by a vision-capable provider adapter.
        """
        return False

    @abstractmethod
    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """
        Generate text output given a user prompt and optional system instruction.
        """
        pass

    async def generate_with_vision(
        self, image_bytes: bytes, prompt: str, system_instruction: str = ""
    ) -> str:
        """
        Analyze image binary given a prompt and optional system instruction.
        """
        raise NotImplementedError(f"AI Provider '{self.provider_name}' does not support vision analysis.")

