# -*- coding: utf-8 -*-
"""Perfil de configuração aplicado a cada instância do Spyder.

Chaves que matam popup são sempre gravadas. O resto (estilo) pode ser
desligado com --sem-estilo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ConfKey = Tuple[str, str]
ConfMap = Dict[ConfKey, object]

CONF_DIRNAME = ".spyder-lab"
FONT_FAMILY = "JetBrains Mono"

# Nomes escondidos no painel Projetos, além dos que o Spyder já oculta
# (.spyproject, __pycache__, .git, ...). Casados pelo basename.
HIDDEN_PATHS = (
    ".venv",
    "venv",
    ".env",
    "env",
    ".tox",
    "dist",
    "build",
    ".eggs",
    "node_modules",
    ".ruff_cache",
    ".mypy_cache",
    ".coverage",
    "htmlcov",
    ".claude",
    ".docs",
    ".github",
    ".gitlab",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".dockerignore",
    ".python-version",
    ".pre-commit-config.yaml",
    "uv.lock",
    "poetry.lock",
    "desktop.ini",
    CONF_DIRNAME,
)

# Variáveis que fariam o Spyder achar que está num env conda.
CONDA_ENV_VARS = (
    "CONDA_EXE",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "CONDA_PROMPT_MODIFIER",
    "CONDA_SHLVL",
    "CONDA_PYTHON_EXE",
    "MAMBA_EXE",
    "MAMBA_ROOT_PREFIX",
)

# Sempre aplicadas: matam diálogo de update, tour, DPI, erros internos,
# confirmações do kernel. Também forçam o interpretador do venv atual.
POPUPS: ConfMap = {
    ("main", "check_updates_on_startup"): False,
    ("main", "show_dpi_message"): False,
    ("main", "show_internal_errors"): False,
    ("main", "prompt_on_exit"): False,
    ("main", "single_instance"): False,
    ("tours", "show_tour_message"): False,
    ("ipython_console", "ask_before_restart"): False,
    ("ipython_console", "ask_before_closing"): False,
    ("ipython_console", "show_reset_namespace_warning"): False,
    ("main_interpreter", "default"): True,
    ("main_interpreter", "custom"): False,
}

# Aparência e editor. Só se --sem-estilo não foi passado.
STYLE: ConfMap = {
    ("appearance", "ui_theme"): "dark",
    ("appearance", "selected"): "spyder/dark",
    ("editor", "wrap"): True,
    ("editor", "edge_line"): True,
    ("editor", "blank_spaces"): False,
    ("main", "panes_locked"): True,
    ("toolbar", "toolbars_visible"): True,
}


def split_names(entries: Sequence[str]) -> set:
    """Repetidos e separados por vírgula viram um set de nomes."""
    return {
        name.strip()
        for entry in entries
        for name in entry.split(",")
        if name.strip()
    }


def resolve_hidden_paths(
    hide: Sequence[str] = (),
    show: Sequence[str] = (),
) -> List[str]:
    names = set(HIDDEN_PATHS) | split_names(hide)
    return sorted(names - split_names(show))


def conf_dir_for(workdir: Path, ephemeral: bool = False) -> Path:
    """Diretório de config do Spyder: persistente por projeto, ou temp."""
    if ephemeral:
        import tempfile

        return Path(tempfile.mkdtemp(prefix="setup-spyder-conf-"))
    path = Path(workdir) / CONF_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def font_dirs() -> Tuple[Path, ...]:
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        windir = os.environ.get("WINDIR") or r"C:\Windows"
        return (
            Path(local) / "Microsoft" / "Windows" / "Fonts",
            Path(windir) / "Fonts",
        )
    if sys.platform == "darwin":
        return (
            Path.home() / "Library" / "Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
        )
    return (
        Path.home() / ".local" / "share" / "fonts",
        Path("/usr/local/share/fonts"),
        Path("/usr/share/fonts"),
    )


def jetbrains_mono_installed() -> List[Path]:
    hits: List[Path] = []
    for directory in font_dirs():
        if not directory.is_dir():
            continue
        hits.extend(sorted(directory.glob("JetBrainsMono*")))
        hits.extend(sorted(directory.glob("JetBrainsMonoNerdFont*")))
    return hits


def spyder_default_font() -> str:
    try:
        from spyder.config.fonts import MONOSPACE

        return MONOSPACE[0]
    except Exception:
        return "Consolas" if os.name == "nt" else "Monospace"


def resolve_editor_font() -> Tuple[str, List[Path]]:
    hits = jetbrains_mono_installed()
    if hits:
        return FONT_FAMILY, hits
    return spyder_default_font(), []


def font_family_value(family: str) -> List[str]:
    """Spyder guarda font/family como lista de fallbacks."""
    try:
        from spyder.config.fonts import MONOSPACE

        rest = [name for name in MONOSPACE if name != family]
        return [family] + rest
    except Exception:
        return [family]


def perfil_completo(font_family: str, com_estilo: bool = True) -> ConfMap:
    valores = dict(POPUPS)
    if com_estilo:
        valores.update(STYLE)
        valores[("appearance", "font/family")] = font_family_value(font_family)
        valores[("appearance", "rich_font/family")] = font_family_value(
            font_family
        )
    return valores


def apply_perfil(conf_dir: Path, valores: ConfMap) -> None:
    """Grava o perfil em SPYDER_CONFDIR. Importa CONF só depois do env."""
    os.environ["SPYDER_CONFDIR"] = str(conf_dir)
    from spyder.config.manager import CONF

    for (secao, chave), valor in valores.items():
        CONF.set(secao, chave, valor)


def reler_perfil(chaves: Iterable[ConfKey]) -> ConfMap:
    from spyder.config.manager import CONF

    return {(secao, chave): CONF.get(secao, chave) for secao, chave in chaves}


def strip_conda_env(env: dict) -> dict:
    limpo = dict(env)
    for key in CONDA_ENV_VARS:
        limpo.pop(key, None)
    return limpo
