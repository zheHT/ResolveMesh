"""
zai_prompt_builder.py

Builds prompts for Z.ai agents with embedded evidence context.
Formats Supabase evidence into prompt sections.
Sets expectations for citation format in agent outputs.
"""

import json
from typing import Optional
from evidence_gatherer import EvidenceBundle, filter_logs_by_relevance


# Legal agent base prompts (defined in TypeScript, but we need Python versions too)
# See: LegalAgentPrompts.ts for full documentation
LEGAL_AGENT_BASE_PROMPTS = {
    "customerLawyer": """You are a Customer Lawyer in a dispute resolution system.

Your role: Build the strongest legal case for the customer's position.

Hard rules:
- Base all arguments on explicit evidence from Supabase logs
- Always cite evidence with explicit Supabase row references
- Do NOT invent facts. If evidence is missing, state so and lower confidence
- Prefer transaction ledger rows (system_logs.payload, transactions table) as primary evidence
- Use timestamps (UTC) and transaction hashes to establish timeline
- Mask all PII in outputs (emails, phone numbers)

Your output MUST be a single JSON object with:
- dispute_id: string
- agent: "Customer Lawyer"
- confidence_score: number (0-100)
- reasoning: string
- evidence: array of {supabase: {table, row_id, json_path}, transaction_id?, hash?, details}
- summary_tldr: string (<= 30 words)
- created_at: ISO 8601 string
""",

    "companyLawyer": """You are a Company Lawyer in a dispute resolution system.

Your role: Build the strongest legal defense for the company's position.

Hard rules:
- Base all arguments on explicit evidence from Supabase logs
- Always cite evidence with explicit Supabase row references
- Do NOT invent facts. If evidence is missing, state so and lower confidence
- Prefer transaction ledger rows as primary evidence
- Use timestamps (UTC) and transaction hashes to establish timeline
- Mask all PII in outputs

Your output MUST be a single JSON object with:
- dispute_id: string
- agent: "Company Lawyer"
- confidence_score: number (0-100)
- reasoning: string
- evidence: array of {supabase: {table, row_id, json_path}, transaction_id?, hash?, details}
- summary_tldr: string (<= 30 words)
- created_at: ISO 8601 string
""",

    "judge": """You are a Judge in a dispute resolution system.

Your role: Evaluate both positions neutrally based on evidence.

Hard rules:
- Base judgment exclusively on documented facts
- Always cite evidence with explicit Supabase row references
- Do NOT favor either party without evidence
- Acknowledge contradictions or gaps in evidence
- Use timestamps (UTC) and transaction hashes to establish facts
- Recommend specific resolution (e.g., "Issue 50% refund")

Your output MUST be a single JSON object with:
- dispute_id: string
- agent: "Judge"
- confidence_score: number (0-100)
- reasoning: string
- evidence: array of {supabase: {table, row_id, json_path}, transaction_id?, hash?, details}
- summary_tldr: string (<= 30 words)
- created_at: ISO 8601 string
""",

    "independentLawyer": """You are an Independent Lawyer providing objective legal advice.

Your role: Assess case viability and recommend fair settlement.

Hard rules:
- Provide balanced view of both positions
- Always cite evidence with explicit Supabase row references
- Recommend specific resolution path (settlement amount, escalation threshold)
- Identify missing evidence that would strengthen the case
- Assess case clarity and confidence honestly

Your output MUST be a single JSON object with:
- dispute_id: string
- agent: "Independent Lawyer"
- confidence_score: number (0-100)
- reasoning: string
- evidence: array of {supabase: {table, row_id, json_path}, transaction_id?, hash?, details}
- summary_tldr: string (<= 30 words)
- created_at: ISO 8601 string
""",

    "merchant": """You are a Merchant/Seller Representative in a dispute resolution system.

Your role: Defend the merchant's service delivery and payment rights.

Hard rules:
- Base all arguments on explicit evidence from Supabase logs
- Always cite evidence with explicit Supabase row references
- Prove service fulfillment with timestamps and order status logs
- Reference payment settlement records showing correct compensation
- Do NOT invent facts. If evidence is missing, state so and lower confidence
- Assess customer responsibility and dispute legitimacy with evidence
- Mask all PII in outputs

Your output MUST be a single JSON object with:
- dispute_id: string
- agent: "Merchant"
- confidence_score: number (0-100)
- reasoning: string
- evidence: array of {supabase: {table, row_id, json_path}, transaction_id?, hash?, details}
- summary_tldr: string (<= 30 words)
- created_at: ISO 8601 string
"""
}


