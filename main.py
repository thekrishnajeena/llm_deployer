from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import os, json, asyncio
from utils.generator import generate_app
from utils.github_utils import create_repo_and_push
from utils.deployer import notify_evaluation_api
from dotenv import load_dotenv
from git import Repo
import shutil
import time


app = FastAPI()
SECRET = os.getenv("APP_SECRET", "my-secret")

load_dotenv()


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

    print(f"⚙️ Processing task '{task}' (Round {round_})", flush=True)

    repo_name = task

    # Step 1: Generate new or modified app
    app_dir = await generate_app(repo_name, data["brief"], data.get("attachments", []))
    print(f"✅ App generated/updated at: {app_dir}", flush=True)

    

    # Step 2: If round > 1, modify existing repo; else create a new one
    if round_ == 1:
        repo_url, commit_sha, pages_url = create_repo_and_push(repo_name, app_dir)
    else:
        repo_url, commit_sha, pages_url = update_existing_repo(repo_name, app_dir)

    # Step 3: Notify evaluation API
    b = notify_evaluation_api(
        evaluation_url=data["evaluation_url"],
        email=data["email"],
        task=task,
        round_=round_,
        nonce=data["nonce"],
        repo_url=repo_url,
        commit_sha=commit_sha,
        pages_url=pages_url
    )

    print(f"✅ Round {round_} for task '{task}' completed successfully! here is {b}", flush=True)



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


# for evaluation have to deleted

@app.post("/api/evaluate")
async def evaluation_endpoint(req: Request):
    data = await req.json()
    print(f"📩 Evaluation API called with data:\n{json.dumps(data, indent=2)}", flush=True)

    # Example: basic validation for testing
    task = data.get("task")
    round_ = data.get("round")
    repo_url = data.get("repo_url")
    pages_url = data.get("pages_url")

    # Log it to a local file (optional)
    with open("evaluation_log.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

    # Return success
    return JSONResponse(
        {
            "status": "ok",
            "message": f"Evaluation received for task '{task}' (round {round_})",
            "repo": repo_url,
            "pages": pages_url,
        },
        status_code=200,
    )
