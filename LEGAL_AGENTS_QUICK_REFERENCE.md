## Quick Reference: Legal Agents for Different Platforms

### 📱 GrabFood Disputes
**Parties Involved**: Customer, GrabFood Platform, Restaurant/Merchant

#### Agent Roles
| Agent | Perspective | Focus |
|-------|-------------|-------|
| **Customer Lawyer** | 👤 Customer | Build case for refund based on food quality/delivery issues |
| **Company Lawyer** | 🏢 GrabFood/Restaurant | Defend service delivery, show no breach |
| **Judge** | ⚖️ Neutral | Evaluate food condition evidence, apply platform policy |
| **Independent Lawyer** | 📋 Advisor | Recommend settlement: full/partial refund or rejection |

#### Example Case: "Burger arrived with mold"
- **Customer Lawyer**: "Photo evidence + delivery timestamp shows food deterioration. Demand full refund."
- **Company Lawyer**: "Order was prepared properly. Photo could be post-delivery. Partial refund acceptable."
- **Judge**: "Evidence supports customer. Food condition at delivery = GrabFood/restaurant liability."
- **Independent Lawyer**: "Issue 75% refund (food cost minus portion consumed evidence)."

---

### 🏦 Banking Disputes
**Parties Involved**: Customer, Bank, Merchant/Vendor, Shopping Mall (optional)

#### Agent Roles
| Agent | Perspective | Focus |
|-------|-------------|-------|
| **Customer Lawyer** | 👤 Customer | Challenge transaction legitimacy, unauthorized charge, etc. |
| **Company Lawyer** | 🏢 Bank/Merchant | Defend transaction, show authorization + settlement |
| **Judge** | ⚖️ Neutral | Evaluate ledger records, apply chargeback rules |
| **Independent Lawyer** | 📋 Advisor | Recommend chargeback outcome + regulatory compliance |

#### Example Case: "Double charged for online purchase"
- **Customer Lawyer**: "Transaction ledger shows duplicate auth on same card 2 minutes apart. Unauthorized duplicate charge."
- **Company Lawyer**: "Both charges show different authorization codes. Customer triggered retry. No system error."
- **Judge**: "Ledger shows sequential settlements. Customer error (impatience) not system error."
- **Independent Lawyer**: "Reject chargeback. Issue apology + $5 credit for inconvenience."

---

### 🎁 E-Commerce Disputes
**Parties Involved**: Customer, Platform, Seller

#### Agent Roles
| Agent | Perspective | Focus |
|-------|-------------|-------|
| **Customer Lawyer** | 👤 Buyer | Item condition/delivery failure |
| **Company Lawyer** | 🏢 Seller/Platform | Item shipped properly, buyer claims invalid |
| **Judge** | ⚖️ Neutral | Evaluate item condition proof, delivery evidence |
| **Independent Lawyer** | 📋 Advisor | Refund/replacement/rejection decision |

#### Example Case: "Phone arrived damaged"
- **Customer Lawyer**: "Photo shows broken screen. Packaging damage evident. Demand full refund."
- **Company Lawyer**: "Item shipped in approved packaging. Buyer signature confirms undamaged. Shipping damage claim needs carrier."
- **Judge**: "Photo evidence supports damage. Delivery signature shows accepted condition."
- **Independent Lawyer**: "Issue full refund OR replacement at customer choice."

---

### 🏧 Generic Payments
**Parties Involved**: Customer, Company, Payment Processor

#### Agent Roles
| Agent | Perspective | Focus |
|-------|-------------|-------|
| **Customer Lawyer** | 👤 Customer | Service not delivered, payment unjustified |
| **Company Lawyer** | 🏢 Company | Service delivered, payment justified |
| **Judge** | ⚖️ Neutral | Verify service delivery evidence |
| **Independent Lawyer** | 📋 Advisor | Recommend refund/reject |

---

## Implementation Map

```typescript
// Frontend: Automatic agent routing
import { routeDispute } from "@/lib/agents-index";

const disputeContext = {
  platform: "GrabFood",  // or "Banking", "E-Commerce", etc.
  issueType: "Food spoilt",
  orderId: "GRB-FOOD-101",
  customerEmail: "customer@email.com",
  amount: 28.50,
  rawDescription: "Burger bread has green spots"
};

const assignment = routeDispute(disputeContext);

// Result:
// {
//   system: "legal",
//   agents: ["customerLawyer", "companyLawyer", "judge", "independentLawyer"],
//   platformContext: {
//     platform: "GrabFood",
//     parties: [
//       { name: "Customer", type: "customer", role: "Complainant" },
//       { name: "GrabFood", type: "platform", role: "Platform Operator" },
//       { name: "Restaurant", type: "merchant", role: "Service Provider" }
//     ]
//   }
// }
```

