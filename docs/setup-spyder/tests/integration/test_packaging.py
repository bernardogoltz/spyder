"""Fase 6: o que precisa estar *dentro* do artefato.

Roda contra a distribuicao instalada por padrao. Apontando
``SETUP_SPYDER_WHEEL`` para um `.whl` construido, os mesmos testes inspecionam
o arquivo - que e o cenario que o plano pede ("testar wheel e sdist em
ambientes limpos, nao apenas instalacao editavel").
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from conftest import not_implemented

pytestmark = [pytest.mark.integration, pytest.mark.phase6]

ASSETS = ("terminal.html", "terminal.js", "xterm.js", "xterm.css")
CDN = ("cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com", "//cdn.")


class Artefato:
    """Vista unificada sobre uma wheel ou sobre o pacote instalado."""

    def __init__(self):
        self.wheel = os.environ.get("SETUP_SPYDER_WHEEL")

    def nomes(self) -> list[str]:
        if self.wheel:
            with zipfile.ZipFile(self.wheel) as zf:
                return zf.namelist()
        import setup_spyder

        raiz = Path(setup_spyder.__file__).parent
        return [
            str(p.relative_to(raiz.parent)).replace("\\", "/")
            for p in raiz.rglob("*")
            if p.is_file()
        ]

    def ler(self, sufixo: str) -> str:
        for nome in self.nomes():
            if nome.endswith(sufixo):
                if self.wheel:
                    with zipfile.ZipFile(self.wheel) as zf:
                        return zf.read(nome).decode("utf-8", "replace")
                import setup_spyder

                raiz = Path(setup_spyder.__file__).parent.parent
                return (raiz / nome).read_text(encoding="utf-8", errors="replace")
        return ""


@pytest.fixture(scope="module")
def artefato():
    return Artefato()


@pytest.mark.parametrize("asset", ASSETS)
def test_os_assets_web_viajam_no_artefato(artefato, asset):
    nomes = artefato.nomes()
    if not any("plugin/assets" in nome for nome in nomes):
        not_implemented("assets web do painel (Fase 3/6)")
    assert any(nome.endswith(f"plugin/assets/{asset}") for nome in nomes), (
        f"{asset} ficou de fora: {[n for n in nomes if 'assets' in n]}"
    )


def test_o_terminal_nao_carrega_javascript_de_cdn(artefato):
    """Secao 6.2: apenas assets empacotados localmente."""
    html = artefato.ler("plugin/assets/terminal.html")
    if not html:
        not_implemented("assets web do painel (Fase 3/6)")
    for host in CDN:
        assert host not in html, f"terminal.html busca script em {host}"
    assert "https://" not in html.replace("https://www.w3.org", ""), (
        "o painel nao deve buscar nada pela rede em tempo de execucao"
    )


def test_o_entry_point_do_plugin_esta_no_artefato(artefato):
    if artefato.wheel:
        texto = artefato.ler("entry_points.txt")
    else:
        from importlib.metadata import distribution

        texto = distribution("setup-spyder").read_text("entry_points.txt") or ""
    if "spyder.plugins" not in texto:
        not_implemented("entry point spyder.plugins na distribuicao (Fase 6)")
    assert "setup_spyder_ai" in texto
    assert "setup_spyder.plugin.plugin:AITerminalPlugin" in texto.replace(" ", "")


def test_as_dependencias_de_pty_sao_condicionais_por_plataforma():
    from importlib.metadata import requires

    declaradas = requires("setup-spyder") or []
    texto = " ".join(declaradas).lower()
    if "pywinpty" not in texto and "ptyprocess" not in texto:
        not_implemented("dependencias de PTY declaradas (Fase 6)")

    windows = [d for d in declaradas if "pywinpty" in d.lower()]
    posix = [d for d in declaradas if "ptyprocess" in d.lower()]
    assert windows and "platform_system" in windows[0], (
        f"pywinpty tem de ser condicional: {windows}"
    )
    assert posix and "platform_system" in posix[0], (
        f"ptyprocess tem de ser condicional: {posix}"
    )


def test_a_faixa_de_spyder_continua_5_x():
    from importlib.metadata import requires

    declaradas = [d.lower() for d in (requires("setup-spyder") or [])]
    spyder = [d for d in declaradas if d.startswith("spyder")]
    assert spyder, "a dependencia de spyder sumiu"
    assert "<6" in spyder[0].replace(" ", ""), (
        f"secao 2.4: a faixa publicada e >=5.5,<6, nao {spyder[0]}"
    )


def test_o_artefato_nao_aponta_para_o_fork_local():
    """Criterio de aceitacao: "O pacote nao contem caminho absoluto para o
    fork local"."""
    from importlib.metadata import distribution

    dist = distribution("setup-spyder")
    direct_url = dist.read_text("direct_url.json")
    if direct_url:
        assert '"editable": true' not in direct_url.replace(" ", ""), (
            f"instalacao editavel apontando para o fork: {direct_url}"
        )

    metadata = dist.read_text("METADATA") or ""
    for pista in ("file://", "C:\\Users", "/home/", "projetos\\spyder", "projetos/spyder"):
        assert pista not in metadata, f"caminho local vazou no METADATA: {pista}"


def test_o_pacote_nao_exige_conda():
    """Criterio de aceitacao: "O projeto nao exige Conda"."""
    from importlib.metadata import requires

    declaradas = " ".join(requires("setup-spyder") or []).lower()
    assert "conda" not in declaradas
