import logging
from typing import List, Tuple, Optional
from app.modules.ingestion.service import ingestion_service
from app.modules.prompts.builder import prompt_builder
from app.modules.ai_engine import get_ai_provider
from app.schemas.processing import (
    ProcessingMode,
    PipelineStep,
    ProcessResponse,
    ExtractionResult,
)

logger = logging.getLogger(__name__)


class ContentProcessor:
    """
    Central orchestration service managing the processing pipeline lifecycle:
    INPUT -> EXTRACTION -> AI ENGINE -> OUTPUT
    """

    async def process_request(
        self,
        mode_input: str,
        prompt: str,
        files: Optional[List[Tuple[str, bytes]]] = None,
    ) -> ProcessResponse:
        try:
            # 1. Validate Mode
            mode_str = mode_input.strip().lower()
            valid_modes = [m.value for m in ProcessingMode]
            if mode_str not in valid_modes:
                return ProcessResponse(
                    success=False,
                    mode=mode_str,
                    error=f"Invalid mode '{mode_input}'. Must be one of: {', '.join(valid_modes)}",
                    pipeline_step=PipelineStep.INPUT,
                )

            mode = ProcessingMode(mode_str)
            files = files or []

            # 2. Input Validation Rules
            if mode == ProcessingMode.SCRATCH and not prompt.strip():
                return ProcessResponse(
                    success=False,
                    mode=mode.value,
                    error="Prompt is required in Scratch mode.",
                    pipeline_step=PipelineStep.INPUT,
                )

            if mode in (ProcessingMode.STRICT, ProcessingMode.NON_STRICT) and not prompt.strip():
                return ProcessResponse(
                    success=False,
                    mode=mode.value,
                    error=f"Prompt is required in {mode.value.title()} mode.",
                    pipeline_step=PipelineStep.INPUT,
                )

            # 3. Extraction Phase
            combined_source_content = ""
            extraction_results: List[ExtractionResult] = []

            if files and mode != ProcessingMode.SCRATCH:
                combined_source_content, extraction_results = ingestion_service.process_files_and_combine(files)

                # Check if file extraction had critical failures
                failed_files = [res.filename for res in extraction_results if res.extraction_status == "failed"]
                if failed_files and not combined_source_content:
                    return ProcessResponse(
                        success=False,
                        mode=mode.value,
                        error=f"Failed to extract content from files: {', '.join(failed_files)}",
                        pipeline_step=PipelineStep.EXTRACTION,
                    )

            if mode == ProcessingMode.STRICT and files and not combined_source_content:
                return ProcessResponse(
                    success=False,
                    mode=mode.value,
                    error="Strict Mode requires readable source content from uploaded files, but no text could be extracted.",
                    pipeline_step=PipelineStep.EXTRACTION,
                )

            # 4. Prompt Builder Phase
            system_instruction, formatted_prompt = prompt_builder.build_prompt(
                mode=mode,
                user_prompt=prompt,
                source_content=combined_source_content,
            )

            # 5. AI Engine Invocation Phase
            provider = get_ai_provider()
            logger.info(f"Invoking AI Provider '{provider.provider_name}' for mode '{mode.value}'")

            generated_output = await provider.generate(
                prompt=formatted_prompt,
                system_instruction=system_instruction,
            )

            # 6. Success Output Response
            file_summaries = [
                {
                    "filename": r.filename,
                    "file_type": r.file_type,
                    "status": r.extraction_status.value,
                    "char_count": len(r.text),
                    "metadata": r.metadata,
                }
                for r in extraction_results
            ]

            return ProcessResponse(
                success=True,
                mode=mode.value,
                content=generated_output,
                pipeline_step=PipelineStep.OUTPUT,
                extracted_files=file_summaries if file_summaries else None,
            )

        except Exception as e:
            logger.exception("ContentProcessor execution error")
            return ProcessResponse(
                success=False,
                mode=mode_input,
                error=f"Processing error: {str(e)}",
                pipeline_step=PipelineStep.AI_ENGINE,
            )


content_processor = ContentProcessor()
