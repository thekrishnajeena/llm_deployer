---
title: Llm Deployer
emoji: 🦀
colorFrom: pink
colorTo: yellow
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# 🦀 LLM Deployer

**LLM Deployer** is a project designed to help students automatically generate, deploy, update, and manage web applications using LLM-assisted code generation and GitHub Pages deployment.

---

## 🎯 Project Overview

This project provides a full workflow for building and revising applications based on instructor-defined tasks. Students receive a task with a detailed brief, use an LLM to generate code, push it to GitHub, and deploy the application to GitHub Pages. Instructors then evaluate the submission using automated static, dynamic, and LLM-based checks.

**Key Features:**

* **Task Handling:** Accepts POST requests containing JSON task briefs with attachments, checks, and metadata.
* **LLM Code Generation:** Generates minimal web applications based on the task brief.
* **GitHub Integration:** Creates or updates repositories, manages rounds of submissions, ensures MIT licensing, and deploys apps via GitHub Pages.
* **Evaluation:** Supports automated checks, including Playwright-based dynamic tests and LLM-based code & documentation evaluation.
* **Revision Workflow:** Allows updating and redeploying apps in subsequent rounds based on instructor feedback.

---

## 🛠 Project Structure

* `main.py` - FastAPI app to receive and process tasks.
* `generate_app.py` - Generates web applications using LLMs.
* `process_task.py` - Handles task workflow including GitHub repo creation, updates, and round management.
* `task_repo_mapping.json` - Maintains mapping of tasks to repositories and rounds.
* `evaluate.py` - Script for instructors to evaluate code quality, documentation, and dynamic behavior.
* `round1.py` / `round2.py` - Scripts to create tasks for round 1 and round 2 submissions.
* `README.md` - Documentation and project guide.

---

## 📦 How It Works

### 1. Build Phase

1. Students host an API endpoint to receive task requests.
2. The endpoint verifies the student-provided secret.
3. Parses the JSON request including attachments and task brief.
4. Uses an LLM to generate a minimal web app.
5. Creates or updates a GitHub repository:

   * Initializes repository with MIT LICENSE and README.md.
   * Pushes generated files.
   * Deploys app to GitHub Pages.
6. Sends JSON response to the evaluation URL containing repo and pages metadata.

### 2. Revise Phase

1. Accepts a second POST request (round 2) to modify or enhance the application.
2. Updates the GitHub repository accordingly.
3. Re-deploys the application to GitHub Pages.
4. Sends updated metadata to the evaluation API.

### 3. Evaluation Phase

Instructors evaluate submissions using:

* Static checks (e.g., LICENSE, README quality, code quality via LLM).
* Dynamic checks using Playwright to validate page functionality.
* LLM-based checks for code readability and documentation.
* Logs results into a centralized database for tracking and reporting.

---

## 🧩 Task JSON Structure

Example request:

```json
{
  "email": "student@example.com",
  "secret": "...",
  "task": "captcha-solver-...",
  "round": 1,
  "nonce": "ab12-...",
  "brief": "Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample.",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Page displays captcha URL passed at ?url=...",
    "Page displays solved captcha text within 15 seconds"
  ],
  "evaluation_url": "https://example.com/notify",
  "attachments": [{ "name": "sample.png", "url": "data:image/png;base64,iVBORw..." }]
}
```

---

## ⚙️ Deployment

1. **Docker SDK:** The project is designed to run with Docker.
2. **GitHub Pages:** Deployed apps are accessible publicly.
3. **Safe Secrets Handling:** Secrets are never committed to Git.

---

## 📝 How to Run Locally

1. Clone the repository:

```bash
git clone https://github.com/yourusername/llm-deployer.git
cd llm-deployer
```

2. Install dependencies (FastAPI, httpx, GitPython, etc.):

```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:

```bash
uvicorn main:app --reload
```

4. Expose your API endpoint and test with a task JSON.

---

## 💡 Notes

* All repositories created must be public and contain MIT LICENSE at root.
* JSON mapping (`task_repo_mapping.json`) ensures correct repository management across rounds.
* Use separate Git remotes if you are also using other platforms (e.g., Hugging Face).
* Attachments are encoded as data URIs and handled securely.

---

## 📚 References

* Hugging Face Spaces Config Reference: [https://huggingface.co/docs/hub/spaces-config-reference](https://huggingface.co/docs/hub/spaces-config-reference)

---

This README ensures that anyone cloning the project or working on it understands the complete workflow, project structure, and deployment process. Done
