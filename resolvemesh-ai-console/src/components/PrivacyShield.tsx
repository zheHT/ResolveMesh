import { motion } from "framer-motion";
import { Eye, EyeOff, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

export function PrivacyShield({
  masked,
  onToggle,
}: {
  masked: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={cn(
        "group flex items-center gap-3 rounded-xl border px-3 py-2 transition-all",
        masked
          ? "border-mint/40 bg-mint/10 hover:bg-mint/15"
          : "border-border/60 bg-background/40 hover:border-border",
      )}
    >
      <Shield
        className={cn("h-4 w-4 transition-colors", masked ? "text-mint" : "text-muted-foreground")}
      />
      <div className="flex flex-col items-start leading-tight">
        <span className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          Privacy Shield
        </span>
        <span className={cn("text-xs font-medium", masked ? "text-mint" : "text-foreground")}>
          {masked ? "PII Masked" : "PII Visible"}
        </span>
      </div>
      <div
        className={cn(
          "ml-2 relative h-5 w-9 rounded-full transition-colors",
          masked ? "bg-mint" : "bg-muted",
        )}
      >
        <motion.div
          layout
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className={cn(
            "absolute top-0.5 h-4 w-4 rounded-full bg-background grid place-items-center shadow",
            masked ? "right-0.5" : "left-0.5",
          )}
        >
          {masked ? (
            <EyeOff className="h-2.5 w-2.5 text-mint" />
          ) : (
            <Eye className="h-2.5 w-2.5 text-muted-foreground" />
          )}
        </motion.div>
      </div>
    </button>
  );
}
