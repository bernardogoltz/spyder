---
name: spyder-plugin-externo
description: >
  Como criar um plugin externo do Spyder 5.x — o caminho recomendado para
  customização pessoal, sem tocar no fork: pacote separado com entry point
  `spyder.plugins`, classe SpyderPluginV2 ou SpyderDockablePlugin,
  PluginMainWidget/PluginMainContainer, config própria (CONF_FILE,
  CONF_DEFAULTS, CONF_VERSION), página em Preferências, e os decorators
  on_plugin_available/on_plugin_teardown/on_conf_change. Use ao criar um plugin
  do zero, ao decidir entre plugin externo e patch no fork, ao empacotar
  (pyproject/setup.py) ou quando o plugin não aparece no Spyder. Gatilhos:
  "criar plugin", "plugin externo", "meu painel", "entry point spyder.plugins",
  "plugin não aparece", "SpyderDockablePlugin".
---

# Plugin externo do Spyder 5.x

## Decida primeiro: plugin externo ou patch no fork?

| Objetivo | Faça |
|---|---|
| Painel novo, ação nova, item de menu, widget na status bar, atalho novo | **Plugin externo.** Sobrevive a `git pull` e a upgrades do Spyder. |
| Mudar comportamento existente do Editor/Console em pontos sem hook | Patch no fork (branch `5.x`) — só quando não houver API. |
| Mudar defaults, tema, atalhos | Nenhum dos dois: é configuração. Veja `spyder-config-atalhos`. |

Prefira plugin externo por padrão. O fork só se paga quando você precisa mudar
código que não expõe extensão.

## Esqueleto do pacote

```
spyder-meuplugin/
  pyproject.toml            # ou setup.py — o que importa é o entry point
  spyder_meuplugin/
    __init__.py             # version + __all__
    plugin.py               # a classe do plugin
    main_widget.py          # PluginMainWidget (se dockável)
    container.py            # PluginMainContainer (se não dockável)
    confpage.py             # página em Preferências (opcional)
    api.py                  # constantes de IDs (actions, seções de menu)
```

Entry point — **o nome tem que ser exatamente igual a `Plugin.NAME`**, senão
`find_external_plugins()` levanta `SpyderAPIError`:

```toml
# pyproject.toml
[project.entry-points."spyder.plugins"]
meuplugin = "spyder_meuplugin.plugin:MeuPlugin"
```

Instalação em modo dev, dentro do mesmo ambiente onde o Spyder roda:

```powershell
pip install -e .
```

Depois é só abrir o Spyder. Não há registro manual em lugar nenhum.

## Templates prontos

- `referencias/plugin-dockavel.py` — plugin com painel, widget, ação, atalho,
  item no menu Tools, config observada. É o template que serve para 90% dos casos.
- `referencias/plugin-sem-painel.py` — plugin só com ações/menus (container),
  para quando você não quer um painel novo.
- `referencias/empacotamento.md` — `pyproject.toml`/`setup.py`, versionamento,
  como declarar dependência do Spyder.

Copie o template, renomeie e vá cortando o que não usar.

## Atributos de classe que você precisa acertar

```python
class MeuPlugin(SpyderDockablePlugin):
    NAME = 'meuplugin'              # == nome do entry point. Obrigatório.
    REQUIRES = [Plugins.Preferences]
    OPTIONAL = [Plugins.MainMenu, Plugins.Editor]
    TABIFY = [Plugins.Help]         # só dockáveis
    WIDGET_CLASS = MeuWidget        # dockável: PluginMainWidget
    # CONTAINER_CLASS = MeuContainer  # não dockável: PluginMainContainer

    CONF_SECTION = NAME
    CONF_FILE = True                # arquivo próprio (padrão para externos)
    CONF_DEFAULTS = CONF_DEFAULTS   # obrigatório se CONF_FILE=True
    CONF_VERSION = '1.0.0'          # idem
    CONF_WIDGET_CLASS = MeuConfPage # página em Preferências

    CAN_BE_DISABLED = True
    REQUIRE_WEB_WIDGETS = False     # True só se usar QtWebEngine
```

Sobre `CONF_FILE`:

- `True` (padrão) → config vai para `~/.spyder-py3/plugins/<CONF_SECTION>/`,
  num arquivo próprio, versionado por `CONF_VERSION`. É o certo para plugin
  externo: não polui o `spyder.ini` e não colide com o Spyder.
- `False` → grava na seção `CONF_SECTION` do `spyder.ini` global. Só faz sentido
  para plugin interno.

`CONF_VERSION` segue semver com regra própria do projeto: **adicionar** opção não
muda a versão; **mudar um default** é bump minor; **remover/renomear** opção é
bump major (aí o Spyder reseta as opções obsoletas).

## Os quatro métodos que todo plugin implementa

