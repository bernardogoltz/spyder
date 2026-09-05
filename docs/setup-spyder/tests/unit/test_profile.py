"""Perfis: resolucao, seed versionado e reset seguro (secoes 5.1 e 5.3).

Contrato exercitado::

    setup_spyder.profile
        SEED_VERSION: int
        resolve_conf_dir(profile="ephemeral", project_root=None,
                         conf_dir=None) -> Path
        seed_profile(conf_dir, *, version=SEED_VERSION) -> bool
        reset_profile(conf_dir, *, project_root=None) -> Path

`seed_profile` devolve ``True`` quando escreveu o seed e ``False`` quando o
perfil ja estava na versao corrente - e o "nao regravar preferencias em toda
inicializacao" da secao 5.3.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from conftest import require_attr, require_module

pytestmark = [pytest.mark.unit, pytest.mark.phase2]


@pytest.fixture()
def profile_mod():
    return require_module("setup_spyder.profile", "modulo de perfis (Fase 2)")


@pytest.fixture()
def resolve_conf_dir(profile_mod):
    return require_attr(profile_mod, "resolve_conf_dir")


# Resolucao do diretorio -------------------------------------------------


def test_efemero_fica_em_area_temporaria_e_nunca_no_home(
    resolve_conf_dir, project_root
):
    conf_dir = resolve_conf_dir(profile="ephemeral", project_root=project_root)
    temp_root = Path(tempfile.gettempdir()).resolve()
    assert temp_root in Path(conf_dir).resolve().parents
    assert Path.home() / ".spyder-py3" != Path(conf_dir)


def test_efemero_da_um_diretorio_novo_a_cada_chamada(resolve_conf_dir, project_root):
    first = resolve_conf_dir(profile="ephemeral", project_root=project_root)
    second = resolve_conf_dir(profile="ephemeral", project_root=project_root)
    assert Path(first) != Path(second)


def test_perfil_de_projeto_mora_dentro_do_repositorio(resolve_conf_dir, project_root):
    conf_dir = Path(resolve_conf_dir(profile="project", project_root=project_root))
    assert conf_dir == project_root / ".spyproject" / "setup-spyder"


def test_perfil_de_projeto_e_estavel_entre_chamadas(resolve_conf_dir, project_root):
    first = resolve_conf_dir(profile="project", project_root=project_root)
    second = resolve_conf_dir(profile="project", project_root=project_root)
    assert Path(first) == Path(second)


def test_conf_dir_explicito_tem_precedencia_sobre_os_dois_modos(
    resolve_conf_dir, project_root, tmp_path
):
    escolhido = tmp_path / "meu-perfil"
    for profile in ("ephemeral", "project"):
        resolved = resolve_conf_dir(
            profile=profile, project_root=project_root, conf_dir=escolhido
        )
        assert Path(resolved) == escolhido


def test_resolucao_aguenta_caminho_com_espaco_e_acento(
    resolve_conf_dir, awkward_project_root
):
    conf_dir = Path(
        resolve_conf_dir(profile="project", project_root=awkward_project_root)
    )
    assert conf_dir.is_absolute()
    assert "análise maçã" in str(conf_dir)


# Seed versionado --------------------------------------------------------


def test_seed_escreve_na_primeira_vez_e_nao_na_segunda(profile_mod, tmp_path):
    seed_profile = require_attr(profile_mod, "seed_profile")
    conf_dir = tmp_path / "perfil"

    assert seed_profile(conf_dir) is True, "o primeiro seed precisa escrever"
    assinatura = {
        path: path.stat().st_mtime_ns
        for path in sorted(conf_dir.rglob("*"))
        if path.is_file()
    }
    assert assinatura, "o seed nao criou nenhum arquivo"

    assert seed_profile(conf_dir) is False, (
        "secao 5.3: nao regravar preferencias em toda inicializacao"
    )
    depois = {
        path: path.stat().st_mtime_ns
        for path in sorted(conf_dir.rglob("*"))
        if path.is_file()
    }
    assert depois == assinatura


def test_seed_e_reaplicado_quando_a_versao_sobe(profile_mod, tmp_path):
    seed_profile = require_attr(profile_mod, "seed_profile")
    version = require_attr(profile_mod, "SEED_VERSION")
    conf_dir = tmp_path / "perfil"

    assert seed_profile(conf_dir, version=version) is True
    assert seed_profile(conf_dir, version=version) is False
    assert seed_profile(conf_dir, version=version + 1) is True


def test_seed_preserva_ajuste_manual_de_chave_nao_semeada(profile_mod, tmp_path):
    """Migrar versao nao pode zerar o perfil inteiro do usuario."""
    seed_profile = require_attr(profile_mod, "seed_profile")
    version = require_attr(profile_mod, "SEED_VERSION")
    conf_dir = tmp_path / "perfil"
    seed_profile(conf_dir, version=version)

    marca = conf_dir / "config" / "marca-do-usuario.txt"
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text("nao me apague", encoding="utf-8")

    seed_profile(conf_dir, version=version + 1)
    assert marca.read_text(encoding="utf-8") == "nao me apague"


# Reset seguro -----------------------------------------------------------


def test_reset_recria_o_perfil_resolvido(profile_mod, tmp_path):
    reset_profile = require_attr(profile_mod, "reset_profile")
    conf_dir = tmp_path / "projeto" / ".spyproject" / "setup-spyder"
    (conf_dir / "config").mkdir(parents=True)
    lixo = conf_dir / "config" / "spyder.ini"
    lixo.write_text("[main]\n", encoding="utf-8")

    reset_profile(conf_dir, project_root=tmp_path / "projeto")
    assert conf_dir.is_dir()
    assert not lixo.exists()


@pytest.mark.parametrize(
    "alvo",
    [
        "home",
        "home_spyder",
        "raiz_do_projeto",
        "temp_root",
        "fora_do_projeto",
    ],
)
def test_reset_recusa_caminho_fora_do_perfil_esperado(
    profile_mod, tmp_path, project_root, alvo
):
    """"--reset-profile so remove/recria o perfil resolvido depois de validar
    que o caminho esta dentro do diretorio esperado" (secao 5.1)."""
    reset_profile = require_attr(profile_mod, "reset_profile")
    alvos = {
        "home": Path.home(),
        "home_spyder": Path.home() / ".spyder-py3",
        "raiz_do_projeto": project_root,
        "temp_root": Path(tempfile.gettempdir()),
        "fora_do_projeto": tmp_path / "outro-lugar",
    }
    caminho = alvos[alvo]
    testemunha = None
    if caminho == alvos["fora_do_projeto"]:
        caminho.mkdir(parents=True, exist_ok=True)
        testemunha = caminho / "importante.txt"
        testemunha.write_text("nao me apague", encoding="utf-8")

    with pytest.raises((ValueError, PermissionError)):
        reset_profile(caminho, project_root=project_root)

    assert caminho.exists(), f"reset_profile apagou {caminho}"
    if testemunha is not None:
        assert testemunha.read_text(encoding="utf-8") == "nao me apague"


def test_reset_nao_segue_link_para_fora_do_projeto(profile_mod, tmp_path, project_root):
    reset_profile = require_attr(profile_mod, "reset_profile")
    alvo = tmp_path / "fora"
    alvo.mkdir()
    (alvo / "importante.txt").write_text("nao me apague", encoding="utf-8")

    link = project_root / ".spyproject" / "setup-spyder"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(alvo, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("sem permissao para criar symlink nesta maquina")

    with pytest.raises((ValueError, PermissionError)):
        reset_profile(link, project_root=project_root)
    assert (alvo / "importante.txt").exists()


def test_perfil_de_projeto_nao_toca_a_config_global(
    resolve_conf_dir, profile_mod, project_root, global_conf_guard
):
    seed_profile = require_attr(profile_mod, "seed_profile")
    conf_dir = resolve_conf_dir(profile="project", project_root=project_root)
    seed_profile(conf_dir)
    assert Path(conf_dir).is_dir()
