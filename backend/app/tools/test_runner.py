

# def run_test(repo_path:str,cmd:None,timeout:int=120):
import json
import subprocess
import os
from pathlib import Path
import shutil
from typing import Any, Optional,Dict, List
import time

try:
    from app.utils.test_utils import (
        _ensure_dirs,
        _write_log_file,
        _parse_junit,
        _default_cmd,
        _parse_failed_tests_from_output,
    )
except ModuleNotFoundError:
    # When this file is executed directly (not as a package module), the
    # top-level package `app` may not be on `sys.path`. Add the `backend`
    # directory (parent of `app`) to `sys.path` so `app` can be imported.
    import sys
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parents[2]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from app.utils.test_utils import (
        _ensure_dirs,
        _write_log_file,
        _parse_junit,
        _default_cmd,
        _parse_failed_tests_from_output,
    )
# import logging

# logger = logging.getLogger(__name__)

def run_test(repo_path:str,
             cmd:Optional[str] = None,
             timeout:int=120,
             use_sandbox:bool=False,
             docker_image:str="autofix-sandbox",
             run_id:Optional[str]=None) -> Dict[str,Any]: 

    repo_path = Path(repo_path).resolve()
    if not repo_path.exists():
        raise FileNotFoundError(f"repo_path not found: {repo_path}")
    
    if repo_path.name == "repo":
        run_dir = repo_path.parent
    else:
        run_dir = repo_path
    
    run_dir = run_dir.resolve()
    _,test_results = _ensure_dirs(run_dir)
    junit_path = test_results / "junit.xml"
    logpath = test_results / "test.log"
    summary_path = test_results / "summary.json"

    if cmd is None:
        cmd = _default_cmd(str(junit_path))
    
    start = time.time()
    stdout = stderr = ""
    exit_code = 0
    status = "success"
    try:
        if use_sandbox:
            #need to write sandbox execution code here
            print("Sandbox execution not implemented yet.")
        else:
            shell_cmd = ["bash","-lc",cmd]
            exit_code,stdout,stderr = subprocess.run(shell_cmd, cwd=str(repo_path), timeout=timeout)
    except subprocess.TimeoutExpired as e:
        status = "timeout"
        print("status: timeout")
        exit_code = -1
        stdout = e.stdout or "" + "\n\n*** TIMEOUT EXPIRED ***\n\n"
        stderr = e.stderr or "" + "\n\n*** TIMEOUT EXPIRED ***\n\n"
    except Exception as e:
        status = "error"
        exit_code = -1
        stderr = (stderr or "") + f"\n\nException: {repr(e)}\n\n"
    
    duration = time.time() - start
    try:
        _write_log_file(logpath,stdout,stderr)
    except Exception:
        pass

    parsed = _parse_junit(junit_path) if junit_path.exists() else {}

    if not parsed.get("failed_tests") and stdout:
        parsed_from_out = _parse_failed_tests_from_output(stdout)
        if parsed_from_out:
            parsed.setdefault("failed_tests",[]).extend(parsed_from_out)
    
    result = {
        "run_id": run_id or run_dir.name,
        "status": status,
        "exit_code": exit_code,
        "failed_tests": parsed.get("failed_tests",[]),  
        "passed_count": parsed.get("passed_count", 0),  
        "failed_count": parsed.get("failed_count", 0),   
        "error_count": parsed.get("error_count", 0),   
        "skipped_count": parsed.get("skipped_count", 0),
        "duration_seconds": round(duration,3),  
        "log_path": str(logpath),
        "junit_xml": str(junit_path) if junit_path.exists() else None,
    }
    
    try:
        with open(summary_path,"w",encoding="utf-8") as f:
            json.dump(result, f)
    except Exception:
        pass
    return result

if __name__ == "__main__":
    # quick local test when invoked directly:
    demo_repo = "/home/yeshwant/AutoFixAgent/backend/runs/b1bff0df-9c35-4b4b-a5c0-ea447611e856/repo"  # change this to your local run folder
    summary = run_test(demo_repo, cmd=None, use_sandbox=False)
    print(summary)