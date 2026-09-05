---
name: spyder-editor
description: >
  Arquitetura do editor de código do Spyder 5.x: a cadeia Editor plugin →
  EditorStack → CodeEditor, os Panels (linha, folding, scrollflag, dropdown) e
  seus PanelsManager, as EditorExtension (fechar aspas/parênteses, snippets,
  docstring), TextDecoration, o highlighter de sintaxe, os provedores de
  autocompletar (LSP/fallback/snippets) e as opções da seção `editor`. Use ao
  mexer em algo do editor de texto, adicionar uma faixa lateral, uma decoração,
  um atalho de edição, mudar comportamento de digitação, ou entender por que
  algo do editor não tem hook. Gatilhos: "CodeEditor", "EditorStack", "panel",
  "editor extension", "syntax highlight", "autocompletar", "LSP", "snippet",
  "decoração no editor".
---

# O editor de código do Spyder 5.x

Esta é a parte mais antiga e mais densa da base. `codeeditor.py` tem ~5700
linhas e boa parte da API de plugins **não alcança** o editor: muita coisa só se
customiza por patch no fork ou por conexão a sinais.

## A cadeia de objetos

```
Editor (plugins/editor/plugin.py)        # o plugin — API antiga (SpyderPluginWidget)
 └─ EditorStack (widgets/editor.py)      # abas, arquivos, split; há uma por painel
     └─ CodeEditor (widgets/codeeditor.py)   # UM arquivo aberto
         ├─ panels        (PanelsManager)   faixas ao redor do texto
         ├─ editor_extensions (EditorExtensionsManager)  comportamento de digitação
         ├─ decorations   (TextDecorationsManager)       realces no texto
         └─ highlighter   (utils/syntaxhighlighters.py)  cores da sintaxe
```

Atalhos para navegar:

- `editor.get_current_editor()` → o `CodeEditor` ativo
- `editor.get_current_editorstack()` → a pilha de abas ativa
- `editor.get_current_filename()`

Cada arquivo aberto é uma instância nova de `CodeEditor`, criada em
`EditorStack.create_new_editor()` (linha ~2577) e configurada por
`CodeEditor.setup_editor(...)` (linha ~821) — o método com dezenas de kwargs que
traduz a config em estado do widget. **É o ponto único onde a config da seção
`editor` vira comportamento.**

## Panels — as faixas ao redor do texto

`spyder/api/panel.py::Panel` (subclasse de `EditorExtension`). Posições:
`Panel.Position.TOP / LEFT / RIGHT / BOTTOM / FLOATING`.

Panels embutidos em `spyder/plugins/editor/panels/`:

| Arquivo | O quê |
|---|---|
| `linenumber.py` | números de linha + marcadores de breakpoint/todo |
| `codefolding.py` | dobradura de blocos |
| `edgeline.py` | a linha vertical dos 79 caracteres |
| `indentationguides.py` | guias de indentação |
| `scrollflag.py` | barra de sinalizadores à direita |
| `classfunctiondropdown.py` | combo de classes/funções no topo |
| `debugger.py` | coluna do depurador |

Registro (em `CodeEditor.__init__`, linhas ~352-433):

```python
self.panels.register(MeuPanel(), position=Panel.Position.RIGHT)
```

Um `Panel` implementa `on_install(editor)`, `paintEvent`, `sizeHint`, e liga/
desliga por `enabled`. `PanelsManager` (`panels/manager.py`) cuida de geometria,
margens e ordem por zona.

**Não há API pública para um plugin externo registrar um panel.** As opções são:
patch em `codeeditor.py`, ou pegar cada `CodeEditor` novo por sinal e chamar
`.panels.register()` de fora (funciona, mas é acoplado a detalhe interno — teste
a cada upgrade).

## EditorExtension — comportamento de digitação

`spyder/api/editorextension.py::EditorExtension`. Diferente de `Panel`, não
desenha nada: intercepta o fluxo de edição. As embutidas
(`plugins/editor/extensions/`) são `CloseQuotesExtension`,
`CloseBracketsExtension`, `SnippetsExtension`, `DocstringWriterExtension`.

Registro em `CodeEditor.__init__` (~597):

```python
self.editor_extensions.add(MinhaExtension())
```

Hooks: `on_install(editor)`, `on_uninstall()`, `on_state_changed(state)`,
`clone_settings(original)`. Recuperar depois:
`editor.editor_extensions.get(MinhaExtension)`.

## Decorações

`spyder/plugins/editor/api/decoration.py::TextDecoration` (adaptado do pyQode).
Serve para pintar realce sobre um trecho: linha atual, célula atual, ocorrências,
resultados de busca.

