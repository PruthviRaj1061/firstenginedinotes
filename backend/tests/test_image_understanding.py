import os
import pytest
import random
from io import BytesIO
from PIL import Image
import fitz

from app.modules.ai_engine.mock_provider import MockProvider
from app.modules.ai_engine.google_provider import GoogleGeminiProvider
from app.modules.ai_engine.openai_provider import OpenAIProvider
from app.modules.ai_engine.openrouter_provider import OpenRouterProvider
from app.modules.ai_engine.groq_provider import GroqProvider
from app.modules.ingestion.image_extractor_utils import (
    extract_images_from_pdf,
    extract_images_from_docx,
    extract_images_from_standalone_image,
    compute_md5_hash,
    ExtractedImageItem,
)
from app.modules.ingestion.image_understanding import (
    ImageUnderstandingService,
    VISION_SYSTEM_INSTRUCTION,
)


def create_sample_pdf_with_image() -> bytes:
    """Helper to create a PDF containing an embedded RGB image with uncompressible noise > 2KB."""
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((50, 50), "Hello document with embedded image.")

    # Create a 300x300 image with random pixels so PNG compressed bytes > 2000 bytes
    img = Image.new("RGB", (300, 300))
    pixels = [
        (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for _ in range(300 * 300)
    ]
    img.putdata(pixels)

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    rect = fitz.Rect(100, 100, 400, 400)
    page.insert_image(rect, stream=img_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_small_icon_pdf() -> bytes:
    """Helper to create a PDF containing a small icon (50x50px) that should be filtered out."""
    doc = fitz.open()
    page = doc.new_page()
    img = Image.new("RGB", (50, 50), color=(0, 255, 0))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    page.insert_image(fitz.Rect(10, 10, 60, 60), stream=img_byte_arr.getvalue())
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# --- 1. Provider Vision Support Tests ---

def test_provider_supports_vision_flags():
    mock = MockProvider()
    assert mock.supports_vision is True

    gemini = GoogleGeminiProvider(api_key="test", model_name="gemini-1.5-flash")
    assert gemini.supports_vision is True

    openai = OpenAIProvider(api_key="test", model_name="gpt-4o")
    assert openai.supports_vision is True

    openrouter = OpenRouterProvider(api_key="test", model_name="nvidia/nemotron-3")
    assert openrouter.supports_vision is True

    groq = GroqProvider(api_key="test", model_name="llama3")
    assert groq.supports_vision is False


@pytest.mark.asyncio
async def test_mock_provider_generate_with_vision():
    mock = MockProvider()
    img_bytes = b"test_image_bytes"
    res = await mock.generate_with_vision(image_bytes=img_bytes, prompt="Describe this image")
    assert "The image is a visual document element" in res


# --- 2. Image Extraction & Filtering Tests ---

def test_extract_images_from_pdf():
    pdf_bytes = create_sample_pdf_with_image()
    extracted = extract_images_from_pdf(pdf_bytes)
    assert len(extracted) == 1
    assert extracted[0].width >= 100
    assert extracted[0].height >= 100
    assert extracted[0].page_number == 1


def test_filter_small_images():
    pdf_bytes = create_small_icon_pdf()
    extracted = extract_images_from_pdf(pdf_bytes)
    # Small images (<100x100 or <2KB) must be filtered out
    assert len(extracted) == 0


def test_compute_image_hash_deduplication():
    b1 = b"test_byte_array_1"
    b2 = b"test_byte_array_1"
    b3 = b"test_byte_array_2"

    h1 = compute_md5_hash(b1)
    h2 = compute_md5_hash(b2)
    h3 = compute_md5_hash(b3)

    assert h1 == h2
    assert h1 != h3


# --- 3. Image Understanding Service Tests ---

@pytest.mark.asyncio
async def test_image_understanding_service_enrichment_mock():
    mock_provider = MockProvider()
    service = ImageUnderstandingService()

    pdf_bytes = create_sample_pdf_with_image()
    images = extract_images_from_pdf(pdf_bytes)

    initial_md = "# Sample Document\nThis is a sample document text."
    enriched_md, meta = await service.analyze_and_enrich_markdown(
        markdown_text=initial_md,
        image_items=images,
        provider=mock_provider,
    )

    assert meta["image_context_method"] == "vision"
    assert meta["images_analyzed"] == 1
    assert meta["image_count"] == 1
    assert "## Embedded Image Context" in enriched_md
    assert "### Image 1 — Page 1" in enriched_md
    assert "The image is a visual document element" in enriched_md


@pytest.mark.asyncio
async def test_image_understanding_service_deduplication():
    mock_provider = MockProvider()
    service = ImageUnderstandingService()

    # Create two ExtractedImageItems with identical MD5 hash
    dummy_bytes = b"identical_image_data_bytes_long_enough"
    md5 = compute_md5_hash(dummy_bytes)

    extracted1 = ExtractedImageItem(
        image_bytes=dummy_bytes,
        page_number=1,
        image_index=1,
        width=120,
        height=120,
        md5_hash=md5,
        context_label="Image 1 — Page 1",
    )
    extracted2 = ExtractedImageItem(
        image_bytes=dummy_bytes,
        page_number=2,
        image_index=2,
        width=120,
        height=120,
        md5_hash=md5,
        context_label="Image 2 — Page 2",
    )

    initial_md = "# Multi-page Doc"
    enriched_md, meta = await service.analyze_and_enrich_markdown(
        markdown_text=initial_md,
        image_items=[extracted1, extracted2],
        provider=mock_provider,
    )

    # Both image items are successfully analyzed and resolved (one via primary vision, one via hash cache)
    assert meta["images_analyzed"] == 2
    # Both images must be referenced in Markdown
    assert "### Image 1 — Page 1" in enriched_md
    assert "### Image 2 — Page 2" in enriched_md


def test_anti_hallucination_prompt_content():
    assert "Describe ONLY information that is directly visible" in VISION_SYSTEM_INSTRUCTION
    assert "CRITICAL SECURITY RULE" in VISION_SYSTEM_INSTRUCTION
    assert "unreadable" in VISION_SYSTEM_INSTRUCTION


@pytest.mark.asyncio
async def test_image_understanding_resilience_when_vision_fails():
    """Verify Markdown creation succeeds even if vision provider fails and OCR is unavailable."""
    class FailingVisionProvider(MockProvider):
        @property
        def supports_vision(self) -> bool:
            return True

        async def generate_with_vision(self, image_bytes: bytes, prompt: str, system_instruction: str = "", image_format: str = "png") -> str:
            raise RuntimeError("Simulated Vision API failure")

    failing_provider = FailingVisionProvider()
    service = ImageUnderstandingService()

    dummy_item = ExtractedImageItem(
        image_bytes=b"dummy_bytes_data",
        page_number=1,
        image_index=1,
        width=200,
        height=200,
        md5_hash=compute_md5_hash(b"dummy_bytes_data"),
        context_label="Image 1 — Page 1",
    )

    initial_md = "# Resilient Document\nDocument body text."
    enriched_md, meta = await service.analyze_and_enrich_markdown(
        markdown_text=initial_md,
        image_items=[dummy_item],
        provider=failing_provider,
    )

    # Document text MUST remain intact
    assert "Document body text." in enriched_md
    # Unavailable metadata metric is correctly tracked
    assert meta["image_context_method"] == "unavailable"
    assert meta["images_analyzed"] == 0
