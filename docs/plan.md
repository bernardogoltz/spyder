# Plano revisado — `setup-spyder` + AI Terminal para Spyder 5.x

Revisado em 2026-09-04. A seção 2.5 fixa o Spyder entregue: fork `bernardogoltz/spyder` via GitHub, não o pacote oficial nem um path local.

## 1. Objetivo

Evoluir o módulo **já existente** `setup-spyder` para que ele:

1. inicie o Spyder customizado (`bernardogoltz/spyder`, API 5.x) instalado no ambiente virtual do projeto, não o pacote oficial do PyPI;
2. use um perfil isolado, sem alterar a configuração global do usuário;
3. carregue um plugin externo chamado **AI Terminal**;
4. execute, dentro desse painel, uma CLI interativa real como `codex` ou `claude`;
5. preserve o comportamento e a API pública atuais do `setup-spyder`.

Fluxo esperado:

```text
projeto/.venv
    └─ uv run setup-spyder --agent codex
          └─ Spyder customizado (GitHub) com perfil isolado
                └─ painel "AI Terminal"
                      └─ Codex CLI em um PTY/ConPTY, no diretório do projeto
```

Exemplo de uso final:

```powershell
uv add --dev setup-spyder
uv run setup-spyder --agent codex
```

Também deverão funcionar:

```powershell
uv run setup-spyder --agent claude
uv run setup-spyder --agent auto
uv run setup-spyder --agent none
```



### Definição de pronto do MVP

O MVP estará pronto quando um pacote instalado por wheel:

- abrir o Spyder customizado a partir do Python do projeto (instalado da internet, não de um path local);
- descobrir o plugin pelo entry point `spyder.plugins`;
- mostrar um terminal que preserve ANSI, entrada interativa, redimensionamento e `Ctrl+C`;
- iniciar `codex` ou `claude` diretamente, sem shell intermediário;
- usar a raiz do projeto como diretório de trabalho;
- encerrar o processo-filho quando o painel ou o Spyder forem fechados;
- não gravar em `~/.spyder-py3` nem armazenar credenciais das CLIs;
- continuar abrindo o Spyder normalmente quando nenhuma CLI estiver instalada.



### Fora do MVP

- criar uma interface de chat própria;
- integrar diretamente as APIs ou SDKs da OpenAI/Anthropic;
- interpretar o fluxo de eventos das CLIs;
- enviar seleção do editor, arquivo atual ou diagnóstico automaticamente;
- instalar ou autenticar as CLIs pelo `setup-spyder`;
- ativar flags de bypass, aprovação automática ou permissões irrestritas;
- alterar o núcleo do Spyder antes de demonstrar que o plugin externo é insuficiente.



## 2. Decisões de arquitetura



### 2.1 Evoluir `setup-spyder`, não criar outro launcher

O pacote já possui os comandos `setup-spyder` e `setup-spyder-integration`, suporte a `--workdir`, `--hide`, `--show`, `--no-launch` e `--keep-config`, além das funções públicas `launch`, `main` e `open_spyder`. A evolução deve manter esses contratos.

O nome de distribuição continua sendo `setup-spyder`. O plugin será incluído na mesma wheel e registrado como plugin externo do Spyder.

### 2.2 Usar um terminal real

O pedido é por uma experiência no estilo Codex/Claude Code CLI. Portanto, o painel não será um `QPlainTextEdit` alimentado por um SDK: ele será um emulador de terminal ligado a um pseudo-terminal.


| Opção                                | Resultado                                                                                     | Decisão                                    |
| ------------------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------ |
| SDK + widget de chat                 | Interface própria, sem a TUI nativa                                                           | Não usar no MVP                            |
| `QProcess` com stdin/stdout em pipes | Não oferece um TTY completo; TUIs podem degradar ou falhar                                    | Não usar como transporte principal         |
| `xterm.js` + PTY/ConPTY              | Preserva a experiência interativa nativa                                                      | Arquitetura escolhida                      |
| `spyder-terminal` 1.2.2              | Boa referência para Spyder 5.2, mas usa servidor local e não deve ser incorporado sem revisão | Usar apenas no protótipo e como referência |




