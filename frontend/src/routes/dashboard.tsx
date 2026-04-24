import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Sparkles, TrendingUp } from "lucide-react";
import { useState, useEffect } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { getAuthUser } from "@/lib/auth";
import { maskEmail } from "@/lib/disputes";
import {
  addCaseNotification,
  getNotificationsVisible,
  getPIIMaskEnabled,
  PII_MASK_CHANGED_EVENT,
} from "@/lib/ui-state";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard")({
  component: Index,
});

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type DashboardDispute = {
  id: string;
  status: string;
  created_at?: string;
  customer_info?: {
    order_id?: string;
    email?: string;
    amount?: number;
    issue_type?: string;
    platform?: string;
    account_id?: string;
    evidence_url?: string;
  };
  agent_reports?: {
    guardian?: {
      summary?: string;
    };
    summary?: string;
  };
};

function Stat({
  label,
  value,
  delta,
  tone = "mint",
}: {
  label: string;
  value: string;
  delta?: string;
  tone?: "mint" | "electric" | "warning";
}) {
  const toneClass =
    tone === "mint" ? "text-mint" : tone === "electric" ? "text-electric" : "text-[oklch(0.82_0.16_80)]";
  return (
    <div className="glass rounded-2xl p-5">
      <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className={`text-3xl font-semibold tabular-nums tracking-tight ${toneClass}`}>
          {value}
        </span>
        {delta && (
          <span className="text-xs text-muted-foreground inline-flex items-center gap-1">
            <TrendingUp className="h-3 w-3" /> {delta}
          </span>
        )}
      </div>
    </div>
  );
}

function statusTone(status: string) {
  const normalized = status.toUpperCase();
  if (normalized.includes("RESOLVED")) return "mint";
  if (normalized.includes("FLAG") || normalized.includes("FRAUD")) return "warning";
  return "electric";
}

function DashboardCard({
  dispute,
  index,
  piiMasked,
}: {
  dispute: DashboardDispute;
  index: number;
  piiMasked: boolean;
}) {
  const tone = statusTone(dispute.status);
  const toneClass =
    tone === "mint" ? "text-mint" : tone === "electric" ? "text-electric" : "text-[oklch(0.82_0.16_80)]";
  const summary = dispute.agent_reports?.guardian?.summary ?? dispute.agent_reports?.summary;
  const amount = dispute.customer_info?.amount;
  const platform = dispute.customer_info?.platform;
  const issueType = dispute.customer_info?.issue_type;
  const email = dispute.customer_info?.email;
  const safeEmail = email ? maskEmail(email, piiMasked) : null;
  const caseNumber = index + 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04, ease: [0.16, 1, 0.3, 1] }}
      className="glass rounded-2xl"
    >
      <Link
        to="/disputes/$id"
        params={{ id: dispute.id }}
        className="block p-5 transition-colors hover:bg-white/5"
      >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap text-[11px] font-mono text-muted-foreground">
            <span>Case #{caseNumber}</span>
            <span className="text-muted-foreground/40">·</span>
            <span>{platform ?? "database"}</span>
          </div>
          <h3 className="mt-1 text-base font-semibold tracking-tight">Case #{caseNumber}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
            {summary || "No summary available from the database record."}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
            {issueType && <span className="rounded-full border border-border/60 px-2 py-0.5">{issueType}</span>}
            {safeEmail && <span className="rounded-full border border-border/60 px-2 py-0.5">{safeEmail}</span>}
          </div>
        </div>

        <div
          className={cn(
            "shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.12em]",
            tone === "mint"
              ? "border-mint/30 bg-mint/10 text-mint"
              : tone === "warning"
                ? "border-[oklch(0.82_0.16_80)]/30 bg-[oklch(0.82_0.16_80)]/10 text-[oklch(0.82_0.16_80)]"
                : "border-electric/30 bg-electric/10 text-electric",
          )}
        >
          {dispute.status}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3 border-t border-border/60 pt-4">
        <div className={cn("text-xs uppercase tracking-[0.18em]", toneClass)}>
          Live from Supabase
        </div>
        <div className="text-[11px] text-muted-foreground">
          {typeof amount === "number"
            ? new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 2,
              }).format(amount)
            : "Database row loaded into dashboard"}
        </div>
      </div>
      </Link>
    </motion.div>
  );
}

