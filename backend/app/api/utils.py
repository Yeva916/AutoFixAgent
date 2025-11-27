import subprocess
import os
import requests
from pathlib import Path
from unidiff import PatchSet

def git_clone(repo_url,dest_dir):
    os.makedirs(dest_dir,exist_ok=True)
    print(f"Cloning repository {repo_url} into {dest_dir}...")
    process = subprocess.run(
        ['git','clone',"--depth","1",repo_url,dest_dir],
        check=True
        )
    if process.returncode != 0:
        raise Exception(f"Git clone failed:{process.stderr}")
    
    return {"status":"success","path":dest_dir}

def git_fetch_pr(repo_path,pr_number):
    print(f"Fetching PR #{pr_number} is repository at {repo_path}...")
    process = subprocess.run(
        ['git','fetch','origin',f"pull/{pr_number}/head:pr_{pr_number}"],
        cwd=repo_path,
        check=True
    )
    if process.returncode != 0:
        raise Exception(f"Git fetch PR failed:{process.stderr}")
    return {"status":"success","pr_branch":f"pr_{pr_number}"} 

def git_checkout(repo_path,pr_number):
    print(f"Checking out branch pr_{pr_number} in repository at {repo_path}...")
    process = subprocess.run(
        ['git','checkout',f"pr_{pr_number}"],
        cwd=repo_path,
        check=True
    )
    if process.returncode != 0:
        raise Exception(f"Git checkout failed:{process.stderr}")
    return {"status":"success","checked_out_branch":f"pr_{pr_number}"}

def get_sha(repo_owner,repo_name,pr_number):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR details: {response.status_code}")
    else:
        pr_data = response.json()
        return {"head": pr_data['head']['sha'], "base": pr_data['base']['sha']}

def get_diff(context_lines,base_commit,pr_branch,repo_path):
    diff = subprocess.run(
        ['git','diff',f"--unified={context_lines}",base_commit,pr_branch],
        cwd = repo_path,
        capture_output=True,
        text=True
    )
    if diff.returncode != 0:
        raise Exception(f"Git diff failed:{diff.stderr}")
    else:
        with open(os.path.join(repo_path,'diff.patch'),'w') as f:
            f.write(diff.stdout)
    return {"message":"Diff generated successfully","diff":diff.stdout}

def parse_diff_to_json(diff_text:str,repo_root:str|Path) -> list[dict]:
    repo_root = Path(repo_root)
    patch_set = PatchSet(diff_text)
    files_changes = []
    for patch in patch_set:

        if patch.is_added_file:
            change_type = "added"
        elif patch.is_removed_file:
            change_type = "deleted"
        elif patch.is_binary_file:
            change_type = "binary_modified"
        else:
            change_type = "modified"
    
        file_path = patch.path

        if patch.is_binary_file:
            files_changes.append({
                "path":file_path,
                "change_type":change_type,
                "diff":"Binary file changed",
                "hunks":[],
                "snippet":"Binary file changed",
                "absolute_path":str(repo_root / file_path)
            })
            continue

        hunks_data = []
        for hunk in patch:
            hunks_data.append({
                "old_start":hunk.source_start,
                "old_lines":hunk.source_length,
                "new_start":hunk.target_start,
                "new_lines":hunk.target_length,
                "hunk_text":str(hunk)
            })
        
        snippet = hunks_data[0]["hunk_text"] if hunks_data else "No content changes"

        files_changes.append({
            "path":file_path,
            "change_type":change_type,
            "diff":str(patch),
            "hunks":hunks_data,
            "snippet":snippet,
            "absolute_path":str(repo_root / file_path)
        })
    return files_changes