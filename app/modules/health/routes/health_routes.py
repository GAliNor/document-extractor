from datetime import datetime

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "OCR Extract API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT,
    }
