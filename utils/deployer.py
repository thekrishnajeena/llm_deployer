import requests
import time

def notify_evaluation_api(evaluation_url, email, task, round_, nonce, repo_url, commit_sha, pages_url):
    payload = {
        "email": email,
        "task": task,
        "round": round_,
        "nonce": nonce,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "pages_url": pages_url
    }

    delay = 1
    for _ in range(6):  # 1,2,4,8,16,32s retries max
        try:
            r = requests.post(evaluation_url, json=payload, timeout=10)
            if r.status_code == 200:
                return True
            else:
                print(f"Evaluation API responded  with {r.status_code}, retrying...")
        except Exception as e:
            print(f"Error notifying evaluation API: {e}. Retrying...")
        time.sleep(delay)
        delay *= 2
    
    print("Failed to notify evaluation API after retries")
    return False
