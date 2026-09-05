---
name: spyder-config-atalhos
description: >
  Sistema de configuração do Spyder 5.x: onde ficam os arquivos do usuário
  (~/.spyder-py3), DEFAULTS em spyder/config/main.py, CONF_VERSION e migração,
  get_conf/set_conf, @on_conf_change, config própria de plugin (CONF_FILE,
  CONF_DEFAULTS), páginas de Preferências (PluginConfigPage) e o sistema de
  atalhos (seção shortcuts, contexto/nome, register_shortcut). Use ao mudar um
  default, adicionar opção nova, criar aba de preferências, criar ou rebindar
  atalho, ou quando uma configuração "não gruda" / volta ao padrão. Gatilhos:
  "spyder.ini", "CONF", "get_conf", "on_conf_change", "atalho", "shortcut",
  "Preferências", "resetar configuração", "CONF_VERSION".
---

# Configuração e atalhos no Spyder 5.x

## Onde os arquivos moram

`spyder/config/base.py::get_conf_path()` resolve o diretório nesta ordem:

1. rodando sob pytest ou `--safe-mode` → diretório temporário limpo
   (`get_clean_conf_dir()`);
2. env var **`SPYDER_CONFDIR`** ou CLI `--conf-dir` → esse caminho;
3. Linux → `$XDG_CONFIG_HOME/spyder-py3` (default `~/.config/spyder-py3`);
4. Windows/macOS → `~/.spyder-py3`.

Neste checkout de dev (`5.x` com sufixo `.dev0`), `get_conf_subfolder()` acrescenta
`-dev`: a config vai para **`~/.spyder-py3-dev`**. Ou seja, rodar do source **não
contamina** a sua instalação normal do Spyder. Isso é a coisa mais importante a
saber antes de experimentar. Para forçar o contrário (usar a config estável no
checkout de dev), `SPYDER_USE_DEV_CONFIG_DIR=false`.

Dentro do diretório:

```
~/.spyder-py3[-dev]/
  config/spyder.ini            # a config global (seções main, editor, shortcuts, ...)
  config/transient.ini         # estado volátil (janelas, últimos arquivos)
  plugins/<conf_section>/      # config própria de cada plugin externo (CONF_FILE=True)
  templates/, history.py, ...
```

Reset: `spyder --reset` apaga tudo; `spyder --defaults` volta aos defaults sem
apagar o resto. Para experimentar sem risco: `spyder --conf-dir C:\temp\spyder-teste`.

## DEFAULTS e versionamento

`spyder/config/main.py` define `DEFAULTS`: lista de `(seção, {opção: valor})`.
As seções principais são `main`, `main_interpreter`, `editor`, `ipython_console`,
`variable_explorer`, `plots`, `historylog`, `help`, `shortcuts`, `completions`,
`appearance` (esta vem de `spyder/config/appearance.py`).

No fim do arquivo: `CONF_VERSION = '74.0.0'`. A regra de bump:

| Mudança | Bump |
|---|---|
| Adicionar opção nova | nenhum |
| Mudar o valor default de uma opção existente | **minor** (74.0.0 → 74.1.0) |
| Remover ou renomear opção | **major** (74.0.0 → 75.0.0) |

Sem o bump, a opção antiga do `spyder.ini` do usuário continua vencendo e a
mudança de default "não faz nada". É a causa nº 1 de "mudei o default e nada
aconteceu".

## Ler e escrever config

Qualquer classe que herde `SpyderConfigurationAccessor` (todo plugin e todo
widget do Spyder herda) tem:

```python
self.get_conf('opcao')                       # da própria CONF_SECTION
self.get_conf('opcao', section='editor')     # de outra seção
self.get_conf('opcao', default=42)
self.get_conf_default('opcao')               # o default, ignorando o usuário
self.set_conf('opcao', valor)
self.remove_conf('opcao')
```

Opções aninhadas usam tupla ou barra: `self.get_conf(('a', 'b'))`.

Fora de um objeto Spyder, o singleton é `from spyder.config.manager import CONF`
e a API é `CONF.get(section, option)` / `CONF.set(...)`.

## Reagir a mudanças: @on_conf_change

Precisa que a classe herde `SpyderConfigurationObserver` (plugins já herdam;
widgets via `SpyderWidgetMixin` também).

```python
from spyder.api.config.decorators import on_conf_change

@on_conf_change(option='max_itens')
def _um(self, value): ...                 # assinatura (self, value)

@on_conf_change(option=['a', 'b'])
def _varios(self, option, value): ...     # assinatura (self, option, value)

@on_conf_change(section='editor', option='blank_spaces')
def _de_outra_secao(self, value): ...

@on_conf_change                            # sem option => a seção inteira
def _secao(self, option, value): ...
```

O plugin também recebe `after_configuration_update(options)` depois de um lote de
mudanças aplicadas pela página de Preferências.

Existe `disable_conf(option)` / `restore_conf(option)` para suprimir notificações
temporariamente — útil quando você mesmo está gravando e não quer o eco.

