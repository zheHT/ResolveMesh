"""
N8n Webhook Integration Configuration for ResolveMesh

Handles incoming dispute data from n8n and forwards to agent analysis
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class N8nComplaintPayload(BaseModel):
    """Payload structure received from n8n webhook (user complaint)"""
    email: str
    amount: float
    order_id: str
    platform: str  # GrabFood, Banking, Ecommerce, Payments
    issue_type: str  # e.g., "Product Damage", "Double Charge", "Quality Issue"
    raw_complaint_text: str
    evidence_url: Optional[str] = None
    account_id: Optional[str] = None
    timestamp: Optional[str] = None


class N8nWebhookConfig:
    """Configuration for n8n incoming webhooks"""
    
    # N8n Webhook URL (where n8n listens for incoming complaints)
    N8N_INCOMING_WEBHOOK = "https://unemployed.app.n8n.cloud/webhook-test/userComplaint"
    
    # Expected webhook payload format documentation
    WEBHOOK_PAYLOAD_SCHEMA = {
        "email": "Customer email address",
        "amount": "Dispute amount in local currency",
        "order_id": "Platform-specific order ID",
        "platform": "One of: GrabFood, Banking, Ecommerce, Payments",
        "issue_type": "Description of dispute type",
        "raw_complaint_text": "Full complaint text from customer",
        "evidence_url": "Optional URL to attached evidence (photo/document)",
        "account_id": "Optional customer account ID",
        "timestamp": "ISO timestamp when complaint was submitted"
    }
    
    # Platform mappings (from data provided)
    PLATFORM_MAPPING = {
        "GrabFood": {
            "table": "disputes",
            "default_fields": ["order_id", "platform", "amount", "issue_type"]
        },
        "Banking": {
            "table": "disputes",
            "default_fields": ["transaction_id", "platform", "amount"]
        },
        "Ecommerce": {
            "table": "disputes",
            "default_fields": ["order_id", "platform", "amount"]
        },
        "Payments": {
            "table": "disputes",
            "default_fields": ["transaction_id", "platform", "amount"]
        }
    }


class N8nToBackendFlow:
    """Flow: N8n receives complaint → Creates dispute in Supabase → Triggers agent analysis"""
    
    FLOW_STEPS = [
        {
            "step": 1,
            "name": "Receive Customer Complaint",
            "source": "ComplaintUI or External Portal",
            "target": "N8n Webhook",
            "endpoint": "https://unemployed.app.n8n.cloud/webhook-test/userComplaint"
        },
        {
            "step": 2,
            "name": "Redact PII & Normalize",
            "source": "N8n HTTP Node",
            "action": "Call POST /api/disputes (create dispute)",
            "target": "Backend /api/disputes endpoint"
        },
        {
            "step": 3,
            "name": "Create Dispute Record",
            "source": "Backend",
            "action": "Insert into disputes table with guardian redaction",
            "target": "Supabase disputes table"
        },
        {
            "step": 4,
            "name": "Trigger Agent Analysis",
            "source": "Backend (optional: via system_logs trigger)",
            "action": "POST /api/agents/analyze",
            "target": "Legal agent processors"
        },
        {
            "step": 5,
            "name": "Store Agent Results",
            "source": "Backend",
            "action": "Update disputes.agent_reports with analysis results",
            "target": "Supabase disputes table"
        },
        {
            "step": 6,
            "name": "Generate Verdict PDF",
            "source": "Backend",
            "action": "POST /generate-pdf (optional n8n call)",
            "target": "Supabase Storage"
        }
    ]


# ============================================================================
# N8N HTTP NODE CONFIGURATION SNIPPETS
# ============================================================================

N8N_HTTP_NODE_CREATE_DISPUTE = {
    "name": "HTTP Request - Create Dispute",
    "method": "POST",
    "url": "http://localhost:8000/api/disputes",  # or deployed backend URL
    "body": {
        "customer_email": "{{ $json.email }}",
        "platform": "{{ $json.platform }}",
        "amount": "{{ $json.amount }}",
        "order_id": "{{ $json.order_id }}",
        "issue_type": "{{ $json.issue_type }}",
        "raw_text": "{{ $json.raw_complaint_text }}",
        "evidence_url": "{{ $json.evidence_url }}",
        "account_id": "{{ $json.account_id }}"
    },
    "headers": {
        "Content-Type": "application/json"
    }
}

N8N_HTTP_NODE_TRIGGER_ANALYSIS = {
    "name": "HTTP Request - Trigger Agent Analysis",
    "method": "POST",
    "url": "http://localhost:8000/api/agents/analyze",  # or deployed backend URL
    "body": {
        "dispute_id": "{{ $json.id }}",  # from previous HTTP response
        "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer", "merchant"]
    },
    "headers": {
        "Content-Type": "application/json"
    }
}

N8N_HTTP_NODE_GENERATE_PDF = {
    "name": "HTTP Request - Generate Verdict PDF",
    "method": "POST",
    "url": "http://localhost:8000/generate-pdf",  # or deployed backend URL
    "body": {
        "dispute_id": "{{ $json.dispute_id }}",
        "template": "verdict",  # or 'police', 'internal'
        "summary": "{{ $json.investigation_summary }}"
    },
    "headers": {
        "Content-Type": "application/json"
    }
}


# ============================================================================
# HELPER FUNCTIONS FOR N8N INTEGRATION
# ============================================================================

def get_n8n_webhook_url() -> str:
    """Get N8n webhook URL from config or environment"""
    return os.getenv("N8N_WEBHOOK_URL", N8nWebhookConfig.N8N_INCOMING_WEBHOOK)


def format_complaint_for_dispute(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert N8n complaint payload to dispute format"""
    return {
        "customer_email": payload.get("email"),
        "platform": payload.get("platform"),
        "amount": payload.get("amount"),
        "order_id": payload.get("order_id"),
        "issue_type": payload.get("issue_type"),
        "raw_text": payload.get("raw_complaint_text"),
        "evidence_url": payload.get("evidence_url"),
        "account_id": payload.get("account_id", "UNKNOWN"),
        "api_key": "INTERNAL_PORTAL"  # Mark as internal/n8n origin
    }


if __name__ == "__main__":
    print("N8n Webhook Configuration")
    print("=" * 60)
    print(f"Incoming Webhook: {N8nWebhookConfig.N8N_INCOMING_WEBHOOK}")
    print("\nExpected Payload Schema:")
    for key, desc in N8nWebhookConfig.WEBHOOK_PAYLOAD_SCHEMA.items():
        print(f"  {key}: {desc}")
    print("\nFlow Steps:")
    for step in N8nToBackendFlow.FLOW_STEPS:
        print(f"  {step['step']}. {step['name']}")
