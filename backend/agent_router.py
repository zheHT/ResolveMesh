"""
agent_router.py

Backend helper for routing disputes to the new legal agent system.
Bridges the TypeScript agent definitions with Python backend logic.

Maps legal agent types to Z.ai prompts and metadata.
"""

from typing import TypedDict, Literal
from enum import Enum

# Agent type definitions
AgentSystem = Literal["operational", "legal"]
OperationalAgent = Literal["negotiator", "advocate", "auditor", "summarizer"]
LegalAgent = Literal["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
AgentType = OperationalAgent | LegalAgent

# Platform types
PlatformName = Literal["grabfood", "banking", "ecommerce", "payments"]


class AgentMetadata(TypedDict):
    """Metadata for an agent"""
    system: AgentSystem
    agent_type: AgentType
    display_name: str
    description: str
    role: str


# Operational agents metadata
OPERATIONAL_AGENTS: dict[OperationalAgent, AgentMetadata] = {
    "negotiator": {
        "system": "operational",
        "agent_type": "negotiator",
        "display_name": "Negotiator",
        "description": "Hash reconciliation specialist",
        "role": "Transaction validator",
    },
    "advocate": {
        "system": "operational",
        "agent_type": "advocate",
        "display_name": "Advocate",
        "description": "Staff rationale validator",
        "role": "Policy compliance checker",
    },
    "auditor": {
        "system": "operational",
        "agent_type": "auditor",
        "display_name": "Auditor",
        "description": "Collusion/anomaly monitor",
        "role": "Fraud detector",
    },
    "summarizer": {
        "system": "operational",
        "agent_type": "summarizer",
        "display_name": "Summarizer",
        "description": "Staff dashboard TL;DR generator",
        "role": "Summary writer",
    },
}

# Legal agents metadata
LEGAL_AGENTS: dict[LegalAgent, AgentMetadata] = {
    "customerLawyer": {
        "system": "legal",
        "agent_type": "customerLawyer",
        "display_name": "Customer Lawyer",
        "description": "Advocates for customer's strongest position",
        "role": "Customer's legal representative",
    },
    "companyLawyer": {
        "system": "legal",
        "agent_type": "companyLawyer",
        "display_name": "Company Lawyer",
        "description": "Advocates for company's strongest defense",
        "role": "Company's legal representative",
    },
    "judge": {
        "system": "legal",
        "agent_type": "judge",
        "display_name": "Judge",
        "description": "Neutral arbiter of dispute",
        "role": "Neutral evaluator",
    },
    "independentLawyer": {
        "system": "legal",
        "agent_type": "independentLawyer",
        "display_name": "Independent Lawyer",
        "description": "Objective legal advisor",
        "role": "Legal advisor",
    },
}

# Platform party definitions
PLATFORM_PARTIES: dict[PlatformName, dict] = {
    "grabfood": {
        "platform": "GrabFood",
        "description": "Food delivery disputes",
        "parties": [
            {"name": "Customer", "type": "customer", "role": "Complainant"},
            {"name": "GrabFood", "type": "platform", "role": "Platform Operator"},
            {"name": "Restaurant", "type": "merchant", "role": "Service Provider"},
        ],
    },
    "banking": {
        "platform": "Banking",
        "description": "Financial transaction disputes",
        "parties": [
            {"name": "Customer", "type": "customer", "role": "Account Holder"},
            {"name": "Bank", "type": "bank", "role": "Payment Processor"},
            {"name": "Merchant", "type": "merchant", "role": "Transaction Recipient"},
        ],
    },
    "ecommerce": {
        "platform": "E-Commerce",
        "description": "Online retail disputes",
        "parties": [
            {"name": "Customer", "type": "customer", "role": "Buyer"},
            {"name": "Platform", "type": "platform", "role": "Marketplace Operator"},
            {"name": "Seller", "type": "merchant", "role": "Product Provider"},
        ],
    },
    "payments": {
        "platform": "Payments",
        "description": "Generic payment disputes",
        "parties": [
            {"name": "Customer", "type": "customer", "role": "Payer"},
            {"name": "Company", "type": "company", "role": "Service Provider"},
        ],
    },
}


def get_agent_metadata(agent_type: AgentType) -> AgentMetadata | None:
    """Get metadata for an agent"""
    if agent_type in OPERATIONAL_AGENTS:
        return OPERATIONAL_AGENTS[agent_type]  # type: ignore
    elif agent_type in LEGAL_AGENTS:
        return LEGAL_AGENTS[agent_type]  # type: ignore
    return None


def get_platform_parties(platform: str) -> dict | None:
    """Get parties involved in a dispute for a given platform"""
    normalized = platform.lower().replace(" ", "")
    for key, config in PLATFORM_PARTIES.items():
        if key == normalized or config["platform"].lower() == platform.lower():
            return config
    return None


def route_dispute_to_agents(
    platform: str, issue_type: str
) -> dict:
    """
    Route a dispute to appropriate agents based on platform.
    
    Returns:
        {
            "system": "legal" | "operational",
            "agents": list of agent types to invoke,
            "platform_context": platform parties and description
        }
    """
    platform_parties = get_platform_parties(platform)
    
    # If we have a known platform with multiple parties, use legal agents
    if platform_parties and len(platform_parties.get("parties", [])) > 1:
        return {
            "system": "legal",
            "agents": ["customerLawyer", "companyLawyer", "judge", "independentLawyer"],
            "platform_context": platform_parties,
        }
    
    # Default to operational agents
    return {
        "system": "operational",
        "agents": ["negotiator", "advocate", "auditor", "summarizer"],
        "platform_context": None,
    }


def get_agent_prompt_instruction(agent_type: LegalAgent, platform: str) -> str:
    """Get specific instruction for a legal agent based on platform"""
    platform_parties = get_platform_parties(platform)
    
    if not platform_parties:
        return ""
    
    instructions = {
        "customerLawyer": f"Build the strongest case for the customer's position based on evidence. Platform: {platform_parties['platform']}, parties: {', '.join(p['name'] for p in platform_parties['parties'])}",
        "companyLawyer": f"Build the strongest defense for the company's position based on evidence. Platform: {platform_parties['platform']}, parties: {', '.join(p['name'] for p in platform_parties['parties'])}",
        "judge": f"Neutrally evaluate both positions based on evidence. Platform: {platform_parties['platform']}, key parties: {', '.join(p['name'] for p in platform_parties['parties'])}",
        "independentLawyer": f"Provide objective legal analysis and settlement recommendation. Platform: {platform_parties['platform']}, parties: {', '.join(p['name'] for p in platform_parties['parties'])}",
    }
    
    return instructions.get(agent_type, "")  # type: ignore


# Export for use in FastAPI routes
__all__ = [
    "AgentMetadata",
    "AgentSystem",
    "OperationalAgent",
    "LegalAgent",
    "AgentType",
    "PlatformName",
    "OPERATIONAL_AGENTS",
    "LEGAL_AGENTS",
    "PLATFORM_PARTIES",
    "get_agent_metadata",
    "get_platform_parties",
    "route_dispute_to_agents",
    "get_agent_prompt_instruction",
]
