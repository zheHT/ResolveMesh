"""
evidence_gatherer.py

Agent-specific evidence gathering service.
Each agent gets a tailored bundle of evidence to work with.

Uses supabase_queries.py as foundation.
"""

from typing import TypedDict, Optional
from supabase_queries import (
    get_dispute_record,
    get_dispute_logs,
    get_dispute_customer_info,
    get_transactions_by_order_id,
    get_timeline,
    find_matching_hashes,
    get_customer_dispute_history,
    search_logs_by_event,
)


class EvidenceBundle(TypedDict):
    """
    Complete evidence package for an agent
    """
    dispute_id: str
    dispute_record: dict
    customer_info: dict
    system_logs: list[dict]
    transactions: list[dict]
    timeline: list[dict]
    hash_cross_ref: dict
    customer_history: list[dict]
    metadata: dict


# ============================================================================
# AGENT-SPECIFIC EVIDENCE GATHERING
# ============================================================================

def gather_evidence_for_customer_lawyer(dispute_id: str) -> Optional[EvidenceBundle]:
    """
    Gather evidence tailored for Customer Lawyer agent
    
    Focus: What proves the customer's claim?
    - Full dispute details
    - Photos/evidence URLs in logs
    - Delivery timestamps
    - Status changes
    - Transaction completion proof
    
    Exclude: Company's internal notes (but include facts they logged)
    """
    try:
        dispute = get_dispute_record(dispute_id)
        if not dispute:
            return None
        
        customer_info = get_dispute_customer_info(dispute_id)
        all_logs = get_dispute_logs(dispute_id, limit=100)
        
        # Get transaction info for order
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        transactions = []
        if order_id:
            transactions = get_transactions_by_order_id(order_id)
        
        timeline = get_timeline(dispute_id, max_events=100)
        hashes = find_matching_hashes(dispute_id)
        
        # Customer history (detect fraud patterns against customer)
        customer_email = dispute["data"].get("customer_info", {}).get("email")
        customer_history = []
        if customer_email:
            customer_history = get_customer_dispute_history(customer_email, limit=5)
        
        return EvidenceBundle(
            dispute_id=dispute_id,
            dispute_record=dispute,
            customer_info=customer_info or {},
            system_logs=all_logs,
            transactions=transactions,
            timeline=timeline,
            hash_cross_ref=hashes,
            customer_history=customer_history,
            metadata={
                "agent": "customerLawyer",
                "purpose": "Build strongest case for customer position",
                "logs_count": len(all_logs),
                "transactions_count": len(transactions),
                "timeline_events": len(timeline),
                "hash_matches": len(hashes)
            }
        )
    except Exception as e:
        print(f"Error gathering evidence for customer lawyer: {e}")
        return None


def gather_evidence_for_company_lawyer(dispute_id: str) -> Optional[EvidenceBundle]:
    """
    Gather evidence tailored for Company Lawyer agent
    
    Focus: What proves service was delivered/claim is invalid?
    - Transaction completion status
    - Merchant/platform status logs
    - Timestamps proving delivery
    - Hash matches across systems
    - Settlement confirmation
    
    Exclude: Obviously biased complaint text (but include facts)
    """
    try:
        dispute = get_dispute_record(dispute_id)
        if not dispute:
            return None
        
        customer_info = get_dispute_customer_info(dispute_id)
        
        # Fetch all logs, focus on delivery/settlement events
        all_logs = get_dispute_logs(dispute_id, limit=100)
        delivery_logs = search_logs_by_event(dispute_id, "DELIVERY")
        settlement_logs = search_logs_by_event(dispute_id, "SETTLEMENT")
        
        # Get transaction info
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        transactions = []
        if order_id:
            transactions = get_transactions_by_order_id(order_id)
        
        timeline = get_timeline(dispute_id, max_events=100)
        hashes = find_matching_hashes(dispute_id)
        
        return EvidenceBundle(
            dispute_id=dispute_id,
            dispute_record=dispute,
            customer_info=customer_info or {},
            system_logs=all_logs,  # Include all, but delivery/settlement were pre-filtered
            transactions=transactions,
            timeline=timeline,
            hash_cross_ref=hashes,
            customer_history=[],  # Not needed for company perspective
            metadata={
                "agent": "companyLawyer",
                "purpose": "Build strongest defense for company position",
                "logs_count": len(all_logs),
                "delivery_logs": len(delivery_logs),
                "settlement_logs": len(settlement_logs),
                "transactions_count": len(transactions),
                "timeline_events": len(timeline),
            }
        )
    except Exception as e:
        print(f"Error gathering evidence for company lawyer: {e}")
        return None