## Config própria de plugin

Para plugin externo, o padrão é arquivo separado:

```python
CONF_SECTION = 'meuplugin'
CONF_FILE = True                                   # ~/.spyder-py3/plugins/meuplugin/
CONF_DEFAULTS = [('meuplugin', {'opcao': True})]   # obrigatório com CONF_FILE=True
CONF_VERSION = '1.0.0'                             # idem, mesma regra de bump
```

`CONF_FILE = False` grava na seção correspondente do `spyder.ini` global — só
para plugin interno.

Dois extras úteis:

- `ADDITIONAL_CONF_OPTIONS = {'secao': {...}}` — o plugin adiciona opções à
  seção de **outro** plugin.
- `ADDITIONAL_CONF_TABS = {'editor': [MinhaTab]}` — o plugin injeta uma aba na
  página de Preferências de outro plugin. As classes herdam de
  `SpyderPreferencesTab` (`spyder/api/preferences.py`). É o caminho para
  "adicionar uma opção minha na tela de preferências do Editor".

## Página de Preferências

```python
from spyder.api.preferences import PluginConfigPage

class MinhaConfPage(PluginConfigPage):
    def setup_page(self):
        chk = self.create_checkbox(_('Ativar'), 'ativar')
        ...
```

E na classe do plugin: `CONF_WIDGET_CLASS = MinhaConfPage` + o par
`register_plugin_preferences` / `deregister_plugin_preferences` nos decorators
de `Plugins.Preferences`.

Helpers disponíveis em `spyder/plugins/preferences/api.py` (todos amarram
sozinhos a opção à config e aplicam no OK/Apply):

`create_checkbox`, `create_radiobutton`, `create_lineedit`, `create_textedit`,
`create_spinbox(prefix, suffix, option, ...)`, `create_combobox`,
`create_file_combobox`, `create_browsedir`, `create_browsefile`,
`create_coloredit`, `create_scedit`, `create_fontgroup`, `create_button`,
`create_tab`.

Passe `section='outra_secao'` num helper para editar opção de outro plugin;
passe `restart=True` para marcar a opção como "requer reiniciar".

## Atalhos

Atalhos vivem na seção **`shortcuts`** do `spyder.ini`, com chave
`"<contexto>/<nome da ação>"`:

```python
'_/close pane':      "Shift+Ctrl+F4",   # contexto '_' = global da aplicação
'_/file switcher':   'Ctrl+P',
'editor/run cell':   "Ctrl+Return",
```

O contexto `_` é o global; senão é o `NAME` do plugin (ou o
`shortcut_context` explícito da ação).

Como uma ação vira atalho configurável:

```python
self.create_action(
    MinhasAcoes.Rodar,
    text=_('Rodar'),
    triggered=self.rodar,
    register_shortcut=True,     # <- sem isso não aparece em Preferências
    shortcut_context='_',       # opcional; default = NAME do plugin
)
```

`spyder/app/mainwindow.py` (~linha 481) varre `plugin.get_actions()` no registro
e chama `self.register_shortcut(action, context, action_name)` para toda ação com
`register_shortcut` verdadeiro. **O nome do atalho na config é o `name` da ação**,
não o texto. Se não houver default na config, o atalho fica em branco e o usuário
define em Preferências → Atalhos.

Todo plugin dockável ganha de graça um atalho `_/switch to <CONF_SECTION>` para
focar o painel.

API programática (plugin `Plugins.Shortcuts`): `register_shortcut`,
`unregister_shortcut`, `get_shortcut(context, name, plugin_name)`,
`set_shortcut(...)`, `apply_shortcuts()`, `reset_shortcuts()`.

## Customizar atalhos sem escrever código

Preferências → Atalhos edita tudo isso pela UI e grava em `spyder.ini`. Para
versionar seu conjunto pessoal, copie a seção `[shortcuts]` do
`~/.spyder-py3/config/spyder.ini` para um arquivo seu e restaure quando trocar de
máquina. Editar o `.ini` com o Spyder aberto não adianta: ele reescreve o arquivo
ao sair.

## Armadilhas

- **Mudou default e nada aconteceu** → faltou bump em `CONF_VERSION`, ou o
  usuário já tem a opção gravada. Teste com `--conf-dir` novo.
- **`@on_conf_change` não dispara** → a classe não herda
  `SpyderConfigurationObserver`, ou você gravou via `CONF.set` com
  `notification=False`.
- **Atalho não aparece em Preferências** → `register_shortcut=False` (o default
  de `create_action`!) ou o plugin `Shortcuts` ainda não estava disponível na hora
  do registro (o mainwindow tem uma fila `shortcut_queue` para isso; se você
  registra ação fora do fluxo normal, ela não entra).
- **Conflito de atalho** → o Spyder avisa mas não impede; o comportamento fica
  indefinido entre as duas ações.
- **`CONF_FILE=True` sem `CONF_DEFAULTS`** → a config nasce vazia e todo
  `get_conf` cai no `default=` passado no call site.
