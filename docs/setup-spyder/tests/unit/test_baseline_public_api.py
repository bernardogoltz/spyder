"""Fase 0 - congela os contratos publicos atuais de `setup-spyder`.

Estes testes rodam contra o pacote como ele esta hoje (0.2.0) e **nao devem
pular**. Eles existem para que a refatoracao da Fase 2 (`cli.py` /
`launcher.py` / `profile.py`) nao quebre quem ja importa o pacote:

    from setup_spyder import launch
    launch()

O plano (secao 2.1) e explicito: "A evolucao deve manter esses contratos".
"""

from __future__ import annotations

import inspect
import sys

import pytest

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

pytestmark = [pytest.mark.unit, pytest.mark.phase0]


# Superficie importavel --------------------------------------------------


def test_exporta_launch_main_e_open_spyder(setup_spyder):
    for name in ("launch", "main", "open_spyder", "__version__"):
        assert hasattr(setup_spyder, name), f"setup_spyder.{name} sumiu"
    assert set(setup_spyder.__all__) >= {
        "__version__",
        "launch",
        "main",
        "open_spyder",
    }


def test_open_spyder_continua_sendo_alias_de_launch(setup_spyder):
    assert setup_spyder.open_spyder is setup_spyder.launch


def test_versao_e_uma_string_com_pontos(setup_spyder):
    assert isinstance(setup_spyder.__version__, str)
    assert setup_spyder.__version__.count(".") >= 2


# Assinatura de `launch` -------------------------------------------------

LAUNCH_KEYWORDS = {
    "no_launch": False,
    "keep_config": False,
    "workdir": None,
    "hide": (),
    "show": (),
}


def test_launch_mantem_o_primeiro_parametro_posicional(setup_spyder):
    parameters = list(inspect.signature(setup_spyder.launch).parameters.values())
    first = parameters[0]
    assert first.name == "spyder_args"
    assert first.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert first.default == ()


@pytest.mark.parametrize("name, default", sorted(LAUNCH_KEYWORDS.items()))
def test_launch_mantem_cada_opcao_atual(setup_spyder, name, default):
    parameters = inspect.signature(setup_spyder.launch).parameters
    assert name in parameters, f"launch() perdeu a opcao {name!r}"
    assert parameters[name].default == default


def test_parametros_novos_de_launch_sao_keyword_only_com_default(setup_spyder):
    """Qualquer opcao nova (`agent`, `profile`, `conf_dir`...) tem de ser
    opcional e nomeada, senao `launch()` sem argumentos deixa de funcionar."""
    parameters = list(inspect.signature(setup_spyder.launch).parameters.values())
    for parameter in parameters[1:]:
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"{parameter.name} precisa ser keyword-only"
        )
        assert parameter.default is not inspect.Parameter.empty, (
            f"{parameter.name} precisa ter valor padrao"
        )


def test_main_aceita_argv_opcional_e_devolve_int(setup_spyder):
    parameters = inspect.signature(setup_spyder.main).parameters
    assert list(parameters) == ["argv"]
    assert parameters["argv"].default is None


# Pontos de entrada de console ------------------------------------------


@pytest.mark.parametrize(
    "script, target",
    [
        ("setup-spyder", "setup_spyder.cli:main"),
        ("setup-spyder-integration", "setup_spyder.integration:main"),
    ],
)
def test_console_scripts_continuam_registrados(script, target):
    found = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert script in found, f"o console_script {script} sumiu da distribuicao"
    assert found[script] == target


def test_o_pacote_nao_depende_de_sdk_de_provedor():
    """Secao 4 do plano: nao adicionar `claude-agent-sdk` nem SDK da OpenAI."""
    from importlib.metadata import requires

    declared = requires("setup-spyder") or []
    lowered = " ".join(declared).lower()
    for forbidden in ("claude-agent-sdk", "anthropic", "openai"):
        assert forbidden not in lowered, (
            f"o MVP nao deve depender de {forbidden}: {declared}"
        )
