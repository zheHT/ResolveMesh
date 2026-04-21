import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ShieldCheck, Activity, Lock, Zap } from "lucide-react";
import { AppShell } from "@/components/AppShell";

export const Route = createFileRoute("/integrity-hub")({
  component: IntegrityHub,
});

const checks = [
  { icon: ShieldCheck, label: "Hallucination rate (7d)", value: "0.04%", ok: true },
  { icon: Activity, label: "Mean verdict latency", value: "412ms", ok: true },
  { icon: Lock, label: "PII redaction coverage", value: "100%", ok: true },
  { icon: Zap, label: "Human override rate", value: "2.1%", ok: true },
];

function IntegrityHub() {
  return (
    <AppShell>
      <div className="px-4 md:px-8 py-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-2 text-xs text-mint uppercase tracking-[0.18em]">
            <ShieldCheck className="h-3.5 w-3.5" /> System Integrity
          </div>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-0.02em]">
            The <span className="gradient-text">Mesh</span> watches itself.
          </h1>
        </motion.div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {checks.map((c, i) => (
            <motion.div
              key={c.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass rounded-2xl p-5"
            >
              <div className="flex items-center justify-between">
                <c.icon className="h-4 w-4 text-mint" />
                <span className="text-[10px] uppercase tracking-[0.14em] text-mint">● Healthy</span>
              </div>
              <div className="mt-4 text-2xl font-semibold tabular-nums">{c.value}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{c.label}</div>
            </motion.div>
          ))}
        </div>

        <div className="mt-8 glass rounded-2xl p-6">
          <h2 className="text-lg font-semibold tracking-tight">Agent Health</h2>
          <div className="mt-4 space-y-3">
            {["Advocate", "Forensics", "Risk Engine", "Policy", "Integrity", "Mesh Router"].map(
              (a, i) => (
                <div key={a} className="flex items-center gap-3">
                  <div className="w-32 text-sm">{a}</div>
                  <div className="flex-1 h-2 rounded-full bg-muted/50 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${88 + (i % 4) * 3}%` }}
                      transition={{ duration: 1, delay: 0.1 * i }}
                      className="h-full rounded-full bg-gradient-to-r from-electric to-mint"
                    />
                  </div>
                  <div className="w-16 text-right text-xs font-mono text-mint">
                    {88 + (i % 4) * 3}%
                  </div>
                </div>
              ),
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
