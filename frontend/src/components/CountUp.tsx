import { useEffect, useRef, useState } from "react";
import { animate, useReducedMotion } from "framer-motion";

/** Animated count-up (design skill, Pattern 4). Respects reduced-motion. */
export function CountUp({
  value,
  format,
  duration = 0.9,
}: {
  value: number;
  format: (n: number) => string;
  duration?: number;
}) {
  const [display, setDisplay] = useState(value);
  const prev = useRef(value);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) {
      setDisplay(value);
      prev.current = value;
      return;
    }
    const controls = animate(prev.current, value, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setDisplay(v),
    });
    prev.current = value;
    return () => controls.stop();
  }, [value, duration, reduce]);

  return <>{format(display)}</>;
}
