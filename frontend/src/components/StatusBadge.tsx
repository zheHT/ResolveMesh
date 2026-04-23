import type { DisputeStatus, RiskLevel } from "@/lib/disputes";
import { cn } from "@/lib/utils";

const statusStyles: Record<DisputeStatus, string> = {
  Investigating:
    "bg-electric/10 text-electric border-electric/30 [&_.dot]:bg-electric",
  Flagged: "bg-destructive/10 text-destructive border-destructive/30 [&_.dot]:bg-destructive",
  "Awaiting Action":
    "bg-warning/10 text-[oklch(0.82_0.16_80)] border-[oklch(0.82_0.16_80)]/30 [&_.dot]:bg-[oklch(0.82_0.16_80)]",
  Resolved: "bg-mint/10 text-mint border-mint/30 [&_.dot]:bg-mint",
};

export function StatusBadge({
  status,
  pulse = false,
}: {
  status: DisputeStatus;
  pulse?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium tracking-tight",
        statusStyles[status],
      )}
    >
      <span
        className={cn(
          "dot h-1.5 w-1.5 rounded-full",
          pulse && status === "Investigating" && "animate-pulse",
        )}
      />
      {status}
    </span>
  );
}

const riskStyles: Record<RiskLevel, string> = {
  Low: "bg-mint/10 text-mint border-mint/25",
  Medium: "bg-[oklch(0.82_0.16_80)]/10 text-[oklch(0.82_0.16_80)] border-[oklch(0.82_0.16_80)]/30",
  High: "bg-[oklch(0.75_0.2_50)]/10 text-[oklch(0.78_0.2_50)] border-[oklch(0.75_0.2_50)]/30",
  Critical: "bg-destructive/10 text-destructive border-destructive/30",
};

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]",
        riskStyles[risk],
      )}
    >
      <span className="font-mono">●</span>
      {risk}
    </span>
  );
}
