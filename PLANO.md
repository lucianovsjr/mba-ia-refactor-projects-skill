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

- [ ] Heurísticas de **linguagem**: arquivos de manifesto (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, `Gemfile`, `composer.json`…) e extensões dominantes
- [ ] Heurísticas de **framework**: imports/dependências (`flask`, `django`, `fastapi`, `express`, `nestjs`, `koa`, `spring`…) e como extrair versão
- [ ] Heurísticas de **banco**: drivers/ORMs (`sqlite3`, `SQLAlchemy`, `pg`, `mongoose`, `prisma`…), arquivos `.db`, `CREATE TABLE`, models
- [ ] **Domínio**: inferir por nomes de tabelas, entidades e rotas
- [ ] **Mapeamento de arquitetura**: classificar em monolito de arquivo único / camadas parciais / MVC; entry point; como encontrar rotas em cada framework
- [ ] Comandos de boot e porta padrão por stack (usados na Fase 3)
- [ ] Formato exato do resumo da Fase 1

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

- [ ] Sinais de detecção escritos de forma acionável (ex.: "f-string ou `+` contendo `SELECT|INSERT|UPDATE|DELETE` com variável de request")
- [ ] Validar que cada achado das Tasks 2–4 é coberto por algum item do catálogo

---

## Task 9 — Referência: Template de relatório (`audit-report-template.md`)

- [ ] Cabeçalho: Project, Stack, Files (n analyzed | ~linhas)
- [ ] `## Summary` com contagem `CRITICAL: x | HIGH: x | MEDIUM: x | LOW: x`
- [ ] `## Findings` — bloco por finding: `### [SEVERIDADE] Nome`, `File: caminho:linha(s)`, `Description`, `Impact`, `Recommendation` (referenciando o ID do catálogo/playbook)
- [ ] Regras: ordenação CRITICAL → LOW, linhas exatas obrigatórias, um finding por ocorrência relevante
- [ ] Rodapé `Total: N findings` + pergunta de confirmação
- [ ] Exemplo preenchido

---

## Task 10 — Referência: Guidelines MVC (`mvc-guidelines.md`)

- [ ] Responsabilidades de cada camada:
  - **Models:** acesso a dados e entidades, sem HTTP
  - **Views/Routes:** mapeamento HTTP → controller, serialização de resposta, sem regra de negócio
  - **Controllers:** orquestram o fluxo/regras de negócio, recebem dependências injetadas
  - **Config:** settings via variáveis de ambiente (com defaults seguros para dev)
  - **Middlewares:** error handler centralizado, validação, CORS
  - **Composition root / entry point:** cria app, injeta dependências, registra rotas
- [ ] Regras de dependência (Routes → Controllers → Models; nunca o inverso)
- [ ] Estrutura alvo por stack: Python/Flask (`src/config`, `src/models`, `src/views` ou `routes`, `src/controllers`, `src/middlewares`, `app.py`) e Node/Express (equivalente em `src/`)
- [ ] Como adaptar projeto já parcialmente organizado (renomear/mover em vez de reescrever; `services/` existente pode virar controllers ou ser mantido como camada de serviço chamada pelo controller)
- [ ] Regra de ouro: **contratos dos endpoints não mudam**

---

## Task 11 — Referência: Playbook de refatoração (`refactoring-playbook.md`)

Requisito: **≥8 padrões** com **antes/depois em código**. Incluir exemplos em Python **e** JavaScript para reforçar a agnosticidade.

- [ ] PB-01 Extrair config para variáveis de ambiente (AP-01)
- [ ] PB-02 Query parametrizada (AP-02)
- [ ] PB-03 Quebrar God Class em model + controller + route por domínio (AP-03)
- [ ] PB-04 Hash de senha forte e serialização sem campos sensíveis (AP-04)
- [ ] PB-05 Mover regra de negócio da rota para controller/service (AP-05)
- [ ] PB-06 Substituir estado global por injeção de dependência / factory (AP-06, AP-07)
- [ ] PB-07 Envolver operações em transação (AP-08)
- [ ] PB-08 Eliminar N+1 com JOIN / eager loading / batch (AP-09)
- [ ] PB-09 Validação de entrada na borda (AP-10)
- [ ] PB-10 Error handler centralizado + exceções de domínio (AP-11)
- [ ] PB-11 Substituir API deprecated pelo equivalente moderno (AP-13)
- [ ] PB-12 Callbacks → async/await (AP-14)
- [ ] PB-13 Constantes nomeadas no lugar de magic numbers (AP-15)
- [ ] Ordem recomendada de aplicação (estrutura → segurança → camadas → qualidade) e passo de validação após cada grupo
- [ ] Commit da skill: `feat: add refactor-arch skill`

