---
name: spyder-dev-ambiente
description: >
  Rodar, depurar e testar o Spyder 5.x a partir deste checkout: ambiente uv
  (não conda), `uv run setup-spyder` num projeto consumidor, `python bootstrap.py`
  para iterar no próprio Spyder, o submódulo setup-spyder/ (launcher, perfis,
  plugin AI Terminal e a suíte do plano), perfil isolado em
  <projeto>/.spyproject/setup-spyder/, pytest com pytest-qt (qtbot), e como
  depurar plugin que não carrega. Use ao montar o ambiente, ao abrir o Spyder
  do source, ao escrever ou rodar um teste, ou quando algo quebra no boot.
  Gatilhos: "rodar do source", "bootstrap.py", "setup-spyder", "uv", "montar
  ambiente", "rodar teste", "pytest", "qtbot", "não abre", "log de debug",
  "submódulo", "pin do fork".
---

# Ambiente de desenvolvimento do Spyder 5.x

Windows / PowerShell é o contexto padrão aqui; onde muda para Linux/macOS está
indicado. **Não use conda.** O interpretador é o do venv do uv.

Dois repositórios, um checkout:

| Onde | O que é | Quem consome |
| --- | --- | --- |
| raiz (`spyder/`, `setup.py`) | o fork `bernardogoltz/spyder`, só o pacote `spyder` | o launcher, por URL Git pinada |
| `setup-spyder/` (submódulo) | `setup-spyder`: CLI, launcher, perfis, plugin `setup_spyder_ai`, suíte do plano | qualquer projeto uv |

O fork **não** empacota `setup_spyder`. Se `import setup_spyder` resolver para
dentro da raiz do fork, algo voltou ao lugar errado.

## Montar o ambiente deste checkout (uma vez)

Python 3.12 — `pyqt5<5.16` não tem wheel confiável acima disso (3.11 também vale).

```powershell
git submodule update --init
uv venv --python 3.12
uv pip install -r requirements\dev-uv.txt
uv pip install -e . --no-deps
uv pip install -e .\setup-spyder --no-deps
```

`requirements/dev-uv.txt` junta runtime (faixa "dev" já afrouxada), testes e o
que o launcher/plugin precisam (`rich`, `pandas`, `pywinpty` no Windows).
`spyder-kernels`, `python-lsp-server` e `qtconsole` vêm do PyPI; não há mais
`external-deps/`. O `--no-deps` nos dois editáveis evita que o uv tente
resolver o `spyder @ git+...` do launcher por cima do fork editável.

Não misture PyQt do conda neste venv.

## Uso diário: Spyder no venv de *outro* projeto

De dentro de qualquer projeto uv (o launcher puxa o fork do GitHub):

```powershell
uv add --dev git+https://github.com/bernardogoltz/setup-spyder
uv run setup-spyder --agent codex        # claude | auto | none
```

Isso abre **este** Spyder no `.venv` daquele diretório, com:

- perfil persistente em `<projeto>/.spyproject/setup-spyder/` (não mexe em
  `~/.spyder-py3`); `--profile ephemeral` / `--ephemeral` usa um temp
- `.spyproject` criado se faltar; seed de preferências versionado (só na
  criação/migração do perfil, nunca regravado a cada boot)
- painel **AI Terminal** (entry point `setup_spyder_ai`): terminal real
  (xterm.js + ConPTY/PTY) rodando `codex` ou `claude`

Flags: `--no-launch`, `--keep-config`, `--ephemeral`, `--profile
{ephemeral,project}`, `--conf-dir <caminho>`, `--reset-profile`,
`--sem-estilo`, `--hide` / `--show`, `--agent`, e depois de `--` as flags do
Spyder (`--debug-info verbose`, `--filter-log`, …).

Para testar o launcher a partir *deste* checkout sem outro projeto:

```powershell
.venv\Scripts\setup-spyder.exe -w C:\um\projeto --agent claude
```

## Rodar do source (iterar neste checkout)

```powershell
python bootstrap.py                          # normal
python bootstrap.py --debug                  # logging verboso
python bootstrap.py --safe-mode              # config limpa e temporária
python bootstrap.py --filter-log spyder.plugins.completion,spyder.plugins.editor
python bootstrap.py -- --hide-console        # tudo após -- vai para o Spyder
```

`--no-install` continua aceito mas não faz nada (não há subrepos).

**A config do bootstrap fica isolada.** Como a versão é `5.6.0.dev0` (não
estável), `get_conf_subfolder()` acrescenta `-dev` e tudo vai para
`~/.spyder-py3-dev`. O `setup-spyder` usa `.spyproject/setup-spyder/` no
projeto e não escreve aí. Detalhes na skill `spyder-config-atalhos`.

Opções úteis do Spyder (repassadas depois de `--`): `--reset`, `--defaults`,
`--conf-dir <caminho>`, `--new-instance`, `--debug-info {minimal,verbose}`,
`--debug-output {terminal,file}`, `--window-title`, `-w/--workdir`, `-p/--project`,
`--opengl {software,desktop,gles}`, `--no-web-widgets`, `--report-segfault`.

`--opengl software` costuma resolver tela preta / artefatos em VM e RDP. O
launcher nunca passa `--no-web-widgets`: o painel AI Terminal é um
`QWebEngineView`.

