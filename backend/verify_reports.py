import requests
import json

# Get list of disputes
r = requests.post('http://localhost:8000/api/disputes', timeout=5)
if r.status_code == 200:
    result = r.json()
    analyses = result.get('analyses', [])
    if analyses:
        dispute_id = analyses[0]['dispute_id']
        print(f"Fetching dispute: {dispute_id[:12]}...\n")
        
        # Fetch full dispute
        r = requests.get(f'http://localhost:8000/api/disputes/{dispute_id}', timeout=5)
        if r.status_code == 200:
            dispute = r.json()
            agent_reports = dispute.get('agent_reports')
            
            if agent_reports:
                print('✅ agent_reports structure found:\n')
                if isinstance(agent_reports, str):
                    try:
                        agent_reports = json.loads(agent_reports)
                    except:
                        pass
                
                print(json.dumps(agent_reports, indent=2))
                
                print("\n" + "="*70)
                print("STRUCTURE VERIFICATION:")
                print("="*70)
                if isinstance(agent_reports, dict):
                    print(f"✅ judgment_phase: {bool(agent_reports.get('judgment_phase'))}")
                    print(f"✅ reporting_phase: {bool(agent_reports.get('reporting_phase'))}")
                    print(f"✅ investigation_phase: {bool(agent_reports.get('investigation_phase'))}")
                    
                    jp = agent_reports.get('judgment_phase', {})
                    print(f"\n   Verdict: {jp.get('verdict')}")
                    print(f"   Confidence: {jp.get('confidence_score')}%")
                    print(f"   Reasoning: {jp.get('reasoning')[:100]}...")
            else:
                print('⚠️  agent_reports is empty')
        else:
            print(f'Error fetching dispute: {r.status_code}')
