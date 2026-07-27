import { motion } from "framer-motion";
import { LoaderBackdrop } from "./LoaderBackdrop";

/**
 * Branded intro / loading screen. A flow-field particle animation drifts behind
 * boot-sequence lines that type in while a progress bar fills, then the whole
 * overlay lifts away (AnimatePresence in App). Sets the editorial tone before
 * the dashboard resolves.
 */
const STEPS = [
  "initializing gateway",
  "warming semantic cache",
  "loading guardrail policies",
  "streaming metrics",
];

export function Loader() {
  return (
    <motion.div
      className="loader"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, filter: "blur(12px)" }}
      transition={{ duration: 0.7, ease: [0.65, 0, 0.35, 1] }}
    >
      <LoaderBackdrop />
      <div className="loader__inner">
        <motion.div
          className="loader__kicker mono"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          CONTROL PLANE
        </motion.div>

        <h1 className="loader__title">
          {"LLM Gateway &".split(" ").map((w, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
            >
              {w}{" "}
            </motion.span>
          ))}
          <motion.em
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            Observability Platform
          </motion.em>
        </h1>

        <ul className="loader__steps mono">
          {STEPS.map((s, i) => (
            <motion.li
              key={s}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.18 }}
            >
              <span className="loader__tick">▸</span> {s}
            </motion.li>
          ))}
        </ul>

        <div className="loader__bar">
          <motion.span
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 1.5, ease: [0.4, 0, 0.2, 1] }}
          />
        </div>
      </div>
    </motion.div>
  );
}
