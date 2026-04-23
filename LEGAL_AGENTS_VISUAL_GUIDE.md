## Legal Agent System - Visual Guides

### 1. Dispute Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Incoming Dispute                          │
│                                                               │
│  Platform: "GrabFood"                                        │
│  Issue: "Food spoilt"                                        │
│  Customer: "My burger had green spots"                       │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│           Agent Router (AgentRouter.ts / agent_router.py)    │
│                                                               │
│  1. Identify Platform: "GrabFood"                            │
│  2. Load Party Context: Customer, GrabFood, Restaurant      │
│  3. Select System: Legal (has multiple parties)             │
└──────────────┬───────────────────────────────────────────────┘
               │
        ┌──────┴──────┬────────────┬────────────┐
        │             │            │            │
        ▼             ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────┐  ┌──────────────┐
   │ Customer│  │ Company │  │Judge │  │Independent  │
   │ Lawyer  │  │ Lawyer  │  │      │  │ Lawyer       │
   │         │  │         │  │      │  │              │
   │Build    │  │Build    │  │Eval- │  │Recommend     │
   │case for │  │defense  │  │uate  │  │settlement    │
   │customer │  │for co.  │  │both  │  │              │
   └────┬────┘  └────┬────┘  └───┬──┘  └────┬─────────┘
        │             │           │          │
        │             │           │          │
        └─────────────┼───────────┼──────────┘
                      │           │
                      ▼           ▼
            ┌──────────────────────────────┐
            │        Z.ai API              │
            │   (chat_once with prompts)   │
            └──────────────┬───────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐         ┌────────┐        ┌────────┐
    │Result  │         │Result  │        │Result  │
    │from C. │         │from Co.│        │from J. │ + Indep.
    │Lawyer  │         │Lawyer  │        │udge    │   Lawyer
    └────────┘         └────────┘        └────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   Investigation Summaries    │
            │                              │
            │  - dispute_id                │
            │  - agent (lawyer name)       │
            │  - confidence_score          │
            │  - reasoning                 │
            │  - evidence (with citations) │
            │  - summary_tldr              │
            └──────────────┬───────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │      Supabase Storage        │
            │                              │
            │  disputes table              │
            │  ├─ id                       │
            │  ├─ agent_routing            │
            │  ├─ agent_reports            │
            │  ├─ investigation_summary    │
            │  └─ ...                      │
            └──────────────────────────────┘
```

---

### 2. Agent Perspective Comparison: GrabFood Example

```
DISPUTE: "Burger arrived with mold"
AMOUNT: $28.50
PARTIES: Customer, GrabFood Platform, Restaurant

┌─────────────────────────────────────────────────────────────────────┐
│                      LEGAL AGENT PERSPECTIVES                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 👤 CUSTOMER LAWYER                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Position:     Demand full refund                                    │
│ Confidence:   95/100                                                │
│                                                                     │
│ Key Evidence:                                                       │
│  ✓ Photo timestamp matches delivery time                           │
│  ✓ Mold visible in food product                                    │
│  ✓ GrabFood policy: food quality guarantee at delivery            │
│  ✓ No customer mishandling evident                                 │
│                                                                     │
│ Reasoning: Food arrived contaminated. GrabFood responsible.        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 🏢 COMPANY LAWYER (GrabFood/Restaurant)                            │
├─────────────────────────────────────────────────────────────────────┤
│ Position:     Offer partial refund ($15) OR replacement            │
│ Confidence:   45/100                                                │
│                                                                     │
│ Key Evidence:                                                       │
│  ✗ Restaurant prepared item per safety standards                   │
│  ✗ Delivery logs show 45-min completion                            │
│  ? Photo could be post-delivery manipulation                       │
│  ? Customer delay in reporting (reported 2 hours later)            │
│                                                                     │
│ Reasoning: Process followed. Photo authenticity unclear.           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ⚖️  JUDGE (Neutral Arbiter)                                         │
├─────────────────────────────────────────────────────────────────────┤
│ Decision:     CUSTOMER WINS - Issue full $28.50 refund             │
│ Confidence:   92/100                                                │
│                                                                     │
│ Factual Findings:                                                   │
│  1. Photo timestamp aligns with delivery completion                │
│  2. Mold contamination visible in photographic evidence            │
│  3. Food safety standards violated at delivery point               │
│  4. GrabFood responsible for ensuring quality at handoff           │
│                                                                     │
│ Legal Principle Applied:                                            │
│  Merchant/Platform liability for defective goods applies at        │
│  point of delivery, regardless of preparation location.           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 📋 INDEPENDENT LAWYER (Settlement Advisor)                         │
├─────────────────────────────────────────────────────────────────────┤
│ Recommendation: Issue full refund + $5 credit                      │
│ Rationale:     High evidence quality supports customer            │
│ Risk Level:    LOW (customer has strong case)                      │
│                                                                     │
│ Settlement Options (ranked):                                       │
│  1️⃣  Full Refund ($28.50) - Recommended                            │
│  2️⃣  Refund + $5 credit (goodwill) - Builds trust                  │
│  3️⃣  Replacement order + $5 credit - Customer may decline          │
│  4️⃣  Partial refund ($20) - Risk of escalation                     │
│                                                                     │
│ Next Steps:                                                        │
│  → Process refund immediately                                      │
│  → Email apology with process explanation                          │
│  → Flag restaurant for quality audit                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3. Platform Party Mapping Diagram

