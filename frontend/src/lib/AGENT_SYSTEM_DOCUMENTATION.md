// AGENT_SYSTEM_DOCUMENTATION.md
# ResolveMesh Dual Agent System

## Overview

ResolveMesh now supports **two distinct agent systems** for dispute resolution:

1. **Operational Agent System** (Legacy) - Focus on transaction reconciliation
2. **Legal Agent System** (New) - Focus on multi-party legal dispute resolution

## Operational Agents (Legacy System)

### Agents
- **Negotiator**: Hash reconciliation specialist, compares transaction hashes in Supabase logs
- **Advocate**: Staff rationale validator, checks if resolutions match logs and policies
- **Auditor**: Collusion/anomaly monitor, detects suspicious patterns
- **Summarizer**: Generates 30-word TL;DR for staff dashboard

### Use Case
Best for internal transaction validation and dispute operationalization.

### Import
```typescript
import { agentPrompts } from "@/lib/ZaiPrompts";

const negotiatorPrompt = agentPrompts.negotiator;
const advocatePrompt = agentPrompts.advocate;
```

---

## Legal Agent System (New)

### Agents
- **Customer Lawyer**: Advocates for the customer's strongest legal position
- **Company Lawyer**: Advocates for the company/merchant's strongest legal defense
- **Judge**: Neutral arbiter evaluating both sides objectively
- **Independent Lawyer**: Objective legal advisor with settlement recommendations

### Supported Platforms

#### GrabFood
**Parties**: Customer, GrabFood Platform, Restaurant/Merchant
- **Issue Types**: Food spoilt, late delivery, incorrect order, missing items
- **Customer Lawyer**: Argues food quality/delivery failure based on evidence
- **Company Lawyer**: Defends that service was delivered as promised
- **Judge**: Evaluates food condition/delivery evidence from GrabFood logs
- **Independent Lawyer**: Assesses refund viability and settlement

#### Banking
**Parties**: Customer, Bank, Merchant/Vendor, Shopping Mall (optional)
- **Issue Types**: Unauthorized charge, duplicate billing, service not received
- **Customer Lawyer**: Disputes transaction legitimacy based on ledger
- **Company Lawyer**: Confirms transaction was authorized and completed
- **Judge**: Evaluates payment evidence under banking regulations
- **Independent Lawyer**: Assesses chargeback viability and settlement

#### E-Commerce
**Parties**: Customer, Platform, Seller
- **Issue Types**: Item not as described, defective, not delivered
- **Customer Lawyer**: Item quality/delivery claims
- **Company Lawyer**: Item shipped/customer responsibility claims
- **Judge**: Evaluates product condition and delivery evidence
- **Independent Lawyer**: Refund/replacement recommendation

### Import & Usage

```typescript
import { legalAgentPrompts } from "@/lib/LegalAgentPrompts";
import { getPlatformContext, getDisputeParties } from "@/lib/PlatformPartyMapping";
import { routeDispute, routeToLegalAgents } from "@/lib/AgentRouter";

// Get prompt for Customer Lawyer
const customerLawyerPrompt = legalAgentPrompts.customerLawyer;

// Get platform context
const grabFoodContext = getPlatformContext("GrabFood");
const parties = getDisputeParties("GrabFood");
// parties = [
//   { name: "Customer", type: "customer", role: "Complainant", ... },
//   { name: "GrabFood", type: "platform", role: "Platform Operator", ... },
//   { name: "Restaurant/Merchant", type: "merchant", role: "Service Provider", ... }
// ]

// Automatically route dispute to legal agents
const disputeContext = {
  platform: "GrabFood",
  issueType: "Food spoilt",
  orderId: "GRB-FOOD-101",
  customerEmail: "customer@example.com",
  amount: 28.50,
  rawDescription: "My burger bread has green spots"
};

const assignment = routeToLegalAgents(disputeContext);
// assignment.agents = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
// assignment.platformContext = { platform: "GrabFood", parties: [...], ... }
// assignment.routing = { 
//   customerLawyer: "Customer perspective...",
//   companyLawyer: "GrabFood/Merchant perspective...",
//   judge: "Neutral evaluation...",
//   independentLawyer: "Assess claim viability..."
// }
```

---

## Agent Router (Smart Routing)

The `AgentRouter` module provides intelligent dispatch:

```typescript
import { routeDispute, getAllAvailableAgents } from "@/lib/AgentRouter";

// Automatic routing based on platform
const assignment = routeDispute(disputeContext);
// Returns legal agents for known platforms (GrabFood, Banking, etc.)
// Returns operational agents for unknown platforms

// Get all available agents
const agents = getAllAvailableAgents();
// agents.operational = ["negotiator", "advocate", "auditor", "summarizer"]
// agents.legal = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]
```

---

## JSON Output Schema (Both Systems)

Both agent systems produce JSON in the same `InvestigationSummary` schema:

