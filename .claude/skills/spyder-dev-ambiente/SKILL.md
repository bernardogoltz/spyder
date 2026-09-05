---
name: spyder-dev-ambiente
description: >
  Rodar, depurar e testar o Spyder 5.x a partir deste checkout: ambiente uv
  (não conda), `uv run setup-spyder` num projeto consumidor, `python bootstrap.py`
  para iterar no próprio Spyder, os subrepos em external-deps, diretório de
  config isolado (.spyder-lab no projeto), pytest com pytest-qt (qtbot), e como
  depurar plugin que não carrega. Use ao montar o ambiente, ao abrir o Spyder
  do source, ao escrever ou rodar um teste, ou quando algo quebra no boot.
  Gatilhos: "rodar do source", "bootstrap.py", "setup-spyder", "uv", "montar
  ambiente", "rodar teste", "pytest", "qtbot", "não abre", "log de debug",
  "external-deps".
---

# Ambiente de desenvolvimento do Spyder 5.x

Windows / PowerShell é o contexto padrão aqui; onde muda para Linux/macOS está
indicado. **Não use conda.** O interpretador é o do venv do uv.

## Montar o ambiente deste checkout (uma vez)

Python 3.12 — `pyqt5<5.16` não tem wheel confiável acima disso.

```powershell
uv venv --python 3.12
uv pip install -r requirements\dev-uv.txt
uv pip install -e . --prerelease=allow
```

`requirements/dev-uv.txt` é o equivalente pip das antigas `requirements/*.yml`
(conda). `setup.py` continua sendo a fonte da verdade do pacote. A versão
deste fork é `5.6.0.dev0`, daí o `--prerelease=allow`.

Não misture PyQt do conda neste venv.

## Uso diário: Spyder no venv de *outro* projeto

O comando `setup-spyder` instala junto com este pacote. De dentro de qualquer
projeto uv:

```powershell
uv add --editable C:\Users\angel\Documents\projetos\spyder --prerelease=allow
uv run setup-spyder
```

Isso abre **este** Spyder no `.venv` daquele diretório, com:

- config persistente em `<projeto>/.spyder-lab/` (não mexe em `~/.spyder-py3`)
- `.spyproject` criado se faltar
- sem popups (update, tour, DPI, deps faltando, confirmação de kernel)
- sem conda (`conda env list` não roda; o kernel é `python -m spyder_kernels.console`)
- painel **Claude Code** (entry point `claude_code`)

Flags úteis: `--no-launch` (só grava config), `--ephemeral` (config temp),
`--sem-estilo`, `--conf-dir <caminho>`, `--hide` / `--show`, e depois de `--`
as flags do Spyder (`--debug`, `--filter-log`, …).

## Rodar do source (iterar neste checkout)

```powershell
python bootstrap.py                          # normal (reinstala subrepos)
python bootstrap.py --debug                  # logging verboso
python bootstrap.py --safe-mode              # config limpa e temporária
python bootstrap.py --no-install             # pula a reinstalação dos subrepos
python bootstrap.py --filter-log spyder.plugins.completion,spyder.plugins.editor
python bootstrap.py -- --hide-console        # tudo após -- vai para o Spyder
```

O `bootstrap.py` verifica os subrepos de `external-deps/` (`spyder-kernels`,
`python-lsp-server`, `qtconsole`) e reinstala em modo editável se você trocou
de/para o branch `master`. Por isso o primeiro boot depois de um `git checkout`
demora — e por isso `--no-install` acelera o ciclo quando você só está
iterando no código do Spyder.

Para o fluxo “já configurado / sem popup / Claude”, prefira `setup-spyder`
mesmo neste checkout, depois do `uv pip install -e .`.

**A config do bootstrap fica isolada.** Como a versão é `5.6.0.dev0` (não
estável), `get_conf_subfolder()` acrescenta `-dev` e tudo vai para
`~/.spyder-py3-dev`. O `setup-spyder` usa `.spyder-lab/` no projeto e não
escreve aí. Detalhes na skill `spyder-config-atalhos`.

Opções úteis do Spyder (repassadas depois de `--`): `--reset`, `--defaults`,
`--conf-dir <caminho>`, `--new-instance`, `--debug-info {minimal,verbose}`,
`--debug-output {terminal,file}`, `--window-title`, `-w/--workdir`, `-p/--project`,
`--opengl {software,desktop,gles}`, `--no-web-widgets`, `--report-segfault`.

`--opengl software` costuma resolver tela preta / artefatos em VM e RDP.

## Ciclo de iteração

Não há hot reload. Editou código Python do Spyder ou do plugin → feche e
reabra. Para não perder tempo:

```powershell
python bootstrap.py --no-install --debug
```

