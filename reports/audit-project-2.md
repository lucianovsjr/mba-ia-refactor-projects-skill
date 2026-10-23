================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node 20.20.0) + Express 4.22.1 (SQLite em memória / driver sqlite3 5.1.7 com callbacks)
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-23

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 5 | LOW: 4

| ID | Severity | Finding | Catalog | Location |
|----|----------|---------|---------|----------|
| F-01 | CRITICAL | Operações sensíveis sem autenticação/autorização | AP-06 | src/AppManager.js:80 |
| F-02 | CRITICAL | Exposição de dados sensíveis em logs | AP-05 | src/AppManager.js:45 |
| F-03 | CRITICAL | Credenciais e segredos hardcoded | AP-01 | src/utils.js:2-5 |
| F-04 | CRITICAL | Armazenamento inseguro de senhas | AP-04 | src/utils.js:17-23 |
| F-05 | CRITICAL | God Class / God File | AP-03 | src/AppManager.js:4-139 |
| F-06 | HIGH | Validação de entrada ausente (derruba o processo) | AP-15 | src/AppManager.js:29-35, 46 |
| F-07 | HIGH | Operação multi-etapa sem transação / sem integridade referencial | AP-11 | src/AppManager.js:50-63 |
| F-08 | HIGH | Regra de negócio na rota (fat controller) | AP-08 | src/AppManager.js:28-78 |
| F-09 | HIGH | Estado global mutável | AP-09 | src/utils.js:9-15 |
| F-10 | HIGH | Acoplamento forte sem injeção de dependência | AP-10 | src/AppManager.js:7 |
| F-11 | HIGH | Configuração de desenvolvimento em produção | AP-07 | src/AppManager.js:1 |
| F-12 | MEDIUM | Tratamento de erro ausente / sem handler central | AP-14 | src/AppManager.js:92-93 |
| F-13 | MEDIUM | Queries N+1 | AP-12 | src/AppManager.js:83-106 |
| F-14 | MEDIUM | Callback hell | AP-17 | src/AppManager.js:37-77 |
| F-15 | MEDIUM | Uso de API deprecated / legada | AP-13 | src/AppManager.js:1, 7 |
| F-16 | MEDIUM | Código duplicado | AP-16 | src/AppManager.js:95-99, 117-122 |
| F-17 | LOW | Magic numbers e strings | AP-19 | src/AppManager.js:46 |
| F-18 | LOW | Nomenclatura ruim | AP-20 | src/AppManager.js:29-33 |
| F-19 | LOW | console.log como mecanismo de log | AP-21 | src/AppManager.js:45 |
| F-20 | LOW | Código morto e imports não usados | AP-22 | src/utils.js:10, 25 |

## Findings

### F-01 [CRITICAL] Operações sensíveis sem autenticação/autorização
File: src/AppManager.js:80, 131-137, 40, 74
Catalog: AP-06
Description: `GET /api/admin/financial-report` (receita e nomes de alunos) e `DELETE /api/users/:id` não têm nenhum middleware de autenticação. No checkout, quando o email já existe (linha 40), o fluxo matricula e cobra em nome desse usuário (linha 74) sem verificar a senha `pwd`.
Impact: Qualquer pessoa lê dados financeiros, apaga usuários e faz compras em nome de terceiros apenas conhecendo o email.
Recommendation: Remover a delegação implícita por email (exigir a senha correta do usuário existente), registrar a proteção das rotas admin/destrutivas como recomendação de auth sem quebrar o contrato público → PB-06
Verified: yes (`POST /api/checkout` com `eml=leonan@fullcycle.com.br` e sem `pwd` retornou 200 e criou a matrícula 2 para Leonan; `DELETE /api/users/1` sem credencial retornou 200; o relatório abriu sem autenticação)

### F-02 [CRITICAL] Exposição de dados sensíveis em logs
File: src/AppManager.js:45
Catalog: AP-05
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave live do gateway a cada checkout.
Impact: PAN de cartão em log viola o PCI-DSS, e a chave do gateway vaza para qualquer agregador de logs.
Recommendation: Logar só os 4 últimos dígitos e nunca a chave; usar logger com nível → PB-05
Verified: yes (log do servidor mostrou `Processando cartão 4000000000000000 na chave pk_live_1234567890abcdef`)

