# Plano de Execução — Skill `refactor-arch`

Plano derivado do [DESAFIO.md](./DESAFIO.md). Cada task tem objetivo, subtarefas, entregáveis e critério de pronto. Execute na ordem: as tasks dependem das anteriores.

## Visão geral

| # | Task | Entregável principal | Depende de |
|---|------|----------------------|------------|
| 0 | Preparação do ambiente | Fork + ambientes rodando | — |
| 1 | Baseline funcional dos 3 projetos | Lista de endpoints + script de smoke test | 0 |
| 2 | Análise manual — code-smells-project | Achados (≥5) | 1 |
| 3 | Análise manual — ecommerce-api-legacy | Achados (≥5) | 1 |
| 4 | Análise manual — task-manager-api | Achados (≥5) | 1 |
| 5 | README — seção "Análise Manual" | `README.md` | 2, 3, 4 |
| 6 | Estrutura da skill + SKILL.md | `.claude/skills/refactor-arch/SKILL.md` | 5 |
| 7 | Referência: análise de projeto | `references/project-analysis.md` | 6 |
| 8 | Referência: catálogo de anti-patterns | `references/anti-patterns-catalog.md` | 5, 6 |
| 9 | Referência: template de relatório | `references/audit-report-template.md` | 8 |
| 10 | Referência: guidelines MVC | `references/mvc-guidelines.md` | 6 |
| 11 | Referência: playbook de refatoração | `references/refactoring-playbook.md` | 8, 10 |
| 12 | Execução — Projeto 1 | `reports/audit-project-1.md` + código refatorado | 7–11 |
| 13 | Execução — Projeto 2 | `reports/audit-project-2.md` + código refatorado | 12 |
| 14 | Execução — Projeto 3 | `reports/audit-project-3.md` + código refatorado | 12 |
| 15 | Iteração / ajustes da skill | Skill sincronizada nos 3 projetos | 12–14 |
| 16 | README — Construção, Resultados, Como Executar | `README.md` completo | 15 |
| 17 | Revisão final e entrega | Repositório público no GitHub | 16 |

---

## Task 0 — Preparação do ambiente

**Objetivo:** ter o repositório como fork público e os 3 projetos executáveis localmente.

- [x] Confirmar que o repositório é um fork público do repositório base (`git remote -v`) — `origin` = `lucianovsjr/mba-ia-refactor-projects-skill`
- [x] Branch de trabalho: commits diretos na `main`
- [x] Python: criar um virtualenv por projeto Flask (`code-smells-project/.venv`, `task-manager-api/.venv`) e instalar `requirements.txt`
- [x] Node: `npm install` em `ecommerce-api-legacy/`
- [x] Garantir `.gitignore` cobrindo `.venv/`, `node_modules/`, `*.db`, `__pycache__/`, `.env` (já coberto pelo boilerplate)
- [x] Atenção macOS: a porta 5000 está ocupada pelo AirPlay Receiver (`ControlCenter`) — `python app.py` falha com *Address already in use*

**Ambiente verificado:** Python 3.11.15, Node v20.20.0, npm 10.8.2.

**Comandos de boot usados localmente (sem alterar o código original):**

| Projeto | Comando | Porta | Smoke test |
|---|---|---|---|
| code-smells-project | `.venv/bin/flask --app app run --port 5001` | 5001 | `GET /produtos` → 200 |
| ecommerce-api-legacy | `npm start` | 3000 | `GET /api/admin/financial-report` → 200 |
| task-manager-api | `.venv/bin/python seed.py && .venv/bin/flask --app app run --port 5002` | 5002 | `GET /tasks` → 200 |

> Os comandos originais (`python app.py`) fixam a porta 5000 no código; para usá-los é preciso desativar o AirPlay Receiver em Ajustes do Sistema.

**Pronto quando:** os 3 projetos sobem com seus comandos originais. ✅ (Python via `flask run` em porta alternativa)

---

## Task 1 — Baseline funcional dos 3 projetos

**Objetivo:** registrar o comportamento *antes* da refatoração para poder provar que nada quebrou depois.

- [x] `code-smells-project`: listar todas as rotas com método e path — 19 rotas
- [x] `ecommerce-api-legacy`: listar rotas e usar o `api.http` como roteiro — 3 rotas
- [x] `task-manager-api`: listar rotas de todos os blueprints — 20 rotas
- [x] Para cada projeto, salvar exemplos de request/response (status code + formato do JSON) de cada endpoint
- [x] Criar um script de smoke test por projeto em `scripts/` para reutilizar na validação

**Entregável:** inventário em [`docs/baseline-endpoints.md`](docs/baseline-endpoints.md), scripts `scripts/smoke-test-project-{1,2,3}.sh` (+ `scripts/lib.sh`) e respostas originais em `scripts/baseline/project-{1,2,3}/`.
**Resultado:** P1 25/25 · P2 7/7 · P3 26/26 checks passando no código original.
**Pronto quando:** cada endpoint tem pelo menos uma chamada documentada com resposta esperada. ✅

---

## Task 2 — Análise manual: `code-smells-project` (Python/Flask, E-commerce)

**Arquivos:** `app.py` (88), `controllers.py` (292), `models.py` (314), `database.py` (86).

