---
name: spyder-ui-integracao
description: >
  Como enfiar UI própria no Spyder 5.x: ações (create_action), menus da
  aplicação (ApplicationMenus + seções), toolbars (ApplicationToolbars),
  widgets na status bar (StatusBarWidget), options menu e toolbar do próprio
  painel, ícones (IconManager/qtawesome), cores (SpyderPalette), stylesheets,
  temas de sintaxe do editor e layouts customizados (BaseGridLayoutType).
  Use ao adicionar item de menu ou botão, criar indicador na barra de status,
  trocar ícone, mexer em cores/tema, ou criar um arranjo de painéis próprio.
  Gatilhos: "adicionar no menu", "botão na toolbar", "status bar", "ícone",
  "tema", "cores", "esquema de sintaxe", "layout de painéis", "stylesheet".
---

# Integrar UI própria no Spyder 5.x

Tudo aqui pressupõe que você está dentro de um plugin (interno ou externo).
Veja `spyder-plugin-externo` para o esqueleto.

## Ações

Toda ação nasce de `create_action` (`spyder/api/widgets/mixins.py:354`), num
widget ou container:

```python
self.create_action(
    MinhasAcoes.Rodar,            # id único; use uma classe de constantes
    text=_('Rodar'),
    icon=self.create_icon('run'),
    icon_text='',                 # texto ao lado do ícone na toolbar
    tip=_('Roda o arquivo atual'),
    triggered=self.rodar,         # OU toggled=... (um dos dois é obrigatório)
    register_shortcut=True,       # expõe em Preferências > Atalhos
    shortcut_context='_',         # '_' = global; default = NAME do plugin
    context=Qt.WidgetWithChildrenShortcut,
)
```

Ação-checkbox amarrada a config (marcar grava a opção sozinho):

```python
self.create_action(
    MinhasAcoes.Auto, text=_('Automático'),
    toggled=True, option='auto', section=None,  # section=None => CONF_SECTION
)
```

Recuperar depois: `self.get_action(MinhasAcoes.Rodar)`. IDs são únicos por
contexto — reuso emite warning e sobrescreve; prefixe com o nome do seu plugin.

## Menus da aplicação

Constantes em `spyder/plugins/mainmenu/api.py`:

```
ApplicationMenus: File Edit Search Source Run Debug Consoles Projects Tools View Help
```

Seções por menu (o item é inserido dentro de uma seção, e as seções são
separadas por linha divisória):

| Menu | Seções |
|---|---|
| File | New, Open, Save, Print, Close, Switcher, Navigation, Restart |
| Edit | UndoRedo, Copy, Editor |
| Search | Search |
| Source | Options, Linting, Cursor, Actions, CodeAnalysis |
| Run | Run, RunExtras, Profile |
| Debug | Run, Options |
| Consoles | New, Restart |
| Projects | New, Open, Extras |
| Tools | Tools, External, Extras |
| View | Top, Pane, Toolbar, Layout, Bottom |
| Help | Documentation, Support, ExternalDocumentation, About |

```python
@on_plugin_available(plugin=Plugins.MainMenu)
def on_main_menu_available(self):
    mainmenu = self.get_plugin(Plugins.MainMenu)
    mainmenu.add_item_to_application_menu(
        self.get_container().minha_acao,
        menu_id=ApplicationMenus.Tools,
        section=ToolsMenuSections.Extras,
        before=OutraAcao.Id,             # opcional, ordena dentro da seção
        before_section=ToolsMenuSections.External,   # opcional, ordena seções
    )

@on_plugin_teardown(plugin=Plugins.MainMenu)
def on_main_menu_teardown(self):
    self.get_plugin(Plugins.MainMenu).remove_item_from_application_menu(
        MinhasAcoes.Id, menu_id=ApplicationMenus.Tools)
```

Também dá para criar um menu de topo novo: `create_application_menu(menu_id,
title)` e depois `remove_application_menu(menu_id)` no teardown. Para uso
pessoal, geralmente é melhor pendurar em Tools → Extras.

O item pode ser uma ação **ou um submenu** (`create_menu` do container).