### F-03 [CRITICAL] Credenciais e segredos hardcoded
File: src/utils.js:2-5
Catalog: AP-01
Description: O objeto `config` traz `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser` e `smtpUser` literais, sem nenhum `process.env`.
Impact: Os segredos ficam versionados no git, sem rotação e sem configuração por ambiente.
Recommendation: Módulo de config lendo `process.env` com defaults seguros de desenvolvimento e `.env.example` → PB-01
Verified: yes (a chave `pk_live_...` aparece no log em runtime, ver F-02)

### F-04 [CRITICAL] Armazenamento inseguro de senhas
File: src/utils.js:17-23, src/AppManager.js:18, 68
Catalog: AP-04
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e corta em 10, ou seja, o "hash" depende só dos primeiros ~12 bits da senha, sem salt. O checkout usa a senha padrão `p || "123456"` (linha 68) e o seed grava `'123'` em texto puro (linha 18).
Impact: Colisões triviais (qualquer senha que comece com `s` + letra de 0x60-0x6F gera o mesmo hash) e senhas reversíveis num vazamento.
Recommendation: `crypto.scrypt` com salt aleatório e verificação com `crypto.timingSafeEqual`; sem senha padrão; seed com hash → PB-04
Verified: yes (`badCrypto('senhaforte') === badCrypto('sa')` → `true`, ambos `c2c2c2c2c2`)

### F-05 [CRITICAL] God Class / God File
File: src/AppManager.js:4-139, src/utils.js:1-25
Catalog: AP-03
Description: `AppManager` abre a conexão (7), cria o schema e o seed (10-23), registra as rotas e implementa nos handlers o SQL e as regras de checkout, relatório e exclusão de 4 domínios (25-138). `utils.js` mistura config, cache global, log e hash de senha.
Impact: Nada pode ser testado isoladamente e qualquer mudança afeta tudo.
Recommendation: Separar em config, database, models por domínio, controllers, routes e composition root → PB-03
Verified: no

### F-06 [HIGH] Validação de entrada ausente (derruba o processo)
File: src/AppManager.js:29-35, 46
Catalog: AP-15
Description: A validação só checa truthiness de `usr/eml/c_id/card`; o tipo de `card` não é verificado e `cc.startsWith("4")` (46) lança `TypeError` dentro de um callback do sqlite3 quando `card` é número. Também não há validação de formato de email nem de `c_id`. Severidade elevada de MEDIUM para HIGH: explorável sem autenticação e derruba o servidor inteiro.
Impact: Uma única requisição sem autenticação encerra o processo (DoS) e dados inválidos chegam ao banco.
Recommendation: Validar o body na borda (tipos, formato de email, cartão numérico em string, `c_id` inteiro) e responder 400 → PB-13
Verified: yes (`POST /api/checkout` com `"card":4111` → conexão encerrada; log: `TypeError: cc.startsWith is not a function` e `Node.js v20.20.0`, processo morreu)

### F-07 [HIGH] Operação multi-etapa sem transação / sem integridade referencial
File: src/AppManager.js:50-63, 66-72, 131-137, 12-16
Catalog: AP-11
Description: Matrícula, pagamento e audit log (50-63) são três INSERTs sem `BEGIN/COMMIT/ROLLBACK`; o usuário novo é criado (69) antes de o pagamento ser decidido, então fica gravado mesmo com pagamento recusado. O `DELETE` de usuário (133) não trata matrículas/pagamentos, ignora `err` e sempre responde sucesso; o schema não tem `FOREIGN KEY`.
Impact: Pagamento sem matrícula (ou vice-versa) em caso de falha, usuários fantasmas e registros órfãos que corrompem o relatório financeiro.
Recommendation: Transação única por caso de uso com rollback, decidir o pagamento antes de escrever, FKs e exclusão em cascata dentro de transação → PB-09
Verified: yes (após `DELETE /api/users/1`, o relatório passou a listar `"student":"Unknown"` com os pagamentos órfãos de 997 e 497)

