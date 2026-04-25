#!/usr/bin/env python3
import requests

dispute_id = '36c644a7-e61e-48fc-a755-03962ecc6584'

# Get dispute detail
r = requests.get('http://localhost:8000/api/disputes/{}'.format(dispute_id), timeout=5)
if r.status_code == 200:
    d = r.json()
    order_id = d.get('customer_info', {}).get('order_id')
    print('Dispute: {}'.format(dispute_id[:12]))
    print('Order ID: {}'.format(order_id))
    print('Status: {}'.format(d.get('status')))
    
    # Get evidence
    r2 = requests.get('http://localhost:8000/api/disputes/{}/evidence?agent_type=judge'.format(dispute_id), timeout=10)
    print('\nEvidence status: {}'.format(r2.status_code))
    if r2.status_code == 200:
        bundle = r2.json().get('bundle', {})
        print('Dispute record found: {}'.format(bool(bundle.get('dispute_record'))))
        print('Transactions: {}'.format(len(bundle.get('transactions', []))))
        print('Merchant record: {}'.format(bool(bundle.get('merchant_record'))))
        print('System logs: {}'.format(len(bundle.get('system_logs', []))))
        
        # Test judge
        print('\nTesting judge agent...')
        r3 = requests.post(
            'http://localhost:8000/api/agents/analyze',
            json={'dispute_id': dispute_id, 'agents': ['judge']},
            timeout=30
        )
        if r3.status_code == 200:
            resp = r3.json()
            print('Judge Status: {}'.format(resp.get('status')))
            print('Valid: {}'.format(resp.get('validation_report', {}).get('all_responses_valid')))
        else:
            print('Judge Error: {} - {}'.format(r3.status_code, r3.text[:100]))
    else:
        print('Error: {}'.format(r2.text[:200]))
else:
    print('Error: {}'.format(r.status_code))