- [x] Ler os 4 arquivos por completo
- [x] Procurar especificamente:
  - Credenciais / `SECRET_KEY` hardcoded, `debug=True` em produção
  - SQL montado com concatenação/f-string (SQL Injection)
  - God Class/God File (`models.py` com SQL + regra de negócio + formatação de vários domínios)
  - Regra de negócio dentro de controllers/rotas
  - Conexão global / estado mutável compartilhado
  - Queries dentro de loops (N+1)
  - Validação de entrada ausente
  - Senhas sem hash, dados sensíveis retornados na resposta
  - Tratamento de erro espalhado / `except` genérico
  - Magic numbers, nomes ruins, código duplicado, `print` como log
  - APIs deprecated (ex.: padrões antigos do Flask/SQLite)
- [x] Para cada achado registrar: **severidade, arquivo:linha, descrição, impacto, justificativa**

**Entregável:** seção "Projeto 1" em [`docs/manual-analysis.md`](docs/manual-analysis.md).
**Resultado:** 17 achados (CRITICAL 5 · HIGH 4 · MEDIUM 5 · LOW 3). SQL Injection (bypass de login), senhas em texto puro e pedido com quantidade negativa comprovados contra a app rodando. Nenhuma API deprecated encontrada.
**Pronto quando:** ≥5 achados com pelo menos 1 CRITICAL/HIGH, 2 MEDIUM e 2 LOW. ✅

---

## Task 3 — Análise manual: `ecommerce-api-legacy` (Node.js/Express, LMS + checkout)

**Arquivos:** `src/app.js` (14), `src/AppManager.js` (141), `src/utils.js` (25), `api.http`.

- [x] Ler os arquivos por completo e o `api.http`
- [x] Procurar especificamente:
  - `AppManager` como God Class (DB + rotas + regra de negócio + checkout)
  - Credenciais/chaves de pagamento hardcoded
  - SQL concatenado com input do usuário
  - Callback hell / falta de async/await, erros de callback ignorados
  - Fluxo de checkout sem transação (inconsistência de dados)
  - Dados de cartão / sensíveis logados ou persistidos
  - Hash de senha fraco/caseiro em `utils.js`
  - Ausência de validação, status HTTP incorretos
  - APIs deprecated do Node/Express (ex.: `new Buffer()`, `body-parser` separado, `res.send(status, body)`, métodos de crypto obsoletos)
  - Magic numbers, nomes genéricos, `var`
- [x] Registrar no mesmo formato da Task 2

**Entregável:** seção "Projeto 2" em [`docs/manual-analysis.md`](docs/manual-analysis.md).
**Resultado:** 16 achados (CRITICAL 5 · HIGH 4 · MEDIUM 4 · LOW 3). Comprovados: colisão do `badCrypto`, checkout em nome de terceiros sem senha, cartão + chave live no log, DELETE gerando órfãos e ordem não determinística no relatório. API legada/deprecated: driver `sqlite3` em estilo callback + dependência transitiva deprecated.
**Pronto quando:** ≥5 achados na mesma distribuição mínima. ✅

---

## Task 4 — Análise manual: `task-manager-api` (Python/Flask, Task Manager, parcialmente organizado)

**Arquivos:** `app.py`, `database.py`, `seed.py`, `models/*`, `routes/*` (task 299, user 211, report 223), `services/notification_service.py`, `utils/helpers.py`.

- [x] Ler todos os arquivos
- [x] Procurar especificamente:
  - Rotas "gordas": regra de negócio e queries direto nos blueprints (falta camada de controller)
  - Credenciais (SMTP, SECRET_KEY) hardcoded em `services/` ou `app.py`
  - Senha com hash fraco (ex.: MD5) ou exposta em `to_dict()`
  - N+1 nos relatórios (`report_routes.py`)
  - Validação duplicada/inconsistente entre rotas e `utils/helpers.py`
  - Código morto / helpers não usados
  - APIs deprecated do SQLAlchemy/Flask (`Query.get()`, `datetime.utcnow()`, `before_first_request`, etc.)
  - Tratamento de erro não centralizado, `except:` genérico
  - Magic numbers (status, limites, prioridades)
- [x] Registrar no mesmo formato

**Entregável:** seção "Projeto 3" em [`docs/manual-analysis.md`](docs/manual-analysis.md).
**Resultado:** 15 achados (CRITICAL 3 · HIGH 3 · MEDIUM 6 · LOW 3). Comprovados: hash MD5 exposto, criação de admin e escalada de privilégio anônimas, 500 em HTML por tipo inválido, `LegacyAPIWarning` do `Query.get()`. Diferencial do projeto parcialmente organizado: camadas `services/`, `utils/` e métodos de domínio existem mas não são usados — falta a camada de controllers.
**Pronto quando:** ≥5 achados na mesma distribuição mínima; destacar o que muda num projeto *já parcialmente em camadas*. ✅

---

## Task 5 — README: seção "Análise Manual"

- [x] Reescrever `README.md` mantendo o link para `DESAFIO.md`
- [x] Criar seção **A) Análise Manual** com uma tabela por projeto: `Severidade | Problema | Arquivo:linha | Justificativa`
- [x] Ordenar por severidade (CRITICAL → LOW)
- [x] Commit: `docs: add manual analysis section to README`