### 2.3 Não acoplar o MVP a um provedor

O plugin conhece perfis de executáveis, não APIs de IA:

- `codex` inicia a Codex CLI interativa;
- `claude` inicia a Claude Code CLI interativa;
- `auto` escolhe uma CLI somente quando a escolha não for ambígua;
- `none` abre o Spyder sem iniciar um agente.

Autenticação, modelo, retomada de sessão e permissões continuam sendo responsabilidade da própria CLI.

### 2.4 Compatibilidade-alvo

- IDE entregue: o fork `bernardogoltz/spyder` (hoje `5.6.0.dev0`, API Spyder 5.x), **não** o pacote `spyder` oficial do PyPI.
- Superfície de API: Spyder 5.x (`>=5.5,<6`). O 5.5.6 oficial permanece só como referência de API, não como dependência nem como o binário que o launcher abre.
- Python: manter a faixa já declarada por `setup-spyder` (`>=3.9`) até que as dependências do terminal imponham uma restrição comprovada.
- Ambiente recomendado ao desenvolver o fork: Python 3.12 (`pyqt5<5.16` não tem wheel confiável acima disso). O `.python-version` 3.11 do launcher continua válido para a suíte do pacote.

### 2.5 O Spyder instalado é o fork publicado na internet

`uv add setup-spyder` / `uv run setup-spyder` tem de instalar e abrir **esta** instância customizada, recuperável da internet, em qualquer máquina. Não aponta para um checkout local e não resolve o Spyder oficial.

| Opção | Resultado | Decisão |
| --- | --- | --- |
| `spyder>=5.5,<6` no PyPI | Instala Spyder-IDE 5.5.6, não este fork | Não usar como fonte |
| Path local (`../..`, `C:\Users\...`, `--editable`) | Só funciona nesta máquina; vaza no artefato | Proibido no pacote publicado |
| `[tool.uv.sources]` só no `pyproject.toml` | Não viaja na wheel; `pip`/`uvx` voltam ao PyPI oficial | Insuficiente sozinho |
| URL Git na dependência publicada | Qualquer consumidor baixa o fork | Canal do MVP |
| Republicar o fork no PyPI com o nome `spyder` | Nome já ocupado pelo Spyder oficial | Impossível |
| Outro nome de distribuição no PyPI, import `spyder` | Índice próprio, sem Git em runtime | Evolução posterior, não bloqueia o MVP |

Dependência publicada do launcher (pin em tag ou commit, nunca path e nunca `main` flutuante):

```toml
dependencies = [
  "pandas>=2.0",
  "rich>=13.9",
  "spyder @ git+https://github.com/bernardogoltz/spyder.git@<tag-ou-commit>",
]
```

A versão do fork é pré-release (`5.6.0.dev0`). Sem aceitar pré-release, o resolvedor ignora o Git e cai no 5.5.6 oficial:

```toml
[tool.uv]
prerelease = "allow"
```

A URL PEP 508 precisa estar em `[project].dependencies` (entra no METADATA da wheel). `[tool.uv.sources]` no repositório do launcher é atalho de desenvolvimento, não substitui isso.

Confirmação depois de instalar:

```powershell
uv run python -c "import spyder; print(spyder.__version__)"
```

Tem de imprimir a versão do fork (`5.6.0.dev0` ou a tag pinada), não `5.5.6`.

Regras:

- Nenhum caminho absoluto ou instalação editável deste checkout entra no artefato, no `METADATA` ou no `uv.lock` publicado.
- `setup-spyder-integration` (GitHub ou `--local`) também tem de resolver o fork pela URL publicada. `--local` testa o launcher ainda não enviado; não troca o Spyder por um path.
- O override Git puxa o pacote `spyder`. `spyder-kernels`, `python-lsp-server` e `qtconsole` continuam do PyPI, salvo falha reproduzível que exija os subrepos.
- Customizações que são “deste IDE” (defaults, patches) vivem em `bernardogoltz/spyder` e viajam com o Git. Launcher, perfil isolado e o plugin **AI Terminal** vivem em `setup-spyder`.
- O fork **deixa de empacotar** `setup_spyder/` na distribuição `spyder` (`get_subpackages('setup_spyder')`, console script `setup-spyder`, entry point interno `claude_code`). Senão, instalar os dois pacotes cria dois módulos `setup_spyder` e o IDE sombra o launcher. O plugin `setup_spyder_ai` registra-se só no `pyproject.toml` do `setup-spyder`.

