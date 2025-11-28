from fastapi import APIRouter
# from app.api.routes import pr_ingest
from app.api.routes import pr_ingest, analysis
api_router = APIRouter()
api_router.include_router(pr_ingest.router)
api_router.include_router(analysis.router)