```python
from spyder.plugins.editor.api.decoration import TextDecoration, DRAW_ORDERS

deco = TextDecoration(cursor, draw_order=DRAW_ORDERS['on_top'])
deco.set_background(QColor(SpyderPalette.COLOR_OCCURRENCE_2))
editor.decorations.add(deco)
```

`DRAW_ORDERS` define a sobreposição: `on_bottom`(0) < `current_cell`(1) <
`codefolding`(2) < `current_line`(3) < `on_top`(4). Empate: a decoração menor
fica na frente.

Este é o caminho **mais barato** para uma customização visual pessoal no editor
(marcar linhas longas, destacar TODOs próprios, etc.), porque só precisa de um
`CodeEditor` na mão — não exige patch.

## Sintaxe

`spyder/utils/syntaxhighlighters.py` — `PythonSH`, `CythonSH`, `MarkdownSH`,
`HtmlSH`, ... Cada um lê as cores do esquema ativo em `appearance` (veja a skill
`spyder-ui-integracao`, seção de temas). Para uma linguagem nova, herde
`BaseSH`/`PygmentsSH` e registre em `guess_pygments_highlighter` /
`get_filetype_lexer`. Um esquema de cores novo **não** exige mexer aqui.

## Autocompletar e LSP

`spyder/plugins/completion/` é um plugin com **provedores plugáveis**:

```
providers/languageserver/  -> python-lsp-server (o principal)
providers/fallback/        -> completar por palavras do buffer
providers/snippets/        -> snippets do usuário
```

Os provedores também entram por entry point — group **`spyder.completions`**
(veja `setup.py`, `spyder_completions_entry_points`). Para um provedor próprio,
herde `SpyderCompletionProvider` (`plugins/completion/api.py`) e declare o entry
point. É a única parte do editor com extensibilidade de primeira classe.

Configuração do LSP: `spyder/config/lsp.py` + Preferências → Completação e
linting. Snippets do usuário: `spyder/config/snippets.py`.

## Opções da seção `editor`

Em `spyder/config/main.py`, seção `editor`. As mais mexidas:
`blank_spaces`, `edge_line`, `edge_line_columns`, `indent_guides`,
`code_folding`, `show_class_func_dropdown`, `scroll_past_end`,
`highlight_current_line`, `highlight_current_cell`, `occurrence_highlighting`,
`todo_list`, `close_parentheses`, `close_quotes`, `add_colons`,
`auto_unindent`, `tab_always_indent`, `intelligent_backspace`, `strip_trailing_spaces_on_modify`,
`always_remove_trailing_spaces`, `format_on_save`, `underline_errors`,
`tab_stop_width_spaces`, `wrap`, `autosave_enabled`, `autosave_interval`.

Para trocar um default: edite `DEFAULTS` **e** faça bump minor em `CONF_VERSION`
(`spyder/config/main.py`), senão o valor antigo do usuário continua vencendo.
Para uso pessoal, mudar em Preferências é mais simples e sobrevive a `git pull`.

## Sinais para se pendurar de fora

Do plugin `Editor`:

```python
sig_dir_opened(str)
sig_file_opened_closed_or_updated(str, str)     # (path, language)
sig_editor_focus_changed()
sig_help_requested(dict)
sig_open_files_finished()
```

Do `EditorStack`: `sig_new_file`, `sig_editor_cursor_position_changed(int, int)`.

Padrão típico para customização externa:

```python
@on_plugin_available(plugin=Plugins.Editor)
def on_editor_available(self):
    editor = self.get_plugin(Plugins.Editor)
    editor.sig_file_opened_closed_or_updated.connect(self._on_arquivo)

def _on_arquivo(self, path, language):
    ce = self.get_plugin(Plugins.Editor).get_current_editor()
    if ce is None or language != 'Python':
        return
    # aplicar decoração, registrar panel, ler texto...
```

## Onde não há hook (aceite ou faça patch)

- Registrar `Panel` ou `EditorExtension` oficialmente por plugin externo.
- Interceptar `keyPressEvent` do `CodeEditor` (linha ~4732).
- Adicionar item ao menu de contexto do editor por API pública.
- Alterar `setup_editor()` sem tocar em `codeeditor.py`.

Nesses casos: branch a partir de `5.x`, commit pequeno e focado, e anote o que
mudou — vai dar conflito no próximo rebase.

## Armadilhas

- **`get_current_editor()` retorna `None`** quando não há arquivo aberto. Sempre
  cheque.
- **Um `CodeEditor` por arquivo.** Configurar "o editor" uma vez não pega os
  arquivos abertos depois; pendure no sinal de abertura.
- **Split view** cria `EditorStack`s extras; `get_current_editorstack()` devolve
  só o ativo. Se sua customização precisa valer em todos, itere sobre
  `editor.editorstacks`.
- **Cor hardcoded numa decoração** fica ilegível no outro tema: use
  `SpyderPalette` / o esquema ativo.
