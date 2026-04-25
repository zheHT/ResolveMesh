"""
BACKEND INTEGRATION GUIDE: Legal Agent System

This guide shows how to integrate the new legal agent system into the backend.
The agent_router.py module provides utilities for routing disputes to appropriate agents.

File: agent_router.py
Purpose: Map disputes to legal agents based on platform context
"""

# ============================================================================
# EXAMPLE 1: Route a dispute to appropriate agents
# ============================================================================

from agent_router import route_dispute_to_agents, get_agent_metadata

# When a dispute comes in
platform = "GrabFood"
issue_type = "Food spoilt"

# Route it automatically
routing = route_dispute_to_agents(platform, issue_type)

# Output:
# {
#     "system": "legal",
#     "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"],
#     "platform_context": {
#         "platform": "GrabFood",
#         "description": "Food delivery disputes",
#         "parties": [
#             {"name": "Customer", "type": "customer", "role": "Complainant"},
#             {"name": "GrabFood", "type": "platform", "role": "Platform Operator"},
#             {"name": "Restaurant", "type": "merchant", "role": "Service Provider"}
#         ]
#     }
# }

# Get metadata for each agent
for agent_type in routing["agents"]:
    metadata = get_agent_metadata(agent_type)
    print(f"{metadata['display_name']}: {metadata['description']}")
    # Output:
    # Customer Lawyer: Advocates for customer's strongest position
    # Company Lawyer: Advocates for company's strongest defense
    # Judge: Neutral arbiter of dispute
    # Independent Lawyer: Objective legal advisor


# ============================================================================
# EXAMPLE 2: Route prompts to Z.ai using the new agent system
# ============================================================================

from zai_client import chat_once
from agent_router import route_dispute_to_agents, get_agent_prompt_instruction

# Define dispute context
dispute_id = "disp-123"
platform = "GrabFood"
issue_type = "Food spoilt"
customer_claim = "Burger bread had green spots when delivered"
merchant_response = "All items checked before dispatch"

# Route to agents
routing = route_dispute_to_agents(platform, issue_type)

# Invoke each legal agent
results = {}

for agent_type in routing["agents"]:
    # Get specific instruction for this agent and platform
    agent_instruction = get_agent_prompt_instruction(agent_type, platform)
    
    # Build complete prompt (you would combine with the Z.ai legal agent prompt)
    prompt = f"""{agent_instruction}

Dispute ID: {dispute_id}
Issue: {issue_type}
Customer Claim: {customer_claim}
Merchant Response: {merchant_response}

Parties Involved: {', '.join(p['name'] for p in routing['platform_context']['parties'])}

Provide your analysis in JSON format matching the investigation summary schema.
"""
    
    # Call Z.ai with the prompt
    response = chat_once(prompt)
    results[agent_type] = response


# ============================================================================
# EXAMPLE 3: Store agent results with routing metadata
# ============================================================================

from database import supabase
from datetime import datetime, timezone
import json

# After getting results from all agents
dispute_id = "disp-123"
routing = route_dispute_to_agents(platform, issue_type)

# Update the disputes record with agent routing and results
update_payload = {
    "agent_routing": {
        "system": routing["system"],
        "agents_invoked": routing["agents"],
        "platform_context": routing["platform_context"],
        "routed_at": datetime.now(timezone.utc).isoformat(),
    },
    "agent_reports": {
        "investigation_summary": results,  # Results from all agents
        "summary_generated_at": datetime.now(timezone.utc).isoformat(),
    }
}

response = supabase.table("disputes").update(update_payload).eq("id", dispute_id).execute()


# ============================================================================
# EXAMPLE 4: Get platform-specific context for display
# ============================================================================

from agent_router import get_platform_parties

platform = "Banking"
parties = get_platform_parties(platform)

# Output:
# {
#     "platform": "Banking",
#     "description": "Financial transaction disputes",
#     "parties": [
#         {"name": "Customer", "type": "customer", "role": "Account Holder"},
#         {"name": "Bank", "type": "bank", "role": "Payment Processor"},
#         {"name": "Merchant", "type": "merchant", "role": "Transaction Recipient"}
#     ]
# }

# Use for logging or UI display
for party in parties["parties"]:
    print(f"{party['name']} ({party['role']})")


# ============================================================================
# EXAMPLE 5: Integration with FastAPI route
# ============================================================================

from fastapi import HTTPException
from pydantic import BaseModel
import json

class DisputeAnalysisRequest(BaseModel):
    dispute_id: str
    platform: str
    issue_type: str
    customer_description: str

@app.post("/analyze/legal")
async def analyze_dispute_with_legal_agents(request: DisputeAnalysisRequest):
    """
    New endpoint that routes disputes to legal agents
    """
    try:
        # Route the dispute
        routing = route_dispute_to_agents(request.platform, request.issue_type)
        
        # Prepare agent invocations
        agent_results = {}
        
        for agent_type in routing["agents"]:
            agent_instruction = get_agent_prompt_instruction(agent_type, request.platform)
            
            prompt = f"""{agent_instruction}

Dispute ID: {request.dispute_id}
Issue Type: {request.issue_type}
Customer Description: {request.customer_description}

Provide analysis in JSON format with:
- dispute_id
- agent (your agent type)
- confidence_score (0-100)
- reasoning
- evidence array
- summary_tldr (<= 30 words)
- created_at (ISO 8601)
"""
            
            # Call Z.ai
            result = chat_once(prompt)
            
            # Parse and validate
            try:
                parsed = json.loads(result)
                agent_results[agent_type] = parsed
            except json.JSONDecodeError:
                agent_results[agent_type] = {
                    "error": "Failed to parse agent response",
                    "raw_response": result
                }
        
        # Store results
        supabase.table("disputes").update({
            "agent_routing": {
                "system": routing["system"],
                "agents_invoked": routing["agents"],
                "platform_context": routing["platform_context"],
            },
            "agent_reports": {
                "investigation_summary": agent_results,
            }
        }).eq("id", request.dispute_id).execute()
        
        return {
            "status": "success",
            "dispute_id": request.dispute_id,
            "routing": routing,
            "agent_results": agent_results,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Integration Checklist
# ============================================================================
#
# [ ] Import agent_router in main.py
# [ ] Create new /analyze/legal endpoint
# [ ] Update dispute routing logic to use route_dispute_to_agents()
# [ ] Store routing metadata in Supabase disputes.agent_routing
# [ ] Update investigation summary schema to accept legal agent results
# [ ] Create UI component to display legal agent perspectives
# [ ] Add option to select agent system (operational vs legal) in frontend
# [ ] Update PDF generation to include agent perspective information
# [ ] Add logging for agent routing decisions
# [ ] Document agent result schemas for Supabase
#
