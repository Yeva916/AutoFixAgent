

import shutil
import subprocess
from typing import Any, Dict, Optional,List,Tuple
from pathlib import Path
import xml.etree.ElementTree as ET
import re



def _write_log_file(log_path:str,stdout:str,stderr:str):
    with open(log_path,"w",encoding="utf-8") as f:
        if stdout:
            f.write(stdout)
        if stderr:
            f.write("\n\n --- STDERR --- \n\n")
            f.write(stderr)

def _ensure_dirs(run_dir :Path) ->Tuple[Path,Path]:
    test_results = run_dir / "test_results"
    test_results.mkdir(parents=True,exist_ok=True)
    return run_dir, test_results

def _default_cmd(junit_path:str) -> str:
    return f"pytest -q --maxfail=1 --disable-warnings --junitxml={junit_path}" # this shoudl be str not List[str] because we are using shell which take a single string


def _parse_junit(junit_xml_path:str) -> Dict[str,Any]:
    result = {
        "passed_count":0,
        "failed_count":0,
        "error_count":0,
        "skipped_count":0,
        "failed_tests":[],
    }
    try:
        tree = ET.parse(junit_xml_path)
        root = tree.getroot()
        suites = root.findall(".//testsuite")
        if not suites and root.tag == "testsuite":
            suites = [root]
        for suite in suites:
            failures = int(suite.attrib.get("failures",0))
            errors = int(suite.attrib.get("errors",0))
            skipped = int(suite.attrib.get("skipped",0))
            tests = int(suite.attrib.get("tests",0))
            result["failed_count"] += failures
            result["error_count"] += errors
            result["skipped_count"] += skipped
            result["passed_count"] += max(0,tests - failures - errors - skipped)

            for case in suite.findall("testcase"):
                failure = case.find("failure")
                error = case.find("error")
                if failure is not None or error is not None:
                    classname = case.attrib.get("classname","")
                    name = case.attrib.get("name","")
                    if classname:
                        nodeid = f"{classname}::{name}"
                    else:
                        nodeid = name
                    result["failed_tests"].append(nodeid)
    except ET.ParseError:
        pass
    return result

def _parse_failed_tests_from_output(stdout:str) -> List[str]:
    pattern = re.compile(r"FAILED\s+([^\s:]+(?:::[^\s:]+)*)")
    found = pattern.findall(stdout or "")
    return list(dict.fromkeys(found))

def _docker_available() -> bool:
    return shutil.which("docker") is not None

def _run_subprocess(cmd: List[str], cwd: Optional[str], timeout: int) -> tuple[int,str,str]:
    result = subprocess.run(
        cmd,
        cwd = cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result.returncode, result.stdout, result.stderr

        
