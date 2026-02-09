import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.core.auth import verify_api_key
from app.core.config import get_settings
from app.modules.ocr.services.docling_service import get_docling_service
from app.modules.ocr.types.docling_types import DoclingResponse, DoclingData
from app.modules.ocr.types.ocr_types import FileInfo

router = APIRouter()
settings = get_settings()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/docling-extract",
    response_model=DoclingResponse,
    dependencies=[Depends(verify_api_key)],
)
async def docling_extract_text(
    file: UploadFile = File(...),
):
    """Extract text from a document using Docling (for benchmarking against EasyOCR)."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPG, PNG, WEBP, PDF",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    docling_service = get_docling_service()
    start_time = time.time()

    try:
        result = docling_service.extract_from_file(
            content, filename=file.filename or "document.pdf"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Docling processing failed: {str(e)}",
        )

    processing_time_ms = int((time.time() - start_time) * 1000)

    return DoclingResponse(
        success=True,
        data=DoclingData(
            text=result["text"],
            markdown=result["markdown"],
            confidence=result["confidence"],
            language_detected=result["language_detected"],
            processing_time_ms=processing_time_ms,
            pages=result.get("pages"),
        ),
        file_info=FileInfo(
            name=file.filename or "unknown",
            size=len(content),
            type=file.content_type or "unknown",
        ),
    )
