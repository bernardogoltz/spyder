---
name: spyder-arquitetura
description: >
  Mapa da base de código do Spyder 5.x: layout de diretórios, o sistema de
  plugins (SpyderPluginV2 / SpyderDockablePlugin / PluginMainWidget /
  PluginMainContainer), descoberta por entry points `spyder.plugins`, o
  registro (SpyderPluginRegistry), o grafo REQUIRES/OPTIONAL e o ciclo de vida
  (on_initialize → on_plugin_available → on_mainwindow_visible → on_close).
  Use para se orientar no repo, achar onde mora uma funcionalidade, entender
  como um plugin é carregado, ou antes de decidir onde encostar uma
  customização. Gatilhos: "onde fica", "como o Spyder carrega", "o que é
  CONTAINER_CLASS", "REQUIRES", "on_plugin_available", "ciclo de vida",
  "arquitetura do Spyder".
---

# Arquitetura do Spyder 5.x

Versão deste checkout: `spyder/__init__.py::version_info` → **5.6.0.dev0** (branch `5.x`).
Cuidado ao buscar na internet: a API do Spyder 6 mudou bastante (Run API nova,
`SpyderApplication`, outra organização de widgets). O que vale aqui é o código.

## Mapa de diretórios

| Caminho | O que é |
|---|---|
| `spyder/api/` | **A API pública de plugins.** É aqui que se programa contra. |
| `spyder/plugins/<nome>/` | Os ~30 plugins internos. Cada um é um mini-app. |
| `spyder/config/` | Sistema de configuração: defaults, `CONF`, versionamento, paths. |
| `spyder/utils/` | Helpers: ícones, paleta, stylesheet, qthelpers, programs, conda/pyenv. |
| `spyder/widgets/` | Widgets genéricos, não ligados a um plugin (tabs, findreplace, browser). |
| `spyder/app/` | Bootstrap: `start.py`, `mainwindow.py`, `find_plugins.py`, `cli_options.py`. |
| `spyder/images/`, `spyder/fonts/` | Assets. Ícones legados em PNG/SVG; os novos vêm do qtawesome. |
| `spyder/locale/` | Traduções (`.po`/`.mo`), gerenciadas pelo Crowdin. |
| `setup-spyder/` | Submódulo (repo próprio): launcher `setup-spyder`, perfis, plugin AI Terminal e a suíte do plano. `spyder-kernels`, `python-lsp-server` e `qtconsole` vêm do PyPI (não há `external-deps/`). |
| `installers/`, `installers-conda/` | Empacotamento. Irrelevante para customização pessoal. |

Regra prática: se a pergunta é "onde está a feature X?", olhe primeiro
`spyder/plugins/`. Os nomes de pasta batem com os painéis da UI
(`variableexplorer`, `ipythonconsole`, `findinfiles`, `outlineexplorer`...).

## Os quatro tipos de classe que importam

```
SpyderPluginV2            → plugin sem painel próprio (Application, MainMenu, Run, Toolbar)
  └─ CONTAINER_CLASS      → PluginMainContainer: guarda ações/menus quando não há painel

SpyderDockablePlugin      → plugin com painel dockável (Editor, Plots, Help, Pylint...)
  └─ WIDGET_CLASS         → PluginMainWidget: o painel em si, com toolbar + options menu
```

- `spyder/api/plugins/new_api.py` — `SpyderPluginV2` e `SpyderDockablePlugin`.
- `spyder/api/widgets/main_widget.py` — `PluginMainWidget`.
- `spyder/api/widgets/main_container.py` — `PluginMainContainer`.
- `spyder/api/plugins/old_api.py` — API Spyder 3/4 (`SpyderPluginWidget`). **Legado.**
  Neste branch, o único plugin ainda nela é o **Editor**
  (`class Editor(SpyderPluginWidget, SpyderConfigurationObserver)`) — o que
  explica por que o editor tem menos hooks que o resto. Não escreva código novo
  nessa API.

O plugin é o "controlador": conhece os outros plugins, mexe em config, expõe API
pública. O widget/container é a "view": constrói ações, menus, toolbars. A
convenção do projeto é que o widget não chama outro plugin diretamente — ele
emite um sinal, e o plugin conecta.

## Descoberta e registro

1. `setup.py` declara o entry point group **`spyder.plugins`** (linhas ~287-337).
   Cada linha é `nome = modulo:Classe`.
2. `spyder/app/find_plugins.py` varre esse group:
   - `find_internal_plugins()` — nomes que existem no enum `Plugins`.
   - `find_external_plugins()` — todo o resto. **É por aqui que um plugin seu entra.**
     O nome do entry point tem que ser idêntico a `plugin_class.NAME`, senão
     levanta `SpyderAPIError`.
3. `spyder/api/plugin_registration/registry.py::SpyderPluginRegistry` resolve o
   grafo de dependências, instancia na ordem e emite as notificações de
   disponibilidade/teardown.
