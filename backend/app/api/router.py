from fastapi import APIRouter
from app.api import health, auth, documents, questions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(questions.router)