## 3. Arquitetura proposta

```text
setup-spyder CLI/API
    │
    ├─ resolve projeto, perfil e provedor
    ├─ cria o processo-filho com o mesmo sys.executable
    └─ define SPYDER_CONFDIR e contexto do plugin antes de importar Spyder
             │
             ▼
Spyder 5.x
    └─ entry point spyder.plugins: setup_spyder_ai
             │
             ▼
AITerminalPlugin (SpyderDockablePlugin)
    └─ AITerminalWidget
          ├─ QWebEngineView com assets locais do xterm.js
          ├─ QWebChannel
          └─ PTYWorker
                ├─ Windows: ConPTY via pywinpty
                └─ POSIX: PTY via ptyprocess/pexpect
                         │
                         ▼
                    codex | claude
```

O canal entre JavaScript e Python deve ser local ao processo por `QWebChannel`. Isso evita abrir uma porta HTTP/WebSocket apenas para transportar entrada e saída do terminal.

Se um protótipo precisar temporariamente de servidor loopback, ele deverá:

- escutar apenas em `127.0.0.1`;
- usar porta atribuída pelo sistema;
- exigir token aleatório por sessão;
- validar `Origin`;
- desativar debug e autoreload;
- encerrar o servidor e todos os processos associados ao fechar o painel.

Essa alternativa não é a arquitetura de entrega.

## 4. Estrutura alvo do pacote

```text
setup-spyder/
├─ pyproject.toml
├─ src/
│  └─ setup_spyder/
│     ├─ __init__.py
│     ├─ cli.py                    # interface atual, ampliada sem quebra
│     ├─ integration.py            # comando atual, preservado
│     ├─ launcher.py               # processo-filho e inicialização do Spyder
│     ├─ profile.py                # perfil efêmero/persistente e seed versionado
│     └─ plugin/
│        ├─ __init__.py
│        ├─ plugin.py              # AITerminalPlugin
│        ├─ main_widget.py         # dock e ações
│        ├─ preferences.py         # provedor, autostart e aparência
│        ├─ providers.py           # resolução segura de codex/claude
│        ├─ pty_worker.py           # ciclo de vida e transporte PTY
│        └─ assets/
│           ├─ terminal.html
│           ├─ terminal.js
│           ├─ xterm.js
│           └─ xterm.css
└─ tests/
   ├─ unit/
   ├─ qt/
   ├─ integration/
   └─ e2e/
```

Entrada adicional em `pyproject.toml`:

```toml
[project.entry-points."spyder.plugins"]
setup_spyder_ai = "setup_spyder.plugin.plugin:AITerminalPlugin"
```

O valor de `AITerminalPlugin.NAME` deve ser exatamente `setup_spyder_ai`, pois o Spyder valida a igualdade entre o nome do entry point e o nome declarado pelo plugin.

Dependências de PTY devem ser condicionais por plataforma e fixadas somente após o protótipo validar versões compatíveis. A dependência de Spyder segue a seção 2.5 (URL Git do fork, pinada, com pré-release permitido):

```toml
dependencies = [
  "pandas>=2.0",
  "rich>=13.9",
  "spyder @ git+https://github.com/bernardogoltz/spyder.git@<tag-ou-commit>",
  "pywinpty>=2; platform_system == 'Windows'",
  "ptyprocess>=0.7; platform_system != 'Windows'",
]
```

Os limites de PTY acima são ilustrativos até a fase de compatibilidade. Não adicionar `claude-agent-sdk` nem SDK da OpenAI ao MVP. Não substituir a URL Git por `spyder>=5.5,<6` do PyPI nem por path local.

## 5. Launcher e perfis



### 5.1 Compatibilidade da CLI

Preservar todos os argumentos existentes e acrescentar:

```text
--agent {auto,codex,claude,none}
--profile {ephemeral,project}
--conf-dir PATH
--reset-profile
```

