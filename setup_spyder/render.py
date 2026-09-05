# -*- coding: utf-8 -*-
"""Texto do transcript do Claude Code — puro, sem Qt."""

from __future__ import annotations

from typing import Any, Iterable, List, Optional


def format_user_line(text: str) -> str:
    return "> {}".format(text.rstrip())


def format_thinking_line() -> str:
    return "⋯ pensamento"


def _preview(value: Any, limit: int = 80) -> str:
    text = str(value).replace("\n", " ")
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def format_tool_line(name: str, input_data: Optional[dict] = None) -> str:
    data = input_data or {}
    for key in ("file_path", "path", "command", "pattern", "query", "glob"):
        if data.get(key):
            return "● {}({})".format(name, _preview(data[key]))
    if data:
        first = next(iter(data.values()))
        return "● {}({})".format(name, _preview(first))
    return "● {}".format(name)


def format_result_line(
    duration_ms: Optional[int] = None,
    cost_usd: Optional[float] = None,
    is_error: bool = False,
    num_turns: Optional[int] = None,
) -> str:
    seconds = (duration_ms or 0) / 1000.0
    cost = ""
    if cost_usd is not None:
        cost = " · ${:.4f}".format(cost_usd)
    status = "erro" if is_error else "ok"
    return "── {} · {:.1f}s{} · {} turno(s)".format(
        status, seconds, cost, num_turns or 0
    )


def format_assistant_blocks(content: Iterable) -> List[str]:
    """Converte blocos de um AssistantMessage em linhas do transcript."""
    linhas: List[str] = []
    for block in content:
        tipo = type(block).__name__
        if tipo == "ThinkingBlock" or hasattr(block, "thinking"):
            linhas.append(format_thinking_line())
            continue
        if tipo == "ToolUseBlock" or (hasattr(block, "name") and hasattr(block, "input")):
            linhas.append(format_tool_line(getattr(block, "name", "?"), getattr(block, "input", {})))
            continue
        text = getattr(block, "text", None)
        if text:
            linhas.append(text.rstrip())
    return linhas
