import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity } from "lucide-react";

type LogLine = {
  t: number; // seconds offset
  agent: string;
  agentColor: "mint" | "electric" | "warning" | "muted";
  message: string;
};

const SCRIPT: LogLine[] = [
  { t: 0.1, agent: "Mesh", agentColor: "muted", message: "Session bound · case context loaded" },
  {
    t: 0.5,
    agent: "Advocate Agent",
    agentColor: "electric",
    message: "Analyzing intent from cardholder narrative…",
  },
  {
    t: 1.1,
    agent: "Forensics Agent",
    agentColor: "mint",
    message: "Cross-referencing 14d device fingerprint history",
  },
  {
    t: 1.7,
    agent: "Forensics Agent",
    agentColor: "mint",
    message: "Match: device_id=fp_8a21b · 12 prior successful auths",
  },
  {
    t: 2.2,
    agent: "Risk Engine",
    agentColor: "warning",
    message: "Geo-velocity check · OK (Δ 4.1km / 36h)",
  },
  {
    t: 2.9,
    agent: "Policy Agent",
    agentColor: "electric",
    message: "Reg E §1005.11 — 60-day window confirmed",
  },
  {
    t: 3.6,
    agent: "Advocate Agent",
    agentColor: "electric",
    message: "Drafting verdict + customer-ready response…",
  },
  {
    t: 4.4,
    agent: "Integrity Agent",
    agentColor: "mint",
    message: "Self-audit pass · 0 hallucinations · 4 citations",
  },
  {
    t: 5.0,
    agent: "Mesh",
    agentColor: "muted",
    message: "Verdict ready · awaiting human verification",
  },
];

const colorMap = {
  mint: "text-mint",
  electric: "text-electric",
  warning: "text-[oklch(0.82_0.16_80)]",
  muted: "text-muted-foreground",
};

export function AuditFeed() {
  const [shown, setShown] = useState<LogLine[]>([]);
  const [done, setDone] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setShown([]);
    setDone(false);
    const timers: number[] = [];
    SCRIPT.forEach((line, i) => {
      const id = window.setTimeout(() => {
        setShown((s) => [...s, line]);
        if (i === SCRIPT.length - 1) setDone(true);
      }, line.t * 600);
      timers.push(id);
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [shown.length]);

  return (
    <div className="glass rounded-2xl flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/60">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Activity className="h-4 w-4 text-mint" />
            {!done && (
              <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-mint animate-pulse" />
            )}
          </div>
          <span className="text-xs font-semibold tracking-tight">Live AI Audit Feed</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono uppercase tracking-[0.14em]">
          <span className={done ? "text-mint" : "text-electric"}>
            {done ? "● COMPLETE" : "● STREAMING"}
          </span>
        </div>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-[11.5px] leading-relaxed space-y-1.5 min-h-[280px] max-h-[420px]"
      >
        <AnimatePresence>
          {shown.map((line, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25 }}
              className="flex gap-2"
            >
              <span className="text-muted-foreground/60 shrink-0">
                [{line.t.toFixed(1)}s]
              </span>
              <span className={`${colorMap[line.agentColor]} shrink-0 font-semibold`}>
                {line.agent}:
              </span>
              <span className="text-foreground/85">{line.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {!done && (
          <div className="flex gap-2 text-muted-foreground/70">
            <span className="caret" />
          </div>
        )}
      </div>
    </div>
  );
}
