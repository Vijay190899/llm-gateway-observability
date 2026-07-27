"""MCP tool-call routing.

The gateway fronts an agent fleet, not just completions, so it can route MCP
tool calls through the same control plane (rate limiting, metrics, tracing). A
small in-process tool registry keeps it end-to-end; a real deployment would
forward to registered MCP servers over the wire.
"""

from __future__ import annotations

import ast
import operator

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


def _calculator(arguments: dict):
    expr = str(arguments.get("expression", ""))
    return _safe_eval(ast.parse(expr, mode="eval").body)


def _echo(arguments: dict):
    return arguments.get("text", "")


def _word_count(arguments: dict):
    return len(str(arguments.get("text", "")).split())


_TOOLS = {
    "calculator": _calculator,
    "echo": _echo,
    "word_count": _word_count,
}


def available_tools() -> list[str]:
    return sorted(_TOOLS)


def call_tool(tool: str, arguments: dict):
    if tool not in _TOOLS:
        raise KeyError(tool)
    return _TOOLS[tool](arguments)
