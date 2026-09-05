"""O entry point `spyder.plugins` e o `NAME` do plugin (secao 4).

`spyder/app/find_plugins.py` levanta `SpyderAPIError` quando o nome do entry
point difere de `plugin_class.NAME`, e engole `ImportError` imprimindo em
STDERR - ou seja, um plugin com import quebrado simplesmente *some*. Estes
testes reproduzem as duas verificacoes fora do Spyder.
"""

from __future__ import annotations

import importlib
import sys

import pytest

from conftest import not_implemented, require_attr, require_module

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

pytestmark = [pytest.mark.unit, pytest.mark.phase0]

EXPECTED_NAME = "setup_spyder_ai"
EXPECTED_TARGET = "setup_spyder.plugin.plugin:AITerminalPlugin"


@pytest.fixture()
def plugin_entry_point():
    found = {ep.name: ep for ep in entry_points(group="spyder.plugins")}
    if EXPECTED_NAME not in found:
        not_implemented(
            f"entry point spyder.plugins:{EXPECTED_NAME} "
            f"(encontrados: {sorted(found)})"
        )
    return found[EXPECTED_NAME]


def test_o_entry_point_aponta_para_a_classe_do_plano(plugin_entry_point):
    assert plugin_entry_point.value.replace(" ", "") == EXPECTED_TARGET


def test_o_modulo_do_entry_point_importa(plugin_entry_point):
    """Um ImportError aqui vira um plugin invisivel no Spyder, nao um erro."""
    module = importlib.import_module(plugin_entry_point.module)
    assert getattr(module, plugin_entry_point.attr, None) is not None


def test_nome_do_entry_point_e_igual_ao_name_da_classe(plugin_entry_point):
    module = importlib.import_module(plugin_entry_point.module)
    plugin_class = getattr(module, plugin_entry_point.attr)
    assert plugin_class.NAME == plugin_entry_point.name, (
        "find_plugins.find_external_plugins() levanta SpyderAPIError quando "
        "esses dois valores divergem"
    )


def test_o_plugin_vem_da_distribuicao_setup_spyder(plugin_entry_point):
    """Secao 2.1: o plugin viaja na mesma wheel do `setup-spyder`."""
    assert plugin_entry_point.dist.name.replace("_", "-") == "setup-spyder"


def test_o_name_nao_colide_com_plugin_interno_do_spyder(spyder_available):
    if not spyder_available:
        pytest.skip("Spyder nao esta instalado neste ambiente")
    from spyder.api.plugins import Plugins
    from spyder.api.utils import get_class_values

    assert EXPECTED_NAME not in get_class_values(Plugins), (
        "um NAME igual ao de um plugin interno faz o Spyder tratar o plugin "
        "como interno e ignorar o externo"
    )


# Forma da classe --------------------------------------------------------


@pytest.fixture()
def plugin_class():
    module = require_module("setup_spyder.plugin.plugin", "AITerminalPlugin (Fase 3)")
    return require_attr(module, "AITerminalPlugin")


@pytest.mark.phase3
def test_a_classe_declara_o_name_esperado(plugin_class):
    assert plugin_class.NAME == EXPECTED_NAME


@pytest.mark.phase3
def test_a_classe_declara_o_grafo_de_dependencias_do_plano(plugin_class):
    if not importlib.util.find_spec("spyder"):
        pytest.skip("Spyder nao esta instalado neste ambiente")
    from spyder.api.plugins import Plugins

    assert Plugins.Preferences in plugin_class.REQUIRES
    assert set(plugin_class.OPTIONAL) >= {
        Plugins.Editor,
        Plugins.Projects,
        Plugins.WorkingDirectory,
        Plugins.MainMenu,
    }
    assert Plugins.IPythonConsole in plugin_class.TABIFY


@pytest.mark.phase3
def test_o_plugin_tem_config_propria(plugin_class):
    assert plugin_class.CONF_FILE is True
    assert getattr(plugin_class, "CONF_DEFAULTS", None), (
        "secao 6: o plugin precisa de CONF_DEFAULTS"
    )
    assert isinstance(getattr(plugin_class, "CONF_VERSION", None), str), (
        "secao 6: o plugin precisa de versao de configuracao"
    )


@pytest.mark.phase3
def test_o_plugin_pede_web_widgets(plugin_class):
    """Secao 6: o painel depende de QWebEngineView."""
    assert getattr(plugin_class, "REQUIRE_WEB_WIDGETS", False) is True


@pytest.mark.phase3
def test_importar_o_plugin_nao_importa_o_backend_de_pty(plugin_class):
    """Secao 6.1: import tardio, senao uma dependencia opcional ausente faz o
    plugin sumir durante a descoberta."""
    del plugin_class
    codigo = (
        "import sys;"
        "import setup_spyder.plugin.plugin;"
        "mods = set(sys.modules);"
        "print([m for m in ('winpty', 'ptyprocess', 'pexpect') if m in mods])"
    )
    import subprocess

    saida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    )
    assert saida.stdout.strip() == "[]", (
        f"backend de PTY importado cedo demais: {saida.stdout.strip()}"
    )
