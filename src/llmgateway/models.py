"""Request/response contracts. OpenAI-compatible on the wire, plus a gateway
metadata block so callers can see what the gateway did (cache, cost, guardrails)."""

from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatRequest(BaseModel):
    model: str = "mock-gpt"
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 512
    # Present for OpenAI compatibility; streaming is not implemented and is ignored.
    stream: bool = False


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class GuardrailReport(BaseModel):
    allowed: bool = True
    input_findings: list[str] = Field(default_factory=list)
    output_findings: list[str] = Field(default_factory=list)
    redacted: bool = False


class GatewayMeta(BaseModel):
    cache_hit: bool = False
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    team: str = "default"
    guardrails: GuardrailReport = Field(default_factory=GuardrailReport)


class Choice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: str = "stop"


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[Choice]
    usage: Usage
    gateway: GatewayMeta


class MCPToolCall(BaseModel):
    tool: str
    arguments: dict = Field(default_factory=dict)
    team: str | None = None


class MCPToolResult(BaseModel):
    tool: str
    result: object
    latency_ms: float = 0.0
    error: str | None = None
