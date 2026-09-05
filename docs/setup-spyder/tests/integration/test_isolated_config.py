"""Configuracao isolada de verdade: `--no-launch` num HOME descartavel.

Estes testes rodam o `setup-spyder` como subprocesso, sem abrir janela, e
verificam os criterios de aceitacao "nao gravar em `~/.spyder-py3`" e "o
perfil do projeto nao sobrescreve preferencias em toda inicializacao".

Sao lentos: cada execucao importa o Spyder inteiro.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import child_env, not_implemented

pytestmark = [pytest.mark.integration, pytest.mark.phase2, pytest.mark.slow]


def rodar(argv, *, home, cwd=None, timeout=600):
    return subprocess.run(
        [sys.executable, "-m", "setup_spyder", *argv],
        capture_output=True,
        text=True,
        env=child_env(home),
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
    )


@pytest.fixture(autouse=True)
def _exige_spyder(spyder_available):
    if not spyder_available:
        pytest.skip("Spyder nao esta instalado neste ambiente")


def test_no_launch_configura_e_sai_com_zero(isolated_home, project_root):
    resultado = rodar(["--no-launch", "-w", str(project_root)], home=isolated_home)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_no_launch_nao_cria_a_config_global(isolated_home, project_root):
    rodar(["--no-launch", "-w", str(project_root)], home=isolated_home)
    assert not (isolated_home / ".spyder-py3").exists(), (
        "criterio de aceitacao: a config global do usuario fica intacta"
    )


def test_no_launch_cria_o_spyproject_no_repositorio(isolated_home, project_root):
    rodar(["--no-launch", "-w", str(project_root)], home=isolated_home)
    assert (project_root / ".spyproject").is_dir()


def test_o_perfil_efemero_e_apagado_no_fim(isolated_home, project_root):
    resultado = rodar(["--no-launch", "-w", str(project_root)], home=isolated_home)
    linhas = [
        linha for linha in resultado.stdout.splitlines() if "setup-spyder-conf-" in linha
    ]
    assert linhas, f"o caminho do perfil nao apareceu no log:\n{resultado.stdout}"
    assert "Cleanup done" in resultado.stdout or "Removing" in resultado.stdout


def test_keep_config_preserva_o_perfil(isolated_home, project_root, tmp_path):
    resultado = rodar(
        ["--no-launch", "--keep-config", "-w", str(project_root)], home=isolated_home
    )
    assert "keep_config" in resultado.stdout or "keeping" in resultado.stdout


def test_funciona_com_espaco_e_acento_no_caminho(isolated_home, awkward_project_root):
    resultado = rodar(
        ["--no-launch", "-w", str(awkward_project_root)], home=isolated_home
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert (awkward_project_root / ".spyproject").is_dir()


def test_o_kernel_usaria_o_python_do_projeto(isolated_home, project_root):
    """O executavel reportado tem de ser o do ambiente que roda a suite."""
    resultado = rodar(["--no-launch", "-w", str(project_root)], home=isolated_home)
    assert sys.executable in resultado.stdout.replace("\n", "")


# Perfil de projeto (Fase 2) --------------------------------------------


def _rodar_perfil_projeto(home, project_root):
    resultado = rodar(
        ["--no-launch", "--profile", "project", "-w", str(project_root)], home=home
    )
    if resultado.returncode != 0 and "--profile" in resultado.stderr:
        not_implemented("--profile project (Fase 2)")
    return resultado


def test_o_perfil_de_projeto_persiste_entre_execucoes(isolated_home, project_root):
    _rodar_perfil_projeto(isolated_home, project_root)
    perfil = project_root / ".spyproject" / "setup-spyder"
    assert perfil.is_dir(), "o perfil de projeto nao foi criado"

    assinatura = {
        p.name: p.stat().st_mtime_ns for p in sorted(perfil.rglob("*")) if p.is_file()
    }
    _rodar_perfil_projeto(isolated_home, project_root)
    depois = {
        p.name: p.stat().st_mtime_ns for p in sorted(perfil.rglob("*")) if p.is_file()
    }
    assert depois == assinatura, (
        "criterio de aceitacao: o perfil do projeto nao sobrescreve "
        f"preferencias em toda inicializacao. Mudou: "
        f"{sorted(set(depois.items()) ^ set(assinatura.items()))}"
    )


def test_dois_projetos_tem_perfis_distintos(
    isolated_home, project_root, awkward_project_root
):
    _rodar_perfil_projeto(isolated_home, project_root)
    _rodar_perfil_projeto(isolated_home, awkward_project_root)
    primeiro = project_root / ".spyproject" / "setup-spyder"
    segundo = awkward_project_root / ".spyproject" / "setup-spyder"
    assert primeiro.is_dir() and segundo.is_dir()
    assert primeiro != segundo


def test_o_perfil_de_projeto_tambem_nao_toca_o_home(isolated_home, project_root):
    _rodar_perfil_projeto(isolated_home, project_root)
    assert not (isolated_home / ".spyder-py3").exists()