```
GRABFOOD ECOSYSTEM
═════════════════════════════════════

          ┌─────────────┐
          │  Customer   │ (Claimer)
          │             │
          └──────┬──────┘
                 │ places order
                 │ disputes if issue
                 │
         ┌───────┴───────┐
         │               │
         ▼               ▼
    ┌─────────┐   ┌──────────────┐
    │GrabFood │───│ Restaurant   │
    │Platform │   │ (Merchant)   │
    └─────────┘   └──────────────┘
    (Mediator)    (Service Provider)

Three Perspectives:
┌─────────────────────────────────┐
│ 👤 Customer Lawyer              │
│    Why customer should win       │
├─────────────────────────────────┤
│ 🏢 Company Lawyer               │
│    Why GrabFood/restaurant      │
│    shouldn't pay                │
├─────────────────────────────────┤
│ ⚖️  Judge                        │
│    Who's actually right based    │
│    on evidence                   │
├─────────────────────────────────┤
│ 📋 Independent Lawyer           │
│    What's fair settlement       │
└─────────────────────────────────┘


BANKING ECOSYSTEM
═════════════════════════════════════

    ┌─────────────┐
    │  Customer   │ (Disputer)
    │  (Cardholder)
    └──────┬──────┘
           │ disputes charge
           │
      ┌────┴─────────┐
      │              │
      ▼              ▼
 ┌─────────┐   ┌──────────┐
 │  Bank   │───│Merchant  │
 │         │   │(Vendor)  │
 └─────────┘   └──────────┘
 (Processor)   (Recipient)

Optional: Shopping Mall context
           │
           ▼
    ┌─────────────┐
    │Shopping Mall│
    │(Location)   │
    └─────────────┘

Four Parties, Four Perspectives:
┌─────────────────────────────────┐
│ 👤 Customer Lawyer              │
│    Why charge was unauthorized  │
├─────────────────────────────────┤
│ 🏢 Company Lawyer (Bank+Merch)  │
│    Why charge is legitimate     │
├─────────────────────────────────┤
│ ⚖️  Judge                        │
│    What transaction records     │
│    definitively show            │
├─────────────────────────────────┤
│ 📋 Independent Lawyer           │
│    Chargeback recommendation    │
│    per banking rules            │
└─────────────────────────────────┘
```

---

### 4. Evidence Citation Pattern

```
Each Agent's Analysis Includes Evidence Citations:

EXAMPLE: GrabFood mold dispute

┌─────────────────────────────────┐
│ Agent Output (JSON)             │
├─────────────────────────────────┤
│                                 │
│ "evidence": [                   │
│   {                             │
│     "supabase": {               │
│       "table": "system_logs",   │ ← Supabase table
│       "row_id": "log-789",      │ ← Specific row
│       "json_path":              │
│         "payload.photo_url"     │ ← JSONB path
│     },                          │
│     "transaction_id":           │
│       "txn-GRB-001",            │ ← Cross-check ID
│     "hash": "abc123...",        │ ← Transaction hash
│     "details":                  │
│       "Photo timestamp 7:32 PM  │ ← Why evidence
│        matches delivery time.   │    matters
│        Visual mold on food      │
│        surface."                │
│   },                            │
│   { ... more evidence items }   │
│ ]                               │
│                                 │
└─────────────────────────────────┘

This ensures:
✓ Every claim is backed by Supabase data
✓ Evidence is verifiable by humans
✓ No hallucination or invented facts
✓ Clear audit trail for compliance
```

---

### 5. Confidence Score Scale

