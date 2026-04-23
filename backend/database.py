import os
import io
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from supabase import create_client, Client

def _load_backend_env() -> None:
    env_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=env_path)

    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        return

    try:
        raw = env_path.read_bytes()
    except OSError:
        return

    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8", errors="replace")

    values = dotenv_values(stream=io.StringIO(text))
    for k, v in values.items():
        if v is not None:
            os.environ[k] = v


_load_backend_env()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client | None = None
if url and key:
    # The 'service_role' key bypasses RLS, giving your backend 'God Mode'
    supabase = create_client(url, key)