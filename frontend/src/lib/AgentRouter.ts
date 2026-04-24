// AgentRouter.ts
// Routes disputes to appropriate agents based on platform, issue type, and context
// Supports both operational and legal agent systems

import { agentPrompts } from "./ZaiPrompts";
import { legalAgentPrompts, type LegalAgentType } from "./LegalAgentPrompts";
import { getPlatformContext, getAgentInstruction } from "./PlatformPartyMapping";

export type AgentSystem = "operational" | "legal";
export type OperationalAgent = "negotiator" | "advocate" | "auditor" | "summarizer";

export interface DisputeContext {
  platform: string;
  issueType: string;
  orderId: string;
  customerEmail: string;
  amount: number;
  rawDescription: string;
}

export interface AgentAssignment {
  agentSystem: AgentSystem;
  agents: string[];
  prompts: Record<string, string>;
  platformContext?: Record<string, any>;
  routing: Record<string, string>;
}

/**
 * Route dispute to operational agents (legacy system)
 * Used for: transaction reconciliation, internal validation
 */
export function routeToOperationalAgents(context: DisputeContext): AgentAssignment {
  return {
    agentSystem: "operational",
    agents: ["negotiator", "advocate", "auditor", "summarizer"],
    prompts: agentPrompts as Record<string, string>,
    routing: {
      negotiator: "Hash reconciliation and transaction validation",
      advocate: "Staff rationale and policy compliance validation",
      auditor: "Collusion and anomaly detection",
      summarizer: "30-word TL;DR for staff dashboard",
    },
  };
}

/**
 * Route dispute to legal agents (new system)
 * Used for: multi-party dispute resolution with legal perspectives
 */
export function routeToLegalAgents(context: DisputeContext): AgentAssignment {
  const platformContext = getPlatformContext(context.platform);

  return {
    agentSystem: "legal",
    agents: ["customerLawyer", "companyLawyer", "judge", "independentLawyer", "merchant"],
    prompts: legalAgentPrompts as Record<string, string>,
    platformContext: platformContext ? {
      platform: platformContext.platform,
      description: platformContext.description,
      parties: platformContext.parties.map(p => ({
        name: p.name,
        type: p.type,
        role: p.role,
      })),
    } : undefined,
    routing: {
      customerLawyer: getAgentInstruction(context.platform, "customerLawyer") || "Build strongest case for customer position",
      companyLawyer: getAgentInstruction(context.platform, "companyLawyer") || "Build strongest defense for company position",
      judge: getAgentInstruction(context.platform, "judge") || "Neutral evaluation of both positions",
      independentLawyer: getAgentInstruction(context.platform, "independentLawyer") || "Objective legal assessment and settlement recommendation",
      merchant: getAgentInstruction(context.platform, "merchant") || "Defend merchant service delivery and payment rights",
    },
  };
}

/**
 * Intelligently route dispute to most appropriate agent system
 * 
 * Decision logic:
 * - If platform has known parties (GrabFood, Banking, etc.) → use legal agents
 * - Otherwise → use operational agents
 */
export function routeDispute(context: DisputeContext): AgentAssignment {
  const platformContext = getPlatformContext(context.platform);

  // If we have platform-specific context with defined parties, use legal agents
  if (platformContext && platformContext.parties.length > 1) {
    return routeToLegalAgents(context);
  }

  // Default to operational agents
  return routeToOperationalAgents(context);
}

/**
 * Get all available agents across both systems
 */
export function getAllAvailableAgents() {
  return {
    operational: Object.keys(agentPrompts),
    legal: Object.keys(legalAgentPrompts),
  };
}

/**
 * Get agent prompt by system and agent name
 */
export function getAgentPrompt(system: AgentSystem, agentName: string): string | null {
  if (system === "operational") {
    return (agentPrompts as Record<string, string>)[agentName] ?? null;
  } else if (system === "legal") {
    return (legalAgentPrompts as Record<string, string>)[agentName] ?? null;
  }
  return null;
}

/**
 * Validate agent name exists in a system
 */
export function isValidAgent(system: AgentSystem, agentName: string): boolean {
  return getAgentPrompt(system, agentName) !== null;
}
