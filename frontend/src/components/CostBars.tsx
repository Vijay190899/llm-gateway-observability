import { motion } from "framer-motion";
import type { ModelRow } from "../types";
import { usd } from "../lib/format";

const SERIES = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)"];

/** Horizontal spend-by-model bars. */
export function CostBars({ rows }: { rows: ModelRow[] }) {
  const max = Math.max(...rows.map((r) => r.cost_usd), 0.000001);
  if (rows.length === 0) return <Empty />;
  return (
    <div className="bars">
      {rows.map((r, i) => (
        <div className="bars__row" key={r.model}>
          <div className="bars__head">
            <span className="bars__name mono">{r.model}</span>
            <span className="bars__val mono">{usd(r.cost_usd)}</span>
          </div>
          <div className="bars__track">
            <motion.div
              className="bars__fill"
              style={{ background: SERIES[i % SERIES.length] }}
              initial={{ width: 0 }}
              animate={{ width: `${(r.cost_usd / max) * 100}%` }}
              transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: i * 0.05 }}
            />
          </div>
          <span className="bars__meta">{r.requests} req</span>
        </div>
      ))}
    </div>
  );
}

function Empty() {
  return <div className="empty">No traffic yet — send a request from the Playground.</div>;
}
