/** Shared axis helpers for the SVG charts. */

export function timeLabel(epochSeconds: number, windowSeconds: number): string {
  const d = new Date(epochSeconds * 1000);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  if (windowSeconds > 43200) {
    // 24h view: include day so midnight boundaries read clearly.
    return `${String(d.getDate()).padStart(2, "0")} ${hh}:${mm}`;
  }
  return `${hh}:${mm}`;
}

/** Pick ~count evenly spaced indices from a series length. */
export function tickIndices(length: number, count = 5): number[] {
  if (length <= count) return Array.from({ length }, (_, i) => i);
  const step = (length - 1) / (count - 1);
  return Array.from({ length: count }, (_, i) => Math.round(i * step));
}

/** A "nice" upper bound for a y-axis so gridlines land on round numbers. */
export function niceMax(max: number): number {
  if (max <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(max)));
  const n = max / pow;
  const step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
  return step * pow;
}
