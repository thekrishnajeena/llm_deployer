from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, json, asyncio
from utils.generator import generate_app
from utils.github_utils import create_repo_and_push
from utils.deployer import notify_evaluation_api
from dotenv import load_dotenv
from git import Repo
import shutil
import time


load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SECRET = os.getenv("APP_SECRET", "24f2005894KJ18062007")

json_file = 'task_repo_mapping.json'

# Load existing data
if os.path.exists(json_file):
    with open(json_file, 'r') as f:
        task_map = json.load(f)
else:
    task_map = {}

@app.get("/")
async def root():
    return JSONResponse({"message": "Hello! Everything's Okay"},
                        status_code=200)

def update_task_map(task, round_):
    print(f"⚙️ Processing task '{task}' (Round {round_})", flush=True)
    
    # Generate a unique repo name based on task and current timestamp
    timestamp = str(time.time()).replace('.', '')
    repo_name = f"{task}-{timestamp}"
    
    # Check if the task exists in the mapping
    if task in task_map:
        if round_ == 1:
            # Overwrite the existing entry for round 1
            task_map[task] = {"repo_name": repo_name, "rounds": [1]}
            print(f"🔄 Overwritten task '{task}' for Round 1.")
        elif round_ == 2:
            # Check if round 1 exists
            if 1 in task_map[task]["rounds"]:
                # Add round 2
                task_map[task]["rounds"].append(2)
                print(f"🔄 Added Round 2 to task '{task}'.")
            else:
                # Create a new entry for round 2
                task_map[task] = {"repo_name": repo_name, "rounds": [1, 2]}
                print(f"🔄 Created new entry for task '{task}' with Round 2.")
    else:
        # Create a new entry for the task
        task_map[task] = {"repo_name": repo_name, "rounds": [round_]}
        print(f"➕ Created new entry for task '{task}'.")

    # Save the updated mapping to the JSON file
    with open(json_file, 'w') as f:
        json.dump(task_map, f, indent=2)
    print(f"✅ Task mapping updated successfully.")


@app.post("/api/task")
async def receive_task(req: Request, background_tasks: BackgroundTasks):
    data = await req.json()

    # Verify secret
    if data.get("secret") != SECRET:
        return JSONResponse({"error": "Invalid secret"}, status_code=403)

    round_ = int(data.get("round", 1))
    task = data.get("task")

    response = {"status": "received", "task": task, "round": round_}
    print(f"✅ Received task '{task}' for round {round_}", flush=True)

    # Run process_task in background
    background_tasks.add_task(asyncio.run, process_task(data))

    return JSONResponse(response, status_code=200)

async def process_task(data):
    task = data["task"]
    round_ = int(data.get("round", 1))
    brief = data.get("brief", "No brief provided.")
    attachments = data.get("attachments", [])
    checks = data.get("checks", [])

    print(f"⚙️ Processing task '{task}' (Round {round_})", flush=True)

    update_task_map(task, round_)
    repo_name = task_map[task]["repo_name"]


    # Step 1: Generate new or modified app
    try:
        app_dir = await generate_app(repo_name, brief, attachments, checks)
        print(f"✅ App generated/updated at: {app_dir}", flush=True)
    except Exception as e:
        print(f"⚠️ App generation failed: {e}", flush=True)
        app_dir = None

    repo_url = commit_sha = pages_url = None

    # Step 2: If app generation succeeded, push to GitHub
    if app_dir:
        try:
            if round_ == 1:
                repo_url, commit_sha, pages_url = create_repo_and_push(repo_name, app_dir)
            else:
                repo_url, commit_sha, pages_url = update_existing_repo(repo_name, app_dir)
        except Exception as e:
            print(f"⚠️ GitHub push failed: {e}", flush=True)

    # Step 3: Notify evaluation API, retry internally, no crash if fails
    try:
        b = notify_evaluation_api(
            evaluation_url=data.get("evaluation_url", ""),
            email=data.get("email", ""),
            task=task,
            round_=round_,
            nonce=data.get("nonce", ""),
            repo_url=repo_url,
            commit_sha=commit_sha,
            pages_url=pages_url
        )
    except Exception as e:
        print(f"⚠️ Evaluation API notification failed: {e}", flush=True)
        b = None

    print(f"✅ Round {round_} for task '{task}' completed! Response: {b}", flush=True)


from git import Repo, GitCommandError

def update_existing_repo(task, app_dir):
    repo_path = f"./{task}"
    github_username = os.getenv("GITHUB_USER")
    github_token = os.getenv("GITHUB_TOKEN")

    # Load repo
    repo = Repo(repo_path)

    # Ensure we are on the branch used in round 1 (usually 'main')
    branch_name = 'main'  # adjust if your round 1 branch was different
    if repo.active_branch.name != branch_name:
        repo.git.checkout(branch_name)

    # Copy new files to repo, skip .git
    for root, _, files in os.walk(app_dir):
        if '.git' in root.split(os.sep):
            continue  # skip git internals

        for f in files:
            src = os.path.join(root, f)
            rel_path = os.path.relpath(src, app_dir)
            dest = os.path.join(repo_path, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            # Overwrite existing files atomically
            try:
                temp_dest = dest + ".tmp"
                shutil.copy2(src, temp_dest)
                os.replace(temp_dest, dest)
            except PermissionError:
                print(f"⚠️ Permission denied for {dest}, skipping.")
            except shutil.SameFileError:
                pass

    # Update README
    readme_path = os.path.join(repo_path, "README.md")
    with open(readme_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n### Round {int(time.time())}\nUpdated according to new brief.\n")

    # Commit changes
    repo.git.add(A=True)
    try:
        repo.index.commit("Round update: modified as per new brief")
    except GitCommandError:
        print("⚠️ No changes to commit.")

    # Push changes to same branch
    origin = repo.remote(name="origin")
    origin.push(refspec=f"{branch_name}:{branch_name}")

    # GitHub Pages URL
    pages_url = f"https://{github_username}.github.io/{task}/"
    commit_sha = repo.head.object.hexsha

    safe_clone_url = f"https://github.com/{github_username}/{task}.git"

    return safe_clone_url, commit_sha, pages_url