4. `spyder/app/mainwindow.py` monta a janela, registra atalhos das ações e
   encaixa os dockwidgets.

O enum de nomes internos está em `spyder/api/plugins/enum.py` (`Plugins.Editor`,
`Plugins.IPythonConsole`, ...). Sempre referencie por esse enum, nunca por string
crua.

## Grafo de dependências

```python
REQUIRES = [Plugins.IPythonConsole]   # sem isso o plugin não carrega
OPTIONAL = [Plugins.Help]             # usa se existir
TABIFY   = [Plugins.VariableExplorer] # com quem dividir aba (só dockáveis)
```

`Plugins.All` em `REQUIRES` é curinga para "todos os plugins disponíveis".
Dependência circular declarada em `REQUIRES` trava o boot; use `OPTIONAL` de um
dos lados para quebrar o ciclo.

## Ciclo de vida (a ordem importa)

| Hook | Quando | Para quê |
|---|---|---|
| `__init__` | instanciação | Não sobrescreva sem chamar `super()`. |
| `on_initialize()` | logo após criar o container/widget | **Obrigatório.** Conectar sinais próprios, criar estado. Aqui os outros plugins ainda NÃO existem. |
| `@on_plugin_available(plugin=X)` | quando X fica pronto | Único lugar seguro para falar com X (`self.get_plugin(X)`). |
| `after_container_creation()` | container/widget criado | Ajustes no widget antes do setup. |
| `before_mainwindow_visible()` | janela montada, ainda oculta | Layout, geometria. |
| `on_mainwindow_visible()` | janela já na tela | Trabalho pesado, diálogos, checagens de rede. |
| `@on_plugin_teardown(plugin=X)` | antes de X morrer | Desfazer o que foi feito no `available`. Simétrico. |
| `can_close()` / `on_close(cancelable)` | fechamento | Salvar estado, vetar saída. |
| `update_font()` / `update_style()` | usuário mudou aparência | Repropagar fonte/tema. |
| `check_compatibility()` (staticmethod) | antes de registrar | Retorna `(bool, str)`; use para exigir SO/dependência. |

Regra de ouro: **tudo que você registra em `on_plugin_available` você desfaz em
`on_plugin_teardown`.** O registry desregistra plugins em runtime (dá para
desabilitar plugin sem reiniciar), e assimetria vira crash.

## Anatomia de um plugin interno

Padrão de pastas (veja `spyder/plugins/pylint/` — é o exemplo mais completo e
ao mesmo tempo pequeno):

```
plugins/pylint/
  plugin.py       # a classe SpyderDockablePlugin
  main_widget.py  # o PluginMainWidget + enums de actions/menus/toolbars
  confpage.py     # a página em Preferências (PluginConfigPage)
  api.py          # constantes públicas (nomes de ações, seções de menu)
  utils.py, images/, tests/
```

`api.py` é convenção do projeto: **classes com constantes string** para IDs de
ações, seções de menu e toolbars, para que outros plugins referenciem sem
importar o widget. Ex.: `spyder/plugins/mainmenu/api.py::ApplicationMenus`.

Exemplo mínimo real (`spyder/plugins/plots/plugin.py`):

```python
class Plots(SpyderDockablePlugin, ShellConnectMixin):
    NAME = 'plots'
    REQUIRES = [Plugins.IPythonConsole]
    TABIFY = [Plugins.VariableExplorer, Plugins.Help]
    WIDGET_CLASS = PlotsWidget
    CONF_SECTION = NAME
    CONF_FILE = False

    @staticmethod
    def get_name(): return _('Plots')
    def get_description(self): return _('Display, explore and save plots.')
    def get_icon(self): return self.create_icon('hist')
    def on_initialize(self):
        self.get_widget().sig_figure_loaded.connect(self._on_first_plot)
```

## Mixins que aparecem em todo lugar

| Mixin | Arquivo | Dá acesso a |
|---|---|---|
| `SpyderConfigurationAccessor` | `api/config/mixins.py` | `get_conf`, `set_conf`, `get_shortcut` |
| `SpyderConfigurationObserver` | `api/config/mixins.py` | habilita `@on_conf_change` |
| `SpyderActionMixin` | `api/widgets/mixins.py` | `create_action`, `get_action(s)` |
| `SpyderMenuMixin` / `SpyderToolbarMixin` / `SpyderToolButtonMixin` | idem | `create_menu`, `create_toolbar`, `create_toolbutton` |
| `SpyderWidgetMixin` | idem | junta os anteriores; base de todo widget do Spyder |
| `ShellConnectMixin` | `api/shellconnect/mixins.py` | plugin com um widget por console IPython |

## Onde continuar

- Criar um plugin próprio → skill `spyder-plugin-externo`
- Configuração e atalhos → skill `spyder-config-atalhos`
- Menus, toolbars, statusbar, ícones, temas → skill `spyder-ui-integracao`
- Mexer no editor de código → skill `spyder-editor`
- Rodar do source e testar → skill `spyder-dev-ambiente`
