"""Argumentos da CLI: o que ja existe nao pode mudar; o que o plano acrescenta.

Secao 5.1 do plano. Os testes dos argumentos novos (`--agent`, `--profile`,
`--conf-dir`, `--reset-profile`) pulam enquanto o argparse ainda nao os
conhece, e viram falha com ``SETUP_SPYDER_STRICT=1``.
"""

from __future__ import annotations

import contextlib
import io

import pytest

from conftest import not_implemented

pytestmark = [pytest.mark.unit, pytest.mark.phase0]


def parse(cli, argv):
    return cli.parse_args(argv)


def parse_or_pending(cli, argv, what):
    """Faz o parse; se o argparse rejeitar a opcao, e entrega pendente."""
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            return cli.parse_args(argv)
    except SystemExit:
        not_implemented(f"{what} (argparse recusou {argv!r})")


# Argumentos de hoje -----------------------------------------------------


def test_sem_argumentos_usa_os_defaults_atuais(setup_spyder_cli):
    args = parse(setup_spyder_cli, [])
    assert args.no_launch is False
    assert args.keep_config is False
    assert args.workdir is None
    assert args.hide == []
    assert args.show == []
    assert args.spyder_args == []


@pytest.mark.parametrize("flag", ["--no-launch", "--keep-config"])
def test_flags_booleanas_continuam_existindo(setup_spyder_cli, flag):
    args = parse(setup_spyder_cli, [flag])
    assert getattr(args, flag.lstrip("-").replace("-", "_")) is True


@pytest.mark.parametrize("flag", ["-w", "--workdir"])
def test_workdir_aceita_forma_curta_e_longa(setup_spyder_cli, flag, tmp_path):
    args = parse(setup_spyder_cli, [flag, str(tmp_path)])
    assert args.workdir == str(tmp_path)


def test_hide_e_show_sao_repetiveis(setup_spyder_cli):
    args = parse(setup_spyder_cli, ["--hide", "a,b", "--hide", "c", "--show", ".github"])
    assert args.hide == ["a,b", "c"]
    assert args.show == [".github"]


def test_argumentos_extras_vao_para_o_spyder_na_ordem(setup_spyder_cli):
    args = parse(setup_spyder_cli, ["--", "--debug-info", "minimal", "--multithread"])
    forwarded = [a for a in args.spyder_args if a != "--"]
    assert forwarded == ["--debug-info", "minimal", "--multithread"]


def test_argumento_desconhecido_ainda_e_erro_de_uso(setup_spyder_cli):
    with contextlib.redirect_stderr(io.StringIO()):
        with pytest.raises(SystemExit) as excinfo:
            setup_spyder_cli.parse_args(["--nao-existe"])
    assert excinfo.value.code == 2


# Blocklist do Project pane ---------------------------------------------


def test_resolve_hidden_paths_soma_hide_e_subtrai_show(setup_spyder_cli):
    resolved = setup_spyder_cli.resolve_hidden_paths(
        hide=["segredo, outro"], show=[".github"]
    )
    assert "segredo" in resolved and "outro" in resolved
    assert ".github" not in resolved
    assert ".venv" in resolved  # continua vindo dos defaults
    assert resolved == sorted(resolved), "a lista precisa ser deterministica"


def test_resolve_hidden_paths_ignora_entradas_vazias(setup_spyder_cli):
    resolved = setup_spyder_cli.resolve_hidden_paths(hide=[" , ,"], show=[""])
    assert "" not in resolved
    assert set(resolved) == set(setup_spyder_cli.HIDDEN_PATHS)


# Argumentos novos do plano ---------------------------------------------


@pytest.mark.phase2
@pytest.mark.parametrize("agent", ["auto", "codex", "claude", "none"])
def test_agent_aceita_os_quatro_perfis(setup_spyder_cli, agent):
    args = parse_or_pending(setup_spyder_cli, ["--agent", agent], "--agent")
    assert args.agent == agent


@pytest.mark.phase2
def test_agent_recusa_provedor_desconhecido(setup_spyder_cli):
    parse_or_pending(setup_spyder_cli, ["--agent", "codex"], "--agent")
    with contextlib.redirect_stderr(io.StringIO()):
        with pytest.raises(SystemExit):
            setup_spyder_cli.parse_args(["--agent", "gpt-hipotetico"])


@pytest.mark.phase2
@pytest.mark.parametrize("profile", ["ephemeral", "project"])
def test_profile_aceita_efemero_e_de_projeto(setup_spyder_cli, profile):
    args = parse_or_pending(setup_spyder_cli, ["--profile", profile], "--profile")
    assert args.profile == profile


@pytest.mark.phase2
def test_profile_efemero_continua_sendo_o_padrao(setup_spyder_cli):
    """Secao 5.1: o padrao inicial nao muda, para nao quebrar usuarios."""
    parse_or_pending(setup_spyder_cli, ["--profile", "project"], "--profile")
    assert parse(setup_spyder_cli, []).profile == "ephemeral"


@pytest.mark.phase2
def test_conf_dir_e_reset_profile_existem(setup_spyder_cli, tmp_path):
    args = parse_or_pending(
        setup_spyder_cli,
        ["--conf-dir", str(tmp_path), "--reset-profile"],
        "--conf-dir / --reset-profile",
    )
    assert args.conf_dir == str(tmp_path)
    assert args.reset_profile is True


@pytest.mark.phase2
def test_opcoes_novas_convivem_com_as_antigas(setup_spyder_cli, tmp_path):
    argv = [
        "--no-launch",
        "--keep-config",
        "-w",
        str(tmp_path),
        "--hide",
        "docs",
        "--agent",
        "codex",
        "--profile",
        "project",
        "--",
        "--debug-info",
        "verbose",
    ]
    args = parse_or_pending(setup_spyder_cli, argv, "combinacao de opcoes novas")
    assert args.no_launch and args.keep_config
    assert args.workdir == str(tmp_path)
    assert args.hide == ["docs"]
    assert args.agent == "codex"
    assert args.profile == "project"
    assert [a for a in args.spyder_args if a != "--"] == ["--debug-info", "verbose"]


@pytest.mark.parametrize(
    "spyder_flag", ["--defaults", "--reset", "--safe-mode", "--no-web-widgets"]
)
def test_o_parser_nao_reclama_de_flags_do_spyder(setup_spyder_cli, spyder_flag):
    """`spyder_args` tem de continuar sendo REMAINDER: flags do Spyder passam
    inteiras, sem virar erro de uso do `setup-spyder`."""
    args = parse(setup_spyder_cli, ["--", spyder_flag])
    assert spyder_flag in args.spyder_args
