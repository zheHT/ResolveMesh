#!/usr/bin/env python3
"""Test with REAL data from Supabase via the backend"""

import requests
import json

BASE_URL = "http://localhost:8000"

print('=== TESTING WITH REAL SUPABASE DATA ===\n')

# Step 1: Get existing disputes
print('1. FETCHING REAL DISPUTES:')
r = requests.get(f'{BASE_URL}/api/disputes', params={'limit': 10})
if r.status_code != 200:
    print(f'   ❌ Error: {r.status_code}')
    exit(1)

disputes = r.json()
print(f'   Found {len(disputes)} disputes in Supabase')

if not disputes:
    print('   ❌ No disputes in database!')
    exit(1)

# Find one with customer_info that has order_id
test_dispute = None
for d in disputes:
    customer_info = d.get('customer_info', {})
    if customer_info and customer_info.get('order_id'):
        test_dispute = d
        break

if not test_dispute:
    print('   Using first dispute (may not have transactions)')
    test_dispute = disputes[0]

dispute_id = test_dispute['id']
order_id = test_dispute.get('customer_info', {}).get('order_id') if test_dispute.get('customer_info') else None

print(f'\n   ✅ USING DISPUTE: {dispute_id}')
print(f'   Order ID: {order_id}')

# Step 2: Get evidence for this dispute
print(f'\n2. FETCHING EVIDENCE FOR DISPUTE:')
r = requests.get(f'{BASE_URL}/api/disputes/{dispute_id}/evidence?agent_type=judge')
if r.status_code != 200:
    print(f'   ❌ Error: {r.status_code}')
    print(f'   Response: {r.text[:300]}')
    exit(1)

bundle = r.json().get('bundle', {})
print(f'   ✅ Disputes data retrieved')
print(f'   Transactions found: {len(bundle.get("transactions", []))}')
print(f'   Merchant record: {bool(bundle.get("merchant_record"))}')
print(f'   System logs: {len(bundle.get("system_logs", []))}')

# Step 3: Test judge agent with REAL data
print(f'\n3. TESTING JUDGE AGENT WITH REAL DATA:')
r = requests.post(
    f'{BASE_URL}/api/agents/analyze',
    json={'dispute_id': dispute_id, 'agents': ['judge']},
    timeout=30
)

if r.status_code != 200:
    print(f'   ❌ Judge failed: {r.status_code}')
    print(f'   Error: {r.text[:300]}')
else:
    response = r.json()
    status = response.get('status')
    validation = response.get('validation_report', {})
    
    print(f'   ✅ Judge agent completed')
    print(f'   Status: {status}')
    print(f'   All responses valid: {validation.get("all_responses_valid")}')
    
    # Show agent response
    judge_response = response.get('agent_responses', {}).get('judge', {})
    if judge_response:
        print(f'   Confidence score: {judge_response.get("confidence_score")}')
        print(f'   Evidence citations: {len(judge_response.get("evidence", []))}')
        
        # Show sample evidence
        evidence = judge_response.get('evidence', [])
        if evidence:
            print(f'\n   Sample evidence citations:')
            for i, ev in enumerate(evidence[:2]):
                sb = ev.get('supabase', {})
                print(f'     [{i+1}] Table: {sb.get("table")}, Row: {sb.get("row_id")[:12]}...')

# Step 4: Try all legal agents
print(f'\n4. TESTING ALL LEGAL AGENTS:')
agents = ['customerLawyer', 'companyLawyer', 'judge', 'independentLawyer']
for agent in agents:
    try:
        r = requests.post(
            f'{BASE_URL}/api/agents/analyze',
            json={'dispute_id': dispute_id, 'agents': [agent]},
            timeout=30
        )
        status = '✅' if r.status_code == 200 else f'❌ {r.status_code}'
        resp_valid = r.json().get('validation_report', {}).get('all_responses_valid', False) if r.status_code == 200 else False
        valid = '✅' if resp_valid else '❌'
        print(f'   {agent:20} {status} Valid: {valid}')
    except Exception as e:
        print(f'   {agent:20} ❌ Error: {str(e)[:50]}')

print('\n=== TEST COMPLETE ===')