**Resultado:** README com visão geral (48 achados no total), 3 tabelas, lições para a skill e placeholders das seções B, C e D.
**Pronto quando:** 3 tabelas, cada uma cumprindo a distribuição mínima. ✅

---

## Task 6 — Estrutura da skill + `SKILL.md`

**Local:** `code-smells-project/.claude/skills/refactor-arch/` (nome e `SKILL.md` são obrigatórios).

Estrutura proposta:

```
.claude/skills/refactor-arch/
├── SKILL.md
└── references/
    ├── project-analysis.md
    ├── anti-patterns-catalog.md
    ├── audit-report-template.md
    ├── mvc-guidelines.md
    └── refactoring-playbook.md
```

- [x] Frontmatter: `name: refactor-arch` e `description` clara (quando usar: auditar e refatorar projeto para MVC) + `argument-hint` para o caminho do relatório
- [x] Corpo do SKILL.md como prompt com **3 fases sequenciais**, cada uma apontando qual referência ler:
  - **Fase 1 — Análise:** ler `project-analysis.md`; detectar linguagem, framework+versão, dependências, banco, domínio, arquitetura atual, nº de arquivos, tabelas; imprimir bloco `PHASE 1: PROJECT ANALYSIS` no formato do desafio
  - **Fase 2 — Auditoria:** ler `anti-patterns-catalog.md` + `audit-report-template.md`; varrer cada arquivo; registrar arquivo:linha exatos; ordenar por severidade; salvar o relatório em `reports/audit-project-N.md` (ou caminho informado); **PARAR e perguntar `Proceed with refactoring (Phase 3)? [y/n]`** — nenhuma alteração de arquivo antes da confirmação
  - **Fase 3 — Refatoração:** ler `mvc-guidelines.md` + `refactoring-playbook.md`; planejar estrutura alvo adaptada ao estado atual (monolito vs. parcialmente organizado); aplicar transformações; preservar contratos dos endpoints (paths, métodos, formato JSON); validar
- [x] Regras de validação explícitas na Fase 3: instalar deps, subir a app em background, chamar cada endpoint original, comparar status/forma, derrubar o processo, re-auditar contra o catálogo; se falhar, corrigir e repetir
- [x] Bloco final `PHASE 3: REFACTORING COMPLETE` com nova árvore e checklist ✓/✗
- [x] Regras gerais: agnóstico de stack (nada de nomes de arquivos dos projetos no SKILL.md), não inventar findings, não alterar comportamento público

**Decisões de design:**
- SKILL.md e referências **em português**; banners e rótulos de saída mantidos em inglês, idênticos ao exemplo do desafio. Conhecimento de domínio fica nas 5 referências, lidas na fase em que são usadas.
- A própria skill captura a baseline de endpoints (Fase 1 inventaria, Fase 3.0 grava respostas) — não depende dos scripts de `scripts/`, o que mantém a skill copiável.
- Relatório salvo só **depois** da resposta do usuário, em `$ARGUMENTS` ou `reports/audit-report.md` — nada é escrito antes da confirmação.
- Única quebra de contrato permitida: remoção de dados sensíveis, que deve ser listada no resumo.
- A skill não faz commit; o usuário revisa e commita.

**Pronto quando:** `/refactor-arch` aparece no Claude Code ao rodar `claude` dentro de `code-smells-project/`. ⏳ (frontmatter validado; confirmação visual no CLI fica para a Task 12, após as referências existirem)

---

## Task 7 — Referência: Análise de projeto (`project-analysis.md`)

- [x] Heurísticas de **linguagem**: arquivos de manifesto (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, `Gemfile`, `composer.json`…) e extensões dominantes
- [x] Heurísticas de **framework**: imports/dependências (`flask`, `django`, `fastapi`, `express`, `nestjs`, `koa`, `spring`…) e como extrair versão
- [x] Heurísticas de **banco**: drivers/ORMs (`sqlite3`, `SQLAlchemy`, `pg`, `mongoose`, `prisma`…), arquivos `.db`, `CREATE TABLE`, models
- [x] **Domínio**: inferir por nomes de tabelas, entidades e rotas
- [x] **Mapeamento de arquitetura**: classificar em monolito de arquivo único / camadas parciais / MVC; entry point; como encontrar rotas em cada framework
- [x] Comandos de boot e porta padrão por stack (usados na Fase 3)
- [x] Formato exato do resumo da Fase 1 — mantido no SKILL.md (fonte única), a referência traz as heurísticas para preenchê-lo

**Extras incluídos:** checagem de *uso real* das camadas (projeto parcialmente organizado), versão **instalada** vs declarada (dependências transitivas sem pin), bloqueios de boot (porta 5000/AirPlay, banco com estado, `timeout` ausente no macOS) e como sondar endpoints para a baseline. ✅

---

## Task 8 — Referência: Catálogo de anti-patterns (`anti-patterns-catalog.md`)

Requisito: **≥8 anti-patterns**, severidades distribuídas, **incluindo APIs deprecated**. Cada item deve ter: ID, nome, severidade, sinais de detecção concretos (por stack quando necessário), exemplo curto, impacto, recomendação, link para o padrão no playbook.

