"""O Spyder acha o plugin - e continua abrindo quando o backend falha.

Secao 9 (Fase 0: "entry point descoberto no Spyder 5.5.6 e no fork local") e
secao 6.1 ("Plugin sumir por ImportError no carregamento" na tabela de riscos).

`find_external_plugins()` engole `ImportError` e so imprime em STDERR, entao a
diferenca entre "plugin degradado" e "plugin invisivel" e exatamente o que
estes testes medem.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from conftest import child_env, not_implemented

pytestmark = [pytest.mark.integration, pytest.mark.phase0, pytest.mark.slow]

NOME = "setup_spyder_ai"

DESCOBRIR = """
import json, sys
from spyder.app.find_plugins import find_external_plugins
achados = find_external_plugins()
print("RESULTADO " + json.dumps(sorted(achados)))
"""

# Mesmo teste, mas com o backend de PTY sabotado antes de qualquer import.
DESCOBRIR_SEM_BACKEND = """
import builtins, json, sys

_real = builtins.__import__
BLOQUEADOS = {"winpty", "ptyprocess", "pexpect"}

def bloqueia(name, *args, **kwargs):
    if name.split(".")[0] in BLOQUEADOS:
        raise ImportError("No module named %r (bloqueado pelo teste)" % name)
    return _real(name, *args, **kwargs)

builtins.__import__ = bloqueia

from spyder.app.find_plugins import find_external_plugins
achados = find_external_plugins()
print("RESULTADO " + json.dumps(sorted(achados)))
"""


def _descobrir(codigo, isolated_home):
    saida = subprocess.run(
        [sys.executable, "-c", codigo],
        capture_output=True,
        text=True,
        env=child_env(isolated_home),
        timeout=300,
    )
    linhas = [
        linha for linha in saida.stdout.splitlines() if linha.startswith("RESULTADO ")
    ]
    assert linhas, f"a sonda nao respondeu.\nstdout={saida.stdout}\nstderr={saida.stderr}"
    return json.loads(linhas[-1][len("RESULTADO ") :]), saida.stderr


@pytest.fixture(autouse=True)
def _exige_spyder(spyder_available):
    if not spyder_available:
        pytest.skip("Spyder nao esta instalado neste ambiente")


def test_o_spyder_descobre_o_plugin(isolated_home):
    achados, stderr = _descobrir(DESCOBRIR, isolated_home)
    if NOME not in achados:
        not_implemented(
            f"plugin externo {NOME} (find_external_plugins achou {achados}; "
            f"stderr={stderr.strip()[:400]})"
        )
    assert NOME in achados


def test_a_descoberta_nao_levanta_spyder_api_error(isolated_home):
    """`SpyderAPIError` aqui significa entry point != PluginClass.NAME."""
    _, stderr = _descobrir(DESCOBRIR, isolated_home)
    assert "SpyderAPIError" not in stderr, stderr


def test_o_plugin_sobrevive_a_ausencia_do_backend_de_pty(isolated_home):
    """Secao 6.1: import tardio, para o plugin degradar em vez de sumir."""
    achados, stderr = _descobrir(DESCOBRIR_SEM_BACKEND, isolated_home)
    if not achados:
        not_implemented(f"plugin externo {NOME} (stderr={stderr.strip()[:400]})")
    assert NOME in achados, (
        "sem pywinpty/ptyprocess o plugin sumiu da descoberta em vez de "
        f"aparecer degradado. stderr={stderr.strip()[:400]}"
    )


def test_a_falha_de_import_nao_e_silenciosa(isolated_home):
    """Secao 10: "capturar stderr/logs para que falhas de descoberta do plugin
    nao sejam silenciosas"."""
    achados, stderr = _descobrir(DESCOBRIR_SEM_BACKEND, isolated_home)
    if NOME not in achados:
        assert stderr.strip(), (
            "o plugin sumiu e nada foi escrito em stderr - falha invisivel"
        )
