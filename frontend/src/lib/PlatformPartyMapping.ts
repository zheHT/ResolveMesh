// PlatformPartyMapping.ts
// Defines the parties involved in disputes across different platforms/services
// Used to route disputes to appropriate agents based on context

export type PartyType = "customer" | "company" | "merchant" | "platform" | "bank" | "payment_processor" | "shopping_mall";

export interface DisputeParty {
  name: string;
  type: PartyType;
  role: string;
  description: string;
}

export interface PlatformContext {
  platform: string;
  description: string;
  parties: DisputeParty[];
  legalAgentRoute: {
    customerLawyer: string;
    companyLawyer: string;
    judge: string;
    independentLawyer: string;
    merchant: string;
  };
}

/**
 * Platform Configurations
 * Each platform defines the parties involved and how agents should be routed
 */
export const platformContexts: Record<string, PlatformContext> = {
  grabfood: {
    platform: "GrabFood",
    description: "Food delivery disputes involving customer, platform, and restaurant",
    parties: [
      {
        name: "Customer",
        type: "customer",
        role: "Complainant",
        description: "Consumer who placed the food order",
      },
      {
        name: "GrabFood",
        type: "platform",
        role: "Platform Operator",
        description: "Food delivery platform managing transactions and disputes",
      },
      {
        name: "Restaurant/Merchant",
        type: "merchant",
        role: "Service Provider",
        description: "Food establishment that prepared/delivered the order",
      },
    ],
    legalAgentRoute: {
      customerLawyer: "Customer perspective - claim of poor food quality, delay, or incorrect order",
      companyLawyer: "GrabFood/Merchant perspective - service was delivered as ordered",
      judge: "Neutral evaluation of food quality/service delivery evidence from GrabFood logs",
      independentLawyer: "Assess claim viability and recommend settlement based on evidence",
      merchant: "Restaurant perspective - order was prepared correctly and delivered on time",
    },
  },

  banking: {
    platform: "Banking",
    description: "Financial disputes involving customer, bank, and potentially merchant/vendor",
    parties: [
      {
        name: "Customer",
        type: "customer",
        role: "Account Holder",
        description: "Customer disputing a transaction",
      },
      {
        name: "Bank",
        type: "bank",
        role: "Payment Processor",
        description: "Financial institution processing transactions",
      },
      {
        name: "Merchant/Vendor",
        type: "merchant",
        role: "Transaction Recipient",
        description: "Business that received payment from customer",
      },
      {
        name: "Shopping Mall",
        type: "shopping_mall",
        role: "Venue Operator (Optional)",
        description: "Shopping complex where merchant operates (if applicable)",
      },
    ],
    legalAgentRoute: {
      customerLawyer: "Customer perspective - unauthorized charge, duplicate billing, or service not received",
      companyLawyer: "Bank/Merchant perspective - transaction was authorized and completed per ledger",
      judge: "Neutral evaluation based on transaction records and payment processor rules",
      independentLawyer: "Assess chargeback viability under banking regulations and settlement recommendation",
      merchant: "Merchant perspective - payment was received and services/goods were delivered",
    },
  },

  ecommerce: {
    platform: "E-Commerce",
    description: "Online retail disputes involving customer, platform, and seller",
    parties: [
      {
        name: "Customer",
        type: "customer",
        role: "Buyer",
        description: "Customer who made the purchase",
      },
      {
        name: "Platform",
        type: "platform",
        role: "Marketplace Operator",
        description: "E-commerce platform facilitating the transaction",
      },
      {
        name: "Seller",
        type: "merchant",
        role: "Product Provider",
        description: "Seller offering products on the platform",
      },
    ],
    legalAgentRoute: {
      customerLawyer: "Buyer perspective - item not as described, defective, or not delivered",
      companyLawyer: "Seller/Platform perspective - item dispatched or customer responsibility",
      judge: "Neutral evaluation of product condition and delivery evidence",
      independentLawyer: "Assess product claim validity and recommend refund/replacement settlement",
      merchant: "Seller perspective - item was dispatched correctly and meets description/conditions",
    },
  },

  payments: {
    platform: "Payments",
    description: "Generic payment disputes",
    parties: [
      {
        name: "Customer",
        type: "customer",
        role: "Payer",
        description: "Customer initiating the payment dispute",
      },
      {
        name: "Company",
        type: "company",
        role: "Service Provider",
        description: "Company providing goods or services",
      },
      {
        name: "Payment Processor",
        type: "payment_processor",
        role: "Transaction Handler",
        description: "Payment processing service",
      },
    ],
    legalAgentRoute: {
      customerLawyer: "Customer perspective - payment issue or service failure",
      companyLawyer: "Company perspective - payment successful and service delivered",
      judge: "Neutral evaluation based on transaction evidence",
      independentLawyer: "Assess dispute viability and recommend resolution",
      merchant: "Merchant perspective - goods/services were delivered and payment should be retained",
    },
  },
};

/**
 * Get platform context by name
 */
export function getPlatformContext(platform: string): PlatformContext | null {
  const normalized = platform.toLowerCase().replace(/\s+/g, "");
  for (const [key, context] of Object.entries(platformContexts)) {
    if (key === normalized || context.platform.toLowerCase() === platform.toLowerCase()) {
      return context;
    }
  }
  return null;
}

/**
 * Get parties involved in a dispute
 */
export function getDisputeParties(platform: string): DisputeParty[] {
  const context = getPlatformContext(platform);
  return context?.parties ?? [];
}

/**
 * Route agent instructions based on platform and party
 */
export function getAgentInstruction(
  platform: string,
  agent: "customerLawyer" | "companyLawyer" | "judge" | "independentLawyer" | "merchant"
): string | null {
  const context = getPlatformContext(platform);
  return context?.legalAgentRoute[agent] ?? null;
}