Lista sugerida (cobre os 3 projetos):

| ID | Anti-pattern | Severidade |
|----|--------------|-----------|
| AP-01 | Hardcoded credentials / secrets | CRITICAL |
| AP-02 | SQL Injection (query concatenada/interpolada) | CRITICAL |
| AP-03 | God Class / God File (DB + negócio + rotas) | CRITICAL |
| AP-04 | Senha em texto puro / hash fraco / dados sensíveis expostos | CRITICAL |
| AP-05 | Regra de negócio no controller/rota (fat controller) | HIGH |
| AP-06 | Estado global mutável / conexão global compartilhada | HIGH |
| AP-07 | Acoplamento forte sem injeção de dependência | HIGH |
| AP-08 | Operações multi-etapa sem transação | HIGH |
| AP-09 | Query N+1 | MEDIUM |
| AP-10 | Validação de entrada ausente | MEDIUM |
| AP-11 | Error handling espalhado / `except` genérico | MEDIUM |
| AP-12 | Código duplicado | MEDIUM |
| AP-13 | Uso de API deprecated (com tabela "obsoleto → moderno" para Python/Flask/SQLAlchemy e Node/Express) | MEDIUM |
| AP-14 | Callback hell / ausência de async-await | MEDIUM |
| AP-15 | Magic numbers / strings | LOW |
| AP-16 | Nomenclatura ruim | LOW |
| AP-17 | `print`/`console.log` como logging, código morto | LOW |

- [x] Sinais de detecção escritos de forma acionável (ex.: "f-string ou `+` contendo `SELECT|INSERT|UPDATE|DELETE` com variável de request")
- [x] Validar que cada achado das Tasks 2–4 é coberto por algum item do catálogo

**Resultado:** catálogo final com **22 anti-patterns** (CRITICAL 6 · HIGH 5 · MEDIUM 7 · LOW 4), cada um com sinais de detecção, grep, exemplo, impacto, recomendação e ID do playbook (PB-01…PB-18). A lista final reorganizou a sugerida acima: separou senha insegura (AP-04), exposição de dados sensíveis (AP-05) e falta de auth (AP-06); incluiu debug em produção (AP-07), CORS (AP-18) e código morto (AP-22).
- AP-13 (deprecated) traz tabelas "obsoleto → moderno" para Python/Flask/SQLAlchemy e Node/Express, considerando a versão instalada.
- Cobertura: os 48 achados manuais mapeiam para algum AP.
- Os greps foram testados nos 3 projetos (aspas em `--include` por causa do zsh; regex de segredo cobre `config["KEY"] = "..."`; padrão extra para SQL concatenado em várias linhas). ✅

---

## Task 9 — Referência: Template de relatório (`audit-report-template.md`)

- [x] Cabeçalho: Project, Stack, Files (n analyzed | ~linhas) + Date
- [x] `## Summary` com contagem `CRITICAL: x | HIGH: x | MEDIUM: x | LOW: x` + tabela-índice dos achados
- [x] `## Findings` — bloco por finding: `### F-xx [SEVERIDADE] Nome`, `File: caminho:linha(s)`, `Catalog: AP-xx`, `Description`, `Impact`, `Recommendation → PB-xx`, `Verified`
- [x] Regras: ordenação CRITICAL → LOW, linhas exatas obrigatórias, um finding por anti-pattern (ocorrências agrupadas)
- [x] Seções fixas `## Deprecated APIs` (sempre presente) e `## Architecture Notes`
- [x] Rodapé `Total: N findings` + pergunta de confirmação
- [x] Exemplo preenchido (projeto fictício, para não enviesar a skill) + checklist antes de imprimir ✅

---

## Task 10 — Referência: Guidelines MVC (`mvc-guidelines.md`)

- [x] Responsabilidades de cada camada:
  - **Models:** acesso a dados e entidades, sem HTTP
  - **Views/Routes:** mapeamento HTTP → controller, serialização de resposta, sem regra de negócio
  - **Controllers:** orquestram o fluxo/regras de negócio, recebem dependências injetadas
  - **Config:** settings via variáveis de ambiente (com defaults seguros para dev)
  - **Middlewares:** error handler centralizado, validação, CORS
  - **Composition root / entry point:** cria app, injeta dependências, registra rotas
- [x] Regras de dependência (Routes → Controllers → Models; nunca o inverso)
- [x] Estrutura alvo por stack: Python/Flask (`src/config`, `src/models`, `src/views` ou `routes`, `src/controllers`, `src/middlewares`, `app.py`) e Node/Express (equivalente em `src/`)
- [x] Como adaptar projeto já parcialmente organizado (renomear/mover em vez de reescrever; `services/` existente pode virar controllers ou ser mantido como camada de serviço chamada pelo controller)
- [x] Regra de ouro: **contratos dos endpoints não mudam**

**Decisão tomada:** exceções de contrato ampliadas de "remover dados sensíveis" para **correções de segurança/integridade** (§5 da referência): desabilitar `/admin/query` e `/admin/reset-db` por padrão, bloquear `role` vindo do body, rejeitar quantidade negativa, 404 em DELETE inexistente. Exigir login nas rotas públicas fica **fora do escopo** (quebraria clientes) e vira recomendação. SKILL.md, catálogo e `docs/baseline-endpoints.md` atualizados para refletir isso. ✅

