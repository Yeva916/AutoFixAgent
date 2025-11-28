# from unittest import result
# from unidiff
import json
from fastapi import APIRouter,HTTPException
from app.models.model import Input
from uuid import uuid4
from app.api.utils import git_clone,git_fetch_pr,git_checkout,get_sha,get_diff,parse_diff_to_json
from pathlib import Path

router = APIRouter(prefix="/pr")
backed_dir = Path(__file__).resolve().parent.parent.parent.parent
@router.post('/ingest')
async def ingest(input:Input):
    #https://github.com/fastapi/full-stack-fastapi-template/pull/1985
    owner_name:str = input.pr_url.path.split('/')[1]
    repo_name:str = input.pr_url.path.split('/')[2]
    pr_number:int = int(input.pr_url.path.split('/')[4])
    run_id: str = str(uuid4())
    try:
        result_1 = git_clone(f"https://github.com/{owner_name}/{repo_name}.git",f"{backed_dir}/runs/{run_id}/repo")
        print(f"result1:{result_1}")

    except Exception as e:
        print("Error during git clone:",e)
    try :
        result_2 = git_fetch_pr(result_1['path'],pr_number)
        # print(result_2)
    except Exception as e:
        print("Error during git fetch PR:",e)
    
    try:
        result_3 = git_checkout(result_1['path'],pr_number)
        # print(result_3)
    except Exception as e:
        print("Error during git checkout:",e)
    
    try:
        sha_info = get_sha(owner_name, repo_name, pr_number)
        
    except Exception as e:
        print("Error fetching SHA info:", e)
    
    try:
        diff_output = get_diff(input.context_lines,sha_info['base'], f"pr_{pr_number}", result_1['path'])

    except Exception as e:
        print("Error generating diff:", e)
    
    try:
        file_changes = parse_diff_to_json(diff_output['diff'],f"{backed_dir}/runs/{run_id}/repo")
    except Exception as e:
        print("Error parsing diff to JSON:", e)

    with open(f"{backed_dir}/runs/{run_id}/changed_files.json","w",encoding="utf-8") as f:
        json.dump(file_changes,f,indent=4)

    return {
        "run_id":run_id,
        "status":"ingest completed",
        "changed_files":file_changes,
        "base_commit":sha_info['base'],
        "head_commit":sha_info['head'],
    }
