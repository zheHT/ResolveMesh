"""
Dispute Analysis Agent
Analyzes PENDING disputes and creates comprehensive reports in the required format.
Stores results in disputes.agent_reports column.
"""

import json
import requests
from datetime import datetime, timezone
from database import supabase


def parse_customer_info(raw_data):
    """Parse customer_info JSONB"""
    if isinstance(raw_data, dict):
        return raw_data
    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data)
        except:
            return {}
    return {}


def parse_ledger_data(raw_data):
    """Parse ledger_data JSONB"""
    if isinstance(raw_data, dict):
        return raw_data
    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data)
        except:
            return {}
    return {}


def get_merchant_notes(order_id):
    """Get merchant internal notes for investigation"""
    try:
        res = supabase.table("merchant_records").select("*").eq("order_id", order_id).execute()
        if res.data:
            merchant = res.data[0]
            notes = merchant.get('internal_notes', '')
            prep_status = merchant.get('prep_status', 'UNKNOWN')
            return {
                'notes': notes or '',
                'prep_status': prep_status,
                'merchant_name': merchant.get('merchant_name', 'Unknown')
            }
    except Exception as e:
        print(f"Error fetching merchant notes: {e}")
    return {'notes': '', 'prep_status': 'UNKNOWN', 'merchant_name': 'Unknown'}


def get_bank_verification(order_id):
    """Check if transaction was verified by bank"""
    try:
        res = supabase.table("transactions").select("*").execute()
        for txn in res.data:
            ledger_data = parse_ledger_data(txn.get('ledger_data', {}))
            if ledger_data.get('order_id') == order_id:
                payment_status = txn.get('payment_status', 'UNKNOWN')
                # bank_verified = True if payment_status is PAID/SUCCESS
                return payment_status.upper() in ['PAID', 'SUCCESS', 'VERIFIED']
    except Exception as e:
        print(f"Error checking bank verification: {e}")
    return False


def analyze_dispute(dispute_id):
    """
    Analyze a single dispute and generate comprehensive report
    Returns report in required format
    """
    try:
        # Get dispute
        dispute_res = supabase.table("disputes").select("*").eq("id", dispute_id).execute()
        if not dispute_res.data:
            return None
        
        dispute = dispute_res.data[0]
        customer_info = parse_customer_info(dispute.get('customer_info', {}))
        order_id = customer_info.get('order_id', 'UNKNOWN')
        issue_type = customer_info.get('issue_type', 'General')
        amount = customer_info.get('amount', 0)
        
        # Get merchant data
        merchant_data = get_merchant_notes(order_id)
        
        # Check bank verification
        bank_verified = get_bank_verification(order_id)
        
        # Analyze issue type and determine verdict
        verdict, confidence_score, reasoning = analyze_issue(
            issue_type,
            amount,
            merchant_data,
            bank_verified
        )
        
        # Generate reports
        tldr = generate_tldr(issue_type, verdict, confidence_score)
        internal_report = generate_internal_report(dispute_id, customer_info, merchant_data, verdict)
        police_report = generate_police_report(dispute_id, customer_info, issue_type, verdict)
        
        # Build final report
        report = {
            "judgment_phase": {
                "verdict": verdict,
                "reasoning": reasoning,
                "confidence_score": confidence_score
            },
            "reporting_phase": {
                "tldr": tldr,
                "internal_full_report": internal_report,
                "external_police_report": police_report
            },
            "investigation_phase": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_points": {
                    "bank_verified": bank_verified,
                    "merchant_notes_flagged": bool(merchant_data.get('notes', ''))
                },
                "sleuth_evidence": f"Order: {order_id}, Merchant: {merchant_data.get('merchant_name')}, Prep Status: {merchant_data.get('prep_status')}"
            }
        }
        
        return report
    
    except Exception as e:
        print(f"Error analyzing dispute {dispute_id}: {e}")
        return None