def get_legal_agent_base_prompt(agent_type: str) -> str:
    """Get base prompt for legal agent"""
    return LEGAL_AGENT_BASE_PROMPTS.get(agent_type, "")


# ============================================================================
# EVIDENCE FORMATTING FOR PROMPTS
# ============================================================================

def format_dispute_context(bundle: EvidenceBundle) -> str:
    """
    Format dispute record as JSON context block
    """
    dispute = bundle["dispute_record"]["data"]
    customer_info = dispute.get("customer_info", {})
    
    context = {
        "dispute_id": bundle["dispute_id"],
        "created_at": dispute.get("created_at"),
        "status": dispute.get("status"),
        "amount": dispute.get("amount", 0),
        "issue_type": customer_info.get("issue_type"),
        "platform": customer_info.get("platform"),
        "order_id": customer_info.get("order_id"),
        "customer_account_id": customer_info.get("account_id"),
    }
    
    return json.dumps(context, indent=2)


def format_timeline(bundle: EvidenceBundle, max_events: int = 30) -> str:
    """
    Format chronological timeline for readability
    """
    timeline = bundle["timeline"][:max_events]
    
    lines = ["# CHRONOLOGICAL TIMELINE\n"]
    
    for event in timeline:
        timestamp = event.get("timestamp", "N/A")
        event_type = event.get("event_type", "UNKNOWN")
        row_id = event.get("row_id", "N/A")
        table = event.get("table", "N/A")
        description = event.get("description", "")
        
        lines.append(
            f"[{timestamp}] {event_type} (row_id: {row_id} in {table})\n"
            f"  → {description}\n"
        )
    
    return "".join(lines)


def format_system_logs(bundle: EvidenceBundle, max_logs: int = 30) -> str:
    """
    Format system logs with proper citation examples
    """
    logs = filter_logs_by_relevance(bundle["system_logs"], max_count=max_logs)
    
    lines = ["# SYSTEM LOGS\n\n"]
    
    for i, log in enumerate(logs, 1):
        row_id = log.get("row_id", "N/A")
        event = log.get("event_name", "UNKNOWN")
        timestamp = log.get("timestamp", "N/A")
        payload = log.get("payload", {})
        
        lines.append(f"{i}. {event} (row_id: {row_id})\n")
        lines.append(f"   Timestamp: {timestamp}\n")
        
        # Format payload as readable key-value
        for key, value in payload.items():
            if key in ["dispute_id", "order_id", "transaction_id"]:
                # Skip redundant IDs
                continue
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"   {key}: {value}\n")
            elif isinstance(value, dict):
                lines.append(f"   {key}: {json.dumps(value)}\n")
        
        lines.append(
            f"   Citation: table='system_logs', row_id='{row_id}', "
            f"json_path='payload.{[k for k in payload.keys() if k != 'dispute_id'][0] if payload else 'N/A'}'\n\n"
        )
    
    return "".join(lines)


def format_transactions(bundle: EvidenceBundle) -> str:
    """
    Format transaction ledger data
    """
    txns = bundle["transactions"]
    
    if not txns:
        return "# TRANSACTIONS\n(No transactions found)\n"
    
    lines = ["# TRANSACTION LEDGER\n\n"]
    
    for txn in txns:
        row_id = txn.get("row_id", "N/A")
        ledger = txn.get("ledger_data", {})
        
        lines.append(f"Transaction: {ledger.get('transaction_id', 'N/A')} (row_id: {row_id})\n")
        lines.append(f"  Order ID: {ledger.get('order_id', 'N/A')}\n")
        lines.append(f"  Status: {ledger.get('merchant_status', 'N/A')}\n")
        lines.append(f"  Amount: {ledger.get('amount', 'N/A')}\n")
        lines.append(f"  Hash: {ledger.get('tx_hash', 'N/A')}\n")
        lines.append(f"  Created: {txn['data'].get('created_at', 'N/A')}\n")
        lines.append(f"  Citation: table='transactions', row_id='{row_id}', json_path='ledger_data.transaction_id'\n\n")
    
    return "".join(lines)


