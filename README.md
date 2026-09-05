# `spyder` — fork bernardogoltz (Spyder 5.x)

![setup-spyder](spyder/images/setup-spyder.gif)

*Copyright © 2009– [Spyder Project Contributors](https://github.com/spyder-ide/spyder/graphs/contributors)
e outros (ver [AUTHORS.txt](AUTHORS.txt)). Alguns arquivos e ícones têm outra
autoria/licença; ver [NOTICE.txt](NOTICE.txt).*

Fork pessoal do [Spyder 5.x](https://github.com/spyder-ide/spyder) (API 5.x,
versão `5.6.0.dev0`), enxuto para um único uso: ser o IDE que o launcher
[`setup-spyder`](https://github.com/bernardogoltz/setup-spyder) abre dentro do
`.venv` de um projeto, com perfil isolado e o painel **AI Terminal**
(`codex` / `claude` num terminal real).

- Este repositório contém **só o pacote `spyder`** (`spyder/`), o `setup.py`
  que o empacota e o mínimo para rodar/testar do source.
- Launcher, perfis, plugin e a suíte de testes do plano vivem no submódulo
  [`setup-spyder/`](setup-spyder/) (repositório próprio). O fork **não**
  empacota nenhum módulo `setup_spyder` nem o script `setup-spyder`.
- O plano de trabalho está em [`docs/plan.md`](docs/plan.md); o mapa curto da
  codebase em [`docs/guia-codebase.md`](docs/guia-codebase.md).

## Uso (em qualquer projeto uv)

O fork nunca é instalado por path local nem pelo PyPI: o `setup-spyder`
declara `spyder @ git+https://github.com/bernardogoltz/spyder.git@<commit>`
e qualquer máquina baixa daqui.

```powershell
uv add --dev git+https://github.com/bernardogoltz/setup-spyder
uv run setup-spyder --agent codex     # ou claude | auto | none
uv run python -c "import spyder; print(spyder.__version__)"   # 5.6.0.dev0
```

> Dependência por URL Git não é aceita pelo PyPI, então `uv add setup-spyder`
> (índice) não serve para esta combinação — use a URL Git do launcher.

## Desenvolvimento deste checkout

Sem conda. Python 3.12 (o `pyqt5<5.16` não tem wheel confiável acima disso;
3.11 também funciona).

```powershell
git clone --recurse-submodules https://github.com/bernardogoltz/spyder
cd spyder
uv venv --python 3.12
uv pip install -r requirements\dev-uv.txt
uv pip install -e . --no-deps               # este fork
uv pip install -e .\setup-spyder --no-deps  # launcher + plugin, do submódulo
```

`spyder-kernels`, `python-lsp-server` e `qtconsole` vêm do PyPI
(`requirements/dev-uv.txt`); não há mais subrepos em `external-deps/`.

Abrir o Spyder deste source:

```powershell
python bootstrap.py                  # config em ~/.spyder-py3-dev
python bootstrap.py --debug -- --hide-console
.venv\Scripts\setup-spyder.exe -w C:\um\projeto --agent claude   # fluxo do launcher
```

Testes:

```powershell
python runtests.py                   # suíte do Spyder (ignora setup-spyder/)
cd setup-spyder
..\.venv\Scripts\python.exe -m pytest tests -p no:cacheprovider     # suíte do plano
```

A suíte do launcher está descrita em
[`setup-spyder/tests/README.md`](setup-spyder/tests/README.md).

## Publicar uma versão do fork para o launcher

1. Commit no fork e `git push origin main`.
2. Em `setup-spyder/pyproject.toml`, troque o pin
   `spyder.git@<commit>` pelo hash (ou tag) recém-publicado.
3. `cd setup-spyder && uv lock && uv run pytest`, commit e push do launcher.
4. No fork, `git add setup-spyder` para atualizar o ponteiro do submódulo e
   commit.

Nunca aponte o launcher para `main` flutuante nem para um path local.

## O que ficou de fora

CI do upstream, instaladores (`installers*/`), `binder/`, `branding/`,
`img_src/`, `scripts/`, `changelogs/`, `external-deps/` e o launcher interno
antigo (`setup_spyder/` + plugin via SDK) foram removidos. Customizações que
são "deste IDE" (defaults, patches) ficam em `spyder/`; tudo que é launcher,
perfil ou painel fica em `setup-spyder/`.
