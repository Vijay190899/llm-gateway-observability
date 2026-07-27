export interface Totals {
  requests: number;
  cache_hits: number;
  cache_hit_rate: number;
  blocked: number;
  cost_usd: number;
  saved_usd: number;
  tokens: number;
  avg_latency_ms: number;
}

export interface ModelRow {
  model: string;
  requests: number;
  cost_usd: number;
}

export interface TeamRow {
  team: string;
  requests: number;
  cost_usd: number;
}

export interface RequestEvent {
  ts: number;
  team: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  latency_ms: number;
  cache_hit: boolean;
  blocked: boolean;
  saved_usd: number;
  findings: string[];
}

export interface MetricsSummary {
  generated_at: number;
  totals: Totals;
  by_model: ModelRow[];
  by_team: TeamRow[];
  recent: RequestEvent[];
}

export interface GuardrailReport {
  allowed: boolean;
  input_findings: string[];
  output_findings: string[];
  redacted: boolean;
}

export interface ChatResponse {
  id: string;
  model: string;
  choices: { message: { role: string; content: string } }[];
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  gateway: {
    cache_hit: boolean;
    latency_ms: number;
    cost_usd: number;
    team: string;
    guardrails: GuardrailReport;
  };
}