Se você mexeu em `spyder-kernels` (dentro de `external-deps/`), aí sim precisa da
reinstalação: rode sem `--no-install` ou `python install_dev_repos.py`.

Os subrepos de `external-deps/` são repositórios git próprios embutidos. Não
commite mudanças neles junto com mudanças do Spyder.

O plugin Claude Code mora em `setup_spyder/plugin/`. Mesma regra: fechar e
reabrir. Se ele não aparecer, o checklist está na skill `spyder-plugin-externo`
(nome do entry point == `NAME` == `claude_code`; erro de import vai para stderr).

## Testes

```powershell
python runtests.py                             # a suíte inteira (demorado)
python runtests.py --run-slow                  # inclui os testes lentos
python runtests.py spyder/plugins/plots        # só um diretório
pytest spyder/plugins/pylint/tests/test_pylint.py -vv
pytest setup_spyder/tests -vv                  # launcher + renderer, sem janela
```

`runtests.py` é só um wrapper que já passa `--ignore=./external-deps`,
`--timeout=120` e as flags de cobertura no CI. Chamar `pytest` direto funciona
igual para um teste específico.

Marcadores declarados em `pytest.ini`: `slow`, `use_introspection`,
`single_instance`, `auto_backend`, `preload_project`, `close_main_window`,
`external_interpreter`, `known_leak`, `no_web_widgets`, entre outros. Testes
marcados `slow` só rodam com `--run-slow`.

Fixtures que importam:

- `qtbot` (pytest-qt) — cria e dirige widgets Qt; use
  `qtbot.addWidget(w)`, `qtbot.keyClicks`, `qtbot.mouseClick`,
  `qtbot.waitUntil(lambda: ..., timeout=5000)`.
- `reset_conf_before_test` (`conftest.py`, autouse) — zera a config entre testes.
  Por isso testes **não** enxergam a sua config pessoal.
- `tmpconfig` (`spyder/utils/fixtures.py`) — um `ConfigurationManager` em
  diretório temporário.
- `main_window` (`spyder/app/tests/conftest.py`) — a janela inteira. Caro;
  use só quando o teste for realmente de integração.

Sob pytest, `get_conf_path()` devolve um diretório temporário limpo — nunca a
config real.

Teste típico de um plugin:

```python
import pytest
from meu_pacote.main_widget import MeuWidget

@pytest.fixture
def widget(qtbot):
    w = MeuWidget('meuplugin', None)
    w.setup()
    qtbot.addWidget(w)
    w.show()
    return w

def test_rodar(widget, qtbot):
    widget.rodar()
    qtbot.waitUntil(lambda: 'rodou' in widget._saida.toPlainText())
```

Testes de Qt sem `qtbot.addWidget` vazam widget e travam a suíte no teardown.

## Depurar

- **Logs:** `--debug` liga logging em nível DEBUG; `--filter-log <módulos>`
  restringe a uma hierarquia. Sem filtro o volume é inútil.
- **Plugin não carrega:** erros de import em `find_external_plugins()` são
  impressos em stderr e engolidos. Rode do terminal, não de um atalho, e leia a
  saída.
- **Ordem de registro:** `mainwindow.py` loga
  `"Registering shortcuts for {NAME}"` e o registry loga a instanciação — dá para
  ver a ordem real do grafo de dependências.
- **Config suja:** quando o comportamento não bate com o código,
  `python bootstrap.py --safe-mode` (config limpa temporária) isola a dúvida.
  Para o launcher: apague `<projeto>/.spyder-lab` ou use `--ephemeral`.
- **Segfault do Qt:** `--report-segfault`; e desconfie de widget sem parent ou de
  sinal conectado a objeto já destruído.
- **Travou no boot:** normalmente é `on_initialize()` de algum plugin fazendo I/O.
  `--filter-log spyder.api.plugin_registration` mostra onde parou.

## Convenções do projeto (se for contribuir upstream)

`CONTRIBUTING.md` tem o processo completo. Resumo do que costuma pegar:

- PEP8 (há `.pep8speaks.yml`); linhas de 79 colunas.
- Comentários de código em inglês, com referência ao issue quando aplicável
  (`# Fixes spyder-ide/spyder#15467`).
- Toda string de UI passa por `from spyder.api.translations import _`.
- Cabeçalho de licença MIT no topo de arquivo novo.
- O changelog fica em `changelogs/Spyder-5.md`, gerado no release — não edite à mão.
- Seções do arquivo marcadas com `# ---- Nome da seção` seguido de uma linha de
  `#` — é o padrão que o Spyder usa para o dropdown de classes/funções do próprio
  editor.

Para customização pessoal nada disso é obrigatório, mas seguir o estilo local
reduz conflito no rebase.