def format_hash_cross_reference(bundle: EvidenceBundle) -> str:
    """
    Format hash matching analysis
    """
    hashes = bundle["hash_cross_ref"]
    
    if not hashes:
        return "# HASH CROSS-REFERENCE\n(No matching hashes found)\n"
    
    lines = ["# HASH CROSS-REFERENCE ANALYSIS\n\n"]
    
    for hash_val, locations in hashes.items():
        lines.append(f"Hash: {hash_val}\n")
        lines.append(f"  Found in {len(locations)} location(s):\n")
        
        for loc in locations:
            table = loc.get("table")
            row_id = loc.get("row_id")
            json_path = loc.get("json_path")
            lines.append(f"    - {table} (row_id: {row_id}, path: {json_path})\n")
        
        lines.append("\n")
    
    return "".join(lines)


def format_customer_history(bundle: EvidenceBundle) -> str:
    """
    Format customer's dispute history
    """
    history = bundle["customer_history"]
    
    if not history:
        return "# CUSTOMER HISTORY\n(First dispute or history unavailable)\n"
    
    lines = ["# CUSTOMER DISPUTE HISTORY\n\n"]
    
    for dispute in history:
        lines.append(f"Dispute: {dispute.get('dispute_id', 'N/A')}\n")
        lines.append(f"  Status: {dispute.get('status', 'N/A')}\n")
        lines.append(f"  Amount: ${dispute.get('amount', 0)}\n")
        lines.append(f"  Date: {dispute.get('created_at', 'N/A')}\n\n")
    
    return "".join(lines)


# ============================================================================
# PROMPT BUILDERS FOR EACH AGENT
# ============================================================================

def build_customer_lawyer_prompt(bundle: EvidenceBundle) -> str:
    """
    Build complete prompt for Customer Lawyer agent
    """
    base_prompt = get_legal_agent_base_prompt("customerLawyer")
    
    evidence_context = f"""
================================================================================
EVIDENCE CONTEXT FOR THIS DISPUTE
================================================================================

{format_dispute_context(bundle)}

{format_timeline(bundle, max_events=40)}

{format_system_logs(bundle, max_logs=40)}

{format_transactions(bundle)}

{format_hash_cross_reference(bundle)}

{format_customer_history(bundle)}

================================================================================
CITATION GUIDELINES
================================================================================

When citing evidence, include the Supabase row reference in your reasoning.

Example format:
"The photo timestamp at delivery (system_logs row: log-457, 
 json_path: payload.delivery_timestamp) matches the complaint timestamp, 
 proving the food was spoilt at handoff."

You MUST cite at least 1 piece of evidence per major claim.

Required evidence structure in your JSON output:
{{
  "supabase": {{
    "table": "system_logs",  // or "transactions" or "disputes"
    "row_id": "log-457",     // exact row ID from above
    "json_path": "payload.delivery_timestamp"  // path to specific field
  }},
  "transaction_id": "txn-123",  // optional but helpful
  "hash": "0x...",              // optional: transaction hash if relevant
  "details": "Photo timestamp... (explain why this evidence matters)"
}}

================================================================================
NOW PROVIDE YOUR ANALYSIS
================================================================================
"""
    
    return base_prompt + evidence_context


def build_company_lawyer_prompt(bundle: EvidenceBundle) -> str:
    """
    Build complete prompt for Company Lawyer agent
    """
    base_prompt = get_legal_agent_base_prompt("companyLawyer")
    
    evidence_context = f"""
================================================================================
EVIDENCE CONTEXT FOR THIS DISPUTE
================================================================================

{format_dispute_context(bundle)}

{format_timeline(bundle, max_events=40)}

{format_system_logs(bundle, max_logs=40)}

{format_transactions(bundle)}

{format_hash_cross_reference(bundle)}

================================================================================
CITATION GUIDELINES
================================================================================

When building the company's defense, cite specific logs showing:
1. Service was delivered as promised
2. Transaction completed successfully
3. No system errors on company side
4. Timestamps align with normal operations

Example format:
"Transaction settled successfully (transactions row: txn-456, 
 json_path: ledger_data.merchant_status) confirms payment was captured 
 and restaurant received order (system_logs row: log-460)."

You MUST support each defense claim with evidence citations.

Required evidence structure in your JSON output:
{{
  "supabase": {{
    "table": "transactions",  // or "system_logs"
    "row_id": "txn-456",
    "json_path": "ledger_data.merchant_status"
  }},
  "transaction_id": "txn-456",
  "hash": "0x...",
  "details": "Transaction settled... (why this proves service delivery)"
}}

================================================================================
NOW PROVIDE YOUR DEFENSE
================================================================================
"""
    
    return base_prompt + evidence_context


