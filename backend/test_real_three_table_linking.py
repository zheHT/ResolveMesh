#!/usr/bin/env python3
"""Test three-table linking with REAL Supabase data"""

import requests
import json

BASE_URL = 'http://localhost:8000'

# Use dispute #2 (has order_id: GRB-999-MYS)
dispute_id = 'e0adb306-92e0-4dd8-a83e-b17cd4e4b43e'
order_id = 'GRB-999-MYS'

print('=== TESTING THREE-TABLE LINKING WITH REAL DATA ===\n')
print('Dispute ID:', dispute_id)
print('Order ID:', order_id)

# Get evidence
print('\n1. FETCHING EVIDENCE FOR THIS DISPUTE:')
r = requests.get(f'{BASE_URL}/api/disputes/{dispute_id}/evidence?agent_type=judge', timeout=10)

if r.status_code != 200:
    print('   ERROR:', r.status_code, r.text[:200])
else:
    bundle = r.json().get('bundle', {})
    
    print('   Dispute record found:', bool(bundle.get('dispute_record')))
    print('   Transactions for this order:', len(bundle.get('transactions', [])))
    print('   Merchant record for this order:', bool(bundle.get('merchant_record')))
    print('   System logs:', len(bundle.get('system_logs', [])))
    
    # Show transaction details if any
    txns = bundle.get('transactions', [])
    if txns:
        print('\n   📦 TRANSACTIONS RETRIEVED:')
        for i, t in enumerate(txns[:2]):
            print('     [{}] ID: {}'.format(i+1, t.get('id', 'unknown')[:12]))
            ld = t.get('ledger_data', {})
            if isinstance(ld, str):
                try:
                    ld = json.loads(ld)
                except:
                    pass
            print('         Amount:', ld.get('amount', 'N/A'))
            print('         Status:', ld.get('status', 'N/A'))
    else:
        print('   ❌ NO TRANSACTIONS FOUND')
    
    # Show merchant record if any
    merchant = bundle.get('merchant_record')
    if merchant:
        print('\n   🏪 MERCHANT RECORD RETRIEVED:')
        print('     Merchant:', merchant.get('merchant_name', 'N/A'))
        print('     Order ID:', merchant.get('order_id', 'N/A'))
    else:
        print('\n   ❌ NO MERCHANT RECORD FOUND')

# Test judge agent with this real data
print('\n2. TESTING JUDGE AGENT WITH REAL DATA:')
r = requests.post(
    f'{BASE_URL}/api/agents/analyze',
    json={'dispute_id': dispute_id, 'agents': ['judge']},
    timeout=30
)

if r.status_code != 200:
    print('   ERROR:', r.status_code)
    print('   Response:', r.text[:300])
else:
    response = r.json()
    judge = response.get('agent_responses', {}).get('judge', {})
    
    print('   Status:', response.get('status'))
    print('   Confidence score:', judge.get('confidence_score', 'N/A'))
    print('   Evidence citations:', len(judge.get('evidence', [])))
    
    # Show sample citations
    evidence = judge.get('evidence', [])
    if evidence:
        print('\n   📌 SAMPLE EVIDENCE CITATIONS:')
        for i, ev in enumerate(evidence[:3]):
            sb = ev.get('supabase', {})
            table = sb.get('table', 'unknown')
            row_id = sb.get('row_id', 'unknown')[:12] if sb.get('row_id') else 'unknown'
            details = ev.get('details', '')[:50]
            print('     [{}] Table: {} | Row: {}...'.format(i+1, table, row_id))
            print('         Details: {}...'.format(details))
    
    validation = response.get('validation_report', {})
    print('\n   Hallucination risk:', validation.get('hallucination_risk', 'unknown'))
    print('   All responses valid:', validation.get('all_responses_valid', 'unknown'))

print('\n=== COMPLETE ===')
