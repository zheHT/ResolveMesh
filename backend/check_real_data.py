#!/usr/bin/env python3
"""Check what real data exists in Supabase"""

from supabase import create_client
import os
import json

url = os.getenv('SUPABASE_URL', 'https://kkxfptzabojdhidzxxyx.supabase.co')
key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtreGZwdHphYm9qZGhpZHp4eXl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU1NzQzMzcsImV4cCI6MjA1MTE1MDMzN30.KT47_OKR0wZdVpKzqI1pxvCMvUCZDj4chYHJwVYu91U')
supabase = create_client(url, key)

print('=== CHECKING SUPABASE DATA ===\n')

# Check disputes
print('1. DISPUTES TABLE:')
disputes = supabase.table('disputes').select('id, issue_type, customer_info').limit(5).execute()
print(f'   Found {len(disputes.data)} disputes')

if disputes.data:
    for i, d in enumerate(disputes.data[:3]):
        order_id = None
        if d.get('customer_info'):
            if isinstance(d['customer_info'], dict):
                order_id = d['customer_info'].get('order_id')
            else:
                try:
                    ci = json.loads(d['customer_info']) if isinstance(d['customer_info'], str) else d['customer_info']
                    order_id = ci.get('order_id')
                except:
                    pass
        print(f'   [{i+1}] ID: {d["id"][:12]}... | Order: {order_id}')
    
    # Use first dispute
    first_dispute = disputes.data[0]
    order_id = None
    if first_dispute.get('customer_info'):
        if isinstance(first_dispute['customer_info'], dict):
            order_id = first_dispute['customer_info'].get('order_id')
        else:
            try:
                ci = json.loads(first_dispute['customer_info'])
                order_id = ci.get('order_id')
            except:
                pass
    
    dispute_id = first_dispute['id']
    print(f'\n   TESTING WITH: {dispute_id}')
    print(f'   Order ID: {order_id}\n')
    
    # Check transactions
    print('2. TRANSACTIONS TABLE:')
    txns = supabase.table('transactions').select('id, ledger_data').limit(50).execute()
    print(f'   Total in table: {len(txns.data)}')
    
    if order_id:
        matching = []
        for t in txns.data:
            ld = t.get('ledger_data')
            if ld:
                if isinstance(ld, dict) and ld.get('order_id') == order_id:
                    matching.append(t)
                elif isinstance(ld, str):
                    try:
                        ld_dict = json.loads(ld)
                        if ld_dict.get('order_id') == order_id:
                            matching.append(t)
                    except:
                        pass
        print(f'   Transactions with order_id "{order_id}": {len(matching)}')
        if matching:
            print(f'   ✅ FOUND {len(matching)} matching transaction(s)')
        else:
            print(f'   ❌ NO transactions found with this order_id')
    
    # Check merchant records
    print('\n3. MERCHANT RECORDS TABLE:')
    merchants = supabase.table('merchant_records').select('id, order_id, merchant_name').limit(50).execute()
    print(f'   Total in table: {len(merchants.data)}')
    
    if order_id:
        matching_merchants = [m for m in merchants.data if m.get('order_id') == order_id]
        print(f'   Merchant records with order_id "{order_id}": {len(matching_merchants)}')
        if matching_merchants:
            print(f'   ✅ FOUND {len(matching_merchants)} matching merchant record(s)')
        else:
            print(f'   ❌ NO merchant records found with this order_id')
    
    # Test evidence retrieval
    print(f'\n4. TESTING EVIDENCE RETRIEVAL:')
    import requests
    r = requests.get(f'http://localhost:8000/api/disputes/{dispute_id}/evidence?agent_type=judge', timeout=10)
    if r.status_code == 200:
        evidence = r.json().get('bundle', {})
        print(f'   Disputes data: {bool(evidence.get("dispute_record"))} ✅')
        print(f'   Transactions found: {len(evidence.get("transactions", []))}')
        print(f'   Merchant record: {bool(evidence.get("merchant_record"))}')
        print(f'   System logs: {len(evidence.get("system_logs", []))}')
    else:
        print(f'   Error: {r.status_code}')
else:
    print('   ❌ No disputes in database!')
