import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.app_init import init_routers, setup_cors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load OCR models at startup to avoid cold start delays."""
    logger.info("Starting OCR API - preloading models...")
    from app.modules.ocr.services.ocr_service import get_ocr_reader
    get_ocr_reader()
    logger.info("EasyOCR models loaded")

    from app.modules.ocr.services.docling_service import get_docling_converter
    get_docling_converter()
    logger.info("Docling converter loaded")

    logger.info("All models loaded - server ready")
    yield
    logger.info("Shutting down OCR API")


app = FastAPI(
    title="OCR Extract API",
    description="API for extracting text from images and PDFs",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"status": "online"}


init_routers(app)
setup_cors(app)
