// Minimal stroke icons (currentColor). Kept inline so there is no icon dependency.
const base = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export const IconActivity = () => (
  <svg {...base}><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
);
export const IconBolt = () => (
  <svg {...base}><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8Z" /></svg>
);
export const IconCoin = () => (
  <svg {...base}><circle cx="12" cy="12" r="9" /><path d="M12 7v10M9.5 9.5a2.5 2 0 0 1 5 0M9.5 14.5a2.5 2 0 0 0 5 0" /></svg>
);
export const IconShield = () => (
  <svg {...base}><path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3Z" /><path d="m9.5 12 1.8 1.8L15 10" /></svg>
);
export const IconGauge = () => (
  <svg {...base}><path d="M12 13 16 9" /><path d="M3.5 16a9 9 0 1 1 17 0" /><circle cx="12" cy="13" r="1.4" fill="currentColor" stroke="none" /></svg>
);
export const IconLayers = () => (
  <svg {...base}><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" /></svg>
);
export const IconPlay = () => (
  <svg {...base}><path d="M6 4v16l13-8L6 4Z" /></svg>
);
export const IconChart = () => (
  <svg {...base}><path d="M3 3v18h18" /><path d="M7 15l3-4 3 2 4-6" /></svg>
);
export const IconSun = () => (
  <svg {...base}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
);
export const IconMoon = () => (
  <svg {...base}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" /></svg>
);
