import requests
import json

# Call the new POST /api/disputes endpoint (no longer creates, now analyzes)
r = requests.post('http://localhost:8000/api/disputes', timeout=10)
if r.status_code == 200:
    result = r.json()
    print('✅ POST /api/disputes - Analyzes PENDING disputes')
    print(f'   Disputes found: {result["disputes_analyzed"]}')
    if result['disputes_analyzed'] > 0:
        print('\n📊 Sample Analysis:')
        for analysis in result['analyses'][:2]:
            print(f'   Order: {analysis["order_id"]}')
            print(f'   Merchant Records: {analysis["merchant_records_found"]}')
            print(f'   Transaction Records: {analysis["transaction_records_found"]}')
            print(f'   3-Table Linkage: {analysis["three_table_linkage"]}')
            print()
else:
    print(f'Error: {r.status_code}')
    print(r.text)
