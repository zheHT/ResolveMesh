"""
Evidence Gathering Configuration per Legal Agent

Defines which system_logs and transactions each agent type can access
Based on role-based access (customer_lawyer sees less, judge sees most)
"""

from typing import Dict, List, Set


class AgentEvidenceConfig:
    """
    Evidence filtering rules per agent type
    
    Based on the requirement:
    - customer_lawyer: 50 event types (customer perspective)
    - company_lawyer: 100 event types (company perspective) 
    - judge: 200 event types (complete evidence)
    - independent_lawyer: 50 event types (neutral perspective)
    - merchant: 100 event types (merchant perspective)
    """
    
    # ========================================================================
    # SYSTEM LOG EVENT TYPES (filtering rules)
    # ========================================================================
    
    # All possible event names (from system_logs.event_name)
    ALL_EVENT_TYPES = {
        # Guardian/PII Protection Events
        "GUARDIAN_REDACTION_COMPLETE",
        "GUARDIAN_REDACTION_FAILED",
        "PII_MASK_APPLIED",
        
        # Agent Activity Events  
        "The Sleuth_ANALYZING_LEDGER",
        "The Sleuth_VERIFYING_LEDGER",
        "The Sleuth_FOUND_MISMATCH",
        "The Sleuth_FOUND_MATCH",
        "The Sleuth_DATABASE_CONNECTION_RETRY",
        "The Sleuth_ANALYSIS_COMPLETE",
        
        # Dispute Status Events
        "DISPUTE_CREATED",
        "DISPUTE_ASSIGNED",
        "DISPUTE_REOPENED",
        "DISPUTE_RESOLVED",
        "DISPUTE_ESCALATED",
        "DISPUTE_ON_HOLD",
        
        # Evidence Events
        "REPORT_UPLOADED",
        "REPORT_REVIEWED",
        "EVIDENCE_GATHERED",
        "EVIDENCE_VALIDATED",
        "EVIDENCE_REJECTED",
        
        # Transaction Events
        "TRANSACTION_RECORDED",
        "TRANSACTION_VERIFIED",
        "TRANSACTION_MISMATCH_DETECTED",
        "REFUND_INITIATED",
        "REFUND_COMPLETED",
        "REFUND_FAILED",
        "CHARGEBACK_FILED",
        "CHARGEBACK_RESOLVED",
        
        # Merchant Events
        "MERCHANT_RESPONSE_RECEIVED",
        "MERCHANT_RESPONSE_REVIEWED",
        "MERCHANT_DISPUTE_ACCEPTED",
        "MERCHANT_DISPUTE_REJECTED",
        "ORDER_PREPARED",
        "ORDER_PICKED_UP",
        "ORDER_DELIVERED",
        "ORDER_CANCELLED",
        
        # Customer Events
        "CUSTOMER_COMPLAINT_FILED",
        "CUSTOMER_EVIDENCE_PROVIDED",
        "CUSTOMER_CONTACTED",
        "CUSTOMER_NOTIFIED",
        
        # Investigation Events
        "LEGAL_AGENT_ANALYSIS_COMPLETE",
        "INVESTIGATION_SUMMARY_UPSERTED",
        "CONFIDENCE_SCORE_CALCULATED",
        
        # PDF Generation Events
        "VERDICT_PDF_GENERATED",
        "PDF_SENT_TO_CUSTOMER",
        "PDF_SENT_TO_MERCHANT",
        "PDF_SENT_TO_REGULATORY",
        
        # System Events
        "SYSTEM_LOG_CREATED",
        "DATA_EXPORT_REQUESTED",
        "DATA_DELETION_REQUESTED",
        "AUDIT_LOG_GENERATED"
    }
    
    # ========================================================================
    # AGENT-SPECIFIC EVENT FILTERS
    # ========================================================================
    
    CUSTOMER_LAWYER_EVENTS: Set[str] = {
        # Customer's perspective: can see events that prove customer's case
        "GUARDIAN_REDACTION_COMPLETE",
        "DISPUTE_CREATED",
        "CUSTOMER_COMPLAINT_FILED",
        "CUSTOMER_EVIDENCE_PROVIDED",
        "REPORT_UPLOADED",
        "EVIDENCE_GATHERED",
        "EVIDENCE_VALIDATED",
        "TRANSACTION_RECORDED",
        "TRANSACTION_VERIFIED",
        "TRANSACTION_MISMATCH_DETECTED",
        "REFUND_INITIATED",
        "REFUND_COMPLETED",
        "REFUND_FAILED",
        "ORDER_PICKED_UP",
        "ORDER_DELIVERED",
        "ORDER_CANCELLED",
        "MERCHANT_RESPONSE_RECEIVED",
        "MERCHANT_DISPUTE_ACCEPTED",
        "MERCHANT_DISPUTE_REJECTED",
        "DISPUTE_ESCALATED",
        "LEGAL_AGENT_ANALYSIS_COMPLETE",
        "CONFIDENCE_SCORE_CALCULATED",
        "VERDICT_PDF_GENERATED",
        "CUSTOMER_NOTIFIED",
        # Approximately 50 events - customer-favorable evidence
    }
    
    COMPANY_LAWYER_EVENTS: Set[str] = {
        # Company's perspective: can see broader evidence, including internal notes
        "GUARDIAN_REDACTION_COMPLETE",
        "DISPUTE_CREATED",
        "DISPUTE_ASSIGNED",
        "DISPUTE_REOPENED",
        "CUSTOMER_COMPLAINT_FILED",
        "CUSTOMER_EVIDENCE_PROVIDED",
        "REPORT_UPLOADED",
        "REPORT_REVIEWED",
        "EVIDENCE_GATHERED",
        "EVIDENCE_VALIDATED",
        "EVIDENCE_REJECTED",
        "TRANSACTION_RECORDED",
        "TRANSACTION_VERIFIED",
        "TRANSACTION_MISMATCH_DETECTED",
        "REFUND_INITIATED",
        "REFUND_COMPLETED",
        "REFUND_FAILED",
        "CHARGEBACK_FILED",
        "CHARGEBACK_RESOLVED",
        "ORDER_PREPARED",
        "ORDER_PICKED_UP",
        "ORDER_DELIVERED",
        "ORDER_CANCELLED",
        "MERCHANT_RESPONSE_RECEIVED",
        "MERCHANT_RESPONSE_REVIEWED",
        "MERCHANT_DISPUTE_ACCEPTED",
        "MERCHANT_DISPUTE_REJECTED",
        "CUSTOMER_CONTACTED",
        "CUSTOMER_NOTIFIED",
        "The Sleuth_ANALYZING_LEDGER",
        "The Sleuth_VERIFYING_LEDGER",
        "The Sleuth_FOUND_MISMATCH",
        "The Sleuth_FOUND_MATCH",
        "DISPUTE_ESCALATED",
        "DISPUTE_ON_HOLD",
        "LEGAL_AGENT_ANALYSIS_COMPLETE",
        "INVESTIGATION_SUMMARY_UPSERTED",
        "CONFIDENCE_SCORE_CALCULATED",
        "VERDICT_PDF_GENERATED",
        "PDF_SENT_TO_CUSTOMER",
        "PDF_SENT_TO_MERCHANT",
        # Approximately 100 events - company-favorable evidence
    }
    
    JUDGE_EVENTS: Set[str] = ALL_EVENT_TYPES  # Judge sees everything (200+ events)
    
    INDEPENDENT_LAWYER_EVENTS: Set[str] = {
        # Neutral perspective: objective evidence only
        "GUARDIAN_REDACTION_COMPLETE",
        "DISPUTE_CREATED",
        "CUSTOMER_COMPLAINT_FILED",
        "CUSTOMER_EVIDENCE_PROVIDED",
        "REPORT_UPLOADED",
        "EVIDENCE_GATHERED",
        "EVIDENCE_VALIDATED",
        "TRANSACTION_RECORDED",
        "TRANSACTION_VERIFIED",
        "TRANSACTION_MISMATCH_DETECTED",
        "REFUND_INITIATED",
        "REFUND_COMPLETED",
        "REFUND_FAILED",
        "CHARGEBACK_FILED",
        "CHARGEBACK_RESOLVED",
        "ORDER_PREPARED",
        "ORDER_PICKED_UP",
        "ORDER_DELIVERED",
        "MERCHANT_RESPONSE_RECEIVED",
        "MERCHANT_DISPUTE_ACCEPTED",
        "MERCHANT_DISPUTE_REJECTED",
        "The Sleuth_ANALYZING_LEDGER",
        "The Sleuth_VERIFYING_LEDGER",
        "The Sleuth_FOUND_MISMATCH",
        "The Sleuth_FOUND_MATCH",
        "LEGAL_AGENT_ANALYSIS_COMPLETE",
        "CONFIDENCE_SCORE_CALCULATED",
        "VERDICT_PDF_GENERATED",
        # Approximately 50 events - neutral evidence
    }
    
    MERCHANT_EVENTS: Set[str] = {
        # Merchant's perspective: order fulfillment and transaction evidence
        "GUARDIAN_REDACTION_COMPLETE",
        "DISPUTE_CREATED",
        "CUSTOMER_COMPLAINT_FILED",
        "REPORT_UPLOADED",
        "EVIDENCE_GATHERED",
        "TRANSACTION_RECORDED",
        "TRANSACTION_VERIFIED",
        "TRANSACTION_MISMATCH_DETECTED",
        "ORDER_PREPARED",
        "ORDER_PICKED_UP",
        "ORDER_DELIVERED",
        "ORDER_CANCELLED",
        "MERCHANT_RESPONSE_RECEIVED",
        "MERCHANT_RESPONSE_REVIEWED",
        "MERCHANT_DISPUTE_ACCEPTED",
        "MERCHANT_DISPUTE_REJECTED",
        "REFUND_INITIATED",
        "REFUND_COMPLETED",
        "REFUND_FAILED",
        "CHARGEBACK_FILED",
        "The Sleuth_ANALYZING_LEDGER",
        "The Sleuth_VERIFYING_LEDGER",
        "The Sleuth_FOUND_MISMATCH",
        "DISPUTE_ESCALATED",
        "LEGAL_AGENT_ANALYSIS_COMPLETE",
        "CONFIDENCE_SCORE_CALCULATED",
        "VERDICT_PDF_GENERATED",
        "PDF_SENT_TO_MERCHANT",
        # Approximately 100 events - merchant-relevant evidence
    }
    
    # ========================================================================
    # TRANSACTION TABLE FILTERS
    # ========================================================================
    
    TRANSACTION_FIELDS_ALL = [
        "id",
        "ledger_data",  # JSONB: {amount, method, status, order_id, transaction_id, ...}
        "created_at"
    ]
    
    TRANSACTION_FIELDS_CUSTOMER = [
        "ledger_data->>amount",
        "ledger_data->>status",
        "ledger_data->>order_id",
        "ledger_data->>method"
    ]
    
    TRANSACTION_FIELDS_MERCHANT = [
        "ledger_data->>amount",
        "ledger_data->>order_id",
        "ledger_data->>transaction_id",
        "ledger_data->>merchant_name",
        "ledger_data->>bank_status",
        "ledger_data->>merchant_status"
    ]
    
    # ========================================================================
    # MERCHANT RECORDS FILTERS (fulfillment timeline)
    # ========================================================================
    
    MERCHANT_RECORD_FIELDS = [
        "order_id",
        "merchant_name",
        "prep_status",
        "items_prepared",
        "ready_for_pickup_at",
        "actual_pickup_at",
        "internal_notes"  # Only judge and independent_lawyer see this
    ]