## Toolbars da aplicação

Constantes em `spyder/plugins/toolbar/api.py`: `ApplicationToolbars.File`,
`.Run`, `.Debug`, `.Main`, `.WorkingDirectory`; seções da Main em
`MainToolbarSections` (`LayoutSection`, `ApplicationSection`).

```python
toolbar = self.get_plugin(Plugins.Toolbar)
toolbar.add_item_to_application_toolbar(
    acao, toolbar_id=ApplicationToolbars.Main,
    section=MainToolbarSections.ApplicationSection)
# teardown:
toolbar.remove_item_from_application_toolbar(
    acao_id, toolbar_id=ApplicationToolbars.Main)
```

Toolbar nova: `create_application_toolbar(toolbar_id, title)` +
`add_application_toolbar(toolbar)`; ela aparece em View → Toolbars.

## Toolbar e options menu do próprio painel

Dentro do `setup()` de um `PluginMainWidget`:

```python
self.add_item_to_toolbar(acao, toolbar=self.get_main_toolbar(),
                         section=MinhasSecoes.Principal)
self.add_item_to_menu(acao, menu=self.get_options_menu(),
                      section=MinhasSecoes.Opcoes)
self.create_toolbar('minha_aux')          # toolbar auxiliar do painel
self.add_corner_widget('meu_widget', widget)
self.create_stretcher()                   # empurra o resto para a direita
```

`ENABLE_SPINNER = True` na classe do widget habilita
`start_spinner()`/`stop_spinner()` no canto do painel.

## Status bar

```python
from spyder.api.widgets.status import StatusBarWidget, BaseTimerStatus
from spyder.plugins.statusbar.plugin import StatusBarWidgetPosition

class MeuStatus(StatusBarWidget):
    ID = 'meu_status'                      # obrigatório e único
    def get_tooltip(self): return _('O que isso mostra')
    def get_icon(self):    return self.create_icon('environment')

# no plugin:
@on_plugin_available(plugin=Plugins.StatusBar)
def on_statusbar_available(self):
    self.get_plugin(Plugins.StatusBar).add_status_widget(
        self._status, position=StatusBarWidgetPosition.Right)

@on_plugin_teardown(plugin=Plugins.StatusBar)
def on_statusbar_teardown(self):
    self.get_plugin(Plugins.StatusBar).remove_status_widget(MeuStatus.ID)
```

`StatusBarWidget` = ícone + label + spinner; `set_value(texto)` atualiza o
label; `sig_clicked` para reagir a clique; `CUSTOM_WIDGET_CLASS` injeta um
widget entre label e spinner. Para algo que atualiza sozinho a cada N ms, herde
`BaseTimerStatus` e implemente `get_value()` (é assim que CPU/memória funcionam).

`ID` sem valor ou repetido levanta `SpyderAPIError`. Os IDs internos estão em
`StatusBar.INTERNAL_WIDGETS_IDS` — não colida com eles.

## Ícones

`self.create_icon('nome')` resolve pelo `IconManager`
(`spyder/utils/icon_manager.py`). O dicionário `_qtaware_icons` lá dentro mapeia
nome → ícone do **qtawesome** (`mdi.*`, Material Design Icons) já colorido com a
paleta. Nomes úteis: `run`, `debug`, `filenew`, `fileopen`, `filesave`,
`configure`, `editclear`, `genericfile`, `environment`, `keyboard`,
`tooloptions`, `log`, `regex`.

Para um ícone que não existe na lista, use qtawesome direto:

```python
import qtawesome as qta
from spyder.utils.palette import SpyderPalette
icon = qta.icon('mdi.rocket-launch', color=SpyderPalette.ICON_1)
```

Ícone próprio em arquivo: defina `IMG_PATH` na classe do plugin (caminho
relativo ao pacote) e carregue com `QIcon(osp.join(self.get_path(), 'images', 'x.svg'))`.

## Cores e stylesheet

