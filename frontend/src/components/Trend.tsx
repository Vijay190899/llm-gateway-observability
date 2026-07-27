import { motion } from "framer-motion";
import { useId } from "react";

/** Area sparkline for a recent series (e.g. per-request latency). */
export function Trend({
  points,
  color = "var(--info)",
  height = 120,
  unit = "",
}: {
  points: number[];
  color?: string;
  height?: number;
  unit?: string;
}) {
  const gid = useId().replace(/:/g, "");
  const W = 640;
  const H = height;
  const pad = 8;
  if (points.length < 2) return <div className="empty">Not enough data yet.</div>;

  const max = Math.max(...points);
  const min = Math.min(...points);
  const span = max - min || 1;
  const x = (i: number) => pad + (i / (points.length - 1)) * (W - pad * 2);
  const y = (v: number) => pad + (1 - (v - min) / span) * (H - pad * 2);

  const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1).toFixed(1)},${H} L${x(0).toFixed(1)},${H} Z`;

  return (
    <div className="trend">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" width="100%" height={H} role="img" aria-label="Recent latency trend">
        <defs>
          <linearGradient id={`g-${gid}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <motion.path d={area} fill={`url(#g-${gid})`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }} />
        <motion.path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <div className="trend__scale mono">
        <span>{min.toFixed(0)}{unit}</span>
        <span>{max.toFixed(0)}{unit}</span>
      </div>
    </div>
  );
}
