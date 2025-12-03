import uuid
from pathlib import Path
from fastapi import APIRouter
from app.tools.test_runner import run_test
router = APIRouter(prefix="/running_test")
backed_dir = Path(__file__).resolve().parent.parent.parent.parent
print("backend dir:",backed_dir)
@router.post("/runs/{run_id}/test")
async def run_tests(run_id: uuid.UUID):
    repo_path = f"{backed_dir}/runs/{run_id}/repo"
    result = run_test(repo_path)
    return {"run_id": run_id,"test_result": result}
    