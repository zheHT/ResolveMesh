import { motion } from "framer-motion";

export function ConfidenceGauge({
  value,
  label = "Verdict Confidence",
}: {
  value: number;
  label?: string;
}) {
  const size = 168;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const verdict =
    value >= 90 ? "Decisive" : value >= 75 ? "High" : value >= 60 ? "Moderate" : "Inconclusive";

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <defs>
            <linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="oklch(0.72 0.18 245)" />
              <stop offset="100%" stopColor="oklch(0.86 0.19 165)" />
            </linearGradient>
          </defs>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="oklch(1 0 0 / 0.06)"
            strokeWidth={stroke}
            fill="none"
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="url(#gauge-grad)"
            strokeWidth={stroke}
            strokeLinecap="round"
            fill="none"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            style={{
              filter: "drop-shadow(0 0 10px oklch(0.86 0.19 165 / 0.5))",
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-4xl font-semibold tabular-nums tracking-tight"
          >
            {value}
            <span className="text-base text-muted-foreground">%</span>
          </motion.span>
          <span className="mt-0.5 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {verdict}
          </span>
        </div>
      </div>
      <span className="mt-3 text-xs text-muted-foreground">{label}</span>
    </div>
  );
}