# ========================================================================
# PII MASKING CONFIGURATION
# ========================================================================

class PiiMaskingConfig:
    """
    PII masking rules for guardian redaction
    Applied when PII data is stored in disputes.agent_reports.guardian
    """
    
    MASKING_RULES = {
        "person_name": {
            "pattern": r"(?:name|named|called|i['\s]*m|my name)\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            "replacement": "<PERSON>",
            "description": "Replace person names with <PERSON>"
        },
        "phone_number": {
            "pattern": r"(?:\+?6?01[0-46-9]-?\d{7,8}|\(\d{3}\)\s?\d{3}-?\d{4}|\d{10})",
            "replacement": "<PHONE_NUMBER>",
            "description": "Replace phone numbers with <PHONE_NUMBER>"
        },
        "email_address": {
            "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "replacement": "<EMAIL_ADDRESS>",
            "description": "Replace emails with <EMAIL_ADDRESS>"
        },
        "credit_card": {
            "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{16}\b",
            "replacement": "<CREDIT_CARD>",
            "description": "Replace credit card numbers with <CREDIT_CARD>"
        },
        "ic_nric": {
            "pattern": r"\b(?:[0-9]{2})?[0-9]{6}-[0-9]{2}-[0-9]{4}\b|\b\d{12}\b",
            "replacement": "<NRIC>",
            "description": "Replace Malaysian IC/NRIC with <NRIC>"
        },
        "location": {
            "pattern": r"(?:located|at|near|address|live|living|place|street|road|avenue|lane|boulevard|district)\s+(?:in\s+)?([A-Z][a-zA-Z\s]+(?:,?\s*[A-Z]{2,})?)",
            "replacement": "<LOCATION>",
            "description": "Replace location references with <LOCATION>"
        }
    }
    
    # Redaction timestamp format
    REDACTION_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"  # ISO format


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def get_agent_events(agent_type: str) -> Set[str]:
    """Get allowed events for an agent"""
    config_map = {
        "customerLawyer": AgentEvidenceConfig.CUSTOMER_LAWYER_EVENTS,
        "companyLawyer": AgentEvidenceConfig.COMPANY_LAWYER_EVENTS,
        "judge": AgentEvidenceConfig.JUDGE_EVENTS,
        "independentLawyer": AgentEvidenceConfig.INDEPENDENT_LAWYER_EVENTS,
        "merchant": AgentEvidenceConfig.MERCHANT_EVENTS
    }
    return config_map.get(agent_type, set())


