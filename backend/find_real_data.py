#!/usr/bin/env python3
import requests

# Try different disputes to find one with real data
disputes_to_try = [
    ('ae02d1fe-5a2e-403e-a1fe-85f0c936e9b2', 'GRB-999-MYS'),  # #3 from list
    ('b2d69686-c6e8-49dd-a2aa-7e5dea72d8f3', 'GRB-67-MYS'),   # #4
    ('ffc42533-f36f-4707-9c62-23ad7abf3eb5', 'GRB-6897-MYS'), # #5
]

for dispute_id, expected_order in disputes_to_try:
    print('\n=== Testing {} ==='.format(dispute_id[:12]))
    
    r = requests.get('http://localhost:8000/api/disputes/{}'.format(dispute_id), timeout=5)
    if r.status_code != 200:
        print('  Fetch failed: {}'.format(r.status_code))
        continue
    
    d = r.json()
    order_id = d.get('customer_info', {}).get('order_id')
    print('  Order ID: {} (expected: {})'.format(order_id, expected_order))
    
    # Get evidence
    r2 = requests.get('http://localhost:8000/api/disputes/{}/evidence'.format(dispute_id), timeout=10)
    if r2.status_code != 200:
        print('  Evidence failed: {}'.format(r2.status_code))
        continue
    
    bundle = r2.json().get('bundle', {})
    txn_count = len(bundle.get('transactions', []))
    has_merchant = bool(bundle.get('merchant_record'))
    
    print('  Transactions: {} (found)'.format(txn_count))
    print('  Merchant record: {}'.format(has_merchant))
    
    if txn_count > 0 or has_merchant:
        print('  ✅ This dispute has real data!')
        print('\n  Testing judge agent...')
        r3 = requests.post(
            'http://localhost:8000/api/agents/analyze',
            json={'dispute_id': dispute_id, 'agents': ['judge']},
            timeout=30
        )
        if r3.status_code == 200:
            resp = r3.json()
            print('  Judge Status: {}'.format(resp.get('status')))
            judge_resp = resp.get('agent_responses', {}).get('judge', {})
            print('  Confidence: {}'.format(judge_resp.get('confidence_score')))
            print('  Evidence citations: {}'.format(len(judge_resp.get('evidence', []))))
        else:
            print('  Judge Error: {}'.format(r3.status_code))
