import { motion } from "framer-motion";
import { pct } from "../lib/format";

/** Cache hit-rate donut. Custom SVG so it matches the design system exactly. */
export function Donut({ rate, hits, total }: { rate: number; hits: number; total: number }) {
  const size = 168;
  const stroke = 16;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = Math.max(0, Math.min(1, rate)) * c;

  return (
    <div className="donut">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Cache hit rate ${pct(rate)}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--chart-b)"
          strokeWidth={stroke}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c - dash }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: "drop-shadow(0 0 8px color-mix(in oklch, var(--chart-b) 50%, transparent))" }}
        />
      </svg>
      <div className="donut__center">
        <div className="donut__pct mono">{pct(rate)}</div>
        <div className="donut__cap">
          {hits} / {total} served from cache
        </div>
      </div>
    </div>
  );
}
