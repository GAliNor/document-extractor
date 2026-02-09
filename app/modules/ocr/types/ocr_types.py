from pydantic import BaseModel


class FileInfo(BaseModel):
    name: str
    size: int
    type: str


class ExtractedImage(BaseModel):
    """A face/photo extracted from the document."""

    image_base64: str
    page: int | None = None
    bbox: dict[str, int]
    image_width: int
    image_height: int


class OCRData(BaseModel):
    text: str
    confidence: float
    language_detected: str
    processing_time_ms: int
    pages: int | None = None
    extracted_images: list[ExtractedImage] | None = None


class OCRResponse(BaseModel):
    success: bool
    data: OCRData
    file_info: FileInfo
