import { createFileRoute } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { Filter, Sparkles, TrendingUp, Check, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { DisputeCard } from "@/components/DisputeCard";
import { getAuthUser } from "@/lib/auth";
import { disputes, type Dispute } from "@/lib/disputes";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard")({
  component: Index,
});

const CHANNELS = ["All channels", "Visa", "Mastercard", "Amex", "ACH"] as const;
type ChannelFilter = (typeof CHANNELS)[number];

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
  const navigate = useNavigate();
  const [channel, setChannel] = useState<ChannelFilter>("All channels");
  const [open_, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!getAuthUser()) {
      navigate({ to: "/login", replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    if (!open_) return;
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open_]);

  const filtered: Dispute[] =
    channel === "All channels" ? disputes : disputes.filter((d) => d.channel === channel);

  const open = disputes.filter((d) => d.status !== "Resolved").length;
  const flagged = disputes.filter((d) => d.status === "Flagged").length;
  const avgConfidence = Math.round(
    disputes.reduce((s, d) => s + d.confidence, 0) / disputes.length,
  );

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
          <h2 className="text-lg font-semibold tracking-tight">
            Pending disputes
            <span className="ml-2 text-xs text-muted-foreground font-normal">
              {filtered.length} of {disputes.length}
            </span>
          </h2>
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setOpen((o) => !o)}
              className={cn(
                "inline-flex items-center gap-2 text-xs rounded-lg px-2.5 py-1.5 border transition-colors",
                channel !== "All channels"
                  ? "border-mint/40 bg-mint/10 text-mint"
                  : "border-border/60 text-muted-foreground hover:text-foreground",
              )}
            >
              <Filter className="h-3.5 w-3.5" />
              {channel}
              <ChevronDown
                className={cn("h-3 w-3 transition-transform", open_ && "rotate-180")}
              />
            </button>
            <AnimatePresence>
              {open_ && (
                <motion.div
                  initial={{ opacity: 0, y: -4, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.97 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-48 rounded-xl glass-strong p-1 z-20 shadow-elegant"
                >
                  {CHANNELS.map((c) => {
                    const count =
                      c === "All channels"
                        ? disputes.length
                        : disputes.filter((d) => d.channel === c).length;
                    const active = channel === c;
                    return (
                      <button
                        key={c}
                        onClick={() => {
                          setChannel(c);
                          setOpen(false);
                        }}
                        className={cn(
                          "w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs transition-colors",
                          active
                            ? "bg-mint/15 text-mint"
                            : "text-muted-foreground hover:text-foreground hover:bg-accent/40",
                        )}
                      >
                        <Check
                          className={cn("h-3.5 w-3.5", active ? "opacity-100" : "opacity-0")}
                        />
                        <span className="flex-1 text-left">{c}</span>
                        <span className="text-[10px] text-muted-foreground tabular-nums">
                          {count}
                        </span>
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {filtered.length === 0 ? (
            <div className="glass rounded-2xl p-10 text-center text-sm text-muted-foreground">
              No disputes on the <span className="text-foreground">{channel}</span> channel.
            </div>
          ) : (
            filtered.map((d, i) => <DisputeCard key={d.id} dispute={d} index={i} />)
          )}
        </div>
      </div>
    </AppShell>
  );
}
