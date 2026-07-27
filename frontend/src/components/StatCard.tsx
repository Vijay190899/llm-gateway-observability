import { motion } from "framer-motion";
import { CountUp } from "./CountUp";

export interface StatCardProps {
  label: string;
  value: number;
  format: (n: number) => string;
  sublabel?: string;
  accent?: string;
  icon: React.ReactNode;
}

export function StatCard({ label, value, format, sublabel, accent = "var(--accent)", icon }: StatCardProps) {
  return (
    <motion.div
      className="glass stat"
      variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }}
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 320, damping: 24 }}
    >
      <div className="stat__top">
        <span className="stat__label">{label}</span>
        <span className="stat__icon" style={{ color: accent, background: `color-mix(in oklch, ${accent} 16%, transparent)` }}>
          {icon}
        </span>
      </div>
      <div className="stat__value mono" style={{ ["--bar" as string]: accent }}>
        <CountUp value={value} format={format} />
      </div>
      {sublabel && <div className="stat__sub">{sublabel}</div>}
      <span className="stat__glow" style={{ background: accent }} aria-hidden />
    </motion.div>
  );
}
