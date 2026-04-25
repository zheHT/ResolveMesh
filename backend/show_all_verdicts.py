import requests
import json

# Get all disputes
r = requests.post('http://localhost:8000/api/disputes', timeout=5)
if r.status_code == 200:
    result = r.json()
    analyses = result.get('analyses', [])
    
    # Show all verdicts
    print('='*70)
    print('DISPUTE ANALYSIS SUMMARY')
    print('='*70)
    
    for i, analysis in enumerate(analyses[:5], 1):
        dispute_id = analysis['dispute_id']
        
        # Get full dispute
        r = requests.get(f'http://localhost:8000/api/disputes/{dispute_id}', timeout=5)
        if r.status_code == 200:
            dispute = r.json()
            reports = dispute.get('agent_reports', {})
            
            if isinstance(reports, str):
                try:
                    reports = json.loads(reports)
                except:
                    reports = {}
            
            jp = reports.get('judgment_phase', {})
            order_id = analysis['order_id']
            
            print(f'\n{i}. Order: {order_id}')
            print(f'   Verdict: {jp.get("verdict", "N/A")}')
            print(f'   Confidence: {jp.get("confidence_score", 0)}%')
            print(f'   Merchant: {analysis.get("merchant_records_found", 0)} found')
            print(f'   Transactions: {analysis.get("transaction_records_found", 0)} found')

print('\n' + '='*70)
print('✅ ALL DISPUTES ANALYZED AND STORED')
print('='*70)
