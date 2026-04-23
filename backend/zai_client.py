import os

from dotenv import load_dotenv
from zai import ZaiClient


load_dotenv()


def get_zai_client() -> ZaiClient:
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ZAI_API_KEY in environment (.env).")
    return ZaiClient(api_key=api_key)


def chat_once(user_message: str, model: str = "glm-5.1") -> str:
    client = get_zai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        thinking={"type": "enabled"},
        max_tokens=512,
        temperature=0.7,
    )

    message = resp.choices[0].message
    content = getattr(message, "content", None)
    return content if content is not None else str(message)


def verify_connection(model: str = "glm-5.1") -> dict:
    """
    Makes a minimal real request to confirm the API key works.
    Returns a small dict suitable for a health endpoint.
    """
    client = get_zai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "ping"}],
        thinking={"type": "disabled"},
        max_tokens=1,
        temperature=0,
    )
    return {
        "model": model,
        "request_id": getattr(resp, "id", None),
        "ok": True,
    }

