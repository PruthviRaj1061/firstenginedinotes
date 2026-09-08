import logging
from typing import List, Tuple, Optional
from app.services.conversion_storage import conversion_storage
from app.modules.ingestion.service import ingestion_service
from app.modules.prompts.builder import prompt_builder
from app.modules.ai_engine import get_ai_provider
from app.schemas.processing import (
    ProcessingMode,
    PipelineStep,
    ProcessResponse,
    ExtractionResult,
    ConversionItem,
)

logger = logging.getLogger(__name__)


class ContentProcessor:
    """
    Central orchestration service managing the processing pipeline lifecycle:
    INPUT -> CONVERSION / MARKDOWN READY -> AI ENGINE -> OUTPUT
    """

    async def process_request(
        self,
        mode_input: str,
        prompt: str,
        files: Optional[List[Tuple[str, bytes]]] = None,
        conversion_ids: Optional[List[str]] = None,
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
            conversion_ids = [cid for cid in (conversion_ids or []) if cid and cid.strip()]

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

            # 3. Source Retrieval / Extraction Phase
            combined_source_content = ""
            extraction_results: List[ExtractionResult] = []
            conversion_items: List[ConversionItem] = []

            if mode != ProcessingMode.SCRATCH:
                # Option A: Conversion IDs passed from prior conversion stage
                if conversion_ids:
                    combined_blocks = []
                    for cid in conversion_ids:
                        meta = conversion_storage.get_metadata(cid)
                        md_text = conversion_storage.get_markdown_text(cid)
                        if meta and md_text is not None:
                            fname = meta.get("original_filename", "document")
                            safe_filename = fname.replace("#", "")
                            combined_blocks.append(f"# Source: {safe_filename}\n\n{md_text.strip()}")

                            conversion_items.append(
                                ConversionItem(
                                    id=cid,
                                    original_filename=fname,
                                    markdown_filename=meta.get("markdown_filename", f"{fname}.md"),
                                    source_size_bytes=meta.get("source_size_bytes", 0),
                                    markdown_size_bytes=meta.get("markdown_size_bytes", len(md_text)),
                                    char_count=meta.get("char_count", len(md_text)),
                                    extraction_method=meta.get("extraction_method", "markitdown"),
                                    output_format="markdown",
                                    fallback_used=meta.get("fallback_used", False),
                                    error_message=meta.get("error_message"),
                                    image_count=meta.get("image_count", 0),
                                    images_filtered=meta.get("images_filtered", 0),
                                    images_unique=meta.get("images_unique", 0),
                                    images_analyzed=meta.get("images_analyzed", 0),
                                    images_unavailable=meta.get("images_unavailable", 0),
                                    image_context_method=meta.get("image_context_method", "none"),
                                    text=md_text if len(md_text) <= 2000 else None,
                                )
                            )
                    combined_source_content = "\n\n---\n\n".join(combined_blocks).strip()

                # Option B: Files directly passed in process request
                elif files:
                    combined_source_content, extraction_results, combined_id = (
                        await ingestion_service.process_files_and_combine(files)
                    )

                    # Build conversion items from extraction results
                    for res in extraction_results:
                        if res.id:
                            meta = conversion_storage.get_metadata(res.id)
                            if meta:
                                conversion_items.append(
                                    ConversionItem(
                                        id=res.id,
                                        original_filename=res.filename,
                                        markdown_filename=meta.get("markdown_filename", f"{res.filename}.md"),
                                        source_size_bytes=meta.get("source_size_bytes", 0),
                                        markdown_size_bytes=meta.get("markdown_size_bytes", len(res.text)),
                                        char_count=len(res.text),
                                        extraction_method=res.extraction_method,
                                        output_format="markdown",
                                        fallback_used=res.fallback_used,
                                        error_message=res.error_message,
                                        image_count=res.image_count,
                                        images_filtered=res.images_filtered,
                                        images_unique=res.images_unique,
                                        images_analyzed=res.images_analyzed,
                                        images_unavailable=res.images_unavailable,
                                        image_context_method=res.image_context_method,
                                        text=res.text if len(res.text) <= 2000 else None,
                                    )
                                )

                    # Check for failures if no content was extracted
                    failed_details = [
                        f"'{res.filename}' ({res.error_message})" if res.error_message else f"'{res.filename}'"
                        for res in extraction_results
                        if res.extraction_status == "failed"
                    ]
                    if failed_details and not combined_source_content:
                        return ProcessResponse(
                            success=False,
                            mode=mode.value,
                            error=f"Failed to extract content from files — {'; '.join(failed_details)}",
                            pipeline_step=PipelineStep.CONVERSION,
                        )

            if mode == ProcessingMode.STRICT and (files or conversion_ids) and not combined_source_content:
                return ProcessResponse(
                    success=False,
                    mode=mode.value,
                    error="Strict Mode requires readable source content from uploaded files, but no text could be extracted.",
                    pipeline_step=PipelineStep.CONVERSION,
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
                    "filename": item.original_filename,
                    "file_type": item.original_filename.split(".")[-1] if "." in item.original_filename else "txt",
                    "status": "success",
                    "char_count": item.char_count,
                    "extraction_method": item.extraction_method,
                    "output_format": item.output_format,
                    "fallback_used": item.fallback_used,
                    "text": item.text,
                    "metadata": {"conversion_id": item.id},
                }
                for item in conversion_items
            ]

            return ProcessResponse(
                success=True,
                mode=mode.value,
                content=generated_output,
                source_markdown=combined_source_content if combined_source_content else None,
                pipeline_step=PipelineStep.OUTPUT,
                extracted_files=file_summaries if file_summaries else None,
                conversions=conversion_items if conversion_items else None,
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