- `spyder/utils/palette.py` exporta **`SpyderPalette`** e **`QStylePalette`**, já
  resolvidos para o tema claro ou escuro em uso (`is_dark_interface()`). Use
  `SpyderPalette.COLOR_ERROR_1`, `.ICON_1`, `.GROUP_3`, `.COLOR_HIGHLIGHT_2` etc.
  **Nunca hardcode hex** num widget: ele fica errado no outro tema.
- `spyder/utils/color_system.py` — as escalas cruas (`Green.B40`, `Gray.B110`...).
- `spyder/utils/stylesheet.py` — `APP_STYLESHEET`, `PANES_TOOLBAR_STYLESHEET`,
  `PANES_TABBAR_STYLESHEET`, `DialogStyle`. Construídos com `qstylizer` em cima
  do `qdarkstyle`. Para estilizar um widget seu, siga o padrão de herdar
  `SpyderStyleSheet` e sobrescrever `set_stylesheet()`.
- O plugin recebe `update_style()` quando o usuário troca claro/escuro —
  reaplique lá o que for dependente de tema.

## Temas de sintaxe do editor

`spyder/config/appearance.py::APPEARANCE` guarda **tudo**: a lista `names` com os
esquemas embutidos (`spyder/dark`, `monokai`, `zenburn`, `solarized/dark`, ...),
o `selected`, as fontes globais (`font/family`, `font/size`, `rich_font/*`), o
`ui_theme` (`automatic`/`dark`/`light`) e, para cada esquema, as chaves
`<nome>/background`, `/currentline`, `/currentcell`, `/occurrence`, `/sideareas`,
`/matched_p`, `/unmatched_p` e as tuplas `(cor, bold, italic)` para `normal`,
`keyword`, `magic`, `builtin`, `definition`, `comment`, `string`, `number`,
`instance`.

Para um esquema pessoal, o caminho fácil é Preferências → Aparência → "Create new
scheme" (grava em `spyder.ini`, seção `appearance`). O caminho versionável é
acrescentar as chaves em `APPEARANCE` e o nome em `names` — mas aí é patch no
fork e exige bump de `CONF_VERSION` em `spyder/config/main.py`.

Quem consome essas cores: `spyder/utils/syntaxhighlighters.py`.

## Layouts de painéis customizados

```python
from spyder.plugins.layout.api import BaseGridLayoutType

class MeuLayout(BaseGridLayoutType):
    ID = 'meu layout'

    def __init__(self, parent_plugin):
        super().__init__(parent_plugin)
        self.add_area([Plugins.Editor], row=0, column=0, row_span=2)
        self.add_area([Plugins.IPythonConsole, Plugins.History],
                      row=0, column=1)
        self.add_area([Plugins.VariableExplorer, Plugins.Plots],
                      row=1, column=1, default=True,
                      hidden_plugin_ids=[Plugins.Plots])
        self.set_column_stretch(0, 3)
        self.set_column_stretch(1, 2)

    def get_name(self):
        return _('Meu layout')
```

Registre pelo atributo de classe do plugin:

```python
CUSTOM_LAYOUTS = [MeuLayout]
```

O plugin `Layout` lê `CUSTOM_LAYOUTS` de cada plugin registrado e chama
`register_layout`. Exatamente uma área deve ter `default=True` (para onde vão os
plugins não listados); duas levantam `SpyderAPIError`. Os layouts embutidos em
`spyder/plugins/layout/layouts.py` são os melhores modelos.

Alternativa sem código: arraste os painéis na mão e use View → Layouts → Save
current layout.

## Armadilhas

- **Adicionar sem remover.** Todo `add_item_to_*` precisa do
  `remove_item_from_*` no `on_plugin_teardown` correspondente.
- **Widget chamando outro plugin.** Quebra a separação do projeto e cria import
  circular. O widget emite sinal; o plugin conecta.
- **Cor hardcoded.** Use `SpyderPalette`.
- **ID de status widget ausente.** `ID = None` levanta `SpyderAPIError` na hora
  de adicionar.
- **`register_shortcut` esquecido.** O default de `create_action` é `False` — a
  ação funciona pelo menu mas não aparece em Preferências → Atalhos.