## Ciclo de iteração

Não há hot reload. Editou código Python do Spyder ou do plugin → feche e
reabra. `python bootstrap.py --debug` para o Spyder; o plugin mora em
`setup-spyder/src/setup_spyder/plugin/`. Se ele não aparecer, o checklist está
na skill `spyder-plugin-externo` (nome do entry point == `NAME` ==
`setup_spyder_ai`; erro de import vai para stderr).

## Testes

Suíte do Spyder (raiz; já ignora `setup-spyder/`):

```powershell
python runtests.py                             # inteira (demorado)
python runtests.py --run-slow
python runtests.py spyder/plugins/plots        # um diretório
pytest spyder/plugins/pylint/tests/test_pylint.py -vv
```

Suíte do plano (launcher + plugin), **de dentro de `setup-spyder/`**, com o
Python do venv da raiz:

```powershell
cd setup-spyder
..\.venv\Scripts\python.exe -m pytest tests -p no:cacheprovider -q
..\.venv\Scripts\python.exe -m pytest tests -m "phase0 or phase2" -q
$env:SETUP_SPYDER_STRICT="1"      # skip de "ainda não entregue" vira falha
$env:SETUP_SPYDER_E2E="1"         # habilita tests/e2e (abre o Spyder de verdade)
```

`setup-spyder/tests/README.md` explica marcadores, fases e o contrato alvo.
Não rode essa suíte a partir da raiz: o `conftest.py` do fork tem uma fixture
autouse que reseta o `CONF` a cada teste.

Marcadores do Spyder em `pytest.ini`: `slow`, `use_introspection`,
`single_instance`, `auto_backend`, `preload_project`, `close_main_window`,
`external_interpreter`, `known_leak`, `no_web_widgets`, entre outros. Testes
marcados `slow` só rodam com `--run-slow`.

Fixtures que importam:

- `qtbot` (pytest-qt) — cria e dirige widgets Qt; use
  `qtbot.addWidget(w)`, `qtbot.keyClicks`, `qtbot.mouseClick`,
  `qtbot.waitUntil(lambda: ..., timeout=5000)`.
- `reset_conf_before_test` (`conftest.py` da raiz, autouse) — zera a config
  entre testes do Spyder.
- `tmpconfig` (`spyder/utils/fixtures.py`) — um `ConfigurationManager` em
  diretório temporário.
- `main_window` (`spyder/app/tests/conftest.py`) — a janela inteira. Caro;
  use só quando o teste for realmente de integração.

Sob pytest, `get_conf_path()` devolve um diretório temporário limpo — nunca a
config real.

Teste típico de um widget de plugin (com `plugin=None` o
`AITerminalWidget` chama `_setup()` sozinho):

```python
import pytest
from setup_spyder.plugin.main_widget import AITerminalWidget

@pytest.fixture
def widget(qtbot):
    w = AITerminalWidget("setup_spyder_ai", None)
    qtbot.addWidget(w)
    return w
```

Testes de Qt sem `qtbot.addWidget` vazam widget e travam a suíte no teardown.
`QtWebEngineWidgets` precisa ser importado antes do `QApplication` existir —
`setup-spyder/tests/qt/conftest.py` já faz isso.

## Publicar o fork para o launcher (pin)

1. commit + `git push origin main` no fork;
2. em `setup-spyder/pyproject.toml`, trocar o hash em
   `spyder @ git+https://github.com/bernardogoltz/spyder.git@<hash>`;
3. `cd setup-spyder; uv lock; uv run pytest`, commit e push do launcher;
4. na raiz, `git add setup-spyder` (ponteiro do submódulo) e commit.

Nunca `main` flutuante, nunca path local, nunca `spyder` do PyPI.

## Depurar

- **Logs:** `--debug` liga logging em nível DEBUG; `--filter-log <módulos>`
  restringe a uma hierarquia. Sem filtro o volume é inútil.
- **Plugin não carrega:** erros de import em `find_external_plugins()` são
  impressos em stderr e engolidos. Rode do terminal, não de um atalho, e leia a
  saída. O backend de PTY (`winpty`/`ptyprocess`) é importado tarde de
  propósito: faltar ele degrada o painel, não some com o plugin.
- **Ordem de registro:** `mainwindow.py` loga
  `"Registering shortcuts for {NAME}"` e o registry loga a instanciação — dá para
  ver a ordem real do grafo de dependências.
- **Config suja:** quando o comportamento não bate com o código,
  `python bootstrap.py --safe-mode` (config limpa temporária) isola a dúvida.
  Para o launcher: `setup-spyder --reset-profile` ou `--ephemeral`.
- **Segfault do Qt:** `--report-segfault`; e desconfie de widget sem parent ou de
  sinal conectado a objeto já destruído.
- **Travou no boot:** normalmente é `on_initialize()` de algum plugin fazendo I/O.
  `--filter-log spyder.api.plugin_registration` mostra onde parou.

## Convenções

Para o `spyder/`: PEP8, 79 colunas, strings de UI via
`from spyder.api.translations import _`, cabeçalho MIT em arquivo novo. Para o
launcher/plugin: `setup-spyder/.claude/skills/cli-code-style/SKILL.md`.