def analyze_dispute_fast(dispute, merchants_by_order, transactions_by_order):
    """
    Analyze dispute using pre-loaded data (O(1) lookups, no Supabase queries)
    Much faster than analyze_dispute() which makes N+1 queries
    """
    try:
        dispute_id = dispute['id']
        customer_info = parse_customer_info(dispute.get('customer_info', {}))
        order_id = customer_info.get('order_id', 'UNKNOWN')
        issue_type = customer_info.get('issue_type', 'General')
        amount = customer_info.get('amount', 0)
        
        # Fast lookups - O(1)
        merchant = merchants_by_order.get(order_id, {})
        merchant_data = {
            'notes': merchant.get('internal_notes', '') or '',
            'prep_status': merchant.get('prep_status', 'UNKNOWN'),
            'merchant_name': merchant.get('merchant_name', 'Unknown')
        }
        
        # Check bank verification
        txn_list = transactions_by_order.get(order_id, [])
        bank_verified = any(t.get('payment_status', '').upper() in ['PAID', 'SUCCESS', 'VERIFIED'] for t in txn_list)
        
        # Analyze issue type and determine verdict
        verdict, confidence_score, reasoning = analyze_issue(
            issue_type,
            amount,
            merchant_data,
            bank_verified
        )
        
        # Generate reports
        tldr = generate_tldr(issue_type, verdict, confidence_score)
        internal_report = generate_internal_report(dispute_id, customer_info, merchant_data, verdict)
        police_report = generate_police_report(dispute_id, customer_info, issue_type, verdict)
        
        # Build final report
        report = {
            "judgment_phase": {
                "verdict": verdict,
                "reasoning": reasoning,
                "confidence_score": confidence_score
            },
            "reporting_phase": {
                "tldr": tldr,
                "internal_full_report": internal_report,
                "external_police_report": police_report
            },
            "investigation_phase": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_points": {
                    "bank_verified": bank_verified,
                    "merchant_notes_flagged": bool(merchant_data.get('notes', ''))
                },
                "sleuth_evidence": f"Order: {order_id}, Merchant: {merchant_data.get('merchant_name')}, Prep Status: {merchant_data.get('prep_status')}"
            }
        }
        
        return report
    
    except Exception as e:
        print(f"Error analyzing dispute with cached data: {e}")
        return None


def analyze_issue(issue_type, amount, merchant_data, bank_verified):
    """
    Determine verdict based on issue characteristics
    Returns: (verdict, confidence_score, reasoning)
    """
    issue_lower = issue_type.lower()
    
    # NOT DELIVERED
    if 'delivered' in issue_lower or 'delivery' in issue_lower:
        if merchant_data['prep_status'] == 'COMPLETED' and not bank_verified:
            return (
                'REFUND_APPROVED',
                85,
                'Merchant confirmed preparation completed but payment not verified. Delivery failure with valid refund claim.'
            )
        elif bank_verified and merchant_data['prep_status'] == 'COMPLETED':
            return (
                'REQUIRES_MANUAL_REVIEW',
                55,
                'Merchant prepared order and payment verified, but customer reports non-delivery. Requires investigation into delivery logistics.'
            )
        else:
            return (
                'DISPUTE_REJECTED',
                65,
                'Insufficient evidence of delivery failure. Merchant has no completion record.'
            )
    
    # WRONG ITEM / INCORRECT ORDER
    elif 'wrong' in issue_lower or 'incorrect' in issue_lower or 'order' in issue_lower:
        if merchant_data.get('notes'):
            return (
                'REQUIRES_MANUAL_REVIEW',
                60,
                f'Merchant notes indicate potential issue: {merchant_data["notes"][:100]}. Requires detailed review.'
            )
        else:
            return (
                'DISPUTE_REJECTED',
                70,
                'No merchant notes confirming preparation issue. Claim lacks supporting evidence.'
            )
    
    # POOR QUALITY / DAMAGED
    elif 'quality' in issue_lower or 'damaged' in issue_lower or 'spoiled' in issue_lower:
        return (
            'REQUIRES_MANUAL_REVIEW',
            50,
            'Quality disputes require customer photo evidence and merchant response. Escalating to manual review.'
        )
    
    # DOUBLE CHARGE / OVERCHARGE
    elif 'double' in issue_lower or 'overcharge' in issue_lower or 'charge' in issue_lower:
        if bank_verified:
            return (
                'REFUND_APPROVED',
                90,
                f'Duplicate/overcharge detected. Amount: ${amount}. Bank verified transaction exists. Refund approved.'
            )
        else:
            return (
                'REQUIRES_MANUAL_REVIEW',
                65,
                'Potential double charge. Bank verification needed before approval.'
            )
    
    # DEFAULT
    else:
        return (
            'REQUIRES_MANUAL_REVIEW',
            45,
            f'Dispute type "{issue_type}" requires detailed investigation by specialist team.'
        )


def generate_tldr(issue_type, verdict, confidence_score):
    """Generate customer-friendly TLDR"""
    messages = {
        'REFUND_APPROVED': f'Your dispute has been approved for refund. Processing within 5-7 business days.',
        'DISPUTE_REJECTED': f'We could not validate your dispute claim. Please contact support if you disagree.',
        'REQUIRES_MANUAL_REVIEW': f'Your case requires specialist review (confidence: {confidence_score}%). You will receive updates within 48 hours.',
        'INSUFFICIENT_DATA': f'We need more information to process your dispute. Please provide additional evidence.',
    }
    return messages.get(verdict, f'Your dispute regarding "{issue_type}" is being reviewed.')


