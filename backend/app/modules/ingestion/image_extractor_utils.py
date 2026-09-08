import io
import os
import zipfile
import hashlib
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from PIL import Image

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    docx = None
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

# Minimum thresholds to ignore tiny icons, decorative lines, and UI bullets
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100
MIN_IMAGE_BYTES = 2000
MAX_IMAGE_DIMENSION = 1560


@dataclass
class ExtractedImageItem:
    image_bytes: bytes
    page_number: Optional[int]
    image_index: int
    width: int
    height: int
    md5_hash: str
    context_label: str
    original_format: str = "png"


def compute_md5_hash(data: bytes) -> str:
    """Computes MD5 hash for image byte deduplication."""
    return hashlib.md5(data).hexdigest()


def resize_image_if_needed(image_bytes: bytes, max_dimension: int = MAX_IMAGE_DIMENSION) -> bytes:
    """
    Resizes image proportionally if max dimension exceeds max_dimension.
    Preserves aspect ratio and text legibility.
    """
    if not image_bytes:
        return image_bytes

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        w, h = pil_img.size

        if w <= max_dimension and h <= max_dimension:
            return image_bytes

        # Calculate proportional downscaling factor
        scale = min(max_dimension / float(w), max_dimension / float(h))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        # Convert RGBA/Palette images to RGB if saving as JPEG
        resample_filter = getattr(Image, "Resampling", Image).LANCZOS
        resized_img = pil_img.resize((new_w, new_h), resample_filter)

        out_buffer = io.BytesIO()
        fmt = pil_img.format if pil_img.format in ["PNG", "JPEG", "WEBP"] else "PNG"
        resized_img.save(out_buffer, format=fmt)
        return out_buffer.getvalue()

    except Exception as e:
        logger.warning(f"[IMAGE_EXTRACTOR] Error resizing image: {e}")
        return image_bytes


def is_meaningful_image(w: int, h: int, byte_length: int) -> bool:
    """
    Conservative filtering: Returns True if image meets minimum width/height/size thresholds.
    """
    return w >= MIN_IMAGE_WIDTH and h >= MIN_IMAGE_HEIGHT and byte_length >= MIN_IMAGE_BYTES


def extract_images_with_stats_from_pdf(file_bytes: bytes) -> Tuple[List[ExtractedImageItem], dict]:
    """
    Extracts embedded images from PDF document using PyMuPDF (fitz).
    Returns (extracted_images_list, extraction_stats_dict).
    """
    if not PYMUPDF_AVAILABLE:
        logger.warning("[IMAGE_EXTRACTOR] PyMuPDF (fitz) not available for PDF image extraction.")
        return [], {"images_detected": 0, "images_filtered": 0, "images_unique": 0}

    images: List[ExtractedImageItem] = []
    global_index = 1
    total_detected = 0
    total_filtered = 0
    seen_hashes = set()

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            image_info_list = page.get_images(full=True)

            for img_idx, img_info in enumerate(image_info_list):
                total_detected += 1
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image.get("image")
                    img_ext = (base_image.get("ext") or "png").lower()
                    w = base_image.get("width", 0)
                    h = base_image.get("height", 0)

                    if not img_bytes:
                        total_filtered += 1
                        continue

                    # Validate bytes with PIL
                    try:
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        pil_w, pil_h = pil_img.size
                        if w == 0 or h == 0:
                            w, h = pil_w, pil_h
                        if not img_ext or img_ext == "png":
                            img_ext = (pil_img.format or "png").lower()
                    except Exception as pil_err:
                        logger.warning(f"[IMAGE_EXTRACTOR] PIL validation failed for PDF image xref {xref}: {pil_err}")
                        total_filtered += 1
                        continue

                    if is_meaningful_image(w, h, len(img_bytes)):
                        resized_bytes = resize_image_if_needed(img_bytes)
                        md5 = compute_md5_hash(img_bytes)
                        context_label = f"Image {global_index} — Page {page_num}"
                        seen_hashes.add(md5)

                        images.append(
                            ExtractedImageItem(
                                image_bytes=resized_bytes,
                                page_number=page_num,
                                image_index=global_index,
                                width=w,
                                height=h,
                                md5_hash=md5,
                                context_label=context_label,
                                original_format=img_ext,
                            )
                        )
                        global_index += 1
                    else:
                        total_filtered += 1
                except Exception as img_err:
                    logger.warning(f"[IMAGE_EXTRACTOR] Failed to extract PDF image xref {xref}: {img_err}")
                    total_filtered += 1

        doc.close()
    except Exception as e:
        logger.error(f"[IMAGE_EXTRACTOR] PDF image extraction error: {e}")

    stats = {
        "images_detected": total_detected,
        "images_filtered": total_filtered,
        "images_unique": len(seen_hashes),
    }

    return images, stats


def extract_images_from_pdf(file_bytes: bytes) -> List[ExtractedImageItem]:
    """
    Extracts embedded images from PDF document using PyMuPDF (fitz).
    Captures page numbers, image indices, dimensions, and MD5 hashes.
    """
    images, _ = extract_images_with_stats_from_pdf(file_bytes)
    return images


def extract_images_from_docx(file_bytes: bytes) -> List[ExtractedImageItem]:
    """
    Extracts embedded images from Microsoft Word (.docx) document via ZIP package media inspection.
    """
    images: List[ExtractedImageItem] = []
    global_index = 1

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            media_files = [f for f in z.namelist() if f.startswith("word/media/")]

            for media_path in sorted(media_files):
                img_bytes = z.read(media_path)
                if not img_bytes or len(img_bytes) < MIN_IMAGE_BYTES:
                    continue

                try:
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    w, h = pil_img.size
                    fmt = (pil_img.format or "png").lower()

                    if is_meaningful_image(w, h, len(img_bytes)):
                        resized_bytes = resize_image_if_needed(img_bytes)
                        md5 = compute_md5_hash(img_bytes)
                        context_label = f"Image {global_index}"

                        images.append(
                            ExtractedImageItem(
                                image_bytes=resized_bytes,
                                page_number=None,
                                image_index=global_index,
                                width=w,
                                height=h,
                                md5_hash=md5,
                                context_label=context_label,
                                original_format=fmt,
                            )
                        )
                        global_index += 1
                except Exception as img_err:
                    logger.warning(f"[IMAGE_EXTRACTOR] Could not read DOCX media '{media_path}': {img_err}")

    except Exception as e:
        logger.error(f"[IMAGE_EXTRACTOR] DOCX image extraction error: {e}")

    return images


def extract_images_from_standalone_image(file_bytes: bytes, filename: str) -> List[ExtractedImageItem]:
    """
    Directly extracts and validates a standalone image file (PNG, JPG, JPEG, WEBP).
    """
    if not file_bytes:
        return []

    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        w, h = pil_img.size
        fmt = (pil_img.format or "png").lower()

        if is_meaningful_image(w, h, len(file_bytes)):
            resized_bytes = resize_image_if_needed(file_bytes)
            md5 = compute_md5_hash(file_bytes)
            clean_filename = os.path.basename(filename)

            return [
                ExtractedImageItem(
                    image_bytes=resized_bytes,
                    page_number=None,
                    image_index=1,
                    width=w,
                    height=h,
                    md5_hash=md5,
                    context_label=f"Image ({clean_filename})",
                    original_format=fmt,
                )
            ]
    except Exception as e:
        logger.error(f"[IMAGE_EXTRACTOR] Standalone image processing error for '{filename}': {e}")

    return []
