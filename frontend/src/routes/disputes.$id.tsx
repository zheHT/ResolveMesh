import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowLeft, Building2, CheckCircle2, CreditCard, Download, Send, User } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { maskEmail, maskPII } from "@/lib/disputes";
import { getPIIMaskEnabled, PII_MASK_CHANGED_EVENT } from "@/lib/ui-state";
import { cn } from "@/lib/utils";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type DisputeDetail = {
  id: string;
  status: string;
  created_at?: string | null;
  customer_info?: {
    email?: string;
    amount?: number;
    order_id?: string;
    platform?: string;
    account_id?: string;
    issue_type?: string;
    evidence_url?: string;
  };
  agent_reports?: {
    guardian?: {
      summary?: string;
      redacted_at?: string;
    };
    summary?: string;
  };
};

type ApiError = {
  detail?: string;
};

type GenericRecord = Record<string, unknown>;

export const Route = createFileRoute("/disputes/$id")({
  component: DisputeInvestigationPage,
});

function safeString(value: unknown) {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  return "N/A";
}

function safeCurrency(value: unknown) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "N/A";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function getNestedStatus(record: GenericRecord | null) {
  if (!record) return null;

  const directStatus = record.status;
  if (typeof directStatus === "string" && directStatus.trim()) {
    return directStatus;
  }

  const ledger = record.ledger_data;
  if (ledger && typeof ledger === "object" && !Array.isArray(ledger)) {
    const ledgerStatus = (ledger as GenericRecord).status;
    if (typeof ledgerStatus === "string" && ledgerStatus.trim()) {
      return ledgerStatus;
    }

    const merchantStatus = (ledger as GenericRecord).merchant_status;
    if (typeof merchantStatus === "string" && merchantStatus.trim()) {
      return merchantStatus;
    }
  }

  return null;
}

function normalizeApiError(errorPayload: unknown, fallbackMessage: string) {
  if (errorPayload && typeof errorPayload === "object") {
    const detail = (errorPayload as ApiError).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }

  return fallbackMessage;
}

function maskSensitiveValue(fieldKey: string, value: string, masked: boolean) {
  if (!masked || value === "N/A") {
    return value;
  }

  const key = fieldKey.toLowerCase();

  if (key.includes("email")) {
    return maskEmail(value, true);
  }

  if (
    key.includes("account") ||
    key.includes("order") ||
    key.includes("card") ||
    key.includes("credential") ||
    key.includes("token") ||
    key.includes("wallet") ||
    key.includes("beneficiary") ||
    key.includes("evidence") ||
    key.includes("phone")
  ) {
    return maskPII(value, true);
  }

  return value;
}

