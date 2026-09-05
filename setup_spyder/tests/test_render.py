# -*- coding: utf-8 -*-
"""Renderizador do transcript, sem Qt."""

from types import SimpleNamespace

from setup_spyder.render import (
    format_assistant_blocks,
    format_result_line,
    format_tool_line,
    format_user_line,
)


def test_format_user():
    assert format_user_line("olá\n") == "> olá"


def test_format_tool_com_path():
    assert format_tool_line("Read", {"file_path": "main.py"}) == "● Read(main.py)"


def test_format_tool_sem_input():
    assert format_tool_line("Bash") == "● Bash"


def test_format_result_ok():
    linha = format_result_line(
        duration_ms=1500, cost_usd=0.0123, is_error=False, num_turns=2
    )
    assert linha.startswith("── ok")
    assert "1.5s" in linha
    assert "$0.0123" in linha
    assert "2 turno" in linha


def test_format_assistant_blocks():
    content = [
        SimpleNamespace(thinking="...", signature="x"),
        SimpleNamespace(name="Read", input={"file_path": "a.py"}),
        SimpleNamespace(text="feito."),
    ]
    linhas = format_assistant_blocks(content)
    assert linhas[0] == "⋯ pensamento"
    assert linhas[1] == "● Read(a.py)"
    assert linhas[2] == "feito."
