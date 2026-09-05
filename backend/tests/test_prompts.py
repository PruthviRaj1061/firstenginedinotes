import pytest
from app.modules.prompts.builder import prompt_builder
from app.schemas.processing import ProcessingMode


def test_strict_prompt_generation():
    sys_inst, user_prompt = prompt_builder.build_prompt(
        mode=ProcessingMode.STRICT,
        user_prompt="Summarize this text",
        source_content="--- FILE: doc.txt ---\nThe quick brown fox jumps over the lazy dog.",
    )

    assert "STRICT MODE" in sys_inst
    assert "ONLY the provided source content" in sys_inst
    assert "The quick brown fox" in user_prompt
    assert "Summarize this text" in user_prompt


def test_non_strict_prompt_generation():
    sys_inst, user_prompt = prompt_builder.build_prompt(
        mode=ProcessingMode.NON_STRICT,
        user_prompt="Expand on the background",
        source_content="--- FILE: summary.md ---\nProject launched in 2026.",
    )

    assert "NON-STRICT MODE" in sys_inst
    assert "expand, and enhance" in sys_inst
    assert "Project launched in 2026" in user_prompt
    assert "Expand on the background" in user_prompt


def test_scratch_prompt_generation():
    sys_inst, user_prompt = prompt_builder.build_prompt(
        mode=ProcessingMode.SCRATCH,
        user_prompt="Write a poem about space exploration",
    )

    assert "SCRATCH MODE" in sys_inst
    assert "Task:\nWrite a poem about space exploration" in user_prompt
    assert "Source Content" not in user_prompt
