export const usd = (n: number, digits = n < 1 ? 4 : 2) =>
  "$" + n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const compact = (n: number) =>
  n.toLocaleString(undefined, { notation: n >= 10000 ? "compact" : "standard" });

export const pct = (n: number) => (n * 100).toFixed(n * 100 >= 10 ? 0 : 1) + "%";

export const ms = (n: number) => (n >= 1000 ? (n / 1000).toFixed(2) + " s" : Math.round(n) + " ms");

export function ago(ts: number): string {
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 5) return "just now";
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}
