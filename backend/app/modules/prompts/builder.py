from typing import Tuple
from app.schemas.processing import ProcessingMode


class PromptBuilder:
    """
    Prompt Builder constructing system instructions and user prompts based on processing mode.
    """

    STRICT_SYSTEM_INSTRUCTION = (
        "You are an exact, factually-grounded AI content processor operating in STRICT MODE.\n"
        "RULES:\n"
        "1. You must use ONLY the provided source content.\n"
        "2. Do NOT use external knowledge, internet information, or personal assumptions.\n"
        "3. Do NOT invent facts, hallucinate, or draw unsupported conclusions.\n"
        "4. If requested information is not present in the supplied material, state clearly: 'The requested information is not present in the provided source material.'"
    )

    NON_STRICT_SYSTEM_INSTRUCTION = (
        "You are an analytical AI content engine operating in NON-STRICT MODE.\n"
        "RULES:\n"
        "1. The provided source content is your primary context.\n"
        "2. You may analyze, interpret, expand, and enhance the information.\n"
        "3. You may add reasonable contextual details while keeping the output centered around the supplied content."
    )

    SCRATCH_SYSTEM_INSTRUCTION = (
        "You are a creative and precise AI content assistant operating in SCRATCH MODE.\n"
        "Execute the user's task directly based on your prompt."
    )

    @classmethod
    def build_prompt(
        self,
        mode: ProcessingMode | str,
        user_prompt: str,
        source_content: str = ""
    ) -> Tuple[str, str]:
        """
        Returns (system_instruction, user_prompt) tuple.
        """
        mode_str = mode.value if isinstance(mode, ProcessingMode) else str(mode).lower()

        if mode_str == ProcessingMode.STRICT.value:
            system_inst = self.STRICT_SYSTEM_INSTRUCTION
            formatted_user_prompt = f"Source Content:\n{source_content}\n\nTask:\n{user_prompt}"
            return system_inst, formatted_user_prompt

        elif mode_str == ProcessingMode.NON_STRICT.value:
            system_inst = self.NON_STRICT_SYSTEM_INSTRUCTION
            formatted_user_prompt = f"Source Content:\n{source_content}\n\nTask:\n{user_prompt}"
            return system_inst, formatted_user_prompt

        elif mode_str == ProcessingMode.SCRATCH.value:
            system_inst = self.SCRATCH_SYSTEM_INSTRUCTION
            formatted_user_prompt = f"Task:\n{user_prompt}"
            return system_inst, formatted_user_prompt

        else:
            raise ValueError(f"Invalid processing mode: '{mode_str}'")


prompt_builder = PromptBuilder()
