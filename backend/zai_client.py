import os
import io
from pathlib import Path

from dotenv import load_dotenv, dotenv_values
from zai import ZaiClient


def _load_backend_env() -> None:
    """
    Load `backend/.env` robustly.

    Some Windows editors save `.env` as UTF-16; python-dotenv may not parse it
    reliably via `load_dotenv(path)` (it can appear as "no keys").
    """
    env_path = Path(__file__).with_name(".env")

    # First try the normal path-based loader.
    load_dotenv(dotenv_path=env_path)

    # If the key is still missing, try decoding and parsing ourselves.
    if os.getenv("ZAI_API_KEY"):
        return

    try:
        raw = env_path.read_bytes()
    except OSError:
        return

    # Heuristic: handle UTF-16 BOM; otherwise fall back to UTF-8.
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8", errors="replace")

    values = dotenv_values(stream=io.StringIO(text))
    for k, v in values.items():
        if v is not None:
            os.environ[k] = v


_load_backend_env()


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

