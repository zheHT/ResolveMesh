# test_conn.py
from database import supabase

def check_connection():
    try:
        # Just try to fetch one row from transactions
        res = supabase.table("transactions").select("*").limit(1).execute()
        print("✅ Connection Successful!")
        print(f"Sample Data Found: {res.data}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    check_connection()