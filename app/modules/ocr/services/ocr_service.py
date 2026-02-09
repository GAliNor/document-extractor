import io
import logging
from typing import Any

import easyocr
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image

from app.core.config import get_settings
from app.modules.ocr.services.face_extraction_service import extract_faces_from_image

settings = get_settings()
logger = logging.getLogger(__name__)

# Global reader instance - loaded once at module import
_ocr_reader: easyocr.Reader | None = None


def get_ocr_reader() -> easyocr.Reader:
    """Get or initialize the OCR reader (singleton at module level)."""
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("Loading EasyOCR models for languages: %s", settings.OCR_LANGUAGES)
        _ocr_reader = easyocr.Reader(
            settings.OCR_LANGUAGES,
            gpu=False,
            verbose=False,
        )
        logger.info("EasyOCR models loaded successfully")
    return _ocr_reader


class OCRService:
    """OCR service for extracting text from images and PDFs."""

    def __init__(self):
        self._reader = get_ocr_reader()

    def _resize_if_large(self, image: Image.Image, max_dimension: int = 2000) -> Image.Image:
        """Resize image if too large to improve OCR speed."""
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * ratio), int(height * ratio))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        return image

    def extract_from_image(
        self, image_bytes: bytes, extract_images: bool = False
    ) -> dict[str, Any]:
        """Extract text from an image, optionally extracting face photos."""
        image = Image.open(io.BytesIO(image_bytes))
        image = self._resize_if_large(image)
        image_np = np.array(image.convert("RGB"))

        # detail=0 returns just text, detail=1 returns (bbox, text, confidence)
        results = self._reader.readtext(image_np, detail=1)

        text_lines = []
        confidences = []

        for bbox, text, confidence in results:
            text_lines.append(text)
            confidences.append(confidence)

        full_text = " ".join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        result = {
            "text": full_text,
            "confidence": round(avg_confidence, 2),
            "language_detected": self._detect_language(full_text),
        }

        if extract_images:
            result["extracted_images"] = extract_faces_from_image(image)

        return result

    def extract_from_pdf(
        self, pdf_bytes: bytes, max_pages: int = 10, extract_images: bool = False
    ) -> dict[str, Any]:
        """Extract text from a PDF by converting pages to images."""
        # Convert with DPI limit for speed (150 is good balance)
        images = convert_from_bytes(pdf_bytes, dpi=150)

        # Limit pages to prevent memory issues and long processing
        total_pages = len(images)
        images = images[:max_pages]

        all_text = []
        all_confidences = []
        all_extracted_images = []

        for i, image in enumerate(images, 1):
            image = self._resize_if_large(image)
            image_np = np.array(image.convert("RGB"))
            results = self._reader.readtext(image_np, detail=1)

            page_text = []
            for bbox, text, confidence in results:
                page_text.append(text)
                all_confidences.append(confidence)

            all_text.append(f"--- Page {i} ---\n{' '.join(page_text)}")

            if extract_images:
                all_extracted_images.extend(
                    extract_faces_from_image(image, page_number=i)
                )

        full_text = "\n\n".join(all_text)
        avg_confidence = (
            sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        )

        result = {
            "text": full_text,
            "confidence": round(avg_confidence, 2),
            "language_detected": self._detect_language(full_text),
            "pages": len(images),
            "total_pages": total_pages,
            "pages_processed": len(images),
        }

        if extract_images:
            result["extracted_images"] = all_extracted_images

        return result

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on French-specific characters."""
        french_chars = set("àâçéèêëîïôùûüÿæœ")
        french_count = sum(1 for c in text.lower() if c in french_chars)
        ratio = french_count / len(text) if text else 0
        return "fr" if ratio > 0.02 else "en"


def get_ocr_service() -> OCRService:
    return OCRService()