Regras:

- `--agent` sobrescreve a preferência salva apenas para aquela execução;
- `--profile ephemeral` mantém o comportamento isolado atual e será o padrão inicial para não quebrar usuários;
- `--profile project` usa `<raiz>/.spyproject/setup-spyder/`;
- `--conf-dir` tem precedência explícita sobre os dois modos;
- `--keep-config` continua válido para perfis efêmeros;
- `--reset-profile` só remove/recria o perfil resolvido depois de validar que o caminho está dentro do diretório esperado.



### 5.2 Processo-filho limpo

O processo principal não deve importar módulos de configuração do Spyder antes de preparar o ambiente. Ele deve iniciar um bootstrap filho usando o mesmo `sys.executable`; o bootstrap então:

1. define `SPYDER_CONFDIR`;
2. define `SETUP_SPYDER_AGENT`, `SETUP_SPYDER_WORKDIR` e a opção de autostart;
3. só então importa e inicia o Spyder;
4. repassa os argumentos adicionais sem alterar sua ordem.

Isso evita reutilizar singletons de configuração inicializados com o diretório errado.

### 5.3 Persistência sem sobrescrever o usuário

As preferências visuais e do plugin devem ser aplicadas como um **seed versionado**, somente ao criar o perfil ou migrar sua versão. Não regravar preferências em toda inicialização.

- Perfil efêmero: diretório temporário exclusivo; pode usar `--new-instance`.
- Perfil de projeto: perfil estável; por padrão, respeitar o mecanismo de instância única do Spyder e não forçar `--new-instance` sobre o mesmo diretório.

O launcher não deve limpar variáveis `CONDA_*` nem alterar a descoberta de ambientes sem um teste que demonstre um conflito real. Ao executar no `.venv` via `uv run`, o Spyder deve usar naturalmente o Python daquele ambiente.

## 6. Plugin `AI Terminal`

Esqueleto esperado:

```python
class AITerminalPlugin(SpyderDockablePlugin):
    NAME = "setup_spyder_ai"
    REQUIRES = [Plugins.Preferences]
    OPTIONAL = [
        Plugins.Editor,
        Plugins.Projects,
        Plugins.WorkingDirectory,
        Plugins.MainMenu,
    ]
    TABIFY = [Plugins.IPythonConsole]
    CONF_FILE = True
```

O plugin deverá definir `CONF_DEFAULTS`, versão de configuração, página de preferências e os hooks de inicialização/encerramento da API do Spyder 5.

`REQUIRE_WEB_WIDGETS` deve permanecer habilitado: o painel depende de `QWebEngineView`. O launcher não deverá passar `--no-web-widgets`.

### 6.1 Carregamento robusto

O backend específico de plataforma não deve ser importado no topo do módulo do plugin. A importação será tardia, no momento de criar o terminal, para que uma dependência opcional ausente produza uma mensagem dentro do painel em vez de fazer o plugin desaparecer durante a descoberta.

Falhas de compatibilidade devem aparecer:

- no próprio painel, com ação sugerida;
- no log/stderr do launcher;
- sem ocultar exceções de importação ou dependências críticas.



### 6.2 Emulador e transporte

O frontend xterm deve receber apenas assets empacotados localmente. Não carregar JavaScript por CDN em tempo de execução.

Contrato mínimo do `PTYWorker`:

- `start(argv, cwd, env)`;
- `write(data)`;
- `resize(rows, cols)`;
- `interrupt()`;
- `terminate(grace_period)`;
- sinais de saída, término e erro;
- encerramento da árvore/process group sem deixar processos órfãos.

O executável deve ser iniciado com lista de argumentos, nunca por concatenação em um shell. O ambiente será herdado, com apenas as adições necessárias ao terminal.

### 6.3 Provedores

Interface interna sugerida:

```python
@dataclass(frozen=True)
class AgentProvider:
    name: str
    executable: str
    argv: tuple[str, ...]
```

Resolução:

1. opção `--agent` explícita;
2. preferência persistida do plugin;
3. se apenas uma CLI conhecida estiver no `PATH`, usar essa CLI;
4. se ambas estiverem disponíveis e não houver preferência, exibir seletor no painel sem iniciar nenhuma;
5. se nenhuma estiver disponível, manter o painel funcional com instrução curta de instalação/verificação.

