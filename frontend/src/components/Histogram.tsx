import { motion } from "framer-motion";
import type { HistogramBin } from "../types";

/** Vertical bar chart for the latency distribution (ms buckets). */
export function Histogram({ bins, color = "var(--info)" }: { bins: HistogramBin[]; color?: string }) {
  const max = Math.max(...bins.map((b) => b.count), 1);
  const total = bins.reduce((s, b) => s + b.count, 0);
  if (total === 0) return <div className="empty">No latency samples in this range.</div>;

  return (
    <div className="hist">
      {bins.map((b, i) => (
        <div key={b.label} className="hist__col" title={`${b.label} ms · ${b.count} requests`}>
          <div className="hist__bar-wrap">
            <span className="hist__count mono">{b.count || ""}</span>
            <motion.div
              className="hist__bar"
              style={{ background: color }}
              initial={{ height: 0 }}
              animate={{ height: `${(b.count / max) * 100}%` }}
              transition={{ duration: 0.6, delay: i * 0.03, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
          <span className="hist__label mono">{b.label}</span>
        </div>
      ))}
    </div>
  );
}
