import { Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowUpRight, Clock, Sparkles, Tag } from "lucide-react";
import type { Dispute } from "@/lib/disputes";
import { StatusBadge, RiskBadge } from "./StatusBadge";

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function DisputeCard({ dispute, index }: { dispute: Dispute; index: number }) {
  const isProcessing = dispute.status === "Investigating";
  const caseNumber = index + 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
    >
      <Link
        to="/disputes/$id"
        params={{ id: dispute.id }}
        className="group block glass rounded-2xl p-5 transition-all hover:border-mint/30 hover:-translate-y-0.5 hover:shadow-[0_24px_60px_-30px_oklch(0.86_0.19_165/0.5)]"
      >
        <div className="flex items-start gap-4">
          <div className="relative shrink-0">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-electric/30 to-mint/30 border border-border/60 grid place-items-center font-mono text-xs text-foreground/90">
              {dispute.customer
                .split(" ")
                .map((n) => n[0])
                .join("")}
            </div>
            {isProcessing && (
              <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-mint animate-pulse-ring" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-[11px] text-muted-foreground">
                Case #{caseNumber}
              </span>
              <span className="text-muted-foreground/50">·</span>
              <span className="inline-flex items-center gap-1 text-[11px] text-electric">
                <Tag className="h-3 w-3" />
                {dispute.category}
              </span>
              <span className="text-muted-foreground/50">·</span>
              <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                <Clock className="h-3 w-3" />
                {timeAgo(dispute.openedAt)}
              </span>
            </div>

            <div className="mt-1 flex items-baseline gap-3 flex-wrap">
              <h3 className="text-base font-semibold tracking-tight text-foreground">
                {dispute.customer}
              </h3>
              <span className="text-sm text-muted-foreground truncate">
                {dispute.reason}
              </span>
            </div>

            <p className="mt-1 text-xs text-muted-foreground/80 truncate">
              {dispute.merchant} · card ••{dispute.cardLast4}
            </p>

            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <StatusBadge status={dispute.status} pulse />
              <RiskBadge risk={dispute.risk} />
              <div className="ml-auto flex items-center gap-3">
                <span className="inline-flex items-center gap-1 rounded-md border border-mint/30 bg-mint/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-mint">
                  <Sparkles className="h-3 w-3" />
                  Refund{" "}
                  <span className="font-mono tabular-nums normal-case tracking-normal">
                    {new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: dispute.currency,
                      maximumFractionDigits: 0,
                    }).format(dispute.suggestedRefund)}
                  </span>
                </span>
                <div className="text-right">
                  <div className="text-base font-semibold tabular-nums">
                    {new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: dispute.currency,
                      maximumFractionDigits: 2,
                    }).format(dispute.amount)}
                  </div>
                  <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    AI confidence{" "}
                    <span className="text-mint font-mono">{dispute.confidence}%</span>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-mint transition-colors" />
              </div>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