def generate_internal_report(dispute_id, customer_info, merchant_data, verdict):
    """Generate detailed internal report"""
    report = f"""
INTERNAL DISPUTE ANALYSIS REPORT
================================
Dispute ID: {dispute_id[:12]}...
Created: {datetime.now(timezone.utc).isoformat()}

CUSTOMER CLAIM:
  Issue: {customer_info.get('issue_type', 'Unknown')}
  Amount: ${customer_info.get('amount', 0)}
  Order ID: {customer_info.get('order_id', 'N/A')}
  Platform: {customer_info.get('platform', 'Unknown')}

MERCHANT INVESTIGATION:
  Merchant: {merchant_data.get('merchant_name', 'Unknown')}
  Prep Status: {merchant_data.get('prep_status', 'Unknown')}
  Internal Notes: {merchant_data.get('notes', 'No notes') or 'No notes'}

VERDICT: {verdict}

NEXT STEPS:
  - Notify customer of decision
  - Process refund if approved
  - Archive case once resolved
"""
    return report.strip()


def generate_police_report(dispute_id, customer_info, issue_type, verdict):
    """Generate police/fraud report for external escalation"""
    if verdict not in ['REFUND_APPROVED', 'DISPUTE_REJECTED']:
        report = f"""
POLICE/FRAUD REPORT
===================
Case ID: {dispute_id}
Date: {datetime.now(timezone.utc).isoformat()}

INCIDENT SUMMARY:
  Type: Potential fraud/{issue_type}
  Platform: {customer_info.get('platform', 'Unknown')}
  Amount: ${customer_info.get('amount', 0)}
  
STATUS: Case requires manual review - not yet escalated to authorities.
ACTION: Pending specialist investigation before external reporting.
"""
    else:
        report = ""  # Only generate for serious cases
    
    return report.strip()


def update_dispute_agent_reports(dispute_id, report):
    """Update disputes table with agent_reports"""
    try:
        result = supabase.table("disputes").update({
            "agent_reports": report
        }).eq("id", dispute_id).execute()
        
        if result.data:
            print(f"✅ Updated dispute {dispute_id[:12]}... with analysis")
            return True
        else:
            print(f"❌ Failed to update dispute {dispute_id}")
            return False
    except Exception as e:
        print(f"❌ Error updating dispute: {e}")
        return False


def analyze_all_pending_disputes():
    """
    Main function: Analyze all PENDING disputes and store reports
    OPTIMIZED: Batch query all related data upfront
    """
    print("=" * 70)
    print("DISPUTE ANALYSIS AGENT - Processing PENDING disputes")
    print("=" * 70)
    
    try:
        # Batch load all data upfront (faster than N+1 queries)
        print("\n🔄 Loading all reference data...")
        pending_res = supabase.table("disputes").select("*").eq("status", "PENDING").execute()
        merchant_res = supabase.table("merchant_records").select("*").execute()
        transaction_res = supabase.table("transactions").select("*").execute()
        
        if not pending_res.data:
            print("\n⚠️  No PENDING disputes found")
            return 0
        
        # Build lookup dictionaries for O(1) access
        merchants_by_order = {}
        for merchant in merchant_res.data:
            order_id = merchant.get('order_id')
            if order_id:
                merchants_by_order[order_id] = merchant
        
        transactions_by_order = {}
        for txn in transaction_res.data:
            ledger_data = parse_ledger_data(txn.get('ledger_data', {}))
            order_id = ledger_data.get('order_id')
            if order_id:
                if order_id not in transactions_by_order:
                    transactions_by_order[order_id] = []
                transactions_by_order[order_id].append(txn)
        
        print(f"✅ Loaded: {len(pending_res.data)} disputes, {len(merchants_by_order)} merchants, {len(transactions_by_order)} transactions")
        print(f"\n🔍 Found {len(pending_res.data)} PENDING disputes")
        
        processed_count = 0
        for dispute in pending_res.data:
            dispute_id = dispute['id']
            print(f"\n📋 Analyzing: {dispute_id[:12]}...")
            
            # Analyze using cached data
            report = analyze_dispute_fast(dispute, merchants_by_order, transactions_by_order)
            
            if report:
                # Update database
                if update_dispute_agent_reports(dispute_id, report):
                    processed_count += 1
                    
                    # Print summary
                    verdict = report['judgment_phase']['verdict']
                    confidence = report['judgment_phase']['confidence_score']
                    print(f"   Verdict: {verdict} ({confidence}% confidence)")
            else:
                print(f"   ❌ Failed to analyze")
        
        print("\n" + "=" * 70)
        print(f"✅ ANALYSIS COMPLETE - {processed_count}/{len(pending_res.data)} disputes updated")
        print("=" * 70)
        
        return processed_count
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 0


if __name__ == "__main__":
    analyze_all_pending_disputes()
