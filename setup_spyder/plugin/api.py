# -*- coding: utf-8 -*-
"""IDs de ação, defaults e versão da config do plugin Claude Code."""


class ClaudeCodeActions:
    Enviar = "claude_code_enviar_action"
    Interromper = "claude_code_interromper_action"
    Limpar = "claude_code_limpar_action"
    NovaSessao = "claude_code_nova_sessao_action"
    AnexarSelecao = "claude_code_anexar_selecao_action"


class ClaudeCodeToolbarSections:
    Principal = "claude_code_principal_section"


class ClaudeCodeOptionsMenuSections:
    Opcoes = "claude_code_opcoes_section"


CONF_DEFAULTS = [
    (
        "claude_code",
        {
            "model": "claude-opus-5",
            "permission_mode": "acceptEdits",
            "effort": "high",
            "anexar_selecao": True,
            "cli_path": "",
            "add_dirs": "",
        },
    ),
]

CONF_VERSION = "1.0.0"

MODELOS = (
    ("Claude Opus 5", "claude-opus-5"),
    ("Claude Sonnet 4", "claude-sonnet-4"),
    ("Claude Haiku 4", "claude-haiku-4"),
)

PERMISSION_MODES = (
    ("Aceitar edições", "acceptEdits"),
    ("Perguntar", "default"),
    ("Planejar", "plan"),
    ("Sem confirmação", "bypassPermissions"),
)

EFFORT_LEVELS = (
    ("Baixo", "low"),
    ("Médio", "medium"),
    ("Alto", "high"),
    ("Máximo", "max"),
)
