import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 1. Load .env from the same directory as this script
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Configuration from Environment Variables
# Using the keys you've already established
API_KEY = os.getenv("ZAI_API_KEY") or os.getenv("ILMU_API_KEY")
# Default to the working ilmu endpoint if not in .env
BASE_URL = os.getenv("ZAI_BASE_URL") or "https://api.ilmu.ai/anthropic/v1/messages"
MODEL_KEY = "ilmu-glm-5.1"

def _get_headers():
    return {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

def chat_once(user_message: str, model: str = MODEL_KEY) -> str:
    """Uses the working 'requests' logic to talk to the AI."""
    if not API_KEY:
        raise RuntimeError("API Key missing! Check your .env file.")

    data = {
        "model": model,
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(BASE_URL, headers=_get_headers(), json=data)
        if response.status_code == 200:
            result = response.json()
            # Extract text using the Anthropic format that worked in your test
            return result['content'][0]['text']
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection Failed: {e}"

def generate_staff_tldr(case_text: str, model: str = MODEL_KEY) -> str:
    """Generates the audit log summary for the dashboard."""
    prompt = (
        "You are the Summarizer Agent for a payments dispute operations dashboard.\n"
        "Task: write ONE TL;DR sentence of 30 words or fewer.\n"
        "Requirements:\n"
        "- <= 30 words\n"
        "- No PII\n"
        "- Output ONLY the text\n\n"
        f"Case details:\n{case_text.strip()}"
    )
    return chat_once(prompt, model=model)

def verify_connection() -> dict:
    """Health check for the backend dashboard."""
    try:
        response = chat_once("ping")
        return {
            "model": MODEL_KEY,
            "ok": "Connection Failed" not in response and "Error" not in response,
            "response_sample": response[:20]
        }
    except:
        return {"ok": False}

# --- TEST BLOCK: Run 'python zai_client.py' to verify ---
if __name__ == "__main__":
    print(f"🚀 Testing connection to {BASE_URL}...")
    res = verify_connection()
    if res["ok"]:
        print("✅ API is responding correctly!")
        print(f"📝 Test TL;DR: {generate_staff_tldr('Customer claims the pizza was cold.')}")
    else:
        print("❌ Still failing. Check if ZAI_API_KEY is correct in .env")