def gather_evidence_for_judge(dispute_id: str) -> Optional[EvidenceBundle]:
    """
    Gather evidence for Judge agent
    
    Focus: Neutral, complete picture
    - ALL available evidence
    - Chronological timeline
    - All hashes and timestamps
    - Customer AND company records
    
    Expectation: Judge will weigh both sides objectively
    """
    try:
        dispute = get_dispute_record(dispute_id)
        if not dispute:
            return None
        
        customer_info = get_dispute_customer_info(dispute_id)
        
        # Get comprehensive logs (increase limit for judge)
        all_logs = get_dispute_logs(dispute_id, limit=200)
        
        # Get transaction info
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        transactions = []
        if order_id:
            transactions = get_transactions_by_order_id(order_id)
        
        # Full timeline
        timeline = get_timeline(dispute_id, max_events=200)
        
        # All hash cross-references
        hashes = find_matching_hashes(dispute_id)
        
        return EvidenceBundle(
            dispute_id=dispute_id,
            dispute_record=dispute,
            customer_info=customer_info or {},
            system_logs=all_logs,
            transactions=transactions,
            timeline=timeline,
            hash_cross_ref=hashes,
            customer_history=[],
            metadata={
                "agent": "judge",
                "purpose": "Neutral evaluation of both positions",
                "completeness": "FULL",
                "logs_count": len(all_logs),
                "transactions_count": len(transactions),
                "timeline_events": len(timeline),
                "hash_matches": len(hashes)
            }
        )
    except Exception as e:
        print(f"Error gathering evidence for judge: {e}")
        return None


def gather_evidence_for_independent_lawyer(dispute_id: str) -> Optional[EvidenceBundle]:
    """
    Gather evidence for Independent Lawyer agent
    
    Focus: Settlement analysis
    - Summary of dispute and positions
    - Historical precedents (customer history, similar disputes)
    - Critical evidence for settlement
    - Risk assessment data
    """
    try:
        dispute = get_dispute_record(dispute_id)
        if not dispute:
            return None
        
        customer_info = get_dispute_customer_info(dispute_id)
        
        # Get key logs (focus on critical events)
        all_logs = get_dispute_logs(dispute_id, limit=50)
        
        # Get transaction info
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        transactions = []
        if order_id:
            transactions = get_transactions_by_order_id(order_id)
        
        # Timeline
        timeline = get_timeline(dispute_id, max_events=50)
        
        # Customer history for settlement pattern analysis
        customer_email = dispute["data"].get("customer_info", {}).get("email")
        customer_history = []
        if customer_email:
            customer_history = get_customer_dispute_history(customer_email, limit=10)
        
        hashes = find_matching_hashes(dispute_id)
        
        return EvidenceBundle(
            dispute_id=dispute_id,
            dispute_record=dispute,
            customer_info=customer_info or {},
            system_logs=all_logs,
            transactions=transactions,
            timeline=timeline,
            hash_cross_ref=hashes,
            customer_history=customer_history,
            metadata={
                "agent": "independentLawyer",
                "purpose": "Settlement recommendation and risk assessment",
                "logs_count": len(all_logs),
                "transactions_count": len(transactions),
                "customer_history_count": len(customer_history),
                "settlement_focus": True
            }
        )
    except Exception as e:
        print(f"Error gathering evidence for independent lawyer: {e}")
        return None