Usar `shutil.which` para descoberta. Não pressupor caminhos de instalação, modelos ou flags específicas de uma versão.

## 7. Experiência do usuário

O painel deve ser um terminal, não um transcript de chat. Barra de ações mínima:

- seletor de provedor;
- **New session**;
- **Restart**;
- **Interrupt** (`Ctrl+C`);
- **Clear**;
- **Close session**;
- indicador de estado: `starting`, `running`, `exited` ou `error`.

Comportamento:

- diretório inicial: raiz resolvida do projeto;
- autostart configurável, desativado quando a escolha de provedor for ambígua;
- troca de provedor: encerra a sessão atual com confirmação quando houver processo ativo;
- troca de projeto/diretório: afeta novas sessões; não move silenciosamente uma sessão em execução;
- atalhos e seleção/cópia seguem o comportamento do terminal incorporado;
- campainha do terminal pode ser desligada nas preferências do painel, sem monkeypatch global de `QApplication.beep`.



## 8. Aparência e “instância própria”

A identidade da instância virá do perfil isolado, preferências versionadas e plugin, não de alterações irreversíveis no Spyder.

O seed inicial pode configurar:

- tema e fonte;
- quebra de linha e opções do editor;
- posição inicial do painel;
- preferência de provedor e autostart;
- avisos rotineiros de atualização, tour ou DPI, apenas quando existirem chaves públicas/estáveis para isso.

Não desabilitar globalmente caixas de erro, avisos de dependência ou mensagens críticas. A ausência do terminal/CLI deve degradar apenas o plugin, nunca impedir o Spyder de abrir.

## 9. Fases de implementação



### Fase 0 — Baseline e ADR

- congelar os contratos públicos atuais de `setup-spyder` com testes;
- registrar uma ADR escolhendo terminal PTY em vez de interface por SDK;
- criar uma matriz mínima Spyder/Python/SO;
- validar o carregamento de um plugin externo vazio a partir de uma wheel.

**Saída:** entry point descoberto no Spyder customizado instalado a partir do GitHub (`bernardogoltz/spyder`), sem editar o núcleo além de deixar de empacotar `setup_spyder` dentro da distribuição `spyder`.

### Fase 1 — Protótipo vertical do terminal

- estudar `spyder-terminal` 1.2.2 apenas como referência compatível com Spyder 5;
- provar xterm + `QWebChannel` + PTY/ConPTY;
- executar primeiro um programa TUI de teste controlado;
- validar ANSI, Unicode, resize, paste, `Ctrl+C` e encerramento;
- confirmar que nenhuma porta TCP é aberta pela solução final.

**Saída:** terminal real e interativo no Windows; repetir os testes no primeiro sistema POSIX suportado.

### Fase 2 — Refatoração segura do launcher

- separar `cli.py`, `launcher.py` e `profile.py`;
- mover a importação do Spyder para o bootstrap filho;
- implementar perfis efêmero e de projeto;
- preservar os argumentos, funções públicas e códigos de saída existentes;
- aplicar seed de configuração versionado.

**Saída:** a suíte atual continua verde e o novo perfil não toca a configuração global.

### Fase 3 — Plugin mínimo

- implementar `AITerminalPlugin` e `AITerminalWidget`;
- empacotar assets web locais;
- implementar `PTYWorker` por plataforma;
- adicionar ações de iniciar, interromper, reiniciar e fechar;
- garantir cleanup em todas as rotas de encerramento.

**Saída:** uma CLI arbitrária roda no painel sem processo órfão.

### Fase 4 — Codex e Claude

- implementar descoberta por `PATH` e seletor de provedor;
- iniciar as CLIs em modo interativo, sem flags inseguras;
- implementar `--agent`, preferência e autostart;
- tratar CLI ausente ou versão incompatível dentro do painel;
- testar com contas já autenticadas, sem automatizar login.

**Saída:** Codex CLI e Claude Code CLI preservam suas TUIs nativas no painel.

### Fase 5 — Polimento da instância

