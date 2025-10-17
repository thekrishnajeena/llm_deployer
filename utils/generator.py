# generator.py
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")

API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
MODEL = "openai/gpt-4.1-mini" 

async def generate_app(task, brief, attachments):
    print(f"⚡ Generating app for task: {task}", flush=True)

    # LLM prompt to generate multiple files
    prompt = f"""
You are a code generator. Generate a minimal web app based on the following brief for {task}:
{brief}

Attachments: {attachments}

Output **only a JSON array of files** with `path` and `content`. Example:

[
  {{"path": "index.html", "content": "<html>...</html>"}},
  {{"path": "script.js", "content": "console.log('Hello')"}},
  {{"path": "styles.css", "content": "body {{ font-family: sans-serif; }}" }}
]

Return only valid JSON. Do not add any extra text.
"""

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a code generator that outputs only JSON file lists."},
            {"role": "user", "content": prompt}
        ]
    }

    timeout = httpx.Timeout(120.0, connect=20.0)  # increase for LLM
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
        except httpx.ReadTimeout:
            print("⚠️ LLM request timed out")
            raise

        if response.status_code != 200:
            print("❌ Error from LLM:", response.text, flush=True)
            raise Exception(f"LLM API error: {response.status_code}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        # print("LLM raw response:", content, flush=True)

 # Parse JSON safely
    try:
        files = json.loads(content)
        if not isinstance(files, list):
            raise ValueError("LLM returned JSON is not a list")
    except json.JSONDecodeError:
        print("❌ LLM did not return valid JSON")
        raise

    # Create visible folder and write files
    app_dir = os.path.join(os.getcwd(), task)  # current directory
    os.makedirs(app_dir, exist_ok=True)

    for f in files:
        file_path = os.path.join(app_dir, f["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Use atomic write: write to temp file then rename
        temp_path = file_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as fp:
            fp.write(f["content"])
        os.replace(temp_path, file_path)  # atomic replace ensures file is closed

    print(f"✅ Generated {len(files)} files at: {app_dir}", flush=True)
    return app_dir