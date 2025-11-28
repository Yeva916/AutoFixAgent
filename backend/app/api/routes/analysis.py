import json
from pathlib import Path
from fastapi import APIRouter
from app.tools.static_analyze import static_analysis
import uuid

router = APIRouter(prefix="/analysis")
backed_dir = Path(__file__).resolve().parent.parent.parent.parent
@router.post("/runs/{run_id}/analyze")
async def analysis(run_id: uuid.UUID):
    repo_path = f"{backed_dir}/runs/{run_id}/repo"
    print(repo_path)
    with open(f"{backed_dir}/runs/{run_id}/changed_files.json","r",encoding="utf-8") as f:
        file_changes = json.load(f)
    files = [file["absolute_path"] for file in file_changes]
    if files:
        diagnostics = static_analysis(repo_path, files)
    else:
        diagnostics = static_analysis(repo_path, None)
    with open(f"{backed_dir}/runs/{run_id}/diagnostics.json","w",encoding="utf-8") as f:
        json.dump(diagnostics,f,indent=4)
    sev_count = {"error":0,"warning":0}
    for diag in diagnostics:
        sev_count[diag["severity"]] += 1
    #print(f"Static analysis completed: {diag_count} issues found ({sev_count['error']} errors, {sev_count['warning']} warnings).")
    return {"run_id": run_id,"status": "analysis completed","sevirity_count": sev_count,"total_diagnostics": len(diagnostics)}