```
┌──────────────────────────────────────────────────────────────┐
│           LEGAL AGENT CONFIDENCE SCORING                     │
└──────────────────────────────────────────────────────────────┘

95-100  ████████████████████ DEFINITIVE
        • Clear contradictory evidence
        • Multiple corroborating Supabase rows
        • Unambiguous timestamps/hashes
        • Example: Photo + timestamp + logs all align

80-94   ████████████████░░░░ STRONG
        • Primary evidence + corroborating rows
        • Minor gaps but clear direction
        • Example: Photo clear but timestamp slightly fuzzy

65-79   ████████████░░░░░░░░ MODERATE
        • Evidence supports position but has gaps
        • Could be interpreted different ways
        • Example: Transaction exists but purpose unclear

50-64   ████████░░░░░░░░░░░░ WEAK
        • Some evidence but contradictions
        • Missing key corroboration
        • Example: Claim vs unclear logs

0-49    ████░░░░░░░░░░░░░░░░ INSUFFICIENT
        • Minimal or conflicting evidence
        • Cannot reliably assess
        • Example: No evidence found in logs

JUDGE = Average confidence of Customer + Company positions
LAWYER = Confidence in recommended settlement path
```

---

### 6. File Structure

```
ResolveMesh/
│
├── resolvemesh-ai-console/src/lib/
│   ├── LegalAgentPrompts.ts          ← Agent role definitions
│   ├── PlatformPartyMapping.ts       ← Platform contexts
│   ├── AgentRouter.ts                ← Routing logic
│   ├── agents-index.ts               ← Convenience exports
│   ├── ZaiPrompts.ts                 ← Updated (added legal)
│   └── AGENT_SYSTEM_DOCUMENTATION.md ← Full frontend guide
│
├── backend/
│   ├── agent_router.py               ← Backend routing
│   ├── BACKEND_INTEGRATION_GUIDE.py  ← Integration examples
│   └── main.py                        ← (Ready for integration)
│
├── LEGAL_AGENT_SYSTEM_SUMMARY.md     ← Implementation overview
└── LEGAL_AGENTS_QUICK_REFERENCE.md   ← Quick lookup guide
```

---

### 7. Agent Invocation Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. Dispute arrives                                         │
│     ↓                                                       │
│  2. Route to agents                                         │
│     ↓                                                       │
│  3. ┌─────────────────────────────────────────────┐       │
│     │ PARALLEL: Invoke all 4 legal agents         │       │
│     │                                               │       │
│     │  → Customer Lawyer    ┐                      │       │
│     │  → Company Lawyer     ├─→ Z.ai API          │       │
│     │  → Judge              ├─→ chat_once()       │       │
│     │  → Independent Lawyer ┘                      │       │
│     │                                               │       │
│     │ Each gets platform context + base prompt     │       │
│     └─────────────────────────────────────────────┘       │
│     ↓                                                       │
│  4. Collect results (4 Investigation Summaries)            │
│     ↓                                                       │
│  5. Validate against schema                                │
│     ↓                                                       │
│  6. Store in Supabase disputes.agent_reports               │
│     ↓                                                       │
│  7. Display to staff:                                       │
│     ✓ Customer Lawyer perspective                          │
│     ✓ Company Lawyer perspective                           │
│     ✓ Judge recommendation                                 │
│     ✓ Independent Lawyer settlement advice                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ FRONTEND (TypeScript)                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Import:                                                 │
│   import { routeDispute } from "@/lib/agents-index";  │
│                                                         │
│ Basic Usage:                                            │
│   const routing = routeDispute(disputeContext);        │
│   // routing.agents = 4 legal agents               │
│   // routing.platformContext = parties info        │
│                                                         │
│ Get Platform Context:                                  │
│   import { getPlatformContext } from "...";           │
│   const context = getPlatformContext("GrabFood");      │
│                                                         │
│ Get Agent Prompt:                                       │
│   import { legalAgentPrompts } from "...";            │
│   const prompt = legalAgentPrompts.customerLawyer;     │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ BACKEND (Python)                                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Import:                                                 │
│   from agent_router import route_dispute_to_agents    │
│                                                         │
│ Basic Usage:                                            │
│   routing = route_dispute_to_agents("GrabFood", "...")│
│   # routing["agents"] = 4 legal agents               │
│   # routing["platform_context"] = parties info      │
│                                                         │
│ Get Party Context:                                      │
│   from agent_router import get_platform_parties       │
│   parties = get_platform_parties("Banking")            │
│                                                         │
│ Get Agent Metadata:                                     │
│   from agent_router import get_agent_metadata         │
│   meta = get_agent_metadata("customerLawyer")          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
