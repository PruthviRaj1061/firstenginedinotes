import os
import json
import time
import uuid
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Base storage directory for converted Markdown artifacts
BASE_TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")
CONVERSIONS_DIR = os.path.join(BASE_TEMP_DIR, "conversions")

# Regex to enforce safe opaque conversion IDs (UUIDs or hexadecimal strings without path traversal)
SAFE_ID_REGEX = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)


class ConversionStorage:
    """
    Service managing temporary Markdown conversion artifacts.
    Handles secure file persistence, metadata indexing, retrieval,
    and automatic expiration cleanup without exposing internal filesystem structures.
    """

    def __init__(self, storage_dir: str = CONVERSIONS_DIR, default_ttl_seconds: int = 3600):
        self.storage_dir = storage_dir
        self.default_ttl_seconds = default_ttl_seconds
        os.makedirs(self.storage_dir, exist_ok=True)

    def is_valid_id(self, conversion_id: str) -> bool:
        """
        Enforce strict validation of conversion IDs to prevent path traversal vulnerabilities.
        """
        if not conversion_id or not isinstance(conversion_id, str):
            return False
        return bool(SAFE_ID_REGEX.match(conversion_id))

    def generate_id(self) -> str:
        """
        Generate a unique opaque conversion ID.
        """
        return uuid.uuid4().hex

    def save_conversion(
        self,
        original_filename: str,
        markdown_text: str,
        source_size_bytes: int,
        extraction_method: str = "markitdown",
        fallback_used: bool = False,
        error_message: Optional[str] = None,
        custom_id: Optional[str] = None,
        image_count: int = 0,
        images_analyzed: int = 0,
        image_context_method: str = "none",
    ) -> Dict[str, Any]:
        """
        Persists generated Markdown content and metadata to disk.
        Returns the metadata dictionary for the saved artifact.
        """
        self.cleanup_expired_artifacts()

        conversion_id = custom_id if (custom_id and self.is_valid_id(custom_id)) else self.generate_id()

        # Derive a safe clean markdown filename, e.g., "report.pdf" -> "report.md"
        base_name = os.path.splitext(os.path.basename(original_filename))[0]
        if not base_name or base_name == ".":
            base_name = "document"
        # Sanitize filename characters for HTTP headers & browser downloads
        clean_base = re.sub(r'[^\w\-\.]', '_', base_name)
        markdown_filename = f"{clean_base}.md"

        markdown_bytes = markdown_text.encode("utf-8")
        markdown_size_bytes = len(markdown_bytes)
        char_count = len(markdown_text)

        metadata = {
            "id": conversion_id,
            "original_filename": os.path.basename(original_filename),
            "markdown_filename": markdown_filename,
            "source_size_bytes": source_size_bytes,
            "markdown_size_bytes": markdown_size_bytes,
            "char_count": char_count,
            "extraction_method": extraction_method,
            "output_format": "markdown",
            "fallback_used": fallback_used,
            "error_message": error_message,
            "created_at": time.time(),
            "image_count": image_count,
            "images_analyzed": images_analyzed,
            "image_context_method": image_context_method,
        }


        md_filepath = os.path.join(self.storage_dir, f"{conversion_id}.md")
        json_filepath = os.path.join(self.storage_dir, f"{conversion_id}.json")

        try:
            with open(md_filepath, "w", encoding="utf-8") as f:
                f.write(markdown_text)

            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(
                f"[CONVERSION_STORAGE] Saved conversion artifact id={conversion_id} file={markdown_filename} size={markdown_size_bytes}B"
            )
            return metadata
        except Exception as e:
            logger.error(f"[CONVERSION_STORAGE] Failed to save conversion artifact '{conversion_id}': {e}")
            raise

    def get_metadata(self, conversion_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves metadata for a valid conversion ID. Returns None if not found or invalid.
        """
        if not self.is_valid_id(conversion_id):
            return None

        json_filepath = os.path.join(self.storage_dir, f"{conversion_id}.json")
        if not os.path.exists(json_filepath):
            return None

        try:
            with open(json_filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[CONVERSION_STORAGE] Error reading metadata for '{conversion_id}': {e}")
            return None

    def get_markdown_filepath(self, conversion_id: str) -> Optional[str]:
        """
        Returns the absolute filesystem path for the Markdown artifact if valid and existing.
        """
        if not self.is_valid_id(conversion_id):
            return None

        md_filepath = os.path.join(self.storage_dir, f"{conversion_id}.md")
        if os.path.exists(md_filepath):
            return md_filepath
        return None

    def get_markdown_text(self, conversion_id: str) -> Optional[str]:
        """
        Reads and returns the Markdown content string for a valid conversion ID.
        """
        filepath = self.get_markdown_filepath(conversion_id)
        if not filepath:
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"[CONVERSION_STORAGE] Error reading Markdown file for '{conversion_id}': {e}")
            return None

    def cleanup_expired_artifacts(self, max_age_seconds: Optional[int] = None):
        """
        Deletes artifacts older than max_age_seconds (default 3600 seconds / 1 hour).
        """
        ttl = max_age_seconds if max_age_seconds is not None else self.default_ttl_seconds
        now = time.time()

        try:
            for filename in os.listdir(self.storage_dir):
                filepath = os.path.join(self.storage_dir, filename)
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > ttl:
                        try:
                            os.remove(filepath)
                            logger.info(f"[CONVERSION_STORAGE] Cleaned up expired artifact file '{filename}'")
                        except Exception as rm_err:
                            logger.warning(f"[CONVERSION_STORAGE] Failed to remove expired file '{filename}': {rm_err}")
        except Exception as e:
            logger.error(f"[CONVERSION_STORAGE] Error during artifact cleanup: {e}")


# Singleton instance
conversion_storage = ConversionStorage()
