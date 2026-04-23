import os
import io
from pathlib import Path

from dotenv import load_dotenv, dotenv_values
from zai._client import ZaiClient  # pyright: ignore[reportMissingImports]


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
    # Support either variable name to match different scripts/configs.
    if os.getenv("ZAI_API_KEY") or os.getenv("ILMU_API_KEY"):
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

def _get_api_key() -> str | None:
    # Prefer ZAI_API_KEY, but allow ILMU_API_KEY for compatibility.
    return os.getenv("ZAI_API_KEY") or os.getenv("ILMU_API_KEY")


def _get_base_url() -> str | None:
    # Optional override, in case the key is for a different gateway/env.
    return os.getenv("ZAI_BASE_URL") or None


def get_zai_client() -> ZaiClient:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "Missing API key in environment (.env). Set ZAI_API_KEY or ILMU_API_KEY."
        )

    base_url = _get_base_url()
    return ZaiClient(api_key=api_key, base_url=base_url)


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
    try:
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
    except Exception as e:
        # Avoid leaking secrets; provide actionable context instead.
        api_key = _get_api_key() or ""
        base_url = _get_base_url() or "https://api.z.ai/api/paas/v4"
        err_name = type(e).__name__
        msg = str(e)
        if "401" in msg or err_name == "APIAuthenticationError":
            raise RuntimeError(
                "ZAI authentication failed (401). "
                "Your environment loaded a key, but the server rejected it. "
                f"base_url={base_url!r}, key_len={len(api_key)}. "
                "If your key is valid, try setting ZAI_BASE_URL in backend/.env to the correct gateway, "
                "or re-check that the key is current."
            ) from e
        raise


def generate_staff_tldr(case_text: str, model: str = "glm-5.1") -> str:
    """
    Generate a <=30-word TL;DR for staff dashboard.
    """
    client = get_zai_client()
    prompt = (
        "You are the Summarizer Agent for a payments dispute operations dashboard.\n"
        "Task: write ONE TL;DR sentence of 30 words or fewer.\n"
        "Requirements:\n"
        "- <= 30 words\n"
        "- Must be factual and action-oriented\n"
        "- No PII\n"
        "- Output ONLY the TL;DR text (no quotes, no labels, no bullet points)\n\n"
        f"Case details:\n{case_text.strip()}\n"
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        thinking={"type": "disabled"},
        max_tokens=80,
        temperature=0.3,
    )

    message = resp.choices[0].message
    content = (getattr(message, "content", None) or "").strip()
    return content or str(message)

