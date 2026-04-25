#!/usr/bin/env python3
import requests
import json

r = requests.get('http://localhost:8000/api/disputes?limit=3', timeout=5)
print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    print('Disputes found:', len(data))
    for i, d in enumerate(data):
        ci = d.get('customer_info', {})
        order_id = ci.get('order_id') if ci else 'N/A'
        dispute_id = d.get('id', 'unknown')[:12]
        print('  [{}] {}... Order: {}'.format(i+1, dispute_id, order_id))
