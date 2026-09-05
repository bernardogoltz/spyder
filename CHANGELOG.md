# Histórico deste fork

Base: Spyder 5.5.6 (upstream `spyder-ide/spyder`, branch `5.x`). O histórico
completo do Spyder está no repositório upstream; os changelogs antigos foram
removidos daqui.

## 5.6.0.dev0 (fork bernardogoltz)

- O repositório contém só o pacote `spyder`: `setup.py` não empacota mais
  `setup_spyder`, o script `setup-spyder`, o plugin `claude_code` nem depende
  de `claude-agent-sdk`/`rich`.
- Launcher, perfis, plugin **AI Terminal** e a suíte do plano vivem no
  submódulo `setup-spyder/` (`bernardogoltz/setup-spyder` 0.3.0), que instala
  este fork por URL Git pinada por commit.
- `spyder-kernels`, `python-lsp-server` e `qtconsole` vêm do PyPI; sem
  `external-deps/`, `install_dev_repos.py` nem lógica de subrepos no
  `bootstrap.py`. Ambiente de desenvolvimento em uv (`requirements/dev-uv.txt`).
- Removidos: CI do upstream, instaladores, `binder/`, `branding/`, `img_src/`,
  `scripts/`, requisitos conda e configuração do check-manifest.
- `setup.py` fixa `pyqt5-qt5`/`pyqtwebengine-qt5 < 5.15.3` no Windows (as
  wheels mais novas do runtime Qt são só Linux/macOS).