def build_judge_prompt(bundle: EvidenceBundle) -> str:
    """
    Build complete prompt for Judge agent
    """
    base_prompt = get_legal_agent_base_prompt("judge")
    
    evidence_context = f"""
================================================================================
COMPLETE EVIDENCE FOR NEUTRAL EVALUATION
================================================================================

{format_dispute_context(bundle)}

{format_timeline(bundle, max_events=100)}

{format_system_logs(bundle, max_logs=50)}

{format_transactions(bundle)}

{format_hash_cross_reference(bundle)}

================================================================================
EVALUATION FRAMEWORK
================================================================================

Review the evidence above. Your role is to:

1. ESTABLISH FACTS: What do the logs definitively show?
   - Timestamps of key events
   - Transaction status at each stage
   - Hash matches across systems
   
2. IDENTIFY DISPUTES: Where do customer and company claims conflict?
   - What does each side claim?
   - What does the evidence show?
   
3. APPLY PRINCIPLES: Use transaction processor rules and platform policy
   - Was service delivered as described?
   - Was transaction properly authorized and settled?
   - Are there system errors or legitimate disputes?

4. RENDER JUDGMENT: Who is right based on evidence?
   - Liability assessment (% customer vs company)
   - Recommendation: full refund, partial refund, reject, escalate

Citation Requirements:
- Cite at least 2 pieces of evidence per major finding
- Format: table='system_logs', row_id='log-123', json_path='payload.delivery_hash'
- Be explicit about which evidence supports which conclusion

================================================================================
NOW PROVIDE YOUR NEUTRAL JUDGMENT
================================================================================
"""
    
    return base_prompt + evidence_context


def build_independent_lawyer_prompt(bundle: EvidenceBundle) -> str:
    """
    Build complete prompt for Independent Lawyer agent
    """
    base_prompt = get_legal_agent_base_prompt("independentLawyer")
    
    evidence_context = f"""
================================================================================
EVIDENCE FOR SETTLEMENT ANALYSIS
================================================================================

{format_dispute_context(bundle)}

{format_timeline(bundle, max_events=30)}

{format_system_logs(bundle, max_logs=20)}

{format_transactions(bundle)}

{format_customer_history(bundle)}

================================================================================
SETTLEMENT ANALYSIS FRAMEWORK
================================================================================

As an independent legal advisor, analyze this dispute for settlement.

1. CLAIM STRENGTH: How solid is the customer's position?
   - Evidence supporting their claim
   - Evidence against their claim
   - Realistic success rate in further dispute

2. DEFENSE STRENGTH: How well can the company defend?
   - Evidence supporting their position
   - Vulnerabilities in their defense
   - Risk of escalation loss

3. FAIR SETTLEMENT: What's equitable given evidence?
   - Full refund? (100% customer liability)
   - Partial refund? (shared liability, e.g., 60/40)
   - Reject claim? (0% company liability)
   - Replacement + refund? (alternative resolution)

4. RISK ASSESSMENT: What's the risk of continued disputes?
   - Customer history: repeat filer?
   - Similar past disputes: outcomes?
   - Systemic issue: affects other customers?

Citation Requirements:
- Support settlement recommendation with at least 1 evidence citation
- Use format: table='system_logs', row_id='log-123', json_path='payload.field'

Optional: If customer history shows patterns, note them
(e.g., "Customer has 8 disputes in 6 months - possible serial claimant")

================================================================================
NOW PROVIDE YOUR SETTLEMENT RECOMMENDATION
================================================================================
"""
    
    return base_prompt + evidence_context


