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

    @abstractmethod
    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """
        Generate text output given a user prompt and optional system instruction.
        """
        pass