---

## Task 12 — Execução no Projeto 1: `code-smells-project`

- [ ] `cd code-smells-project && claude "/refactor-arch"`
- [ ] Fase 1: conferir Python, Flask 3.1.1, flask-cors, domínio E-commerce, 4 arquivos, tabelas `produtos, usuarios, pedidos, itens_pedido`
- [ ] Fase 2: conferir ≥5 findings que batem com a Task 2, ≥1 CRITICAL/HIGH, linhas exatas, ordenação, pausa para confirmação
- [ ] Salvar output da Fase 2 em `reports/audit-project-1.md` (na raiz do repositório)
- [ ] Confirmar `y` → Fase 3
- [ ] Validar: estrutura MVC criada, app sobe, endpoints da baseline (Task 1) respondem igual
- [ ] Preencher checklist de validação (Fases 1, 2 e 3) e guardar logs/screenshots da app rodando
- [ ] Commit: `refactor(code-smells-project): apply refactor-arch skill`

**Pronto quando:** todos os critérios de aceite atendidos neste projeto.

---

## Task 13 — Execução no Projeto 2: `ecommerce-api-legacy`

- [ ] Copiar a skill: `cp -R code-smells-project/.claude ecommerce-api-legacy/`
- [ ] `cd ecommerce-api-legacy && claude "/refactor-arch"`
- [ ] Fase 1: Node.js, Express 4.x, sqlite3, domínio LMS com checkout, 3 arquivos-fonte
- [ ] Fase 2: ≥5 findings, ≥1 CRITICAL/HIGH, APIs deprecated se houver, pausa
- [ ] Salvar em `reports/audit-project-2.md`
- [ ] Fase 3 + validação com o `api.http` / smoke test
- [ ] Checklist + logs
- [ ] Commit: `refactor(ecommerce-api-legacy): apply refactor-arch skill`

---

## Task 14 — Execução no Projeto 3: `task-manager-api`

- [ ] Copiar a skill: `cp -R code-smells-project/.claude task-manager-api/`
- [ ] `cd task-manager-api && claude "/refactor-arch"`
- [ ] Fase 1: Python/Flask 3.0.0, Flask-SQLAlchemy, domínio Task Manager, arquitetura "camadas parciais"
- [ ] Fase 2: problemas encontrados mesmo com camadas existentes (segurança, performance, rotas gordas)
- [ ] Salvar em `reports/audit-project-3.md`
- [ ] Fase 3: melhora incremental sem reescrever do zero; `seed.py` continua funcionando; **todos** os endpoints respondem
- [ ] Checklist + logs
- [ ] Commit: `refactor(task-manager-api): apply refactor-arch skill`

---

## Task 15 — Iteração e ajustes da skill

**Objetivo:** corrigir lacunas descobertas nas Tasks 12–14 (o desafio prevê 2–4 iterações).

- [ ] Anotar, por execução, o que falhou: finding não detectado, linha errada, estrutura inadequada, app quebrada, skill não pausou
- [ ] Ajustar a referência correspondente (catálogo, playbook, guidelines) — não "remendar" o código manualmente
- [ ] Para re-executar: `git restore`/`git checkout` do projeto ao estado original e rodar a skill de novo
- [ ] Manter **a mesma versão da skill** nos 3 projetos (comparar com `diff -r` entre as 3 pastas `.claude/skills/refactor-arch`)
- [ ] Registrar desafios e soluções (alimenta a seção B do README)

**Pronto quando:** os 4 critérios de aceite passam em 3/3 projetos com a skill idêntica nas três cópias.

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