### F-08 [HIGH] Regra de negócio na rota (fat controller)
File: src/AppManager.js:28-78, 80-129, 131-137
Catalog: AP-08
Description: O handler de checkout (50 linhas) faz parsing, validação, busca de curso/usuário, criação de usuário, aprovação de pagamento (`cc.startsWith("4")`, 46), matrícula, auditoria e cache. O handler do relatório agrega receita no próprio callback.
Impact: As regras não podem ser testadas sem HTTP e banco e não há um lugar único para cada uma.
Recommendation: Rotas só com HTTP, controllers com a orquestração e models só com SQL → PB-07
Verified: no

### F-09 [HIGH] Estado global mutável
File: src/utils.js:9-15, 10, 25, src/AppManager.js:59
Catalog: AP-09
Description: `let globalCache = {}` recebe uma entrada por checkout (`last_checkout_<id>`) sem limite e sem leitura; `let totalRevenue = 0` é exportado como primitivo (cópia congelada).
Impact: Vazamento de memória proporcional ao número de usuários e estado divergente entre instâncias.
Recommendation: Remover o cache/contador sem uso (ou dar escopo e limite) → PB-08
Verified: no

### F-10 [HIGH] Acoplamento forte sem injeção de dependência
File: src/AppManager.js:7, 10, src/app.js:8-10
Catalog: AP-10
Description: O construtor instancia `new sqlite3.Database(':memory:')` e o `app.js` monta tudo via `AppManager` sem composition root; não há como injetar outro banco.
Impact: Impossível testar com outro banco/fake e o boot fica acoplado ao seed.
Recommendation: `buildApp({ db, config })` como composition root, com models recebendo o `db` por parâmetro → PB-08
Verified: no

### F-11 [HIGH] Configuração de desenvolvimento em produção
File: src/AppManager.js:1, src/utils.js:6, src/app.js:12
Catalog: AP-07
Description: `require('sqlite3').verbose()` ativa stack traces longos sempre; porta `3000` fixa no código, sem `process.env.PORT`.
Impact: Overhead e traces detalhados em produção; não é possível configurar por ambiente.
Recommendation: Porta/env vindos da config; `verbose()` só em desenvolvimento → PB-01
Verified: no

### F-12 [MEDIUM] Tratamento de erro ausente / sem handler central
File: src/AppManager.js:38, 57, 92-93, 104, 106, 133-135
Catalog: AP-14
Description: `err` é ignorado em vários callbacks; `enrollments.length` (93) é acessado sem checar `err` (crash se a query falhar); erro de banco na busca do curso vira 404 (38); o DELETE ignora o erro. Não há middleware `(err, req, res, next)` e as respostas de erro são texto puro.
Impact: Exceções derrubam o processo, status incorretos e clientes sem formato de erro previsível.
Recommendation: Erros de domínio + middleware central de erro e 404 → PB-12
Verified: yes (exceção não tratada no callback derrubou o processo, ver F-06)

### F-13 [MEDIUM] Queries N+1
File: src/AppManager.js:83-106
Catalog: AP-12
Description: Para cada curso roda uma query de matrículas (92) e, para cada matrícula, uma de usuário (104) e uma de pagamento (106).
Impact: 1 + C + 2E queries por chamada; a latência cresce com o volume.
Recommendation: Um único `SELECT` com `LEFT JOIN` e agrupamento em memória → PB-10
Verified: no

### F-14 [MEDIUM] Callback hell
File: src/AppManager.js:26, 37-77, 83-128
Catalog: AP-17
Description: Cinco níveis de callbacks no checkout, `const self = this` para alternar com `this.lastID`, e contadores manuais `coursesPending--/enrPending--` no relatório.
Impact: Difícil de ler, erros mal propagados e ordem de resposta não determinística.
Recommendation: Wrapper com Promises + `async/await` e `try/catch` encaminhando para o handler central → PB-15
Verified: yes (o mesmo relatório retornou `Docker` primeiro em uma chamada e `Clean Architecture` primeiro em outra)

### F-15 [MEDIUM] Uso de API deprecated / legada
File: src/AppManager.js:1, 7, 37, 40, 50, 54, 57, 83, 92, 104, 106, 133, package.json:11
Catalog: AP-13
Description: Uso exclusivo da API de callbacks do `sqlite3@5.1.7`, que puxa dependências transitivas deprecated instaladas (`inflight@1.0.6`, `glob@7.2.3`, `rimraf@3.0.2`, `npmlog@6.0.2`, `gauge@4.0.4`, `are-we-there-yet@3.0.1`, `@npmcli/move-file@1.1.2`).
Impact: Avisos de deprecated no install, `inflight` com vazamento de memória conhecido e quebra em upgrades.
Recommendation: Encapsular o driver com Promises (`util.promisify`) no módulo de banco; avaliar `node:sqlite` (Node ≥ 22.5) ou `better-sqlite3` → PB-11
Verified: no