```python
@staticmethod
def get_name():           return _('Meu Plugin')     # aparece na UI
def get_description(self): return _('O que ele faz.')
def get_icon(self):        return self.create_icon('genericfile')
def on_initialize(self):   ...                        # obrigatório
```

`create_icon(nome)` usa o `IconManager` (`spyder/utils/icon_manager.py`); os
nomes válidos estão no dicionário lá dentro. Para ícone próprio, veja a skill
`spyder-ui-integracao`.

## Conversar com outros plugins

Nunca chame `self.get_plugin(X)` dentro de `on_initialize()` — X pode não existir
ainda. Use os decorators:

```python
from spyder.api.plugin_registration.decorators import (
    on_plugin_available, on_plugin_teardown)

@on_plugin_available(plugin=Plugins.MainMenu)
def on_main_menu_available(self):
    mainmenu = self.get_plugin(Plugins.MainMenu)
    mainmenu.add_item_to_application_menu(
        self.get_container().minha_acao,
        menu_id=ApplicationMenus.Tools,
        section=ToolsMenuSections.Tools,
    )

@on_plugin_teardown(plugin=Plugins.MainMenu)
def on_main_menu_teardown(self):
    mainmenu = self.get_plugin(Plugins.MainMenu)
    mainmenu.remove_item_from_application_menu(
        MinhasAcoes.Rodar, menu_id=ApplicationMenus.Tools)
```

`on_plugin_teardown` **exige** o kwarg `plugin=`; sem ele levanta `ValueError`.
Para plugins em `OPTIONAL`, os decorators simplesmente não disparam se o plugin
não existir — não precisa de `if`.

Registrar-se em Preferências é sempre o mesmo par:

```python
@on_plugin_available(plugin=Plugins.Preferences)
def on_preferences_available(self):
    self.get_plugin(Plugins.Preferences).register_plugin_preferences(self)

@on_plugin_teardown(plugin=Plugins.Preferences)
def on_preferences_teardown(self):
    self.get_plugin(Plugins.Preferences).deregister_plugin_preferences(self)
```

## O widget

`PluginMainWidget` (dockável) exige três métodos:

```python
class MeuWidget(PluginMainWidget):
    def get_title(self):     return _('Meu Plugin')   # título do dock
    def setup(self):         ...  # cria ações, menus, toolbars — chamado 1x
    def update_actions(self): ... # habilita/desabilita conforme o estado
```

`PluginMainContainer` (não dockável) exige `setup()` e `update_actions()`.

Dentro de `setup()` você tem, via `SpyderWidgetMixin`: `create_action`,
`create_menu`, `create_toolbar`, `create_toolbutton`, `add_item_to_toolbar`,
`add_item_to_menu`, `get_options_menu()`, `get_main_toolbar()`.

O widget também tem `ENABLE_SPINNER = True` para ganhar
`start_spinner()`/`stop_spinner()` no canto — útil para operação longa.

## Comunicação widget → plugin

Convenção do projeto: o widget declara um `Signal`, o plugin conecta em
`on_initialize()`. Não importe outro plugin dentro do widget.

```python
# no widget
sig_algo_aconteceu = Signal(str)

# no plugin
def on_initialize(self):
    self.get_widget().sig_algo_aconteceu.connect(self._tratar)
```

## Checklist quando o plugin não aparece

1. `pip show spyder-meuplugin` — está instalado **no mesmo ambiente** do Spyder?
2. `python -c "from importlib.metadata import entry_points; print([e for e in entry_points(group='spyder.plugins')])"`
   — o seu entry point está listado?
3. Nome do entry point == `NAME` da classe? (mismatch = `SpyderAPIError`)
4. Erro de import é engolido e impresso em stderr por `find_external_plugins()`.
   Rode `python bootstrap.py --debug` e leia o console.
5. `check_compatibility()` retornando `False`?
6. Plugin desabilitado em Preferências → Application → Plugins.
7. `CONF_FILE=True` sem `CONF_DEFAULTS`/`CONF_VERSION` → config vazia, opções
   voltando ao default silenciosamente.

## Armadilhas

- **Assimetria available/teardown.** Se você adiciona item de menu no
  `available` e não remove no `teardown`, desabilitar o plugin em runtime quebra.
- **Nome de ação duplicado.** IDs de ação são globais por contexto; reuso emite
  warning e sobrescreve. Use uma classe `MinhasAcoes` em `api.py` com prefixo.
- **`REQUIRES` inchado.** Tudo que estiver em `REQUIRES` e faltar impede o plugin
  de carregar. Na dúvida, use `OPTIONAL`.
- **Trabalho pesado em `on_initialize()`.** Atrasa o boot do Spyder inteiro.
  Mande para `on_mainwindow_visible()`.
- **API antiga.** Tutoriais de blog frequentemente mostram `SpyderPluginWidget`
  (Spyder 3/4). Está em `spyder/api/plugins/old_api.py` e é legado.
