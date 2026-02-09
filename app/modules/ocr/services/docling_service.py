import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_docling_converter: DocumentConverter | None = None


def get_docling_converter() -> DocumentConverter:
    """Get or initialize the Docling converter (singleton at module level)."""
    global _docling_converter
    if _docling_converter is None:
        logger.info("Loading Docling document converter...")
        _docling_converter = DocumentConverter()
        logger.info("Docling converter loaded successfully")
    return _docling_converter


class DoclingService:
    """Docling-based document extraction service for benchmarking."""

    def __init__(self):
        self._converter = get_docling_converter()

    def extract_from_file(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """Extract text from a document using Docling."""
        suffix = Path(filename).suffix or ".pdf"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            result = self._converter.convert(tmp_path)

            markdown_text = result.document.export_to_markdown()
            plain_text = self._markdown_to_plain_text(markdown_text)

            pages = None
            if hasattr(result.document, "num_pages"):
                pages = result.document.num_pages()
            elif hasattr(result.document, "pages"):
                pages = len(result.document.pages)

            return {
                "text": plain_text,
                "markdown": markdown_text,
                "confidence": None,
                "language_detected": self._detect_language(plain_text),
                "pages": pages,
            }
        finally:
            os.unlink(tmp_path)

    def _markdown_to_plain_text(self, markdown: str) -> str:
        """Strip markdown syntax for fair text comparison with EasyOCR output."""
        text = markdown
        text = re.sub(r"#{1,6}\s+", "", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on French-specific characters."""
        french_chars = set("àâçéèêëîïôùûüÿæœ")
        french_count = sum(1 for c in text.lower() if c in french_chars)
        ratio = french_count / len(text) if text else 0
        return "fr" if ratio > 0.02 else "en"


def get_docling_service() -> DoclingService:
    return DoclingService()
