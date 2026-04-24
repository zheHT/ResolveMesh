#!/usr/bin/env python
from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
db = create_client(url, key)

# Get the latest dispute (just get the first one)
result = db.table('disputes').select('id, customer_info, agent_reports').limit(1).execute()
if result.data:
    dispute = result.data[0]
    print('✅ LATEST DISPUTE IN SUPABASE:')
    print(f'   ID: {dispute["id"]}')
    print(f'   Customer Email: {dispute["customer_info"].get("email", "N/A")}')
    print(f'   Amount: ${dispute["customer_info"].get("amount", "N/A")}')
    print(f'   Platform: {dispute["customer_info"].get("platform", "N/A")}')
    if 'guardian' in dispute.get('agent_reports', {}):
        summary = dispute['agent_reports']['guardian'].get('summary', '')
        print(f'\n   📄 Redacted Text Sample:')
        print(f'      {summary[:150]}...')
        print(f'\n   🔐 PII Masking Status:')
        has_person = '<PERSON>' in summary
        has_phone = '<PHONE_NUMBER>' in summary
        has_location = '<LOCATION>' in summary
        print(f'      Names masked: {"✅ YES" if has_person else "❌ NO"}')
        print(f'      Phones masked: {"✅ YES" if has_phone else "❌ NO"}')
        print(f'      Locations masked: {"✅ YES" if has_location else "❌ NO"}')
else:
    print('❌ No disputes found')
