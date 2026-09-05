# Guia curto da codebase para o `setup-spyder`

> Escopo: saber o mínimo necessário do fork `spyder/` para entregar o launcher e o plugin externo **AI Terminal** descritos em [`plan.md`](plan.md). O objetivo não é desenvolver o Spyder inteiro.

## Mapa de relevância

| Prioridade | Área/arquivo | O que é preciso saber | Para quê no projeto |
|---|---|---|---|
| **Dominar** | `setup_spyder/` | Esta deve ser a codebase do produto: CLI/API pública, launcher, perfis e plugin. Hoje só existe `__init__.py`; `cli.py` e o restante ainda precisam ser criados. | Quase toda a implementação do MVP deve ficar aqui e ser distribuída na wheel `setup-spyder`. |
| **Dominar** | `docs/plan.md` | Escopo, decisões, fases, critérios de aceite e itens explicitamente fora do MVP. | É a fonte de verdade para evitar expansão acidental do produto. |
| **Entender** | `spyder/app/find_plugins.py` | Plugins externos são encontrados pelo grupo de entry points `spyder.plugins`; o nome do entry point deve ser igual a `PluginClass.NAME`. Erros de importação são enviados ao stderr. | Fazer `setup_spyder_ai` ser descoberto de uma wheel e impedir que dependências opcionais derrubem seu carregamento. |
| **Entender** | `spyder/api/plugins/new_api.py` | Contrato de `SpyderDockablePlugin`: `NAME`, `REQUIRES`, `OPTIONAL`, `WIDGET_CLASS`, configuração, `on_initialize()` e `on_close()`. | Implementar o ciclo de vida do painel e encerrar terminal/processo-filho corretamente. |
| **Entender** | `spyder/api/widgets/main_widget.py` | Contrato de `PluginMainWidget`, ações, toolbar/menu, foco e fechamento do widget. | Construir o dock do AI Terminal sem depender de detalhes da janela principal. |
| **Copiar como referência** | `spyder/app/tests/spyder-boilerplate/` | É o menor exemplo local de plugin dockável, página de preferências, ação e widget. | Começar pelo esqueleto correto, reduzindo leitura desnecessária do núcleo. |
| **Consultar** | `spyder/plugins/history/plugin.py` | Exemplo real e pequeno de dependências obrigatórias/opcionais, preferências e hooks de disponibilidade/teardown. | Integrar opcionalmente Preferences, IPython Console e outros plugins usando a API pública. |
| **Entender** | `spyder/config/base.py` | `SPYDER_CONFDIR` determina o diretório de configuração; precisa estar definido antes da importação que inicializa a configuração. | Isolar perfis e nunca escrever na configuração global do usuário. |
| **Entender** | `spyder/app/start.py` e `spyder/app/cli_options.py` | Ordem do bootstrap, `--conf-dir`, `--new-instance`, `--workdir` e encaminhamento de argumentos. | Criar o processo-filho limpo e preservar a CLI do Spyder. Atenção: `--profile` já significa outra coisa no Spyder; deve ser consumido pelo launcher, não repassado. |
| **Consultar** | `spyder/api/plugins/enum.py` | Nomes canônicos de `Plugins.Preferences`, `Editor`, `Projects`, `WorkingDirectory`, `MainMenu` e `IPythonConsole`. | Declarar `REQUIRES`, `OPTIONAL` e `TABIFY` sem strings frágeis. |
| **Consultar** | `spyder/app/mainwindow.py` | Onde plugins externos são registrados e onde o fechamento global acontece. | Diagnosticar integração e shutdown somente se os testes do plugin mostrarem um problema. Não é ponto normal de alteração. |
| **Validar** | `setup.py`, `MANIFEST.in` e futuro `pyproject.toml` do pacote | Entry point, dependências condicionais e inclusão dos assets locais do xterm. | Garantir que wheel/sdist funcionem; instalação editável sozinha não prova o empacotamento. |
| **Validar** | `bootstrap.py`, `pytest.ini`, `runtests.py`, `spyder/app/tests/` | Como executar o fork e seus testes; quais testes já cobrem descoberta e CLI. | Usar o fork como bancada de compatibilidade com Spyder 5.6.dev, não como produto a ser reescrito. |

