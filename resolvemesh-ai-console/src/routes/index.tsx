import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Filter, Sparkles, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { DisputeCard } from "@/components/DisputeCard";
import { disputes } from "@/lib/disputes";

export const Route = createFileRoute("/")({
  component: Index,
});

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

function Index() {
  const open = disputes.filter((d) => d.status !== "Resolved").length;
  const flagged = disputes.filter((d) => d.status === "Flagged").length;
  const avgConfidence = Math.round(
    disputes.reduce((s, d) => s + d.confidence, 0) / disputes.length,
  );

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
            { label: "Open Cases", value: String(open), delta: "+2 today", tone: "mint" as const },
            {
              label: "Flagged · Critical",
              value: String(flagged),
              delta: "ATO cluster",
              tone: "warning" as const,
            },
            {
              label: "Avg AI Confidence",
              value: `${avgConfidence}%`,
              delta: "+4.1%",
              tone: "electric" as const,
            },
            { label: "SLA Compliance", value: "99.4%", delta: "30d", tone: "mint" as const },
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
          <h2 className="text-lg font-semibold tracking-tight">Pending disputes</h2>
          <button className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground border border-border/60 rounded-lg px-2.5 py-1.5">
            <Filter className="h-3.5 w-3.5" />
            All channels
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {disputes.map((d, i) => (
            <DisputeCard key={d.id} dispute={d} index={i} />
          ))}
        </div>
      </div>
    </AppShell>
  );
}
