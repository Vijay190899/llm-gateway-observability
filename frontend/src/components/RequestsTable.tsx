import { AnimatePresence, motion } from "framer-motion";
import type { RequestEvent } from "../types";
import { ago, ms, usd } from "../lib/format";

function Tag({ ev }: { ev: RequestEvent }) {
  if (ev.blocked) return <span className="tag tag--danger">blocked</span>;
  if (ev.cache_hit) return <span className="tag tag--cache">cache hit</span>;
  return <span className="tag tag--live">upstream</span>;
}

export function RequestsTable({ rows }: { rows: RequestEvent[] }) {
  if (rows.length === 0) return <div className="empty">Requests will stream in here.</div>;
  return (
    <div className="feed" role="list">
      <AnimatePresence initial={false}>
        {rows.slice(0, 12).map((ev) => (
          <motion.div
            role="listitem"
            key={`${ev.ts}-${ev.model}-${ev.latency_ms}`}
            className="feed__row"
            layout
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          >
            <Tag ev={ev} />
            <span className="feed__model mono">{ev.model}</span>
            <span className="feed__team">{ev.team}</span>
            <span className="feed__lat mono">{ms(ev.latency_ms)}</span>
            <span className="feed__cost mono">{ev.cache_hit ? "$0.00" : usd(ev.cost_usd)}</span>
            <span className="feed__findings">
              {ev.findings.slice(0, 2).map((f) => (
                <span className="chip" key={f}>
                  {f}
                </span>
              ))}
            </span>
            <span className="feed__time">{ago(ev.ts)}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
