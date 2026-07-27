import { motion } from "framer-motion";
import { useId } from "react";
import { niceMax, tickIndices, timeLabel } from "../lib/ticks";

export interface Band {
  values: number[];
  color: string;
  label: string;
}

const W = 720;
const H = 216;
const M = { l: 46, r: 14, t: 14, b: 26 };

/** Stacked (or single) area chart with a time x-axis and gridlines. */
export function AreaChart({
  bands,
  times,
  windowSeconds,
  yFormat,
}: {
  bands: Band[];
  times: number[];
  windowSeconds: number;
  yFormat: (n: number) => string;
}) {
  const gid = useId().replace(/:/g, "");
  const n = times.length;
  const x0 = M.l;
  const x1 = W - M.r;
  const y0 = M.t;
  const y1 = H - M.b;

  if (n < 2) return <div className="empty">Not enough data in this range.</div>;

  const totals = times.map((_, i) => bands.reduce((s, b) => s + (b.values[i] ?? 0), 0));
  const yMax = niceMax(Math.max(...totals, 0));
  const px = (i: number) => x0 + (i / (n - 1)) * (x1 - x0);
  const py = (v: number) => y1 - (v / yMax) * (y1 - y0);

  // Cumulative lower edge for stacking.
  const lower = times.map(() => 0);
  const areas = bands.map((b) => {
    const upper = times.map((_, i) => lower[i] + (b.values[i] ?? 0));
    const top = upper.map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`);
    const bottom = lower
      .map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`)
      .reverse();
    const path = `M${top.join(" L")} L${bottom.join(" L")} Z`;
    const line = `M${top.map((p) => p).join(" L")}`;
    for (let i = 0; i < n; i++) lower[i] = upper[i];
    return { path, line, color: b.color };
  });

  const grid = [0, 0.25, 0.5, 0.75, 1];
  const ticks = tickIndices(n, 5);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Time series">
        <defs>
          {areas.map((a, i) => (
            <linearGradient key={i} id={`a-${gid}-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={a.color} stopOpacity="0.42" />
              <stop offset="100%" stopColor={a.color} stopOpacity="0.03" />
            </linearGradient>
          ))}
        </defs>

        {/* gridlines + y labels */}
        {grid.map((g) => {
          const y = y1 - g * (y1 - y0);
          return (
            <g key={g}>
              <line x1={x0} y1={y} x2={x1} y2={y} className="chart__grid" />
              <text x={x0 - 8} y={y + 3} className="chart__ylabel" textAnchor="end">
                {yFormat(g * yMax)}
              </text>
            </g>
          );
        })}

        {/* areas (draw last band first so earlier bands sit on top visually) */}
        {areas.map((a, i) => (
          <g key={i}>
            <motion.path
              d={a.path}
              fill={`url(#a-${gid}-${i})`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
            />
            <motion.path
              d={a.line}
              fill="none"
              stroke={a.color}
              strokeWidth={1.75}
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.9, ease: "easeOut" }}
            />
          </g>
        ))}

        {/* x labels */}
        {ticks.map((i) => (
          <text key={i} x={px(i)} y={H - 8} className="chart__xlabel" textAnchor="middle">
            {timeLabel(times[i], windowSeconds)}
          </text>
        ))}
      </svg>

      {bands.length > 1 && (
        <div className="chart__legend">
          {bands.map((b) => (
            <span key={b.label} className="chart__key">
              <span className="chart__swatch" style={{ background: b.color }} />
              {b.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