function DisputeInvestigationPage() {
  const { id } = Route.useParams();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dispute, setDispute] = useState<DisputeDetail | null>(null);
  const [ledgerRecord, setLedgerRecord] = useState<GenericRecord | null>(null);
  const [merchantRecord, setMerchantRecord] = useState<GenericRecord | null>(null);
  const [ledgerError, setLedgerError] = useState<string | null>(null);
  const [merchantError, setMerchantError] = useState<string | null>(null);
  const [piiMasked, setPiiMasked] = useState(true);

  useEffect(() => {
    setPiiMasked(getPIIMaskEnabled());

    const syncMask = () => setPiiMasked(getPIIMaskEnabled());
    window.addEventListener(PII_MASK_CHANGED_EVENT, syncMask);
    window.addEventListener("storage", syncMask);

    return () => {
      window.removeEventListener(PII_MASK_CHANGED_EVENT, syncMask);
      window.removeEventListener("storage", syncMask);
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadInvestigationData() {
      try {
        setLoading(true);
        setError(null);
        setLedgerError(null);
        setMerchantError(null);

        const disputeResponse = await fetch(`${API_BASE_URL}/api/disputes/${id}`, {
          signal: controller.signal,
        });

        if (!disputeResponse.ok) {
          let parsedError: unknown = null;
          try {
            parsedError = await disputeResponse.json();
          } catch {
            parsedError = null;
          }
          throw new Error(normalizeApiError(parsedError, "Failed to load dispute details."));
        }

        const disputePayload = (await disputeResponse.json()) as DisputeDetail;
        if (!disputePayload || typeof disputePayload !== "object") {
          throw new Error("Invalid dispute detail payload.");
        }

        setDispute(disputePayload);

        const orderId = disputePayload.customer_info?.order_id;
        if (!orderId) {
          setLedgerError("No order_id found in dispute payload.");
          setMerchantError("No order_id found in dispute payload.");
          return;
        }

        const [ledgerResult, merchantResult] = await Promise.allSettled([
          fetch(`${API_BASE_URL}/api/ledger/${encodeURIComponent(orderId)}`, {
            signal: controller.signal,
          }),
          fetch(`${API_BASE_URL}/api/merchant/${encodeURIComponent(orderId)}`, {
            signal: controller.signal,
          }),
        ]);

        if (ledgerResult.status === "fulfilled") {
          if (ledgerResult.value.ok) {
            const payload = (await ledgerResult.value.json()) as GenericRecord;
            setLedgerRecord(payload);
          } else {
            let parsedError: unknown = null;
            try {
              parsedError = await ledgerResult.value.json();
            } catch {
              parsedError = null;
            }
            setLedgerError(normalizeApiError(parsedError, "Bank ledger record not found."));
          }
        } else {
          setLedgerError("Failed to reach bank ledger endpoint.");
        }

        if (merchantResult.status === "fulfilled") {
          if (merchantResult.value.ok) {
            const payload = (await merchantResult.value.json()) as GenericRecord;
            setMerchantRecord(payload);
          } else {
            let parsedError: unknown = null;
            try {
              parsedError = await merchantResult.value.json();
            } catch {
              parsedError = null;
            }
            setMerchantError(normalizeApiError(parsedError, "Merchant record not found."));
          }
        } else {
          setMerchantError("Failed to reach merchant endpoint.");
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Failed to load investigation data.");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadInvestigationData();
    return () => controller.abort();
  }, [id]);

  const bankStatus = useMemo(() => getNestedStatus(ledgerRecord), [ledgerRecord]);
  const merchantStatus = useMemo(() => getNestedStatus(merchantRecord), [merchantRecord]);

  const discrepancy = useMemo(() => {
    if (!bankStatus || !merchantStatus) {
      return null;
    }

    const left = bankStatus.toLowerCase();
    const right = merchantStatus.toLowerCase();

    if (left === right) {
      return null;
    }

    return `Bank says ${bankStatus}, Merchant says ${merchantStatus}.`;
  }, [bankStatus, merchantStatus]);

  const complaintText =
    dispute?.agent_reports?.guardian?.summary ??
    dispute?.agent_reports?.summary ??
    "No complaint text available in agent reports.";

  const investigationSummary =
    discrepancy ??
    "Triangulation is still in progress. Final decision summary will be generated once all validations are complete.";

  return (
    <AppShell>
      <div className="px-4 md:px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <Link
              to="/dashboard"
              className="h-8 w-8 grid place-items-center rounded-lg border border-border/60 hover:bg-accent/50"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <div className="text-xs text-muted-foreground font-mono">Case ID {id}</div>
              <h1 className="text-2xl font-semibold tracking-tight">Dispute Triangulation</h1>
            </div>
          </div>
          <div className="text-xs text-muted-foreground font-mono">
            Status: {safeString(dispute?.status)}
          </div>
        </div>

        {loading ? (
          <div className="glass rounded-2xl p-10 mt-6 text-center text-sm text-muted-foreground">
            Loading dispute details...
          </div>
        ) : error ? (
          <div className="glass rounded-2xl p-10 mt-6 text-center text-sm text-destructive">
            {error}
          </div>
        ) : (
          <>
            {discrepancy && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass rounded-2xl p-4 mt-6 border border-[oklch(0.82_0.16_80)]/40 bg-[oklch(0.82_0.16_80)]/10"
              >
                <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-[oklch(0.82_0.16_80)]">
                  <AlertTriangle className="h-3.5 w-3.5" /> Discrepancy Detected
                </div>
                <p className="mt-1 text-sm text-foreground/90">{discrepancy}</p>
              </motion.div>
            )}

            <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
              <ColumnCard
                icon={<User className="h-4 w-4" />}
                title="Customer (Claims)"
                subtitle="Original complaint and provided metadata"
              >
                <FieldRow k="Email" v={safeString(dispute?.customer_info?.email)} masked={piiMasked} />
                <FieldRow k="Order ID" v={safeString(dispute?.customer_info?.order_id)} masked={piiMasked} />
                <FieldRow k="Issue Type" v={safeString(dispute?.customer_info?.issue_type)} masked={piiMasked} />
                <FieldRow k="Platform" v={safeString(dispute?.customer_info?.platform)} masked={piiMasked} />
                <FieldRow k="Amount" v={safeCurrency(dispute?.customer_info?.amount)} masked={piiMasked} />
                <FieldRow k="Evidence URL" v={safeString(dispute?.customer_info?.evidence_url)} masked={piiMasked} />
                <div className="mt-4 rounded-xl border border-border/60 p-3 bg-background/30">
                  <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    Complaint Text
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-foreground/90">
                    {maskPII(complaintText, piiMasked)}
                  </p>
                </div>
              </ColumnCard>

              <ColumnCard
                icon={<CreditCard className="h-4 w-4" />}
                title="Company (Transactions)"
                subtitle="Digital Twin ledger response"
              >
                {ledgerError ? (
                  <InlineError text={ledgerError} />
                ) : ledgerRecord ? (
                  <JsonBlock data={ledgerRecord} masked={piiMasked} />
                ) : (
                  <EmptyState text="No bank ledger data returned." />
                )}
              </ColumnCard>

              <ColumnCard
                icon={<Building2 className="h-4 w-4" />}
                title="Merchant (Operations)"
                subtitle="Third-party merchant record"
              >
                {merchantError ? (
                  <InlineError text={merchantError} />
                ) : merchantRecord ? (
                  <JsonBlock data={merchantRecord} masked={piiMasked} />
                ) : (
                  <EmptyState text="No merchant data returned." />
                )}
              </ColumnCard>
            </div>

            <InvestigationResultCard
              status={safeString(dispute?.status)}
              summary={investigationSummary}
            />
          </>
        )}
      </div>
    </AppShell>
  );
}

function ColumnCard({
  icon,
  title,
  subtitle,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center gap-2 text-xs text-mint">
        {icon}
        <span className="uppercase tracking-[0.14em]">{title}</span>
      </div>
      <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>
      <div className="mt-4">
        <ExpandableContent>{children}</ExpandableContent>
      </div>
    </div>
  );
}

function ExpandableContent({ children }: { children: React.ReactNode }) {
  const [expanded, setExpanded] = useState(false);
  const [isOverflowing, setIsOverflowing] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const maxHeight = 320;

  useEffect(() => {
    const element = contentRef.current;
    if (!element) return;

    const checkOverflow = () => {
      const hasOverflow = element.scrollHeight > maxHeight;
      setIsOverflowing(hasOverflow);
      if (!hasOverflow) {
        setExpanded(false);
      }
    };

    checkOverflow();

    window.addEventListener("resize", checkOverflow);
    return () => window.removeEventListener("resize", checkOverflow);
  }, [children]);

  return (
    <div>
      <div
        ref={contentRef}
        className={cn(
          "space-y-2 transition-[max-height] duration-200",
          isOverflowing && !expanded ? "max-h-[320px] overflow-hidden" : "max-h-none",
        )}
      >
        {children}
      </div>

      {isOverflowing && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="rounded-lg border border-border/60 px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent/40"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        </div>
      )}
    </div>
  );
}

function FieldRow({ k, v, masked }: { k: string; v: string; masked: boolean }) {
  const displayValue = maskSensitiveValue(k, v, masked);

  return (
    <div className="rounded-lg border border-border/60 p-2.5 bg-background/30">
      <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{k}</div>
      <div
        className={cn(
          "mt-0.5 text-sm break-all",
          displayValue === "N/A" ? "text-muted-foreground" : "text-foreground",
        )}
      >
        {displayValue}
      </div>
    </div>
  );
}

function InlineError({ text }: { text: string }) {
  return <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{text}</div>;
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-lg border border-border/60 bg-background/30 p-3 text-sm text-muted-foreground">{text}</div>;
}

function JsonBlock({ data, masked }: { data: GenericRecord; masked: boolean }) {
  const entries = Object.entries(data);

  if (entries.length === 0) {
    return <EmptyState text="No fields available." />;
  }

  return (
    <div className="space-y-2">
      {entries.map(([key, value]) => {
        const displayValue =
          value && typeof value === "object"
            ? JSON.stringify(value, null, 2)
            : typeof value === "string"
              ? value
              : String(value);
        const maskedValue = maskSensitiveValue(key, displayValue, masked);

        return (
          <div key={key} className="rounded-lg border border-border/60 p-2.5 bg-background/30">
            <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{key}</div>
            <pre className="mt-1 text-xs whitespace-pre-wrap break-all text-foreground/90">{maskedValue}</pre>
          </div>
        );
      })}
    </div>
  );
}

function InvestigationResultCard({ status, summary }: { status: string; summary: string }) {
  const normalized = status.toLowerCase();
  const isResolved = ["resolved", "closed", "complete", "completed"].some((value) => normalized.includes(value));

  return (
    <div className="glass rounded-2xl p-5 mt-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-sm uppercase tracking-[0.14em] text-mint">Investigation Result</h2>
        <div
          className={cn(
            "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium",
            isResolved
              ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-300"
              : "border-[oklch(0.82_0.16_80)]/40 bg-[oklch(0.82_0.16_80)]/10 text-[oklch(0.92_0.11_95)]",
          )}
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              isResolved ? "bg-emerald-300" : "bg-[oklch(0.82_0.16_80)] animate-pulse",
            )}
          />
          {isResolved ? "Resolved" : safeString(status)}
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-border/60 bg-background/30 p-4">
        <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Result Summary</div>
        <p className="mt-2 text-sm leading-relaxed text-foreground/90">{summary}</p>
      </div>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-border/60 bg-background/30 px-3 py-2.5 text-sm font-medium hover:bg-accent/50 transition-colors"
        >
          <Download className="h-4 w-4" />
          Download Report
        </button>
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-electric/40 bg-electric/10 px-3 py-2.5 text-sm font-medium text-electric hover:bg-electric/15 transition-colors"
        >
          <Send className="h-4 w-4" />
          Send Report
        </button>
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-400/40 bg-emerald-400/10 px-3 py-2.5 text-sm font-medium text-emerald-300 hover:bg-emerald-400/15 transition-colors"
        >
          <CheckCircle2 className="h-4 w-4" />
          Close Case
        </button>
      </div>
    </div>
  );
}
