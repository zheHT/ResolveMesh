// agents-index.ts
// Convenience barrel exports for the dual agent system
// Makes it easier to import agent-related functionality

// Operational agents (legacy)
export { agentPrompts } from "./ZaiPrompts";

// Legal agents (new)
export { legalAgentPrompts, type LegalAgentType } from "./LegalAgentPrompts";

// Platform context and utilities
export { 
  getPlatformContext, 
  getDisputeParties, 
  getAgentInstruction,
  type DisputeParty,
  type PlatformContext,
  type PartyType,
  platformContexts,
} from "./PlatformPartyMapping";

// Agent routing
export {
  routeDispute,
  routeToLegalAgents,
  routeToOperationalAgents,
  getAllAvailableAgents,
  getAgentPrompt,
  isValidAgent,
  type AgentSystem,
  type OperationalAgent,
  type DisputeContext,
  type AgentAssignment,
} from "./AgentRouter";

/**
 * Quick start examples:
 * 
 * // 1. Get a specific agent prompt
 * import { agentPrompts, legalAgentPrompts } from "@/lib/agents-index";
 * const prompt = legalAgentPrompts.customerLawyer;
 * 
 * // 2. Route a dispute automatically
 * import { routeDispute } from "@/lib/agents-index";
 * const assignment = routeDispute(disputeContext);
 * 
 * // 3. Get platform context
 * import { getPlatformContext, getDisputeParties } from "@/lib/agents-index";
 * const context = getPlatformContext("GrabFood");
 * const parties = getDisputeParties("Banking");
 * 
 * // 4. Validate agent names
 * import { isValidAgent } from "@/lib/agents-index";
 * if (isValidAgent("legal", "customerLawyer")) { ... }
 */
