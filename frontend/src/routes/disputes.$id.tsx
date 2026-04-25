import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowLeft, Building2, CheckCircle2, CreditCard, Download, Send, User, Activity } from "lucide-react";
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

type Log = {
  id?: string;
  event_name: string;
  visibility: string;
  payload?: GenericRecord;
  created_at?: string;
};

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

function normalizeOrderId(value: unknown) {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }

  return null;
}

function extractOrderId(record: GenericRecord | null) {
  if (!record) return null;

  const directOrderId = normalizeOrderId(record.order_id);
  if (directOrderId) {
    return directOrderId;
  }

  const ledger = record.ledger_data;
  if (ledger && typeof ledger === "object" && !Array.isArray(ledger)) {
    const ledgerOrderId = normalizeOrderId((ledger as GenericRecord).order_id);
    if (ledgerOrderId) {
      return ledgerOrderId;
    }
  }

  const merchantData = record.merchant_data;
  if (merchantData && typeof merchantData === "object" && !Array.isArray(merchantData)) {
    const merchantOrderId = normalizeOrderId((merchantData as GenericRecord).order_id);
    if (merchantOrderId) {
      return merchantOrderId;
    }
  }

  const customerInfo = record.customer_info;
  if (customerInfo && typeof customerInfo === "object" && !Array.isArray(customerInfo)) {
    const customerOrderId = normalizeOrderId((customerInfo as GenericRecord).order_id);
    if (customerOrderId) {
      return customerOrderId;
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
  const [logs, setLogs] = useState<Log[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const logsIntervalRef = useRef<NodeJS.Timeout | null>(null);

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

        const expectedOrderId = normalizeOrderId(disputePayload.customer_info?.order_id);
        if (!expectedOrderId) {
          setLedgerError("No order_id found in dispute payload.");
          setMerchantError("No order_id found in dispute payload.");
          return;
        }

        const [ledgerResult, merchantResult] = await Promise.allSettled([
          fetch(`${API_BASE_URL}/api/ledger/${encodeURIComponent(expectedOrderId)}`, {
            signal: controller.signal,
          }),
          fetch(`${API_BASE_URL}/api/merchant/${encodeURIComponent(expectedOrderId)}`, {
            signal: controller.signal,
          }),
        ]);

        if (ledgerResult.status === "fulfilled") {
          if (ledgerResult.value.ok) {
            const payload = (await ledgerResult.value.json()) as GenericRecord;
            const ledgerOrderId = extractOrderId(payload);
            if (!ledgerOrderId) {
              setLedgerError("Company transaction is missing order_id; linkage check failed.");
            } else if (ledgerOrderId !== expectedOrderId) {
              setLedgerError(
                `Company order_id mismatch. Expected ${expectedOrderId}, got ${ledgerOrderId}.`,
              );
            } else {
              setLedgerRecord(payload);
            }
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
            const merchantOrderId = extractOrderId(payload);
            if (!merchantOrderId) {
              setMerchantError("Merchant record is missing order_id; linkage check failed.");
            } else if (merchantOrderId !== expectedOrderId) {
              setMerchantError(
                `Merchant order_id mismatch. Expected ${expectedOrderId}, got ${merchantOrderId}.`,
              );
            } else {
              setMerchantRecord(payload);
            }
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

  // Fetch logs with live polling
  useEffect(() => {
    async function fetchLogs() {
      try {
        setLogsLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/logs/${id}`);
        if (response.ok) {
          const data = (await response.json()) as Log[];
          setLogs(data || []);
        }
      } catch (err) {
        console.error("Failed to fetch logs:", err);
      } finally {
        setLogsLoading(false);
      }
    }

    fetchLogs();

    // Poll for new logs every 3 seconds
    logsIntervalRef.current = setInterval(() => {
      fetchLogs();
    }, 3000);

    return () => {
      if (logsIntervalRef.current) {
        clearInterval(logsIntervalRef.current);
      }
    };
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

            <LogsCard logs={logs} isLoading={logsLoading} />

            <InvestigationResultCard
              status={safeString(dispute?.status)}
              summary={investigationSummary}
              caseId={id}
            />
          </>
        )}
      </div>
    </AppShell>
  );
}

function formatLogTime(dateString: string | undefined): string {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  } catch {
    return "N/A";
  }
}

function getLogIcon(eventName: string): React.ReactNode {
  const name = eventName.toLowerCase();
  if (name.includes("guardian") || name.includes("redaction")) {
    return <Activity className="h-3.5 w-3.5 text-cyan-400" />;
  }
  if (name.includes("upload") || name.includes("report")) {
    return <Activity className="h-3.5 w-3.5 text-emerald-400" />;
  }
  if (name.includes("status")) {
    return <Activity className="h-3.5 w-3.5 text-blue-400" />;
  }
  if (name.includes("pdf")) {
    return <Activity className="h-3.5 w-3.5 text-purple-400" />;
  }
  return <Activity className="h-3.5 w-3.5 text-muted-foreground" />;
}

function LogsCard({ logs, isLoading }: { logs: Log[]; isLoading: boolean }) {
  return (
    <div className="glass rounded-2xl p-5 mt-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <h2 className="text-sm uppercase tracking-[0.14em] text-mint">Activity Feed</h2>
          {isLoading && <div className="h-2 w-2 rounded-full bg-mint animate-pulse" />}
        </div>
        <div className="text-xs text-muted-foreground">{logs.length} event{logs.length !== 1 ? "s" : ""}</div>
      </div>

      <div className="mt-4">
        {logs.length === 0 ? (
          <div className="rounded-xl border border-border/60 bg-background/30 p-4 text-sm text-muted-foreground text-center">
            No activity yet. Updates will appear here as the investigation progresses.
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {logs.map((log, index) => {
              const payload = log.payload as GenericRecord | undefined;
              const message =
                (payload?.message as string) ||
                (payload?.event as string) ||
                log.event_name.replace(/_/g, " ");

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="rounded-lg border border-border/40 bg-background/50 p-3 hover:border-border/60 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {getLogIcon(log.event_name)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs uppercase tracking-[0.1em] font-medium text-foreground/80">
                          {log.event_name.replace(/_/g, " ")}
                        </span>
                        {log.visibility && (
                          <span
                            className={cn(
                              "text-[10px] px-2 py-0.5 rounded-full font-medium",
                              log.visibility === "PUBLIC"
                                ? "bg-cyan-500/20 text-cyan-300"
                                : "bg-muted text-muted-foreground",
                            )}
                          >
                            {log.visibility}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground ml-auto flex-shrink-0">
                          {formatLogTime(log.created_at)}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-foreground/70 break-words">{message}</p>
                      {payload?.dispute_id && (
                        <div className="mt-2 text-xs text-muted-foreground/60 font-mono">
                          ID: {payload.dispute_id}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function InvestigationResultCard({ status, summary, caseId }: { status: string; summary: string; caseId: string }) {
  const normalized = status.toLowerCase();
  const isResolved = ["resolved", "closed", "complete", "completed"].some((value) => normalized.includes(value));
  const [isClosing, setIsClosing] = useState(false);
  const navigate = useNavigate();

  const handleDownloadReport = async () => {
    try {
      const pdfUrl = `https://ztamcvkqxjucvaiziwqs.supabase.co/storage/v1/object/public/investigation-reports/${caseId}/internal.pdf`;
      
      // Create a temporary link and trigger download
      const response = await fetch(pdfUrl);
      if (!response.ok) {
        throw new Error("Failed to download report");
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `investigation-report-${caseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Failed to download report. Please try again.");
    }
  };

  const handleCloseCase = async () => {
    if (!window.confirm("Are you sure you want to close this case? This action cannot be undone.")) {
      return;
    }

    setIsClosing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/disputes/${caseId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to close case");
      }

      // Successfully deleted, navigate back to dashboard
      navigate({ to: "/dashboard" });
    } catch (error) {
      console.error("Close case failed:", error);
      alert(`Failed to close case: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsClosing(false);
    }
  };

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
          onClick={handleDownloadReport}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-border/60 bg-background/30 px-3 py-2.5 text-sm font-medium hover:bg-accent/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="h-4 w-4" />
          Download Report
        </button>
        <button
          type="button"
          disabled
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-electric/40 bg-electric/10 px-3 py-2.5 text-sm font-medium text-electric hover:bg-electric/15 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Coming soon"
        >
          <Send className="h-4 w-4" />
          Send Report
        </button>
        <button
          type="button"
          onClick={handleCloseCase}
          disabled={isClosing}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-400/40 bg-emerald-400/10 px-3 py-2.5 text-sm font-medium text-emerald-300 hover:bg-emerald-400/15 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <CheckCircle2 className="h-4 w-4" />
          {isClosing ? "Closing..." : "Close Case"}
        </button>
      </div>
    </div>
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
