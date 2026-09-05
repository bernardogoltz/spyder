"""Resolucao de projeto/workdir e o processo-filho limpo (secoes 5.1 e 5.2).

Contrato exercitado::

    setup_spyder.launcher
        resolve_workdir(workdir=None, cwd=None) -> Path
        build_child_command(*, conf_dir, workdir, agent, autostart,
                            spyder_args=()) -> tuple[list[str], dict[str, str]]

`build_child_command` devolve o comando do bootstrap filho e o ambiente que
ele recebe. O plano exige que o processo principal *nao* importe a config do
Spyder: quem define ``SPYDER_CONFDIR`` e o pai, quem importa o Spyder e o
filho.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from conftest import require_attr, require_module

pytestmark = [pytest.mark.unit, pytest.mark.phase2]


@pytest.fixture()
def launcher():
    return require_module("setup_spyder.launcher", "launcher separado (Fase 2)")


@pytest.fixture()
def resolve_workdir(launcher):
    return require_attr(launcher, "resolve_workdir")


@pytest.fixture()
def build_child_command(launcher):
    return require_attr(launcher, "build_child_command")


# Workdir ----------------------------------------------------------------


def test_sem_workdir_usa_o_diretorio_corrente(resolve_workdir, project_root):
    assert Path(resolve_workdir(cwd=project_root)) == project_root.resolve()


def test_workdir_relativo_e_resolvido_contra_o_cwd(resolve_workdir, project_root):
    resolved = resolve_workdir(workdir="src", cwd=project_root)
    assert Path(resolved) == (project_root / "src").resolve()


def test_workdir_sempre_absoluto_e_normalizado(resolve_workdir, project_root):
    resolved = Path(resolve_workdir(workdir="src/../src", cwd=project_root))
    assert resolved.is_absolute()
    assert ".." not in resolved.parts


def test_workdir_com_espaco_e_acento_sobrevive_intacto(
    resolve_workdir, awkward_project_root
):
    resolved = Path(resolve_workdir(workdir=awkward_project_root))
    assert resolved == awkward_project_root.resolve()
    assert resolved.is_dir()


def test_workdir_aceita_str_e_path(resolve_workdir, project_root):
    assert Path(resolve_workdir(workdir=str(project_root))) == Path(
        resolve_workdir(workdir=project_root)
    )


# Processo-filho ---------------------------------------------------------


@pytest.fixture()
def child(build_child_command, tmp_path, project_root):
    command, env = build_child_command(
        conf_dir=tmp_path / "perfil",
        workdir=project_root,
        agent="codex",
        autostart=True,
        spyder_args=["--debug-info", "verbose", "--multithread"],
    )
    return command, env


def test_o_filho_usa_o_mesmo_interpretador(child):
    command, _ = child
    assert command[0] == sys.executable, (
        "o Spyder tem de subir com o Python do .venv do projeto"
    )


def test_o_comando_e_uma_lista_de_argumentos(child):
    command, _ = child
    assert isinstance(command, list)
    assert all(isinstance(part, str) for part in command)


def test_o_ambiente_carrega_o_contexto_antes_de_importar_o_spyder(child, tmp_path):
    _, env = child
    assert env["SPYDER_CONFDIR"] == str(tmp_path / "perfil")
    assert env["SETUP_SPYDER_AGENT"] == "codex"
    assert "SETUP_SPYDER_WORKDIR" in env
    assert env["SETUP_SPYDER_AUTOSTART"] in {"0", "1"}


def test_o_ambiente_do_usuario_e_herdado(child):
    _, env = child
    herdadas = [k for k in os.environ if k in env and k.isupper()]
    assert herdadas, "o ambiente do usuario nao pode ser descartado"


def test_o_launcher_nao_limpa_as_variaveis_conda(build_child_command, tmp_path,
                                                 project_root, monkeypatch):
    """Secao 5.3: nao mexer na descoberta de ambientes sem um caso comprovado."""
    monkeypatch.setenv("CONDA_PREFIX", "/opt/conda/envs/demo")
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "demo")
    _, env = build_child_command(
        conf_dir=tmp_path / "perfil", workdir=project_root, agent="none",
        autostart=False,
    )
    assert env.get("CONDA_PREFIX") == "/opt/conda/envs/demo"
    assert env.get("CONDA_DEFAULT_ENV") == "demo"


def test_os_argumentos_extras_chegam_na_ordem(child):
    command, _ = child
    posicoes = [
        command.index(arg)
        for arg in ("--debug-info", "verbose", "--multithread")
        if arg in command
    ]
    assert len(posicoes) == 3, f"argumentos extras sumiram de {command}"
    assert posicoes == sorted(posicoes)


def test_o_launcher_nao_desliga_os_web_widgets(child):
    command, _ = child
    assert "--no-web-widgets" not in command, (
        "secao 6: o painel depende de QWebEngineView"
    )


def test_perfil_efemero_pode_forcar_nova_instancia(build_child_command, tmp_path,
                                                   project_root):
    command, _ = build_child_command(
        conf_dir=tmp_path / "perfil", workdir=project_root, agent="none",
        autostart=False, profile="ephemeral",
    )
    assert "--new-instance" in command


def test_perfil_de_projeto_respeita_a_instancia_unica(build_child_command, tmp_path,
                                                      project_root):
    """Secao 5.3: nao forcar --new-instance sobre o mesmo diretorio de perfil."""
    command, _ = build_child_command(
        conf_dir=tmp_path / "perfil", workdir=project_root, agent="none",
        autostart=False, profile="project",
    )
    assert "--new-instance" not in command


def test_agente_desligado_nao_vaza_provedor_para_o_filho(build_child_command,
                                                         tmp_path, project_root):
    _, env = build_child_command(
        conf_dir=tmp_path / "perfil", workdir=project_root, agent="none",
        autostart=False,
    )
    assert env["SETUP_SPYDER_AGENT"] == "none"
    assert env["SETUP_SPYDER_AUTOSTART"] == "0"