---

## Code Examples by Platform

### GrabFood Example
```python
# Backend routing
from agent_router import route_dispute_to_agents, get_agent_prompt_instruction

routing = route_dispute_to_agents("GrabFood", "Food spoilt")
# routing["agents"] = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]

# Get platform-specific instructions for each agent
for agent in routing["agents"]:
    instruction = get_agent_prompt_instruction(agent, "GrabFood")
    # instruction includes party context: Customer, GrabFood, Restaurant
```

### Banking Example
```python
routing = route_dispute_to_agents("Banking", "Double charge")
# routing["agents"] = ["customerLawyer", "companyLawyer", "judge", "independentLawyer"]

# Parties context automatically included:
# - Customer (disputing the charge)
# - Bank (payment processor)
# - Merchant (charge recipient)
```

---

## Agent Output Example: GrabFood Dispute

All agents output the same JSON schema:

```json
{
  "dispute_id": "GRB-2026-001",
  "agent": "Customer Lawyer",
  "confidence_score": 90,
  "reasoning": "Photo evidence of mold on burger matches delivery timestamp. GrabFood responsible for food quality per service agreement.",
  "evidence": [
    {
      "supabase": {
        "table": "system_logs",
        "row_id": "log-789",
        "json_path": "payload.event_photo_url"
      },
      "transaction_id": "txn-123456",
      "details": "Photo timestamp 7:32 PM matches delivery completion timestamp. Visual mold evidence on food product."
    }
  ],
  "summary_tldr": "Photo evidence confirms food spoilage at delivery. Customer entitled to full refund.",
  "created_at": "2026-04-23T14:30:00+00:00"
}
```

---

## Party Mapping Reference

| Platform | Party 1 | Party 2 | Party 3 | Party 4 |
|----------|---------|---------|---------|---------|
| **GrabFood** | Customer | GrabFood (Platform) | Restaurant (Merchant) | — |
| **Banking** | Customer | Bank | Merchant | Shopping Mall (opt) |
| **E-Commerce** | Customer | Platform | Seller | — |
| **Payments** | Customer | Company | Payment Processor | — |

---

## When to Use Which System

### Use Legal Agents When:
- ✅ Multiple parties involved in dispute (customer + company + merchant)
- ✅ Need perspectives from different stakeholders
- ✅ Dispute resolution requires legal analysis
- ✅ Platform has defined parties (GrabFood, Banking, etc.)

### Use Operational Agents When:
- ✅ Internal transaction validation needed
- ✅ Hash reconciliation required
- ✅ Simple, single-perspective analysis
- ✅ Unknown platforms

### Automatic Selection:
```typescript
routeDispute(context)  // Automatically selects based on platform
```

---

## Key Files Reference

| Purpose | Frontend File | Backend File |
|---------|---------------|--------------|
| **Agent Prompts** | `LegalAgentPrompts.ts` | `agent_router.py` |
| **Party Definitions** | `PlatformPartyMapping.ts` | `agent_router.py` |
| **Routing Logic** | `AgentRouter.ts` | `agent_router.py` |
| **Usage Examples** | `AGENT_SYSTEM_DOCUMENTATION.md` | `BACKEND_INTEGRATION_GUIDE.py` |

---

## Quick Start Commands

### TypeScript (Frontend)
```typescript
// Route dispute automatically
import { routeDispute } from "@/lib/agents-index";
const assignment = routeDispute(disputeContext);

// Get specific agent prompt
import { legalAgentPrompts } from "@/lib/agents-index";
const prompt = legalAgentPrompts.customerLawyer;

// Get platform context
import { getPlatformContext } from "@/lib/agents-index";
const context = getPlatformContext("GrabFood");
```

### Python (Backend)
```python
# Route dispute
from agent_router import route_dispute_to_agents
routing = route_dispute_to_agents("GrabFood", "Food spoilt")

# Get agent metadata
from agent_router import get_agent_metadata
metadata = get_agent_metadata("customerLawyer")

# Get platform parties
from agent_router import get_platform_parties
parties = get_platform_parties("Banking")
```

---

## Status
✅ Implementation Complete
- 4 Legal Agents: Customer Lawyer, Company Lawyer, Judge, Independent Lawyer
- 4 Platforms: GrabFood, Banking, E-Commerce, Payments (extensible)
- Fully Type-Safe: TypeScript + Python
- Evidence-Based: All agents cite Supabase rows
- Backward Compatible: Operational agents still available
