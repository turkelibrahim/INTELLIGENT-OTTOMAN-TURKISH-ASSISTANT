"""
Ana API router'ı. Tüm alt route'ları birleştirir.
"""
from fastapi import APIRouter

from app.api.routes.analysis import router as analysis_router
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.modernization import router as modernization_router
from app.api.routes.ocr_review import router as ocr_review_router
from app.api.routes.pages import router as pages_router
from app.api.routes.preprocessing import router as preprocessing_router
from app.api.routes.transliteration import router as transliteration_router
from app.api.routes.chat import router as chat_router
from app.api.routes.export import router as export_router
from app.api.routes.document_export import router as document_export_router
from app.api.routes.document_analysis import router as document_analysis_router
from app.api.routes.ocr import router as ocr_router
from app.api.routes.ground_truth import router as ground_truth_router
from app.api.routes.annotation import router as annotation_router
from app.api.routes.system import router as system_router

api_router = APIRouter()

api_router.include_router(analysis_router)
api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(modernization_router)
api_router.include_router(ocr_review_router)
api_router.include_router(pages_router)
api_router.include_router(preprocessing_router)
api_router.include_router(transliteration_router)
api_router.include_router(chat_router)
api_router.include_router(export_router, prefix="/annotation", tags=["Annotation Export"])
api_router.include_router(document_export_router)
api_router.include_router(document_analysis_router)
api_router.include_router(ocr_router)
api_router.include_router(ground_truth_router)
api_router.include_router(annotation_router, prefix="/annotation", tags=["Annotation"])
api_router.include_router(system_router)