def gather_evidence_for_merchant(dispute_id: str) -> Optional[EvidenceBundle]:
    """
    Gather evidence for Merchant/Seller agent
    
    Focus: Service delivery and payment rights
    - Order fulfillment status and timestamps
    - Payment settlement records
    - Merchant operational metrics and dispute history
    - Customer behavior patterns
    """
    try:
        dispute = get_dispute_record(dispute_id)
        if not dispute:
            return None
        
        customer_info = get_dispute_customer_info(dispute_id)
        
        # Get logs focusing on fulfillment and payment events
        all_logs = get_dispute_logs(dispute_id, limit=100)
        
        # Filter for merchant-relevant events: order status, payment settlement, fulfillment
        merchant_relevant_logs = [
            log for log in all_logs
            if any(kw in log.get("event_name", "").upper() 
                   for kw in ["FULFILLMENT", "PAYMENT", "SETTLEMENT", "ORDER_STATUS", "DELIVERY", "CONFIRMED"])
        ]
        
        # Get transaction info (payment records)
        order_id = dispute["data"].get("customer_info", {}).get("order_id")
        transactions = []
        if order_id:
            transactions = get_transactions_by_order_id(order_id)
        
        # Timeline for order progression
        timeline = get_timeline(dispute_id, max_events=50)
        
        # Merchant's own dispute history with this customer (if available)
        customer_email = dispute["data"].get("customer_info", {}).get("email")
        customer_history = []
        if customer_email:
            customer_history = get_customer_dispute_history(customer_email, limit=10)
        
        hashes = find_matching_hashes(dispute_id)
        
        return EvidenceBundle(
            dispute_id=dispute_id,
            dispute_record=dispute,
            customer_info=customer_info or {},
            system_logs=merchant_relevant_logs if merchant_relevant_logs else all_logs,
            transactions=transactions,
            timeline=timeline,
            hash_cross_ref=hashes,
            customer_history=customer_history,
            metadata={
                "agent": "merchant",
                "purpose": "Service delivery and payment defense",
                "logs_count": len(merchant_relevant_logs if merchant_relevant_logs else all_logs),
                "transactions_count": len(transactions),
                "customer_history_count": len(customer_history),
                "merchant_focus": True
            }
        )
    except Exception as e:
        print(f"Error gathering evidence for merchant: {e}")
        return None


# ============================================================================
# GENERIC GATHERING (for any agent type)
# ============================================================================

def gather_evidence(dispute_id: str, agent_type: str) -> Optional[EvidenceBundle]:
    """
    Route to appropriate evidence gathering based on agent type
    
    Args:
        dispute_id: The dispute being analyzed
        agent_type: One of: "customerLawyer", "companyLawyer", "judge", "independentLawyer", "merchant"
    
    Returns:
        EvidenceBundle with agent-specific evidence
    """
    if agent_type == "customerLawyer":
        return gather_evidence_for_customer_lawyer(dispute_id)
    elif agent_type == "companyLawyer":
        return gather_evidence_for_company_lawyer(dispute_id)
    elif agent_type == "judge":
        return gather_evidence_for_judge(dispute_id)
    elif agent_type == "independentLawyer":
        return gather_evidence_for_independent_lawyer(dispute_id)
    elif agent_type == "merchant":
        return gather_evidence_for_merchant(dispute_id)
    else:
        print(f"Unknown agent type: {agent_type}")
        return None


# ============================================================================
# EVIDENCE SUMMARY (for context builders)
# ============================================================================

def summarize_evidence_bundle(bundle: EvidenceBundle) -> dict:
    """
    Create a concise summary of evidence bundle for debugging/logging
    """
    return {
        "dispute_id": bundle["dispute_id"],
        "agent": bundle["metadata"].get("agent"),
        "dispute_amount": bundle["dispute_record"]["data"].get("amount"),
        "dispute_status": bundle["dispute_record"]["data"].get("status"),
        "logs_count": len(bundle["system_logs"]),
        "transactions_count": len(bundle["transactions"]),
        "timeline_events": len(bundle["timeline"]),
        "unique_hashes": len(bundle["hash_cross_ref"]),
        "customer_history_count": len(bundle["customer_history"]),
        "metadata": bundle["metadata"]
    }


# ============================================================================
# EVIDENCE FILTRATION (for context size management)
# ============================================================================

def filter_logs_by_relevance(logs: list[dict], max_count: int = 30) -> list[dict]:
    """
    Filter logs to most relevant ones if count exceeds limit
    
    Priority:
    1. DELIVERY/REFUND/COMPLAINT events
    2. Events with photo/evidence URLs
    3. Most recent events
    """
    if len(logs) <= max_count:
        return logs
    
    # Separate by priority
    priority_events = []
    detail_events = []
    
    priority_keywords = ["DELIVERY", "REFUND", "COMPLAINT", "CHARGE", "SETTLEMENT", "EVIDENCE"]
    
    for log in logs:
        event_name = log.get("event_name", "").upper()
        has_url = "url" in str(log.get("payload", {})).lower()
        
        if any(kw in event_name for kw in priority_keywords) or has_url:
            priority_events.append(log)
        else:
            detail_events.append(log)
    
    # Take most recent from details
    detail_events = sorted(detail_events, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Combine: priority first, then recent details
    result = priority_events + detail_events[:max_count - len(priority_events)]
    
    # Re-sort by timestamp
    result.sort(key=lambda x: x.get("timestamp", ""))
    
    return result[:max_count]
