"""Runtime guardrails applied inline on the request and the response.

Three concerns, mapped to the OWASP LLM Top 10:
  - Prompt injection            -> LLM01
  - Insecure output handling    -> LLM02 (active markup in model output)
  - Sensitive info disclosure   -> LLM06 (PII in prompts or responses)

Findings are returned tagged with their OWASP id. PII is redacted rather than
blocked; injection above the configured policy blocks the request.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Prompt injection -------------------------------------------------------
_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "override-instructions",
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
    ),
    ("disregard", re.compile(r"disregard\s+(the\s+)?(system|previous|above)", re.I)),
    (
        "reveal-system-prompt",
        re.compile(r"(reveal|show|print|repeat)\s+(your|the)\s+system\s+prompt", re.I),
    ),
    ("role-override", re.compile(r"you\s+are\s+now\s+(a|an|the)\b", re.I)),
    ("jailbreak-persona", re.compile(r"\b(DAN|developer\s+mode|do\s+anything\s+now)\b", re.I)),
    (
        "exfiltrate",
        re.compile(
            r"(send|post|exfiltrate|leak)\s+.*\b(api[_\s-]?key|secret|token|password)", re.I
        ),
    ),
]

# --- PII --------------------------------------------------------------------
_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit-card", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("phone", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")),
    ("ip-address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]

# --- Insecure output --------------------------------------------------------
_OUTPUT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("script-tag", re.compile(r"<\s*script", re.I)),
    ("js-uri", re.compile(r"javascript:\s*", re.I)),
    ("event-handler", re.compile(r"\bon(?:error|load|click)\s*=", re.I)),
]


@dataclass
class GuardrailOutcome:
    allowed: bool = True
    input_findings: list[str] = field(default_factory=list)
    output_findings: list[str] = field(default_factory=list)
    redacted: bool = False
    safe_input: str = ""
    safe_output: str = ""


def _redact_pii(text: str) -> tuple[str, list[str]]:
    findings: list[str] = []
    for name, pattern in _PII_PATTERNS:
        if pattern.search(text):
            findings.append(f"LLM06:{name}")
            text = pattern.sub(f"[REDACTED:{name}]", text)
    return text, findings


def scan_input(text: str, block_on_injection: bool = True) -> tuple[bool, list[str], str]:
    """Returns (allowed, findings, redacted_text) for a prompt."""
    findings = [f"LLM01:{name}" for name, pat in _INJECTION_PATTERNS if pat.search(text)]
    safe, pii = _redact_pii(text)
    findings.extend(pii)
    injected = any(f.startswith("LLM01") for f in findings)
    allowed = not (injected and block_on_injection)
    return allowed, findings, safe


def scan_output(text: str) -> tuple[list[str], str]:
    """Returns (findings, sanitized_text) for a model response."""
    findings = [f"LLM02:{name}" for name, pat in _OUTPUT_PATTERNS if pat.search(text)]
    safe, pii = _redact_pii(text)
    findings.extend(pii)
    return findings, safe
