import time

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File

from app.core.auth import verify_api_key
from app.core.config import get_settings
from app.modules.ocr.services.ocr_service import get_ocr_service
from app.modules.ocr.types.ocr_types import OCRResponse, OCRData, ExtractedImage, FileInfo

router = APIRouter()
settings = get_settings()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_PDF_TYPE = "application/pdf"
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/extract", response_model=OCRResponse, dependencies=[Depends(verify_api_key)])
async def extract_text(
    file: UploadFile = File(...),
    extract_images: bool = Query(
        default=False,
        description="Extract face/photo images from the document using face detection",
    ),
):
    """Extract text from an image or PDF file, optionally extracting face photos."""
    if file.content_type not in ALLOWED_IMAGE_TYPES and file.content_type != ALLOWED_PDF_TYPE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: JPG, PNG, WEBP, PDF",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    ocr_service = get_ocr_service()
    start_time = time.time()

    try:
        if file.content_type == ALLOWED_PDF_TYPE:
            result = ocr_service.extract_from_pdf(content, extract_images=extract_images)
        else:
            result = ocr_service.extract_from_image(content, extract_images=extract_images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    processing_time_ms = int((time.time() - start_time) * 1000)

    extracted_images = None
    if "extracted_images" in result:
        extracted_images = [ExtractedImage(**img) for img in result["extracted_images"]]

    return OCRResponse(
        success=True,
        data=OCRData(
            text=result["text"],
            confidence=result["confidence"],
            language_detected=result["language_detected"],
            processing_time_ms=processing_time_ms,
            pages=result.get("pages"),
            extracted_images=extracted_images,
        ),
        file_info=FileInfo(
            name=file.filename or "unknown",
            size=len(content),
            type=file.content_type or "unknown",
        ),
    )