---

## Task 11 — Referência: Playbook de refatoração (`refactoring-playbook.md`)

Requisito: **≥8 padrões** com **antes/depois em código**. Incluir exemplos em Python **e** JavaScript para reforçar a agnosticidade.

Lista final (alinhada aos IDs do catálogo da Task 8) — **18 padrões**, todos com antes/depois:

- [x] PB-01 Config via env (AP-01, AP-07, AP-18) · PB-02 Queries parametrizadas (AP-02) · PB-03 Quebrar God Class (AP-03)
- [x] PB-04 Hash de senha com KDF (AP-04) · PB-05 Serialização por lista branca + logs mascarados (AP-05) · PB-06 Endpoints perigosos e escalada de privilégio (AP-06)
- [x] PB-07 Regra de negócio → controller (AP-08) · PB-08 App factory + DI (AP-09, AP-10) · PB-09 Transação e integridade (AP-11)
- [x] PB-10 N+1 → JOIN/eager/GROUP BY (AP-12) · PB-11 APIs deprecated (AP-13) · PB-12 Error handler central (AP-14)
- [x] PB-13 Validação na borda (AP-15) · PB-14 Duplicação → fonte única (AP-16) · PB-15 Callbacks → async/await (AP-17)
- [x] PB-16 Constantes (AP-19) · PB-17 Renomear/código morto (AP-20, AP-22) · PB-18 Logger (AP-21)
- [x] Ordem recomendada de aplicação e validação após cada grupo
- [x] Snippets críticos executados: scrypt (Node) e werkzeug (Python), wrapper Promise do sqlite3 + transação com rollback, JOIN do N+1, decremento atômico de estoque ✅

---

## Task 12 — Execução no Projeto 1: `code-smells-project`

- [x] `cd code-smells-project && claude "/refactor-arch ../reports/audit-project-1.md"`
- [x] Fase 1: Python 3.11.15, Flask 3.1.1, flask-cors, domínio E-commerce, 4 arquivos (~780 linhas), tabelas `produtos, usuarios, pedidos, itens_pedido`, 19 rotas (batem com a baseline da Task 1); detectou o bloqueio da porta 5000 e usou `flask run --port 5001` sem alterar arquivos — saída em `reports/analysis-project-1.md`
- [x] Fase 2: **20 findings** (CRITICAL 7 · HIGH 4 · MEDIUM 5 · LOW 4) — cobrem os 17 da análise manual; linhas exatas; ordenados; seção Deprecated presente ("None detected", verificado com `PYTHONWARNINGS=always`); pausa registrada (`User response: y`)
- [x] Relatório salvo em `reports/audit-project-1.md`; saídas das Fases 1 e 3 em `reports/analysis-project-1.md` e `reports/refactor-project-1.md`
- [x] Confirmar `y` → Fase 3
- [x] Validar: estrutura MVC criada, app sobe, endpoints da baseline (Task 1) respondem igual
- [x] Preencher checklist de validação (Fases 1, 2 e 3)
- [ ] Commit: `refactor(code-smells-project): apply refactor-arch skill`

**Validação independente (fora da skill):**
- Smoke test: **25/25** (ajustado só para as 2 mudanças de contrato aprovadas: `/admin/query` e `/admin/reset-db` → 404). Antes do ajuste: 23/25, as 2 falhas eram exatamente essas.
- Formato das respostas vs baseline: **20/25 idênticos**; as 5 diferenças são todas mudanças aprovadas (`senha` removida em `/usuarios`, `secret_key`/`db_path`/`debug` removidos do `/health`, admin desligado).
- Ataques da análise manual repetidos: SQLi no login → 401; nome com apóstrofo → 201; quantidade negativa → 400 com estoque intacto; login sem body → 400.
- Greps do catálogo no código novo: 0 SQL concatenado, 0 `print`, 0 `debug=True`/`0.0.0.0`, 0 segredos literais, 0 `except` genérico, 0 `global`.
- Boot sem Traceback/DeprecationWarning; `Debug mode: off`; host `127.0.0.1`.

**Checklist de validação — Projeto 1:**

| Fase | Item | Status |
|---|---|---|
| 1 | Linguagem detectada corretamente | ✅ Python 3.11.15 |
| 1 | Framework detectado corretamente | ✅ Flask 3.1.1 |
| 1 | Domínio descrito corretamente | ✅ E-commerce (produtos, pedidos, usuários) |
| 1 | Nº de arquivos condiz com a realidade | ✅ 4 arquivos / ~780 linhas |
| 2 | Relatório segue o template | ✅ |
| 2 | Cada finding tem arquivo e linhas exatos | ✅ |
| 2 | Findings ordenados CRITICAL → LOW | ✅ |
| 2 | Mínimo de 5 findings | ✅ 20 |
| 2 | Detecção de APIs deprecated incluída | ✅ seção presente — nenhuma nas versões instaladas |
| 2 | Pausa e pede confirmação antes da Fase 3 | ✅ |
| 3 | Estrutura de diretórios segue MVC | ✅ `src/{config,database,models,controllers,views,middlewares,services,utils}` |
| 3 | Configuração extraída (sem hardcoded) | ✅ `src/config/settings.py` + `.env.example` |
| 3 | Models abstraem dados | ✅ `produto_model`, `usuario_model`, `pedido_model` |
| 3 | Views/Routes separadas | ✅ 6 blueprints + `serializers.py` |
| 3 | Controllers concentram o fluxo | ✅ 6 controllers |
| 3 | Error handling centralizado | ✅ `middlewares/error_handler.py` |
| 3 | Entry point claro | ✅ `app.py` → `create_app()` |
| 3 | Aplicação inicia sem erros | ✅ |
| 3 | Endpoints originais respondem corretamente | ✅ 25/25 (com as mudanças de contrato aprovadas) |

