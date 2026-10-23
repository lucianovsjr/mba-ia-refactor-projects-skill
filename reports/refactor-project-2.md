================================
PHASE 3: REFACTORING COMPLETE
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node 20.20.0) + Express 4.22.3 (SQLite em memória / sqlite3 6.0.1 com wrapper de Promises)
Date:    2026-10-23
Audit:   [audit-project-2.md](audit-project-2.md)

## New Project Structure
```
ecommerce-api-legacy/
├── package.json                     # start: node src/app.js; express ^4.22.3, sqlite3 ^6.0.1
├── .env.example                     # PORT, DATABASE_FILE, LOG_LEVEL, ADMIN_TOKEN
└── src/
    ├── app.js                       # entry point: buildApp() + listen(config.port)
    ├── server.js                    # composition root: monta db, models, services, controllers e rotas
    ├── config/index.js              # lê process.env com defaults de dev
    ├── database/connection.js       # wrapper com Promises, transaction() serializada, schema com FKs, seed com hash
    ├── models/
    │   ├── userModel.js             # findByEmail, create, deleteById (cascade)
    │   ├── courseModel.js           # findActiveById
    │   ├── enrollmentModel.js       # createWithPayment (matrícula + pagamento + auditoria)
    │   └── reportModel.js           # um único SELECT com LEFT JOIN
    ├── controllers/
    │   ├── checkoutController.js    # valida, autentica usuário existente, cobra e grava em transação
    │   ├── reportController.js      # agrega receita/alunos por curso
    │   └── userController.js        # exclusão com 404
    ├── routes/                      # só HTTP: checkoutRoutes, adminRoutes, userRoutes
    ├── services/paymentService.js   # gateway simulado, log com cartão mascarado
    ├── middlewares/
    │   ├── errorHandler.js          # asyncHandler + handler central (texto, como na baseline)
    │   └── adminGuard.js            # opt-in via ADMIN_TOKEN
    └── utils/                       # constants, errors, crypto (scrypt), logger, validators
```

## Changes
- F-01 → checkout com email existente passa a exigir a senha correta (401); guarda admin opt-in via `ADMIN_TOKEN`
- F-02 → log só com os 4 últimos dígitos do cartão; a chave do gateway não é mais logada
- F-03 → segredos removidos (eram config morta); config via env + `.env.example`
- F-04 → `badCrypto` trocado por `crypto.scrypt` com salt + `timingSafeEqual`; sem senha padrão; seed com hash
- F-05 → `AppManager.js` e `utils.js` apagados; código separado por camada e por domínio
- F-06 → validação na borda (strings, email, `c_id` inteiro, cartão com 12–19 dígitos, `pwd` string) → 400
- F-07 → usuário + matrícula + pagamento + auditoria numa transação, só depois de o pagamento ser aprovado; FKs `ON DELETE CASCADE`; DELETE com 404
- F-08 → regras de checkout e relatório saíram das rotas para os controllers e o `paymentService`
- F-09 → `globalCache` e `totalRevenue` removidos
- F-10 → `buildApp({ config, logger, db })` com injeção por factory
- F-11 → sem `sqlite3.verbose()`; porta via `PORT`
- F-12 → erros de domínio + middleware central; JSON malformado → 400; erro inesperado → 500 "Erro interno"
- F-13 → relatório com 1 query (antes eram 1 + C + 2E)
- F-14 → async/await em tudo; contadores e `self = this` removidos; ordem determinística (`ORDER BY`)
- F-15 → sqlite3 5.1.7 → 6.0.1 (sem inflight/glob@7/rimraf@3/npmlog/gauge); wrapper com Promises; `npm audit fix` (proxy-addr 2.0.8, 0 vulnerabilidades)
- F-16 → montagem do relatório num único lugar
- F-17 → `PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`, `COURSE_ACTIVE`, `UNKNOWN_STUDENT`
- F-18 → nomes descritivos internos (campos do contrato `usr/eml/pwd/c_id/card` mantidos)
- F-19 → logger com nível (`LOG_LEVEL`)
- F-20 → configs, cache e imports mortos removidos

## Contract changes
- `POST /api/checkout` com email existente e senha ausente ou errada: 200 → 401 "Credenciais inválidas" (bloqueia compra em nome de terceiros)
- `POST /api/checkout` de usuário novo sem `pwd`: 200 (senha "123456" implícita) → 400 "Bad Request"
- `POST /api/checkout` com `card` não string ou não numérico, email inválido ou `c_id` não inteiro: antes derrubava o processo ou era aceito → 400 "Bad Request"
- `DELETE /api/users/:id` inexistente: 200 → 404 "Usuário não encontrado"; id não numérico → 400
- `DELETE /api/users/:id` com sucesso: o texto mudou para "Usuário deletado" (o original dizia que os dados ficavam sujos, o que deixou de ser verdade); matrículas e pagamentos do usuário saem em cascata, então somem do relatório em vez de aparecer como "Unknown"
- `GET /api/admin/financial-report`: ordem dos cursos agora determinística (por id); o formato não mudou

## Validation
  ✓ Application boots without errors (`npm start`; log limpo, inclusive com `--trace-deprecation`)
  ✓ All endpoints respond correctly (8/15 requisições da baseline iguais; as 7 diferenças são as mudanças de contrato acima: #08, #11–#15, e #09, que só difere por causa de #08)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (MEDIUM/LOW restantes: autenticação das rotas admin/DELETE é opt-in, não obrigatória, por regra de contrato; recomendado definir `ADMIN_TOKEN` em produção. Uma única conexão SQLite com operações serializadas durante transações limita o throughput; aceitável para SQLite em memória)

Verificações extras:
- Concorrência: 6 checkouts simultâneos intercalados com 6 relatórios → nenhum relatório com matrícula sem pagamento (corrigida uma leitura suja encontrada na primeira rodada, com fila + `AsyncLocalStorage` em `database/connection.js`)
- Rollback: falha no meio de uma transação → nenhuma matrícula gravada
- `ADMIN_TOKEN=s3cret`: relatório/DELETE sem header → 403; com header → 200

## How to run
```bash
npm install            # Node >= 20.17
npm start              # http://localhost:3000, seed automático
```
- O banco é em memória (`DATABASE_FILE=:memory:`) e reinicia a cada boot.
- Opcionais: `PORT`, `DATABASE_FILE`, `LOG_LEVEL`, `ADMIN_TOKEN` (veja `.env.example`).
- Padrão que mudou: requer Node >= 20.17 por causa do sqlite3 6.x.
================================
