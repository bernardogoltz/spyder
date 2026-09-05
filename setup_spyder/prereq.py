# -*- coding: utf-8 -*-
"""Checagens do CLI/credencial — só texto, nunca diálogo."""

from __future__ import annotations

import os
import shutil
from typing import List


def diagnose_prerequisites(cli_path: str = "") -> List[str]:
    avisos: List[str] = []
    exe = (cli_path or "").strip() or shutil.which("claude")
    if not exe:
        avisos.append(
            "CLI `claude` não está no PATH. Instale o Claude Code ou "
            "aponte o caminho em Preferências → Claude Code."
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        avisos.append(
            "ANTHROPIC_API_KEY não definida. Se você já fez `claude login`, "
            "pode ignorar; senão, exporte a chave ou autentique o CLI."
        )
    return avisos
