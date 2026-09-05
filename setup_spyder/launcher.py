# -*- coding: utf-8 -*-
"""Sobe o Spyder no sys.executable do venv, com config isolada."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from setup_spyder.patches import render_launcher
from setup_spyder.perfil import (
    apply_perfil,
    conf_dir_for,
    perfil_completo,
    reler_perfil,
    resolve_editor_font,
    resolve_hidden_paths,
    strip_conda_env,
)


def force_writable(path: Path) -> None:
    try:
        path.chmod(path.stat().st_mode | stat.S_IWRITE)
    except OSError:
        pass


def remove_tree(path: Path) -> None:
    """Apaga uma árvore; no Windows tenta de novo depois de limpar read-only."""
    shutil.rmtree(path, ignore_errors=True)
    if not path.is_dir():
        return
    for item in path.rglob("*"):
        force_writable(item)
    force_writable(path)
    shutil.rmtree(path, ignore_errors=True)


def ensure_spyproject(root: Path) -> Path:
    """Cria `.spyproject` se ainda não existir (projeto Spyder vazio)."""
    spyproject = root / ".spyproject"
    if spyproject.is_dir():
        return spyproject
    (spyproject / "config").mkdir(parents=True, exist_ok=True)
    from spyder.plugins.projects.api import EmptyProject

    EmptyProject(root_path=str(root))
    return spyproject


def write_launcher(conf_dir: Path, argv: Sequence[str], hidden: Sequence[str]) -> Path:
    launcher = conf_dir / "launch_spyder.py"
    launcher.write_text(render_launcher(argv, hidden), encoding="utf-8")
    return launcher


def spyder_ini(conf_dir: Path) -> Path:
    return Path(conf_dir) / "config" / "spyder.ini"


def launch(
    spyder_args: Sequence[str] = (),
    *,
    no_launch: bool = False,
    keep_config: bool = False,
    ephemeral: bool = False,
    sem_estilo: bool = False,
    workdir: str | Path | None = None,
    conf_dir: str | Path | None = None,
    hide: Sequence[str] = (),
    show: Sequence[str] = (),
    log=None,
) -> int:
    """Configura e (opcionalmente) abre o Spyder neste venv.

    `log` é um callable(str) para mensagens; o CLI passa o logger do rich.
    """
    def _log(msg: str) -> None:
        if log is not None:
            log(msg)

    workdir = Path(workdir).resolve() if workdir else Path.cwd().resolve()
    extra_args = [a for a in spyder_args if a != "--"]

    try:
        import spyder  # noqa: F401
        import spyder_kernels  # noqa: F401
    except ImportError as exc:
        _log("dependência ausente: {}".format(exc))
        _log(
            "neste projeto: uv add --editable "
            "<checkout-deste-spyder> --prerelease=allow"
        )
        return 1

    font_family, _fonts = resolve_editor_font()
    valores = perfil_completo(font_family, com_estilo=not sem_estilo)

    if conf_dir is not None:
        destino = Path(conf_dir).resolve()
        destino.mkdir(parents=True, exist_ok=True)
        apagar_ao_sair = False
    else:
        destino = conf_dir_for(workdir, ephemeral=ephemeral)
        apagar_ao_sair = ephemeral and not keep_config

    ensure_spyproject(workdir)
    apply_perfil(destino, valores)

    lidas = reler_perfil(
        [
            ("main", "check_updates_on_startup"),
            ("tours", "show_tour_message"),
            ("appearance", "ui_theme"),
            ("appearance", "font/family"),
            ("editor", "wrap"),
        ]
    )
    for chave, valor in lidas.items():
        _log("{} = {!r}".format(".".join(chave), valor))

    ini = spyder_ini(destino)
    _log("config: {}".format(ini if ini.is_file() else destino))

    if no_launch:
        _log("no_launch: Spyder não será aberto.")
        return 0

    spyder_argv = [
        shutil.which("spyder") or "spyder",
        "--conf-dir",
        str(destino),
        "--new-instance",
        "-w",
        str(workdir),
        "-p",
        str(workdir),
        *extra_args,
    ]
    hidden = resolve_hidden_paths(hide, show)
    script = write_launcher(destino, spyder_argv, hidden)
    _log("ocultos no painel Projetos: {}".format(", ".join(hidden)))
    _log("launcher: {}".format(script))

    env = strip_conda_env(os.environ)
    env["SPYDER_CONFDIR"] = str(destino)
    cmd = [sys.executable, str(script)]
    try:
        completed = subprocess.run(cmd, check=False, env=env)
        return completed.returncode
    finally:
        if apagar_ao_sair:
            remove_tree(destino)
