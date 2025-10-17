# generator.py
import os
import json
import httpx
from dotenv import load_dotenv
import asyncio

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
MODEL = "openai/gpt-4.1-mini" 

async def generate_app(task, brief, attachments, checks):
    print(f"⚙️ Processing task '{task}'...", flush=True)

    # Format attachments and checks nicely for the LLM
    attachments_text = "\n".join(
        [f"- {a.get('name', 'unknown')}" for a in attachments]
    ) or "No attachments provided."

    checks_text = "\n".join(f"- {chk}" for chk in checks) or "No explicit checks."

    prompt = f"""
You are an expert web app generator. Build a **static web app** suitable for direct deployment on **GitHub Pages**.

## Requirements:
- Base it on the task: "{task}"
- Follow this project brief:
  {brief}
- Consider these evaluation checks:
  {checks_text}
- Reference attachments if relevant:
  {attachments_text}
- Use only HTML, CSS, and JavaScript.
- Write a good Readme file(dont take much time).
- Avoid Node.js, Python, or server-side code.
- Make it responsive and mobile-friendly.
- Include MIT license notice if required.
- Place main entry as `index.html`.
- Return ONLY a valid JSON array of objects with fields:
  - `path`: file path (string)
  - `content`: file contents (string)

Example format:
[
  {{"path": "index.html", "content": "<!DOCTYPE html>..."}},
  {{"path": "style.css", "content": "body {{ font-family: sans-serif; }}"}},
  {{"path": "script.js", "content": "console.log('App loaded')"}}
]
    """

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a strict JSON-only code generator for deployable static web apps."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }

    timeout = httpx.Timeout(180.0, connect=30.0)
    retries = 3

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                response = await client.post(API_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    break
                else:
                    print(f"⚠️ Attempt {attempt+1}: API returned {response.status_code}", flush=True)
            except httpx.RequestError as e:
                print(f"⚠️ Attempt {attempt+1} failed: {e}", flush=True)
            await asyncio.sleep(2 * (attempt + 1))
        else:
            raise Exception("❌ Failed to reach LLM API after multiple retries")

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    try:
        files = json.loads(content)
        if not isinstance(files, list):
            raise ValueError("Expected a JSON array of file objects")
    except json.JSONDecodeError:
        print("❌ Invalid JSON returned by LLM:", content[:400])
        raise

    app_dir = os.path.join(os.getcwd(), task)
    os.makedirs(app_dir, exist_ok=True)

    for f in files:
        file_path = os.path.join(app_dir, f["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        tmp_path = file_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fp:
            fp.write(f["content"])
        os.replace(tmp_path, file_path)

    print(f"✅ Generated {len(files)} files for '{task}' in {app_dir}")
    print(f"🚀 Deployable on GitHub Pages — just push this folder to your repo!")

    return app_dir
