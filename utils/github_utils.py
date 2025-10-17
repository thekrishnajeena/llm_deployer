
import os
from github import Github
from git import Repo
import requests
import time
from  dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN =  os.getenv
# os.getenv("GITHUB_TOKEN")  # Your personal access token
GITHUB_USER = "krsna-arch"
# os.getenv("GITHUB_USER")    # GitHub username

def create_repo_and_push(task_name, local_dir):
    """
    Create a GitHub repo for task_name, push local_dir content,
    add MIT LICENSE, README.md, and enable GitHub Pages.
    """
    g = Github(GITHUB_TOKEN)
    user = g.get_user()

    # Create unique repo name
    repo_name = task_name
    print(f"Creating repo: {repo_name}")
    repo = user.create_repo(
        name=repo_name,
        description=f"Auto-generated repo for task: {task_name}",
        private=False,  # Public repo
        auto_init=False,
    )

    # Add MIT LICENSE
    license_text = """MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
..."""  # full MIT text
    with open(os.path.join(local_dir, "LICENSE"), "w") as f:
        f.write(license_text)

    # Add README.md
    readme_text = f"""# {task_name}

This repository contains a minimal web app generated automatically.

## Setup

```bash
git clone https://github.com/{GITHUB_USER}/{repo_name}.git
cd {repo_name}
# open index.html in browser
Usage
Open index.html in your browser.

Code Explanation
index.html: main HTML

script.js: JavaScript

styles.css: CSS (if any)

License
MIT
"""
    with open(os.path.join(local_dir, "README.md"), "w") as f:
        f.write(readme_text)

# Initialize git, commit & push
    repo_local = Repo.init(local_dir)
    repo_local.git.add(A=True)
    repo_local.index.commit("Initial commit: generated app files")

    remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"

    if "origin" in [r.name for r in repo_local.remotes]:
        origin = repo_local.remote("origin")
        origin.set_url(remote_url)
    else:
        origin = repo_local.create_remote("origin", remote_url)

    origin.push(refspec="master:main")

    print(f"✅ Pushed to GitHub: https://github.com/{GITHUB_USER}/{repo_name}")

    # Enable GitHub Pages
    pages_url = enable_github_pages(GITHUB_USER, repo_name, GITHUB_TOKEN)


    commit_sha = repo_local.head.commit.hexsha
    return repo.clone_url,  commit_sha, pages_url


def enable_github_pages(github_username, repo_name, github_token):
    """
    Enables GitHub Pages for a repo on the 'main' branch at root path.
    Returns the public Pages URL once it's live.
    """
    pages_api = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/pages"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }

    data = {"source": {"branch": "main", "path": "/"}}
    resp = requests.post(pages_api, headers=headers, json=data)

    print("📡 Enabling GitHub Pages:", resp.status_code, resp.text)

    pages_url = f"https://{github_username}.github.io/{repo_name}/"

    # Wait until GitHub Pages becomes live
    for i in range(12):
        try:
            r = requests.get(pages_url)
            if r.status_code == 200:
                print(f"✅ GitHub Pages is live at {pages_url}")
                return pages_url
        except Exception:
            pass
        time.sleep(5)

    print("⚠️ GitHub Pages not live yet, returning expected URL anyway.")
    return pages_url