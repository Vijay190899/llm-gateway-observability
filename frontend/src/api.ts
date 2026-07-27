import type { ChatResponse, MetricsSummary } from "./types";

// Relative paths — proxied to the gateway by Vite (dev) or nginx (container).
export async function getMetrics(): Promise<MetricsSummary> {
  const r = await fetch("/metrics");
  if (!r.ok) throw new Error(`metrics ${r.status}`);
  return r.json();
}

export async function getHealth(): Promise<{ status: string; backend: string; tracing: boolean }> {
  const r = await fetch("/health");
  if (!r.ok) throw new Error(`health ${r.status}`);
  return r.json();
}

export interface ChatOk {
  ok: true;
  data: ChatResponse;
}
export interface ChatErr {
  ok: false;
  status: number;
  error: string;
  findings?: string[];
}

export async function sendChat(
  team: string,
  model: string,
  content: string,
): Promise<ChatOk | ChatErr> {
  const r = await fetch("/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Team": team },
    body: JSON.stringify({ model, messages: [{ role: "user", content }] }),
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detail = body?.detail ?? {};
    return {
      ok: false,
      status: r.status,
      error: detail.error ?? `request failed (${r.status})`,
      findings: detail.findings,
    };
  }
  return { ok: true, data: body as ChatResponse };
}

export async function listMcpTools(): Promise<string[]> {
  const r = await fetch("/v1/mcp/tools");
  if (!r.ok) return [];
  return (await r.json()).tools ?? [];
}

export async function callMcp(tool: string, args: Record<string, unknown>) {
  const r = await fetch("/v1/mcp/call", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, arguments: args }),
  });
  return r.json();
}