- página de preferências;
- seed visual versionado;
- integração opcional com Working Directory e Projects;
- logs diagnósticos e mensagens acionáveis;
- documentação de instalação, atualização, autenticação e solução de problemas.

**Saída:** experiência previsível em primeiro uso e em perfis já existentes.

### Fase 6 — Empacotamento e release

- testar wheel e sdist em ambientes limpos, não apenas instalação editável;
- validar que assets, entry point e dependências condicionais estão no artefato;
- validar que o METADATA puxa `bernardogoltz/spyder` por URL Git pinada, sem path local e sem o Spyder oficial;
- testar `uv add --dev setup-spyder` numa máquina sem o checkout do fork e confirmar `spyder.__version__` do fork;
- testar upgrade de `setup-spyder` 0.2.0;
- atualizar changelog e publicar uma versão minor, sugerida `0.3.0`.

**Saída:** instalação reproduzível com `uv add --dev setup-spyder` (pré-release permitido) e execução com `uv run setup-spyder` abrindo o fork, não o Spyder oficial.

## 10. Estratégia de testes



### Unitários

- resolução de projeto e diretório de trabalho;
- precedência de `--agent` e perfil;
- descoberta de executáveis;
- criação, migração e reset seguro do perfil;
- construção de `argv` sem shell;
- preservação dos argumentos atuais;
- igualdade entre entry point e `PluginClass.NAME`.



### Qt/plugin

- registro e fechamento do dock;
- estados visuais do processo;
- envio de input e resize com backend falso;
- erro de dependência exibido no painel;
- inicialização do Spyder mesmo quando o backend do terminal falha.



### PTY por plataforma

Usar um pequeno programa TUI determinístico para verificar:

- códigos ANSI e Unicode;
- entrada caractere a caractere;
- resize;
- `Ctrl+C`;
- código de saída;
- encerramento da árvore de processos.

Não depender de rede, conta ou credencial real nesses testes.

### Integração/E2E

- instalar a wheel em ambiente limpo, sem checkout local do fork;
- abrir o Spyder customizado resolvido pela URL publicada (`5.6.0.dev0` ou a tag pinada), não o 5.5.6 oficial;
- validar projeto com espaços e caracteres não ASCII no caminho;
- abrir dois projetos com perfis distintos;
- confirmar que o kernel usa o Python do projeto;
- confirmar que não houve escrita na configuração global;
- testar `codex`, `claude`, ambas presentes e nenhuma presente;
- confirmar ausência de porta TCP aberta pelo plugin;
- confirmar ausência de processo-filho após fechar painel e aplicativo;
- capturar stderr/logs para que falhas de descoberta do plugin não sejam silenciosas.



## 11. Critérios de aceitação

- [ ] `uv run setup-spyder` preserva o comportamento atual.
- [ ] `uv run setup-spyder --agent codex` abre o Codex no painel quando disponível.
- [ ] `uv run setup-spyder --agent claude` abre o Claude no painel quando disponível.
- [ ] O painel é um terminal TTY real, com ANSI, resize e `Ctrl+C`.
- [ ] Nenhuma credencial ou token de API é salvo pelo plugin.
- [ ] Nenhuma flag de bypass é adicionada implicitamente.
- [ ] Nenhum servidor local é necessário para o transporte do terminal.
- [ ] Nenhum processo do agente fica órfão após o encerramento.
- [ ] A wheel contém o entry point e todos os assets web.
- [ ] O Spyder abre mesmo sem CLI ou backend PTY disponível.
- [ ] O perfil do projeto não sobrescreve preferências em toda inicialização.
- [ ] O pacote não contém caminho absoluto nem dependência editável para um checkout local.
- [ ] `uv add setup-spyder` instala o Spyder de `github.com/bernardogoltz/spyder`, não o pacote oficial do PyPI.
- [ ] A versão importável de `spyder` é a do fork pinado, não `5.5.6`.
- [ ] A distribuição `spyder` do fork não empacota `setup_spyder` nem o script `setup-spyder`.
- [ ] O projeto não exige Conda.



## 12. Riscos e mitigação


