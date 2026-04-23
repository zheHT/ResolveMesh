export type DisputeStatus = "Investigating" | "Flagged" | "Awaiting Action" | "Resolved";
export type RiskLevel = "Low" | "Medium" | "High" | "Critical";
export type ComplaintCategory =
  | "Fraud"
  | "Service Not Rendered"
  | "Duplicate Charge"
  | "Product Not as Described"
  | "Unauthorized Recurring"
  | "Account Takeover";

export type Dispute = {
  id: string;
  caseId: string;
  customer: string;
  customerEmail: string;
  cardLast4: string;
  amount: number;
  currency: string;
  merchant: string;
  reason: string;
  category: ComplaintCategory;
  suggestedRefund: number;
  status: DisputeStatus;
  risk: RiskLevel;
  confidence: number; // 0-100
  openedAt: string; // ISO
  channel: "Visa" | "Mastercard" | "Amex" | "ACH";
  agentSummary: string;
};

export const disputes: Dispute[] = [
  {
    id: "1",
    caseId: "RM-48201",
    customer: "Marcus Chen",
    customerEmail: "marcus.chen@northwave.io",
    cardLast4: "4421",
    amount: 1284.5,
    currency: "USD",
    merchant: "Stripe • Linear Software",
    reason: "Unrecognized recurring charge",
    category: "Unauthorized Recurring",
    suggestedRefund: 1284.5,
    status: "Investigating",
    risk: "High",
    confidence: 82,
    openedAt: "2026-04-19T13:22:00Z",
    channel: "Visa",
    agentSummary:
      "Customer disputes a recurring SaaS charge initiated 14 days after free trial. Device fingerprint matches prior successful sessions; geo-IP consistent.",
  },
  {
    id: "2",
    caseId: "RM-48198",
    customer: "Priya Anand",
    customerEmail: "priya.a@helixlabs.com",
    cardLast4: "0918",
    amount: 4290.0,
    currency: "USD",
    merchant: "Apple • App Store",
    reason: "Fraudulent transaction",
    category: "Fraud",
    suggestedRefund: 4290.0,
    status: "Flagged",
    risk: "Critical",
    confidence: 94,
    openedAt: "2026-04-19T11:08:00Z",
    channel: "Mastercard",
    agentSummary:
      "Three rapid in-app purchases from a new device located 2,800km from cardholder's home cluster. Likely account takeover.",
  },
  {
    id: "3",
    caseId: "RM-48177",
    customer: "Daniel Okafor",
    customerEmail: "d.okafor@meridian.bank",
    cardLast4: "2210",
    amount: 312.18,
    currency: "USD",
    merchant: "Uber • Rides",
    reason: "Service not received",
    category: "Service Not Rendered",
    suggestedRefund: 312.18,
    status: "Awaiting Action",
    risk: "Low",
    confidence: 71,
    openedAt: "2026-04-19T08:44:00Z",
    channel: "Visa",
    agentSummary:
      "Trip cancelled by driver per ride logs. Refund eligible under merchant policy. Drafted partial credit recommendation.",
  },
  {
    id: "4",
    caseId: "RM-48164",
    customer: "Sasha Volkov",
    customerEmail: "sasha@volkov-design.studio",
    cardLast4: "7732",
    amount: 9870.0,
    currency: "EUR",
    merchant: "Lufthansa • Flight Booking",
    reason: "Duplicate charge",
    category: "Duplicate Charge",
    suggestedRefund: 4935.0,
    status: "Investigating",
    risk: "Medium",
    confidence: 88,
    openedAt: "2026-04-19T07:12:00Z",
    channel: "Amex",
    agentSummary:
      "Two identical authorizations within 8 seconds. One captured, one expired. Confirmed duplicate via merchant ARN match.",
  },
  {
    id: "5",
    caseId: "RM-48150",
    customer: "Helena Park",
    customerEmail: "helena.park@orbital.energy",
    cardLast4: "5567",
    amount: 624.0,
    currency: "USD",
    merchant: "Shopify • Threadbox Co.",
    reason: "Item not as described",
    category: "Product Not as Described",
    suggestedRefund: 312.0,
    status: "Awaiting Action",
    risk: "Low",
    confidence: 67,
    openedAt: "2026-04-18T22:01:00Z",
    channel: "Visa",
    agentSummary:
      "Photographic evidence supports cardholder claim. Recommending merchant outreach before chargeback filing.",
  },
  {
    id: "6",
    caseId: "RM-48132",
    customer: "Yusuf Rahman",
    customerEmail: "y.rahman@sigmacapital.co",
    cardLast4: "1145",
    amount: 18420.0,
    currency: "USD",
    merchant: "Coinbase • Crypto Buy",
    reason: "Authorized push payment fraud",
    category: "Account Takeover",
    suggestedRefund: 18420.0,
    status: "Flagged",
    risk: "Critical",
    confidence: 96,
    openedAt: "2026-04-18T19:45:00Z",
    channel: "ACH",
    agentSummary:
      "Pattern matches APP-fraud cluster S-114. Beneficiary wallet flagged on Chainalysis 36 minutes after transfer.",
  },
];

export function getDispute(id: string): Dispute | undefined {
  return disputes.find((d) => d.id === id || d.caseId === id);
}

export function maskPII(text: string, mask: boolean): string {
  if (!mask) return text;
  return text.replace(/[A-Za-z0-9]/g, (c) => (/[A-Za-z0-9]/.test(c) ? "•" : c));
}

export function maskEmail(email: string, mask: boolean): string {
  if (!mask) return email;
  const [user, domain] = email.split("@");
  if (!domain) return "•".repeat(email.length);
  return `${"•".repeat(Math.max(3, user.length))}@${domain}`;
}
