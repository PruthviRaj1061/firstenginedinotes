from abc import ABC, abstractmethod
from app.schemas.processing import ExtractionResult


class BaseExtractor(ABC):
    """
    Abstract Base Extractor interface for all document and image extractors.
    """

    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        """
        Extract text and metadata from file bytes.
        """
        pass