**Pronto quando:** todos os critérios de aceite atendidos neste projeto. ✅

---

## Task 13 — Execução no Projeto 2: `ecommerce-api-legacy`

- [x] Copiar a skill: `cp -R code-smells-project/.claude/skills/refactor-arch ecommerce-api-legacy/.claude/skills/` — `diff -r` idêntico (antes e depois da execução)
- [x] `cd ecommerce-api-legacy && claude "/refactor-arch ../reports/audit-project-2.md"`
- [x] Fase 1: Node v20.20.0, Express 4.22.1 (declarada ^4.18.2), sqlite3 5.1.7 em memória, domínio LMS com checkout, 3 arquivos (~180 linhas), 5 tabelas, 3 rotas — saída em `reports/analysis-project-2.md`
- [x] Fase 2: **20 findings** (CRITICAL 5 · HIGH 6 · MEDIUM 5 · LOW 4) — cobrem os 16 da análise manual **e acharam um novo**: `"card": 4111` (número) derruba o processo (DoS sem auth); seção Deprecated **preenchida** (API de callbacks do sqlite3 + 7 dependências transitivas deprecated); pausa registrada
- [x] Salvar em `reports/audit-project-2.md`; Fase 3 em `reports/refactor-project-2.md`
- [x] Fase 3 + validação com o smoke test
- [x] Checklist + logs
- [ ] Commits: `chore(ecommerce-api-legacy): add refactor-arch skill` e `refactor(ecommerce-api-legacy): apply refactor-arch skill`

**Validação independente (fora da skill):**
- Smoke test **7/7 sem nenhum ajuste no script** (os casos da baseline continuam válidos: o checkout do Leonan usa a senha correta `123`).
- Formato vs baseline: 6/7 idênticos; único diff é o texto do DELETE (mudança declarada). Erros seguem em texto puro, como na baseline. Relatório financeiro com o mesmo conteúdo, agora em ordem determinística.
- Ataques repetidos: checkout em nome de terceiro com senha errada/ausente → 401; `card` numérico → 400 e o processo segue vivo; `card: "4"` → 400; DELETE 999 → 404; após DELETE 1 o relatório não tem mais "Unknown" (cascade).
- Log com cartão mascarado (`**** **** **** 4444`) e sem chave do gateway; boot limpo com `--trace-deprecation`.
- Greps do catálogo: 0 SQL concatenado, 0 segredos literais, 0 `console.*` fora do logger, 0 `verbose()`/estado global.
- **Atenção:** a skill atualizou dependências (`sqlite3` 5.1.7 → 6.0.1, `express` → 4.22.3 via `npm audit fix`) para eliminar as transitivas deprecated. O sqlite3 6.x exige **Node ≥ 20.17** (ambiente local: 20.20.0 ✅). Rota inexistente continua 404 HTML do Express (igual à baseline) — LOW remanescente.

**Checklist de validação — Projeto 2:**

| Fase | Item | Status |
|---|---|---|
| 1 | Linguagem detectada corretamente | ✅ JavaScript / Node v20.20.0 |
| 1 | Framework detectado corretamente | ✅ Express 4.22.1 (instalada vs ^4.18.2 declarada) |
| 1 | Domínio descrito corretamente | ✅ LMS / cursos com checkout |
| 1 | Nº de arquivos condiz com a realidade | ✅ 3 arquivos / ~180 linhas |
| 2 | Relatório segue o template | ✅ |
| 2 | Cada finding tem arquivo e linhas exatos | ✅ |
| 2 | Findings ordenados CRITICAL → LOW | ✅ |
| 2 | Mínimo de 5 findings | ✅ 20 |
| 2 | Detecção de APIs deprecated incluída | ✅ F-15 + tabela com 2 linhas |
| 2 | Pausa e pede confirmação antes da Fase 3 | ✅ |
| 3 | Estrutura de diretórios segue MVC | ✅ `src/{config,database,models,controllers,routes,middlewares,services,utils}` |
| 3 | Configuração extraída (sem hardcoded) | ✅ `src/config/index.js` + `.env.example` |
| 3 | Models abstraem dados | ✅ `userModel`, `courseModel`, `enrollmentModel`, `reportModel` |
| 3 | Views/Routes separadas | ✅ `checkoutRoutes`, `adminRoutes`, `userRoutes` |
| 3 | Controllers concentram o fluxo | ✅ 3 controllers + `paymentService` |
| 3 | Error handling centralizado | ✅ `middlewares/errorHandler.js` (+ `asyncHandler`) |
| 3 | Entry point claro | ✅ `src/app.js` → `buildApp()` em `server.js` |
| 3 | Aplicação inicia sem erros | ✅ `npm start` |
| 3 | Endpoints originais respondem corretamente | ✅ 7/7 |