| Risco | Mitigação |
| --- | --- |
| `spyder>=5.5,<6` resolver o 5.5.6 oficial | URL Git do fork em `[project].dependencies` + `prerelease = "allow"` |
| Path local vazar no artefato | proibir `--editable`/path no METADATA e no lock publicado; pin Git |
| `[tool.uv.sources]` não viajar na wheel | a URL PEP 508 vive nas dependências do projeto, não só no uv |
| Dois módulos `setup_spyder` (fork + launcher) | o fork deixa de empacotar `setup_spyder`; o plugin registra-se só no launcher |
| Instalar o Spyder oficial por cima do fork (mesmo nome) | documentar que o launcher puxa o Git; não misturar `uv add spyder` do PyPI |
| APIs internas divergirem entre 5.5 e o fork 5.6.dev | limitar o uso à API pública de plugins; o binário alvo é só o fork |
| Comportamento diferente de PTY no Windows/POSIX | backends isolados, testes de contrato comuns e CI por plataforma |
| `QWebEngine` ausente ou desabilitado | verificação de compatibilidade e erro restrito ao painel |
| Plugin sumir por `ImportError` no carregamento | imports tardios, teste da wheel e preservação de stderr/logs |
| Processo do agente sobreviver ao Spyder | process group/job object, timeout e encerramento escalonado |
| Perfil persistente ser usado por duas instâncias | respeitar instância única e bloquear o perfil de projeto |
| Mudança de flags das CLIs | iniciar o comando-base e não hardcodar modelo/opções frágeis |
| Terminal incorporado ampliar superfície de ataque | assets locais, sem listener TCP, sem shell e sem comandos concatenados |
| Confusão entre `uvx` e ambiente do projeto | documentar `uv add --dev` + `uv run` como caminho canônico |




## 13. Evoluções posteriores

Depois do MVP estável, uma segunda modalidade poderá oferecer integração estruturada com o editor. Ela deve ser separada do terminal nativo e usar interfaces próprias para automação, por exemplo saída JSON não interativa ou protocolos oficiais dos agentes.

Possíveis recursos futuros:

- enviar arquivo/seleção atual sob ação explícita do usuário;
- aplicar diffs com visualização e confirmação;
- mostrar eventos estruturados em painel próprio;
- registrar sessões por projeto;
- suportar provedores configuráveis por comando, mantendo allowlist e revisão de argumentos.



## 14. Referências



### Código local

- `[setup.py](../setup.py)` — registro e descoberta de plugins no fork; ponto de remoção do `setup_spyder` empacotado.
- `[spyder/app/find_plugins.py](../spyder/app/find_plugins.py)` — validação dos entry points externos.
- `[spyder/api/plugins/new_api.py](../spyder/api/plugins/new_api.py)` — API `SpyderDockablePlugin` do Spyder 5.
- `[spyder/config/base.py](../spyder/config/base.py)` — resolução de `SPYDER_CONFDIR`.
- `[spyder/app/cli_options.py](../spyder/app/cli_options.py)` — opções reais da CLI do Spyder.
- `https://github.com/bernardogoltz/spyder` — origem publicada do IDE que o launcher instala.
- `https://github.com/bernardogoltz/setup-spyder` — origem publicada do launcher (submódulo em `external-deps/setup-spyder`).



### Fontes oficiais

- [Spyder 5 — tutorial de desenvolvimento de plugins](https://docs.spyder-ide.org/5/workshops/plugin-development.html)
- [Spyder 5 — plugin Terminal](https://docs.spyder-ide.org/5/plugins/terminal.html)
- [Spyder 5.5.6](https://github.com/spyder-ide/spyder/releases/tag/v5.5.6)
- `spyder-terminal` [1.2.2 para Spyder 5.2.x](https://github.com/spyder-ide/spyder-terminal/releases/tag/v1.2.2)
- [Terminado](https://github.com/jupyter/terminado)
- [pywinpty](https://github.com/andfoy/pywinpty)
- [Codex CLI — referência oficial](https://developers.openai.com/codex/cli/reference)
- [Codex CLI — modo não interativo](https://developers.openai.com/codex/noninteractive)
- [Claude Code — referência da CLI](https://code.claude.com/docs/en/cli-usage)

