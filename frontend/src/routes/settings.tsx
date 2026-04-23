import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Settings as SettingsIcon } from "lucide-react";
import { AppShell } from "@/components/AppShell";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <AppShell>
      <div className="px-4 md:px-8 py-8 max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-[0.18em]">
            <SettingsIcon className="h-3.5 w-3.5" /> Workspace
          </div>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-0.02em]">Settings</h1>
        </motion.div>

        <div className="mt-8 space-y-4">
          {[
            {
              title: "Mesh autonomy",
              desc: "Allow agents to issue provisional credits ≤ $250 without human review.",
              on: true,
            },
            {
              title: "PII default-mask",
              desc: "Cardholder data is hidden until staff actively unmasks per case.",
              on: true,
            },
            {
              title: "Slack notifications",
              desc: "Ping #disputes-critical for any Critical risk verdict.",
              on: true,
            },
            {
              title: "Sandbox mode",
              desc: "Decisions write to ledger but do not execute on rails.",
              on: false,
            },
          ].map((row) => (
            <div key={row.title} className="glass rounded-2xl p-5 flex items-center gap-4">
              <div className="flex-1">
                <div className="text-sm font-semibold">{row.title}</div>
                <div className="text-xs text-muted-foreground">{row.desc}</div>
              </div>
              <div
                className={`relative h-6 w-11 rounded-full transition-colors ${
                  row.on ? "bg-mint" : "bg-muted"
                }`}
              >
                <div
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-background transition-all ${
                    row.on ? "right-0.5" : "left-0.5"
                  }`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