function Index() {
  const navigate = useNavigate();
  const [disputes, setDisputes] = useState<DashboardDispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [piiMasked, setPiiMasked] = useState(true);

  useEffect(() => {
    if (!getAuthUser()) {
      navigate({ to: "/login", replace: true });
    }
  }, [navigate]);

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
    let primed = false;
    let knownDisputeIds = new Set<string>();

    async function loadDisputes(showSpinner: boolean) {
      try {
        if (showSpinner) {
          setLoading(true);
        }
        setError(null);

        const response = await fetch(`${API_BASE_URL}/api/disputes`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          let errorMessage = "Failed to load disputes from the database.";
          try {
            const errorPayload = (await response.json()) as { detail?: string };
            if (typeof errorPayload?.detail === "string" && errorPayload.detail.trim()) {
              errorMessage = errorPayload.detail;
            }
          } catch {
            // Ignore JSON parse errors and keep fallback message.
          }
          throw new Error(errorMessage);
        }

        const payload = await response.json();
        if (!Array.isArray(payload)) {
          throw new Error("Disputes API returned an invalid payload.");
        }

        const activeDisputes = payload.filter(
          (dispute) => dispute.status.toUpperCase() !== "RESOLVED",
        );

        const currentIds = new Set<string>(
          activeDisputes
            .map((dispute) => dispute.id)
            .filter((id): id is string => typeof id === "string" && id.trim().length > 0),
        );

        if (!primed) {
          primed = true;
          knownDisputeIds = currentIds;
        } else {
          const newDisputes = activeDisputes.filter(
            (dispute) => !knownDisputeIds.has(dispute.id),
          );

          if (getNotificationsVisible()) {
            newDisputes.forEach((dispute) => {
              addCaseNotification({
                disputeId: dispute.id,
                status: dispute.status,
                createdAt: dispute.created_at,
              });
            });
          }

          knownDisputeIds = currentIds;
        }

        setDisputes(activeDisputes);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Failed to load disputes.");
      } finally {
        if (!controller.signal.aborted) {
          if (showSpinner) {
            setLoading(false);
          }
        }
      }
    }

    loadDisputes(true);
    const timer = window.setInterval(() => {
      void loadDisputes(false);
    }, 20000);

    const onVisibilityChange = () => {
      if (!document.hidden) {
        void loadDisputes(false);
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      controller.abort();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, []);

  const open = disputes.length;
  const orderedDisputes = [...disputes].sort((left, right) => {
    const leftTime = left.created_at ? Date.parse(left.created_at) : Number.POSITIVE_INFINITY;
    const rightTime = right.created_at ? Date.parse(right.created_at) : Number.POSITIVE_INFINITY;

    if (leftTime !== rightTime) {
      return leftTime - rightTime;
    }

    return 0;
  });
  const flagged = disputes.filter((d) => {
    const status = d.status.toUpperCase();
    return status.includes("FLAG") || status.includes("FRAUD");
  }).length;
  const awaiting = disputes.filter((d) => {
    const status = d.status.toUpperCase();
    return status.includes("PENDING") || status.includes("BRIEF") || status.includes("REVIEW");
  }).length;

  if (!getAuthUser()) {
    return null;
  }

  return (
    <AppShell>
      <div className="px-4 md:px-8 py-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="flex items-center gap-2 text-xs text-mint">
            <Sparkles className="h-3.5 w-3.5" />
            <span className="uppercase tracking-[0.18em]">Inbox · Live</span>
          </div>
          <h1 className="mt-3 text-4xl md:text-5xl font-semibold tracking-[-0.02em] leading-[1.05]">
            Disputes the <span className="gradient-text">Mesh</span> can't decide alone.
          </h1>
          <p className="mt-3 text-sm md:text-base text-muted-foreground max-w-2xl">
            Six cases routed to your queue. Every verdict ships with a verifiable audit trail and
            a one-click reversal.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8">
          {[
            { label: "Open Cases", value: String(open), delta: "+ live", tone: "mint" as const },
            {
              label: "Flagged · Critical",
              value: String(flagged),
              delta: "database sync",
              tone: "warning" as const,
            },
            {
              label: "Awaiting Review",
              value: String(awaiting),
              delta: "non-resolved",
              tone: "warning" as const,
            },
            {
              label: "Database Rows",
              value: String(disputes.length),
              delta: "Supabase",
              tone: "electric" as const,
            },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.05, duration: 0.4 }}
            >
              <Stat {...s} />
            </motion.div>
          ))}
        </div>

        <div className="mt-10 flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight">
            Pending disputes
            <span className="ml-2 text-xs text-muted-foreground font-normal">{disputes.length}</span>
          </h2>
        </div>

        <div className="mt-4 space-y-3">
          {loading ? (
            <div className="glass rounded-2xl p-10 text-center text-sm text-muted-foreground">
              Loading disputes from Supabase...
            </div>
          ) : error ? (
            <div className="glass rounded-2xl p-10 text-center text-sm text-destructive">
              {error}
            </div>
          ) : disputes.length === 0 ? (
            <div className="glass rounded-2xl p-10 text-center text-sm text-muted-foreground">
              No active disputes were returned from the database.
            </div>
          ) : (
            orderedDisputes.map((dispute, index) => (
              <DashboardCard key={dispute.id} dispute={dispute} index={index} piiMasked={piiMasked} />
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}