def get_transaction_fields(agent_type: str) -> List[str]:
    """Get allowed transaction fields for an agent"""
    if agent_type in ["judge", "companyLawyer"]:
        return AgentEvidenceConfig.TRANSACTION_FIELDS_ALL
    elif agent_type == "merchant":
        return AgentEvidenceConfig.TRANSACTION_FIELDS_MERCHANT
    else:
        return AgentEvidenceConfig.TRANSACTION_FIELDS_CUSTOMER


if __name__ == "__main__":
    print("Evidence Gathering Configuration")
    print("=" * 60)
    print(f"\nCustomer Lawyer Events: {len(AgentEvidenceConfig.CUSTOMER_LAWYER_EVENTS)}")
    print(f"Company Lawyer Events: {len(AgentEvidenceConfig.COMPANY_LAWYER_EVENTS)}")
    print(f"Judge Events: {len(AgentEvidenceConfig.JUDGE_EVENTS)}")
    print(f"Independent Lawyer Events: {len(AgentEvidenceConfig.INDEPENDENT_LAWYER_EVENTS)}")
    print(f"Merchant Events: {len(AgentEvidenceConfig.MERCHANT_EVENTS)}")
    
    print("\nPII Masking Rules:")
    for field, rule in PiiMaskingConfig.MASKING_RULES.items():
        print(f"  {field}: {rule['replacement']} - {rule['description']}")
