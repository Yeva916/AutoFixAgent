# import sys
# print("RUNNING WITH PYTHON:", sys.executable)
# print("LOOKING FOR PACKAGES IN:", sys.path)
from fastapi import APIRouter
# from app.api.routes import pr_ingest
from app.api.routes import pr_ingest, analysis,running_test
api_router = APIRouter()
api_router.include_router(pr_ingest.router)
api_router.include_router(analysis.router)
api_router.include_router(running_test.router)