import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client | None = None
if url and key:
    # The 'service_role' key bypasses RLS, giving your backend 'God Mode'
    supabase = create_client(url, key)