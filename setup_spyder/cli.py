# -*- coding: utf-8 -*-
"""CLI: uv run setup-spyder."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from setup_spyder.launcher import launch as _launch

WINDOWS = sys.platform == "win32"


def enable_utf8_output() -> None:
    """Evita crash do ✓ no console cp1252 do Windows."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        encoding = (getattr(stream, "encoding", "") or "").lower()
        if encoding.replace("-", "") == "utf8":
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


if WINDOWS:
    enable_utf8_output()

console = Console(highlight=False)


def _prefix() -> Text:
    return Text("setup-spyder", style="bold cyan")


def log(message: str) -> None:
    console.print(Text.assemble(_prefix(), " ", (message, "white")), soft_wrap=True)


def log_ok(message: str) -> None:
    console.print(
        Text.assemble(_prefix(), " ", ("✓ ", "bold green"), (message, "green")),
        soft_wrap=True,
    )


def log_warn(message: str) -> None:
    console.print(
        Text.assemble(_prefix(), " ", ("! ", "bold yellow"), (message, "yellow")),
        soft_wrap=True,
    )


def log_error(message: str) -> None:
    console.print(
        Text.assemble(_prefix(), " ", ("✗ ", "bold red"), (message, "red")),
        soft_wrap=True,
    )


def print_banner(version: str, workdir: Path) -> None:
    body = Text()
    body.append("setup-spyder", style="bold white")
    body.append(" v{}".format(version), style="dim")
    body.append("\nSpyder 5.x neste venv", style="cyan")
    body.append(" · sem conda · sem popups · Claude Code\n\n", style="dim")
    body.append("projeto ", style="white")
    body.append(workdir.name, style="bold bright_cyan")
    body.append("\n")
    body.append(str(workdir), style="dim")
    console.print()
    console.print(
        Panel(
            body,
            title="[bold cyan]setup-spyder[/]",
            subtitle="[dim]config em .spyder-lab/ · ~/.spyder-py3 intacto[/]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def print_env(workdir: Path) -> None:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), expand=False)
    table.add_column(style="dim cyan")
    table.add_column(style="bold white")
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Executable", sys.executable)
    table.add_row("Environment", sys.prefix)
    table.add_row("Workdir", str(workdir))
    console.print(table)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="setup-spyder",
        description=(
            "Abre este Spyder 5.x no venv do diretório atual: projeto já "
            "configurado, sem conda, sem popups, com o painel do Claude Code. "
            "Use de dentro de um projeto uv: uv run setup-spyder"
        ),
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Só grava a config; não abre a janela.",
    )
    parser.add_argument(
        "--keep-config",
        action="store_true",
        help="Com --ephemeral, não apaga o diretório de config ao sair.",
    )
    parser.add_argument(
        "--ephemeral",
        action="store_true",
        help="Config em temp (descartável). O padrão é <projeto>/.spyder-lab/.",
    )
    parser.add_argument(
        "--sem-estilo",
        action="store_true",
        help="Não aplica tema/fonte; só as chaves que matam popup.",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        default=None,
        help="Diretório de trabalho (padrão: diretório atual).",
    )
    parser.add_argument(
        "--conf-dir",
        default=None,
        help="Sobrescreve o diretório de config do Spyder.",
    )
    parser.add_argument(
        "--hide",
        action="append",
        default=[],
        metavar="NOME[,NOME...]",
        help="Nomes extras a esconder no painel Projetos.",
    )
    parser.add_argument(
        "--show",
        action="append",
        default=[],
        metavar="NOME[,NOME...]",
        help="Nomes a manter visíveis (desfaz um default, ex. --show .github).",
    )
    parser.add_argument(
        "spyder_args",
        nargs=argparse.REMAINDER,
        help="Argumentos extras para o Spyder (depois de --).",
    )
    return parser.parse_args(argv)


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
) -> int:
    from setup_spyder import __version__

    destino = Path(workdir).resolve() if workdir else Path.cwd().resolve()
    print_banner(__version__, destino)
    print_env(destino)

    def _log(message: str) -> None:
        if message.startswith("dependência"):
            log_error(message)
        elif "no_launch" in message:
            log_ok(message)
        else:
            log(message)

    code = _launch(
        spyder_args,
        no_launch=no_launch,
        keep_config=keep_config,
        ephemeral=ephemeral,
        sem_estilo=sem_estilo,
        workdir=destino,
        conf_dir=conf_dir,
        hide=hide,
        show=show,
        log=_log,
    )
    if code == 0:
        log_ok("Spyder encerrou." if not no_launch else "config pronta.")
    else:
        log_warn("Spyder saiu com código {}".format(code))
    return code


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return launch(
        args.spyder_args,
        no_launch=args.no_launch,
        keep_config=args.keep_config,
        ephemeral=args.ephemeral,
        sem_estilo=args.sem_estilo,
        workdir=args.workdir,
        conf_dir=args.conf_dir,
        hide=args.hide,
        show=args.show,
    )


if __name__ == "__main__":
    raise SystemExit(main())