---

## Task 14 — Execução no Projeto 3: `task-manager-api`

- [x] Copiar a skill: `cp -R code-smells-project/.claude/skills/refactor-arch task-manager-api/.claude/skills/` — `diff -r` idêntico (commit `12a317f`)
- [x] `cd task-manager-api && claude "/refactor-arch ../reports/audit-project-3.md"`
- [x] Fase 1: Python 3.11.15, Flask 3.0.0, SQLAlchemy 2.1.6 transitiva sem pin, domínio Task Manager, 15 arquivos (~1158 linhas), 3 tabelas, 22 rotas, **"Parcialmente em camadas"** com a lista exata de camadas não usadas (`services/`, `utils/helpers.py`, `is_overdue`/`validate_*`/`is_admin`) — saída em `reports/analysis-project-3.md`
- [x] Fase 2: **19 findings** (CRITICAL 4 · HIGH 4 · MEDIUM 7 · LOW 4) — cobrem os 15 da análise manual; Deprecated **preenchida** (`Query.get()` com `LegacyAPIWarning` observado, Query API legada, `datetime.utcnow()`); pausa registrada
- [x] Salvar em `reports/audit-project-3.md`; Fase 3 em `reports/refactor-project-3.md`
- [x] Fase 3: melhora incremental — `models/` e `routes/` **mantidos e enxugados**, `controllers/`, `config/`, `middlewares/` criados, `services/` e `helpers.py` mortos removidos; `seed.py` usa a factory; **todos** os endpoints respondem
- [x] Checklist + logs
- [ ] Commit: `refactor(task-manager-api): apply refactor-arch skill`

**Validação independente (fora da skill):**
- Smoke test **26/26 sem ajuste no script**; também `GET /` e `GET /health` iguais à baseline.
- Formato vs baseline: 22/26 idênticos; os 4 diffs são todos `password` removido (mudança aprovada).
- **Valores** das 10 respostas de leitura (tasks, busca, stats, usuários, relatórios, categorias) **idênticos** à baseline, ignorando timestamps.
- Ataques repetidos: criar admin anônimo → `role: user`; promover Maria → continua `user`; `priority: "alta"` → 400 JSON (antes 500 HTML); `PUT /categories` com `null` → 400; nenhum `password` nas respostas; rota inexistente → 404 JSON.
- Boot com `PYTHONWARNINGS=always`: **nenhum `LegacyAPIWarning`** (antes: 1 por chamada de `Query.get`).
- Greps: 0 `Query.get(`, 0 `datetime.utcnow`, 0 `except:`, 0 `debug=True`; rotas sem acesso a banco; controllers sem import de Flask. `md5` só em `models/user.py:45` (verificação de hash legado + rehash); `print` só no `seed.py` (CLI). `routes/task_routes.py`: 299 → 46 linhas.
- **Remanescente (aceito pela regra §5):** rotas destrutivas públicas e token `fake-jwt-token-` previsível — registrado como recomendação.

**Problema de qualidade da skill encontrado (→ Task 15):** F-07 ("exclusão de categoria deixa tasks órfãs", HIGH) era **falso positivo** — o `backref` do SQLAlchemy já anula a FK (verificado na análise manual da Task 4). A própria skill detectou na Fase 3, via baseline, e anotou a correção no relatório; mas a Fase 2 não deveria tê-lo reportado. Sem ele, o relatório tem 18 achados válidos (HIGH 3) — critérios de aceite continuam atendidos.

**Checklist de validação — Projeto 3:**

| Fase | Item | Status |
|---|---|---|
| 1 | Linguagem detectada corretamente | ✅ Python 3.11.15 |
| 1 | Framework detectado corretamente | ✅ Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.6) |
| 1 | Domínio descrito corretamente | ✅ Task Manager (tasks, usuários, categorias, relatórios) |
| 1 | Nº de arquivos condiz com a realidade | ✅ 15 arquivos / ~1158 linhas |
| 2 | Relatório segue o template | ✅ |
| 2 | Cada finding tem arquivo e linhas exatos | ✅ |
| 2 | Findings ordenados CRITICAL → LOW | ✅ |
| 2 | Mínimo de 5 findings | ✅ 19 (18 válidos) |
| 2 | Detecção de APIs deprecated incluída | ✅ F-13 + tabela com 3 linhas |
| 2 | Pausa e pede confirmação antes da Fase 3 | ✅ |
| 3 | Estrutura de diretórios segue MVC | ✅ `config/`, `models/`, `controllers/`, `routes/` (Views), `middlewares/`, `utils/` |
| 3 | Configuração extraída (sem hardcoded) | ✅ `config/settings.py` + `.env.example` |
| 3 | Models abstraem dados | ✅ `Task`, `User`, `Category` com consultas e regras de domínio |
| 3 | Views/Routes separadas | ✅ 5 blueprints + `serializers.py` |
| 3 | Controllers concentram o fluxo | ✅ 4 controllers (sem import de Flask) |
| 3 | Error handling centralizado | ✅ `middlewares/error_handler.py` |
| 3 | Entry point claro | ✅ `app.py` → `create_app()` |
| 3 | Aplicação inicia sem erros | ✅ |
| 3 | Endpoints originais respondem corretamente | ✅ 26/26 + `/` e `/health` |