```json
{
  "dispute_id": "disp-123",
  "agent": "Customer Lawyer",
  "confidence_score": 85,
  "reasoning": "Based on transaction logs, customer's claim of food quality failure is supported by delivery timestamp and order status.",
  "evidence": [
    {
      "supabase": {
        "table": "system_logs",
        "row_id": "log-456",
        "json_path": "payload.dispute_id"
      },
      "transaction_id": "txn-789",
      "hash": "abc123def456",
      "details": "Order status changed to 'delivered' at 7:30 PM, 15 minutes after customer complaint timestamp."
    }
  ],
  "summary_tldr": "Food delivery confirmed spoilt per timestamp evidence. Recommend 100% refund.",
  "created_at": "2026-04-23T10:30:00+00:00"
}
```

### Required Fields
- `dispute_id`: Unique dispute identifier
- `agent`: Agent name (e.g., "Customer Lawyer", "Negotiator")
- `confidence_score`: 0-100 numeric score
- `reasoning`: Detailed explanation of position/finding
- `evidence`: Array with ≥1 items, each citing Supabase row
- `summary_tldr`: ≤30 words
- `created_at`: ISO 8601 timestamp

### Evidence Citation Rules
Each evidence item **must** include:
- `supabase.table`: Table name (e.g., "system_logs", "transactions")
- `supabase.row_id`: Unique row identifier
- Either `transaction_id` or `hash` for cross-checking
- `details`: Human-readable explanation

---

## Migration Guide

### From Operational to Legal Agents

**Before** (Operational System):
```typescript
const prompt = agentPrompts.advocate;
// Validation-focused output
```

**After** (Legal System with Platform Context):
```typescript
import { legalAgentPrompts, getPlatformContext } from "@/lib/LegalAgentPrompts";

const prompt = legalAgentPrompts.companyLawyer;
const context = getPlatformContext("GrabFood");
// Legal perspective + multi-party context
```

### Updating Dispute Processing

**Before**:
```typescript
// Operational routing
const agents = ["negotiator", "advocate", "auditor", "summarizer"];
```

**After**:
```typescript
// Intelligent routing
import { routeDispute } from "@/lib/AgentRouter";

const assignment = routeDispute(disputeContext);
// Automatically selects legal or operational agents
// Provides platform context if available
```

---

## Adding New Platforms

To add support for a new platform, update `PlatformPartyMapping.ts`:

```typescript
export const platformContexts: Record<string, PlatformContext> = {
  // ... existing platforms ...
  
  mynewplatform: {
    platform: "My New Platform",
    description: "Description of disputes on this platform",
    parties: [
      {
        name: "Customer",
        type: "customer",
        role: "Buyer/User",
        description: "...",
      },
      {
        name: "Company",
        type: "company",
        role: "Service Provider",
        description: "...",
      },
    ],
    legalAgentRoute: {
      customerLawyer: "Customer perspective on this platform...",
      companyLawyer: "Company perspective on this platform...",
      judge: "Neutral evaluation for this platform...",
      independentLawyer: "Legal assessment for this platform...",
    },
  },
};
```

---

## Implementation Checklist

- [x] Created `LegalAgentPrompts.ts` with 4 legal agent prompts
- [x] Created `PlatformPartyMapping.ts` with platform contexts
- [x] Created `AgentRouter.ts` for intelligent dispatch
- [x] Updated `ZaiPrompts.ts` to export both systems
- [ ] Integrate with n8n workflow for agent invocation
- [ ] Add UI components to select agent system and platform
- [ ] Update backend routing in `main.py` to use AgentRouter
- [ ] Create dashboard visualization of agent perspectives
- [ ] Document evidence citation patterns per platform

---

## Files Changed/Created

| File | Type | Purpose |
|------|------|---------|
| `LegalAgentPrompts.ts` | NEW | Legal agent prompt definitions |
| `PlatformPartyMapping.ts` | NEW | Platform context and party definitions |
| `AgentRouter.ts` | NEW | Dispute routing logic |
| `ZaiPrompts.ts` | UPDATED | Added legal agent exports and documentation |

---

## Example Usage: Full Dispute Routing

```typescript
import { routeDispute } from "@/lib/AgentRouter";
import { ingestInvestigationSummary } from "@/lib/investigationSummary.ingest";

// 1. Define dispute context
const disputeContext = {
  platform: "GrabFood",
  issueType: "Food spoilt",
  orderId: "GRB-FOOD-101",
  customerEmail: "customer@example.com",
  amount: 28.50,
  rawDescription: "Burger bread had green spots",
};

// 2. Route to appropriate agents
const assignment = routeDispute(disputeContext);
// Result: Legal agents routed for GrabFood + platform context provided

// 3. Send prompts to Z.ai for each agent
const results = await Promise.all([
  callZai(assignment.prompts.customerLawyer),
  callZai(assignment.prompts.companyLawyer),
  callZai(assignment.prompts.judge),
  callZai(assignment.prompts.independentLawyer),
]);

// 4. Validate and ingest results
const ingestionResults = results.map(r => ingestInvestigationSummary(r));

// 5. Store in Supabase disputes table
await storeInvestigationSummaries(ingestionResults);
```

---

## Questions?

Refer to:
- Agent prompts: `LegalAgentPrompts.ts`, `ZaiPrompts.ts`
- Platform definitions: `PlatformPartyMapping.ts`
- Routing logic: `AgentRouter.ts`
- Schema validation: `investigationSummary.schema.ts`
