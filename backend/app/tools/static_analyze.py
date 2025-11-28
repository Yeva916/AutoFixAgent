import os   # bug -> unable to stop __pycache__ analysis
import subprocess
import logging
from typing import Any, Dict, List, Optional
import shutil
import json
import logging
from pathlib import Path
import uuid
logger = logging.getLogger(__name__)

def run_command(command:List[str],cwd:str,timeout=30) -> str:
    """Run a command in a subprocess and return its output."""
    try:
        result = subprocess.run(command,cwd=cwd,timeout=timeout,capture_output=True,text=True)
        return result.stdout
    except subprocess.TimeoutExpired as e:
        logging.warning(f"Command '{' '.join(command)}' failed with error: {e.stderr}")
        return ""
    except Exception as e:
        logging.error(f"Command '{' '.join(command)}' timed out after {timeout} seconds.")
        return ""

def parse_flake8(cwd:str,target:str) -> List[Dict[str,Any]]:
    if not shutil.which("flake8"):
        logging.error("flake8 is not installed or not found in PATH.")
        return []
    # print(target)
    command = [
        "flake8",
        "--format=%(path)s::%(row)d::%(col)d::%(code)s::%(text)s",
    ]
    command.extend(target)

    output = run_command(command,cwd)
    diagnostics = []
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            
            parts = line.split("::")
            if len(parts) >= 5:

                file_path, line_no, col_no, code, message = parts[:5]
                severity = "error" if code.startswith(("E","F")) else "warning"
                diagnostics.append({
                    "tool":"flake8",
                    "file_path":file_path,
                    "line":int(line_no),
                    "col":int(col_no),
                    "code":code,
                    "message":message,
                    "severity":severity,
                    "raw":line
                })
        except ValueError:
            continue
    
    return diagnostics

def parse_mypy(cwd:str,target:str) -> List[Dict[str,Any]]:
    if not shutil.which("mypy"):
        logging.error("mypy is not installed or not found in PATH.")
        return []
    
    command = ["mypy", "--show-column-numbers", "--ignore-missing-imports", "--no-error-summary", target]
    diagnostics = []
    output = run_command(command,cwd)
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            # Expected: src/main.py:10:5: error: message
            parts = line.split(":", 4) # Split into max 5 parts
            if len(parts) >= 4:
                # Check if col exists (mypy sometimes omits it)
                file_path = parts[0].strip()
                
                # Handling cases where col might be missing in older versions
                if parts[2].isdigit():
                    line_num = int(parts[1])
                    col_num = int(parts[2])
                    severity_raw = parts[3].strip()
                    message = parts[4].strip()
                else:
                    line_num = int(parts[1])
                    col_num = 0 # Default if missing
                    severity_raw = parts[2].strip()
                    message = parts[3].strip()

                diagnostics.append({
                    "tool": "mypy",
                    "file_path": file_path,
                    "line": line_num,
                    "col": col_num,
                    "code": "TYPE", # Mypy doesn't always have codes
                    "severity": "error" if "error" in severity_raw else "warning",
                    "message": message,
                    "raw": line
                })
        except Exception:
            continue

    return diagnostics

def parse_pylint(cwd: str, target: str) -> List[Dict[str, Any]]:
    """
    Runs pylint and requests JSON output directly.
    """
    if not shutil.which("pylint"):
        logger.warning("pylint not found")
        return []

    cmd = ["pylint", "--output-format=json", target]
    
    
    # Pylint often returns non-zero exit codes for issues, so we ignore exit codes
    output = run_command(cmd, cwd)
    diagnostics = []
    try:
        # Pylint outputs a JSON array
        items = json.loads(output)
        for item in items:
            # Map Pylint 'type' to our severity
            # types: convention, refactor, warning, error, fatal
            sev_map = {
                "error": "error",
                "fatal": "error",
                "warning": "warning",
                "convention": "warning",
                "refactor": "warning"
            }
            
            diagnostics.append({
                "tool": "pylint",
                "file_path": item.get("path", ""),
                "line": item.get("line", 0),
                "col": item.get("col", 0),
                "code": item.get("message-id", ""), # e.g., C0111
                "severity": sev_map.get(item.get("type"), "warning"),
                "message": item.get("message", ""),
                "raw": json.dumps(item)
            })
    except json.JSONDecodeError:
        logger.warning("Failed to parse pylint JSON output")
        pass

    return diagnostics

def static_analysis(repo_path:str,files:Optional[List[str]]) -> List[Dict[str,Any]]:
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Directory {repo_path} does not exist.")
    
    # targets = files if files else ["."]  
    targets = files if files else ["."]
    # print(targets)

    diagnostics = []
    diagnostics.extend(parse_flake8(repo_path,targets))
    
    diagnostics.extend(parse_mypy(repo_path,"."))

    if files:
        for file in files:
            diagnostics.extend(parse_pylint(repo_path,file))
    else:
        diagnostics.extend(parse_pylint(repo_path,"."))

    return diagnostics

if __name__ == "__main__":
    backed_dir = Path(__file__).resolve().parent.parent.parent
    run_id:uuid.UUID = uuid.UUID("66737005-69e6-4234-9b55-b9d61a93bd6a")
    repo_path = f"{backed_dir}/runs/{run_id}/repo"
    
    with open(f"{backed_dir}/runs/{run_id}/changed_files.json","r",encoding="utf-8") as f:
        file_changes = json.load(f)
    files = [file["absolute_path"] for file in file_changes]
    diagnostics = static_analysis(repo_path,files)
    for diag in diagnostics:
        # print(f"{diag['tool']}: {diag['file_path']}:{diag['line']}:{diag['col']} {diag['code']} {diag['message']}")
        print(f"{diag['tool']}: {diag['file_path']}:{diag['line']}:{diag['col']} {diag['code']} {diag['message']}")

