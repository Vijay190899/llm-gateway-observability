import { motion } from "framer-motion";
import { niceMax, tickIndices, timeLabel } from "../lib/ticks";

export interface Line {
  points: number[];
  color: string;
  label: string;
}

const W = 720;
const H = 216;
const M = { l: 46, r: 14, t: 14, b: 26 };

/** Multi-line chart with a time x-axis, gridlines and a legend. */
export function LineChart({
  lines,
  times,
  windowSeconds,
  yFormat,
}: {
  lines: Line[];
  times: number[];
  windowSeconds: number;
  yFormat: (n: number) => string;
}) {
  const n = times.length;
  const x0 = M.l;
  const x1 = W - M.r;
  const y0 = M.t;
  const y1 = H - M.b;
  if (n < 2) return <div className="empty">Not enough data in this range.</div>;

  const yMax = niceMax(Math.max(...lines.flatMap((l) => l.points), 0));
  const px = (i: number) => x0 + (i / (n - 1)) * (x1 - x0);
  const py = (v: number) => y1 - (v / yMax) * (y1 - y0);
  const path = (pts: number[]) =>
    "M" + pts.map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(" L");

  const grid = [0, 0.25, 0.5, 0.75, 1];
  const ticks = tickIndices(n, 5);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Line chart">
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
        {lines.map((l) => (
          <motion.path
            key={l.label}
            d={path(l.points)}
            fill="none"
            stroke={l.color}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.9, ease: "easeOut" }}
          />
        ))}
        {ticks.map((i) => (
          <text key={i} x={px(i)} y={H - 8} className="chart__xlabel" textAnchor="middle">
            {timeLabel(times[i], windowSeconds)}
          </text>
        ))}
      </svg>
      <div className="chart__legend">
        {lines.map((l) => (
          <span key={l.label} className="chart__key">
            <span className="chart__swatch" style={{ background: l.color }} />
            {l.label}
          </span>
        ))}
      </div>
    </div>
  );
}
