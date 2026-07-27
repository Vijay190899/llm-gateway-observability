import { useEffect, useRef } from "react";

/**
 * Loading-screen background: a flow-field of particles drifting along an
 * evolving noise field, leaving fading cyan/teal streaks. Canvas 2D, a couple
 * hundred particles, DPR-capped; honours prefers-reduced-motion. Purely
 * decorative and unmounts with the loader.
 */
function hash(x: number, y: number): number {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
}
function noise(x: number, y: number): number {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const xf = x - xi;
  const yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash(xi, yi);
  const b = hash(xi + 1, yi);
  const c = hash(xi, yi + 1);
  const d = hash(xi + 1, yi + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}

export function LoaderBackdrop() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 1.25);
    let w = 0;
    let h = 0;
    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#0a0f15";
      ctx.fillRect(0, 0, w, h);
    };
    resize();
    window.addEventListener("resize", resize);

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const COUNT = reduce ? 0 : Math.min(520, Math.floor((w * h) / 3600));
    type P = { x: number; y: number; px: number; py: number; hue: number; life: number };
    const rnd = () => Math.random();
    const spawn = (): P => {
      const x = rnd() * w;
      const y = rnd() * h;
      return { x, y, px: x, py: y, hue: 168 + rnd() * 34, life: 40 + rnd() * 160 };
    };
    const particles: P[] = Array.from({ length: COUNT }, spawn);

    const SCALE = 0.0022;
    const SPEED = 0.9;
    let t = 0;
    let raf = 0;

    const step = () => {
      // Translucent fade for streak trails.
      ctx.fillStyle = "rgba(10, 15, 21, 0.08)";
      ctx.fillRect(0, 0, w, h);

      ctx.lineWidth = 1.1;
      for (const p of particles) {
        const angle = noise(p.x * SCALE + t, p.y * SCALE - t) * Math.PI * 4;
        p.px = p.x;
        p.py = p.y;
        p.x += Math.cos(angle) * SPEED;
        p.y += Math.sin(angle) * SPEED;
        p.life -= 1;

        if (p.x < 0 || p.x > w || p.y < 0 || p.y > h || p.life <= 0) {
          Object.assign(p, spawn());
          continue;
        }
        ctx.strokeStyle = `hsla(${p.hue}, 85%, 62%, 0.42)`;
        ctx.beginPath();
        ctx.moveTo(p.px, p.py);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
      }
      t += 0.0009;
      raf = requestAnimationFrame(step);
    };
    if (!reduce) step();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={ref} className="loader__canvas" aria-hidden />;
}
