import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Settings as SettingsIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import {
  getMeshAutonomyEnabled,
  getNotificationsVisible,
  getPIIMaskEnabled,
  getSandboxModeEnabled,
  PII_MASK_CHANGED_EVENT,
  setMeshAutonomyEnabled,
  setNotificationsVisible,
  setPIIMaskEnabled,
  setSandboxModeEnabled,
  UI_SETTINGS_CHANGED_EVENT,
} from "@/lib/ui-state";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const [meshAutonomy, setMeshAutonomy] = useState(true);
  const [piiMasked, setPiiMasked] = useState(true);
  const [notificationsVisible, setNotificationsVisibleState] = useState(true);
  const [sandboxMode, setSandboxMode] = useState(false);

  useEffect(() => {
    setMeshAutonomy(getMeshAutonomyEnabled());
    setPiiMasked(getPIIMaskEnabled());
    setNotificationsVisibleState(getNotificationsVisible());
    setSandboxMode(getSandboxModeEnabled());

    const syncSettings = () => {
      setMeshAutonomy(getMeshAutonomyEnabled());
      setPiiMasked(getPIIMaskEnabled());
      setNotificationsVisibleState(getNotificationsVisible());
      setSandboxMode(getSandboxModeEnabled());
    };

    window.addEventListener(PII_MASK_CHANGED_EVENT, syncSettings);
    window.addEventListener(UI_SETTINGS_CHANGED_EVENT, syncSettings);
    window.addEventListener("storage", syncSettings);

    return () => {
      window.removeEventListener(PII_MASK_CHANGED_EVENT, syncSettings);
      window.removeEventListener(UI_SETTINGS_CHANGED_EVENT, syncSettings);
      window.removeEventListener("storage", syncSettings);
    };
  }, []);

  const settingsRows = [
    {
      title: "Mesh autonomy",
      desc: "Allow agents to issue provisional credits ≤ $250 without human review.",
      on: meshAutonomy,
      onToggle: () => setMeshAutonomyEnabled(!meshAutonomy),
    },
    {
      title: "PII default-mask",
      desc: "Cardholder data is hidden until staff actively unmasks per case.",
      on: piiMasked,
      onToggle: () => setPIIMaskEnabled(!piiMasked),
    },
    {
      title: "Notification center visibility",
      desc: "Show or hide the top-right notification center for new normal, critical, and spam case (suspected_fraud) uploads.",
      on: notificationsVisible,
      onToggle: () => setNotificationsVisible(!notificationsVisible),
    },
    {
      title: "Sandbox mode",
      desc: "Decisions write to ledger but do not execute on rails.",
      on: sandboxMode,
      onToggle: () => setSandboxModeEnabled(!sandboxMode),
    },
  ] as const;

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
          {settingsRows.map((row) => (
            <div key={row.title} className="glass rounded-2xl p-5 flex items-center gap-4">
              <div className="flex-1">
                <div className="text-sm font-semibold">{row.title}</div>
                <div className="text-xs text-muted-foreground">{row.desc}</div>
              </div>
              <button
                type="button"
                aria-label={`Toggle ${row.title}`}
                aria-checked={row.on}
                role="switch"
                onClick={row.onToggle}
                className={`relative h-6 w-11 rounded-full transition-colors ${
                  row.on ? "bg-mint" : "bg-muted"
                } cursor-pointer`}
              >
                <div
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-background transition-all ${
                    row.on ? "right-0.5" : "left-0.5"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