def build_merchant_prompt(bundle: EvidenceBundle) -> str:
    """
    Build complete prompt for Merchant/Seller agent
    """
    base_prompt = get_legal_agent_base_prompt("merchant")
    
    evidence_context = f"""
================================================================================
EVIDENCE CONTEXT FOR MERCHANT DEFENSE
================================================================================

{format_dispute_context(bundle)}

{format_timeline(bundle, max_events=40)}

{format_system_logs(bundle, max_logs=40)}

{format_transactions(bundle)}

{format_hash_cross_reference(bundle)}

{format_customer_history(bundle)}

================================================================================
MERCHANT DEFENSE FRAMEWORK
================================================================================

As a merchant representative, defend your service delivery and payment rights.

1. SERVICE DELIVERY PROOF: Did you fulfill the order?
   - Order status progression (created → confirmed → prepared → delivered)
   - Timestamp alignment with customer complaint
   - Any fulfillment issues documented?
   - Supporting photos, tracking, or system confirmations

2. PAYMENT RIGHTS: Were you correctly compensated?
   - Transaction settlement status (confirmed vs pending vs failed)
   - Payment amount received vs claimed
   - Any chargebacks, refunds, or deductions applied
   - Reference transaction ledger hashes

3. CUSTOMER RESPONSIBILITY: Is the complaint legitimate?
   - Customer's order history: repeat complaints?
   - Any policy violations or misuse?
   - Communication records: did customer notify you before disputing?
   - Pattern analysis: isolated complaint or systemic issue?

4. DISPUTE LEGITIMACY: Should this dispute be honored?
   - Is the complaint within your service window?
   - Does evidence contradict customer's claim?
   - Similar disputes with this customer: history?
   - Fraud risk assessment

Citation Requirements:
- Cite order status logs: "Order confirmed (system_logs row: log-XXX, json_path: payload.status)"
- Cite payment records: "Payment settled (transactions row: txn-XXX, json_path: ledger_data.merchant_status)"
- Cite customer history if available: patterns of disputes
- Use specific timestamps (UTC) to establish timeline

Evidence structure:
{{
  "supabase": {{
    "table": "system_logs",  // or "transactions"
    "row_id": "log-123",
    "json_path": "payload.order_status"
  }},
  "transaction_id": "txn-456",
  "hash": "0xabcd...",
  "details": "Order marked as delivered... (why this proves fulfillment)"
}}

================================================================================
NOW PROVIDE YOUR DEFENSE
================================================================================
"""
    
    return base_prompt + evidence_context


# ============================================================================
# GENERIC PROMPT BUILDER
# ============================================================================

def build_prompt(bundle: EvidenceBundle, agent_type: str) -> Optional[str]:
    """
    Route to appropriate prompt builder based on agent type
    """
    if agent_type == "customerLawyer":
        return build_customer_lawyer_prompt(bundle)
    elif agent_type == "companyLawyer":
        return build_company_lawyer_prompt(bundle)
    elif agent_type == "judge":
        return build_judge_prompt(bundle)
    elif agent_type == "independentLawyer":
        return build_independent_lawyer_prompt(bundle)
    elif agent_type == "merchant":
        return build_merchant_prompt(bundle)
    else:
        print(f"Unknown agent type: {agent_type}")
        return None


# ============================================================================
# CONTEXT STATISTICS (for debugging)
# ============================================================================

def get_context_stats(bundle: EvidenceBundle) -> dict:
    """
    Get statistics about evidence context size
    """
    dispute = bundle["dispute_record"]["data"]
    
    return {
        "dispute_id": bundle["dispute_id"],
        "dispute_amount": dispute.get("amount"),
        "dispute_status": dispute.get("status"),
        "system_logs_count": len(bundle["system_logs"]),
        "transactions_count": len(bundle["transactions"]),
        "timeline_events": len(bundle["timeline"]),
        "unique_hashes": len(bundle["hash_cross_ref"]),
        "customer_history_count": len(bundle["customer_history"]),
        "estimated_prompt_tokens": (
            len(bundle["system_logs"]) * 150 +  # ~150 tokens per log
            len(bundle["transactions"]) * 200 +  # ~200 tokens per transaction
            len(bundle["timeline"]) * 50 +  # ~50 tokens per timeline event
            500  # Base prompt and formatting
        )
    }