## O que é dispensável para o MVP

| Pode ficar de fora agora | Motivo | Quando voltaria a importar |
|---|---|---|
| Implementação interna dos plugins `editor`, `plots`, `variableexplorer`, `pylint`, `profiler`, `completion`, `help` etc. | O terminal só precisa da API pública e de integrações opcionais rasas. | Ao criar ações explícitas como “enviar seleção/arquivo” depois do MVP. |
| `spyder-kernels`, console IPython, depurador e protocolo Jupyter/ZMQ | A CLI de IA rodará em PTY/ConPTY próprio, não dentro de um kernel. | Se surgir integração estruturada com execução Python ou estado do console. |
| `external-deps/python-lsp-server`, `qtconsole` e `spyder-kernels` | São subprojetos de desenvolvimento do Spyder, sem participação no transporte do terminal. | Apenas diante de falha reproduzível causada por uma dessas integrações. |
| `installers/`, `installers-conda/`, `binder/`, `branding/`, `img_src/` e release do Spyder | A entrega é uma wheel externa instalada no ambiente do projeto. | Se um dia houver distribuição própria do IDE inteiro. |
| Temas, tour, layouts globais, sistema de updates e preferências internas não públicas | O perfil isolado deve aplicar apenas um seed pequeno e versionado. | No polimento, e somente para chaves públicas/estáveis verificadas. |
| Arquitetura completa de `mainwindow.py` e mudanças no núcleo `spyder/` | Um plugin externo é a fronteira arquitetural escolhida. | Só após um teste demonstrar concretamente que a API pública é insuficiente. |
| SDKs/APIs da OpenAI ou Anthropic, chat próprio e parsing de eventos | O MVP preserva a TUI nativa de `codex`/`claude` em um terminal real. | Em uma modalidade futura, separada do terminal. |
| Conda e descoberta customizada de ambientes | O caminho canônico é `.venv` + `uv run`; o Python do processo deve ser `sys.executable`. | Apenas se a compatibilidade futura declarar Conda como requisito. |

## Ordem de leitura recomendada

| Ordem | Leia | Pare quando souber responder |
|---:|---|---|
| 1 | `docs/plan.md` | “O que constitui o MVP e o que está fora dele?” |
| 2 | `spyder/app/tests/spyder-boilerplate/spyder_boilerplate/spyder/plugin.py` | “Qual é o menor plugin dockável válido?” |
| 3 | `spyder/app/find_plugins.py` + trecho de entry points em `setup.py` | “Como a wheel é descoberta e qual nome precisa coincidir?” |
| 4 | `spyder/api/plugins/new_api.py` + `spyder/api/widgets/main_widget.py` | “Quais hooks e classes públicas controlam criação, integração e cleanup?” |
| 5 | `spyder/config/base.py` + `spyder/app/start.py` + `spyder/app/cli_options.py` | “O que precisa ser definido antes de importar/iniciar o Spyder?” |
| 6 | `spyder/plugins/history/plugin.py` | “Como conectar dependências opcionais sem acoplar o plugin ao núcleo?” |

## Regra prática de decisão

| Se a tarefa envolve… | Trabalhe em… | Evite… |
|---|---|---|
| argumentos, projeto, perfil ou processo-filho | `setup_spyder/cli.py`, `launcher.py`, `profile.py` | alterar `spyder/app/start.py` |
| painel, preferências ou sessão do agente | `setup_spyder/plugin/` | adicionar um plugin interno ao `setup.py` deste fork |
| ANSI, teclado, resize, `Ctrl+C` ou cleanup | frontend xterm + `pty_worker.py` e testes de contrato | pipes simples de `QProcess` como transporte principal |
| descoberta que falha | entry point da wheel, `NAME`, imports tardios e logs | mascarar `ImportError` ou corrigir o núcleo sem reproduzir a falha |
| aparência da “instância própria” | seed versionado no perfil isolado | monkeypatches globais ou regravação de preferências a cada início |

**Linha divisória:** se uma mudança no diretório `spyder/` parece necessária para entregar o MVP, primeiro escreva um teste de integração que prove a limitação. O resultado preferido continua sendo corrigir `setup_spyder/` e manter o fork apenas como ambiente de validação.
