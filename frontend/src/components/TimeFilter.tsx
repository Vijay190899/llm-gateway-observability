import { motion } from "framer-motion";

export interface Range {
  label: string;
  seconds: number;
}

export const RANGES: Range[] = [
  { label: "30m", seconds: 1800 },
  { label: "1h", seconds: 3600 },
  { label: "3h", seconds: 10800 },
  { label: "6h", seconds: 21600 },
  { label: "12h", seconds: 43200 },
  { label: "24h", seconds: 86400 },
];

export function TimeFilter({ value, onChange }: { value: number; onChange: (s: number) => void }) {
  return (
    <div className="tf" role="tablist" aria-label="Time range">
      <span className="tf__label mono">RANGE</span>
      <div className="tf__group">
        {RANGES.map((r) => {
          const active = r.seconds === value;
          return (
            <button
              key={r.seconds}
              role="tab"
              aria-selected={active}
              className={`tf__chip mono ${active ? "tf__chip--on" : ""}`}
              onClick={() => onChange(r.seconds)}
            >
              {active && (
                <motion.span
                  layoutId="tf-pill"
                  className="tf__pill"
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                />
              )}
              <span className="tf__chip-text">last {r.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
