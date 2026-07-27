import { motion } from "framer-motion";
import type { FindingRow } from "../types";

const COLORS: Record<string, string> = {
  LLM01: "var(--chart-a)",
  LLM02: "var(--chart-b)",
  LLM06: "var(--c3)",
};

/** Guardrail findings by OWASP LLM Top 10 category. */
export function Findings({ rows }: { rows: FindingRow[] }) {
  const max = Math.max(...rows.map((r) => r.count), 1);
  const total = rows.reduce((s, r) => s + r.count, 0);
  if (total === 0) return <div className="empty">No guardrail events in this range. All clear.</div>;

  return (
    <div className="bars">
      {rows.map((r, i) => (
        <div className="bars__row" key={r.code}>
          <div className="bars__head">
            <span className="bars__name">
              <span className="chip chip--owasp">{r.code}</span> {r.label}
            </span>
            <span className="bars__val mono">{r.count}</span>
          </div>
          <div className="bars__track">
            <motion.div
              className="bars__fill"
              style={{ background: COLORS[r.code] ?? "var(--accent)" }}
              initial={{ width: 0 }}
              animate={{ width: `${(r.count / max) * 100}%` }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: i * 0.06 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
