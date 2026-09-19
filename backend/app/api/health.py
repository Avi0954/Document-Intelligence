from fastapi import APIRouter
from app.services.llm import gemini_llm_service
from app.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
def check_health():
    llm_status = gemini_llm_service.is_configured()
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "llm_configured": llm_status,
        "llm_model": settings.GEMINI_MODEL,
        "environment": "development"
    }
