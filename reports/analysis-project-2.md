================================
PHASE 1: PROJECT ANALYSIS
================================
Project: ecommerce-api-legacy
Date:    2026-10-23
Note:    Análise do código **original** (antes da refatoração da Fase 3). Linhas e arquivos citados referem-se a essa versão.

```
Language:      JavaScript (Node.js v20.20.0)
Framework:     Express 4.22.1 (declarada ^4.18.2)
Dependencies:  express 4.22.1, sqlite3 5.1.7 (declarada ^5.1.6)
Database:      SQLite em memória (':memory:') via driver puro sqlite3 com callbacks, SQL escrito à mão
Domain:        LMS / plataforma de cursos com checkout: users, courses, enrollments, payments, audit_logs
Architecture:  Monolítica — `AppManager.js` cria a conexão, o schema, o seed, registra as rotas e contém SQL + regras; `utils.js` mistura config, cache global e "crypto"
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs
Entry point:   src/app.js (npm start → node src/app.js, porta 3000)
Endpoints:     3 rotas
```

## Inventário de arquivos-fonte
| Arquivo | Linhas | Responsabilidades |
|---|---|---|
| `src/app.js` | 14 | Criação da app Express, `express.json()`, instancia `AppManager`, chama `initDb()` e `setupRoutes()`, `app.listen` na porta da config |
| `src/AppManager.js` | 141 | Conexão SQLite em memória, DDL e seed, registro das 3 rotas, SQL, regra de checkout (aprovação de pagamento, criação de usuário, matrícula, auditoria), agregação do relatório financeiro, exclusão de usuário |
| `src/utils.js` | 25 | Config com segredos literais, cache global (`globalCache`), contador `totalRevenue`, log com `console.log`, hash de senha caseiro (`badCrypto`) |

Excluídos: `node_modules/`, `.git/`, `.claude/`, `package-lock.json`. `package.json` (manifesto), `README.md` e `api.http` (coleção HTTP de exemplo) foram lidos, mas não contam como código-fonte.

## Banco de dados
- Conexão criada no construtor de `AppManager` (`src/AppManager.js:7`) com `new sqlite3.Database(':memory:')` e `require('sqlite3').verbose()` (`src/AppManager.js:1`).
- Schema (`CREATE TABLE`, sem `IF NOT EXISTS`) e seed rodam no boot via `initDb()` (`src/AppManager.js:10-23`), chamado por `src/app.js:9`.
- Seed: 1 usuário (`leonan@fullcycle.com.br`, senha `'123'` em texto puro), 2 cursos (Clean Architecture 997.00, Docker 497.00), 1 matrícula e 1 pagamento `PAID`.
- Sem chaves estrangeiras declaradas; `user_id`, `course_id` e `enrollment_id` são FKs só lógicas.
- Por ser em memória, o estado é reiniciado a cada boot.

## Arquitetura atual
- **Entry point:** `src/app.js`; rotas registradas com `app.post/get/delete` dentro de `AppManager.setupRoutes` (`src/AppManager.js:25-138`).
- **Regra de negócio:** inteiramente nos handlers de `AppManager.js` (aprovação por `card.startsWith("4")`, criação implícita de usuário, cálculo de receita).
- **Acesso a dados:** SQL direto nos handlers, em callbacks aninhados.
- **Uso das camadas:** `app.js` → `AppManager` → `utils`; não há models, controllers nem routes separados. Em `utils.js`, `totalRevenue` é importado e nunca usado, e `globalCache` só é escrito.
- **Config:** literais em `src/utils.js:1-7` (inclusive porta 3000); nenhuma leitura de variável de ambiente.

## Inventário de endpoints (contrato)
```
POST    /api/checkout                 -> handler inline   src/AppManager.js:28
GET     /api/admin/financial-report   -> handler inline   src/AppManager.js:80
DELETE  /api/users/:id                -> handler inline   src/AppManager.js:131
```

## Como subir
```bash
npm install
npm start                # node src/app.js, porta 3000 fixa
```
- Porta 3000 livre; nenhum bloqueio encontrado.
- Seed automático no boot; nenhuma variável de ambiente obrigatória.
- A porta é fixa em `src/utils.js:6` (`PORT` do ambiente não é lida).
================================