---

## Task 15 — Iteração e ajustes da skill

**Objetivo:** corrigir lacunas descobertas nas Tasks 12–14 (o desafio prevê 2–4 iterações).

- [x] Anotar, por execução, o que falhou: finding não detectado, linha errada, estrutura inadequada, app quebrada, skill não pausou
- [x] Ajustar a referência correspondente (catálogo, playbook, guidelines) — não "remendar" o código manualmente
- [x] Para re-executar: `git restore`/`git checkout` do projeto ao estado original e rodar a skill de novo — **não foi necessário**: os critérios de aceite passaram nas 3 execuções na 1ª tentativa
- [x] Manter **a mesma versão da skill** nos 3 projetos (comparar com `diff -r` entre as 3 pastas `.claude/skills/refactor-arch`)
- [x] Registrar desafios e soluções (alimenta a seção B do README)

**Lições das 3 execuções e ajustes feitos:**

| # | Observado | Onde | Ajuste |
|---|---|---|---|
| 1 | Falso positivo F-07 (P3): "categoria apagada deixa tasks órfãs" — o `backref` do SQLAlchemy já anula a FK | `anti-patterns-catalog.md` AP-11 | Bloco "Não é órfão": exige confirmação dinâmica antes de reportar órfãos com ORM |
| 2 | Regra geral para comportamento implícito de ORM/framework | `anti-patterns-catalog.md` "Como usar" | Novo passo 2: confirmar com a app rodando ou não registrar |
| 3 | Greps com lista de arquivos em variável falham no zsh (sem word splitting) | `anti-patterns-catalog.md` "Como usar" | Aviso explícito |
| 4 | `curl -H` guardado em variável sem aspas → body não parseado → 400 falso | `project-analysis.md` §7.4 | Aviso sobre aspas no header |
| 5 | P2: skill subiu `sqlite3` 5→6 (exige Node ≥ 20.17) | `SKILL.md` §3.2 | Upgrade major só para corrigir achado, checando o runtime, declarando `engines`/`python_requires` e documentando |
| 6 | P3: skill corrigiu o falso positivo no relatório salvo (bom comportamento, mas não estava previsto) | `SKILL.md` §3.3 | Formalizado: marcar `Correção (Fase 3): falso positivo` sem apagar o achado |

**O que funcionou bem e foi mantido:** pausa na Fase 2 (3/3), detecção do bloqueio da porta 5000 (P1, P3), contrato preservado com exceções de segurança listadas, reaproveitamento das camadas no P3, achado novo não previsto na análise manual (DoS por `card` numérico no P2).

**Versão da skill:** os relatórios em `reports/` foram gerados com a versão anterior a estes ajustes (commits até `12a317f`). Os ajustes são incrementais (prevenção de falso positivo e robustez de comandos) e não mudam o fluxo das fases.

**Pronto quando:** os 4 critérios de aceite passam em 3/3 projetos com a skill idêntica nas três cópias. ✅

---

## Task 16 — README: Construção da Skill, Resultados e Como Executar

- [ ] **B) Construção da Skill:** estrutura do SKILL.md e referências; anti-patterns escolhidos e por quê; estratégia de agnosticidade; desafios encontrados e soluções
- [ ] **C) Resultados:**
  - Tabela de findings por severidade dos 3 relatórios
  - Árvore antes/depois de cada projeto
  - Checklist de validação preenchido para cada projeto
  - Logs/screenshots das apps rodando após refatoração (salvar imagens em `docs/` ou similar)
  - Observações sobre o comportamento em stacks diferentes
- [ ] **D) Como Executar:** pré-requisitos (Claude Code instalado/autenticado, Python 3.x, Node.js), comandos da skill em cada projeto, como validar (boot + chamadas aos endpoints)
- [ ] Commit: `docs: complete README with skill design, results and usage`

---

## Task 17 — Revisão final e entrega

- [ ] Conferir estrutura final do repositório contra a seção "Estrutura do repositório" do desafio:
  - `.claude/skills/refactor-arch/` nos 3 projetos (com `SKILL.md` + 5 áreas de referência)
  - Código refatorado dos 3 projetos commitado
  - `reports/audit-project-{1,2,3}.md`
  - `README.md` com seções A, B, C, D
- [ ] Rodar os 3 projetos uma última vez a partir de um clone limpo
- [ ] Garantir que nenhum segredo real, `.db`, `.venv` ou `node_modules` foi commitado
- [ ] `git push` para o fork público e conferir no GitHub
- [ ] Revisar critérios de aceite:

| Critério | P1 | P2 | P3 |
|---|---|---|---|
| Fase 1 detecta stack corretamente | [ ] | [ ] | [ ] |
| Fase 2 encontra ≥5 findings | [ ] | [ ] | [ ] |
| Fase 2 inclui ≥1 CRITICAL ou HIGH | [ ] | [ ] | [ ] |
| Fase 3 — aplicação funciona após refatoração | [ ] | [ ] | [ ] |
