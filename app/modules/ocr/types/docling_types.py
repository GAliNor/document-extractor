from pydantic import BaseModel

from app.modules.ocr.types.ocr_types import FileInfo


class DoclingData(BaseModel):
    text: str
    markdown: str
    confidence: float | None = None
    language_detected: str
    processing_time_ms: int
    pages: int | None = None
    engine: str = "docling"


class DoclingResponse(BaseModel):
    success: bool
    data: DoclingData
    file_info: FileInfo