### F-16 [MEDIUM] Código duplicado
File: src/AppManager.js:95-99, 117-122
Catalog: AP-16
Description: O bloco "push no report, `coursesPending--`, se zero `res.json(report)`" está copiado em dois ramos.
Impact: Correções precisam ser feitas em dois lugares e as cópias tendem a divergir.
Recommendation: Eliminar com a reescrita em JOIN/async (um único ponto de montagem do relatório) → PB-14
Verified: no

### F-17 [LOW] Magic numbers e strings
File: src/AppManager.js:37, 46, 48, 54, 108, src/utils.js:19, 22
Catalog: AP-19
Description: Prefixo `"4"` aprova cartão (46), status `"PAID"/"DENIED"` repetidos (46, 48, 108), `active = 1` (37), `10000`/`10` no hash (19, 22).
Impact: Regras escondidas e espalhadas.
Recommendation: Constantes nomeadas (`APPROVED_CARD_PREFIX`, `PaymentStatus`) → PB-16
Verified: no

### F-18 [LOW] Nomenclatura ruim
File: src/AppManager.js:4, 29-33, src/utils.js:12, 17
Catalog: AP-20
Description: Variáveis `u, e, p, cid, cc`, `let` em valores que não mudam, nomes como `AppManager`, `badCrypto`, `logAndCache`.
Impact: Prejudica a leitura e esconde a intenção.
Recommendation: Nomes descritivos internamente, mantendo os campos do contrato (`usr`, `eml`, `pwd`, `c_id`, `card`) → PB-17
Verified: no

### F-19 [LOW] console.log como mecanismo de log
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Catalog: AP-21
Description: Logs via `console.log` com prefixo manual `[LOG]`, sem níveis.
Impact: Não dá para filtrar/desligar por ambiente e aumenta o risco de vazar dados (F-02).
Recommendation: Logger mínimo com nível vindo da config → PB-18
Verified: no

### F-20 [LOW] Código morto e imports não usados
File: src/utils.js:2-3, 5, 9-10, 25, src/AppManager.js:2, 16, 57
Catalog: AP-22
Description: `totalRevenue` importado e nunca usado (AppManager.js:2); `globalCache` só é escrito; `config.dbUser/dbPass/smtpUser` nunca lidos; `audit_logs` é gravado mas nunca consultado (não é morto, é trilha de auditoria, mantido).
Impact: Falsa impressão de funcionalidades (cache, receita total, SMTP) que não existem.
Recommendation: Remover o que não é usado → PB-17
Verified: no

## Deprecated APIs
| Location | Deprecated API | Modern replacement | Evidence |
|----------|----------------|--------------------|----------|
| src/AppManager.js:1, 7, 37-133 | API de callbacks do `sqlite3` (`db.get/run/all(sql, cb)`) | Wrapper com Promises (`util.promisify`) + `async/await`; `node:sqlite` ou `better-sqlite3` | sqlite3 5.1.7 instalado |
| package.json:11 (transitivas do sqlite3) | `inflight`, `glob@7`, `rimraf@3`, `npmlog`, `gauge`, `are-we-there-yet`, `@npmcli/move-file` | Removidas com a troca/atualização do driver | Versões instaladas em node_modules: 1.0.6, 7.2.3, 3.0.2, 6.0.2, 4.0.4, 3.0.1, 1.1.2 |

## Architecture Notes
- Current: Monolítica — `AppManager.js` concentra conexão, schema, seed, rotas, SQL e regras de 4 domínios; `utils.js` mistura config, cache e hash
- Layers present but unused: none (o único "módulo de apoio", `utils.js`, tem exports mortos: `totalRevenue`, `globalCache`)
- Target: MVC — config via env, database com Promises, models por domínio, controllers com as regras, routes só com HTTP, middleware central de erro e composition root `buildApp`

================================
Total: 20 findings
================================
User response: y (prosseguir para a Fase 3)
