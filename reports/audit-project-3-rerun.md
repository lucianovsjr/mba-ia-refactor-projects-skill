================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.11.15 + Flask 3.0.0 (SQLite / Flask-SQLAlchemy 3.1.1 + SQLAlchemy 2.1.6)
Files:   16 analyzed | ~1160 lines of code
Date:    2026-10-23

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 7 | LOW: 4

| ID | Severity | Finding | Catalog | Location |
|----|----------|---------|---------|----------|
| F-01 | CRITICAL | Sensitive Data Exposure (password hash) | AP-05 | models/user.py:21 |
| F-02 | CRITICAL | Privilege Escalation / Missing AuthZ | AP-06 | routes/user_routes.py:52, 71-78 |
| F-03 | CRITICAL | Insecure Password Storage (MD5) | AP-04 | models/user.py:29, 32 |
| F-04 | CRITICAL | Hardcoded Credentials | AP-01 | app.py:13 |
| F-05 | HIGH | Debug Mode / Fixed Dev Config | AP-07 | app.py:34 |
| F-06 | HIGH | Fat Controller + Abandoned Layers | AP-08 | routes/task_routes.py:11-63 |
| F-07 | HIGH | Tight Coupling / No App Factory | AP-10 | app.py:9, 30-31 |
| F-08 | MEDIUM | Missing/Inconsistent Input Validation | AP-15 | routes/task_routes.py:113 |
| F-09 | MEDIUM | Generic Error Handling / No Central Handler | AP-14 | routes/task_routes.py:62 |
| F-10 | MEDIUM | N+1 Queries | AP-12 | routes/task_routes.py:41-57 |
| F-11 | MEDIUM | Duplicated Code | AP-16 | routes/task_routes.py:30-39 |
| F-12 | MEDIUM | Permissive CORS | AP-18 | app.py:15 |
| F-13 | MEDIUM | Deprecated API | AP-13 | routes/task_routes.py:42 |
| F-14 | MEDIUM | Mutable Global State (dead code) | AP-09 | services/notification_service.py:6, 31 |
| F-15 | LOW | print as Logging | AP-21 | routes/task_routes.py:149 |
| F-16 | LOW | Dead Code and Unused Imports | AP-22 | utils/helpers.py:1-116 |
| F-17 | LOW | Magic Numbers and Strings | AP-19 | routes/task_routes.py:96, 99 |
| F-18 | LOW | Poor Naming | AP-20 | routes/report_routes.py:24-28 |

## Findings

### F-01 [CRITICAL] Sensitive Data Exposure (password hash)
File: models/user.py:16-25, routes/user_routes.py:33, 85, 129, 209
Catalog: AP-05
Description: `User.to_dict()` inclui `'password': self.password` (linha 21). É usado direto nas respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
Impact: Qualquer cliente, sem autenticação, obtém o hash MD5 de qualquer usuário, que se reverte trivialmente (ver F-03).
Recommendation: Serialização por lista branca, sem `password` → PB-05
Verified: yes (`GET /users/1` e `POST /login` retornaram `"password":"81dc9bdb52d04dc20036dbd8313ed055"`, o MD5 de `1234`)

### F-02 [CRITICAL] Privilege Escalation / Missing AuthZ
File: routes/user_routes.py:52, 71-78, 119-125, 134-151, 210, routes/task_routes.py:225-238, routes/report_routes.py:211-222, models/user.py:34-38
Catalog: AP-06
Description: `POST /users` aceita `role` do body (`data.get('role', 'user')`) e `PUT /users/<id>` aceita `role` e `active`, então qualquer pessoa vira `admin`. O "token" do login é previsível (`'fake-jwt-token-' + str(user.id)`), `User.is_admin()` nunca é chamado e todas as rotas destrutivas (`DELETE /users`, `/tasks`, `/categories`) são abertas.
Impact: Auto-promoção a administrador, falsificação de token e exclusão de dados por qualquer cliente.
Recommendation: Ignorar campos de privilégio vindos do body em rotas públicas e registrar a autenticação real (JWT assinado + checagem de `is_admin`) como recomendação → PB-06
Verified: yes (`POST /users {"role":"admin",...}` → 201 com `"role":"admin"`; o estado foi restaurado)

### F-03 [CRITICAL] Insecure Password Storage (MD5)
File: models/user.py:3, 29, 32, routes/user_routes.py:64, 115, seed.py:19, 26, 33
Catalog: AP-04
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()`, sem salt, e `check_password` compara com `==`, sem tempo constante. A senha mínima é de 4 caracteres, e o seed usa `1234`, `abcd` e `pass`.
Impact: Um vazamento (já possível via F-01) expõe as senhas em segundos com rainbow tables.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`, com migração transparente dos hashes MD5 legados no login → PB-04
Verified: yes (os hashes no banco são o MD5 puro das senhas do seed)

### F-04 [CRITICAL] Hardcoded Credentials
File: app.py:13, services/notification_service.py:7-10
Catalog: AP-01
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` e as credenciais SMTP literais (`self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`). Nenhum valor vem de `os.environ`.
Impact: Os segredos ficam versionados no git, sem rotação nem configuração por ambiente.
Recommendation: Módulo `config.py` lendo variáveis de ambiente, mais `.env.example` → PB-01
Verified: no

### F-05 [HIGH] Debug Mode / Fixed Dev Config
File: app.py:34, 11
Catalog: AP-07
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` e `SQLALCHEMY_DATABASE_URI` fixa em `'sqlite:///tasks.db'`.
Impact: Com `python app.py`, o debugger do Werkzeug fica exposto na rede (execução remota de código). Porta e banco não são configuráveis, e a porta 5000 colide com o AirPlay no macOS.
Recommendation: `DEBUG`, `HOST`, `PORT` e `DATABASE_URL` vindos da config/env, com debug desligado por padrão → PB-01
Verified: no

### F-06 [HIGH] Fat Controller + Abandoned Layers
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299, routes/user_routes.py:42-90, 92-132, 153-183, routes/report_routes.py:12-101, 103-155, 157-222, models/task.py:38-60, utils/helpers.py:57-108, services/notification_service.py:4-48
Catalog: AP-08
Description: Os handlers fazem parsing, validação de domínio, verificação de FKs, cálculo de "atrasado", estatísticas e serialização no próprio corpo da rota, como `create_task` (70 linhas) e `summary_report` (90 linhas). O CRUD de categorias mora em `report_routes.py`. As camadas abandonadas são `Task.validate_status/validate_priority/is_overdue`, `helpers.process_task_data` e `NotificationService`: nunca são chamados enquanto a mesma lógica está copiada nas rotas.
Impact: Não há um lugar único para cada regra, testar exige HTTP e banco, e as regras divergem (a validação de criar é diferente da de atualizar).
Recommendation: Rotas finas (HTTP) → controllers por domínio (tasks, users, categories, reports) → models com os métodos de domínio. Remover ou ligar as camadas mortas → PB-07
Verified: no

### F-07 [HIGH] Tight Coupling / No App Factory
File: app.py:9, 30-31, seed.py:2, routes/task_routes.py:2, routes/user_routes.py:2, routes/report_routes.py:2
Catalog: AP-10
Description: `app = Flask(__name__)` no nível do módulo, com config fixa, e `db.create_all()` executado no import. O `seed.py` importa a app global (`from app import app, db`) e as rotas usam `db.session` diretamente.
Impact: Importar o módulo já cria o schema, não dá para trocar o banco ou a config em testes, e não há composition root.
Recommendation: `create_app(config)` como composition root e seed usando a factory → PB-08
Verified: no

### F-08 [MEDIUM] Missing/Inconsistent Input Validation
File: routes/task_routes.py:113, 166-171, 182, 261, 264, routes/report_routes.py:180, 196-202, routes/user_routes.py:102-103, 124-125
Catalog: AP-15
Description: `priority < 1` sem checar o tipo (uma string vira `TypeError`). `int(priority)` e `int(user_id)` na busca, sem tratamento. `PUT /categories` usa `'name' in data` sem checar `None`. `color` não é validado, embora `is_valid_color` exista. `PUT /users` aceita `name` vazio e `active` de qualquer tipo. A validação de título no PUT não faz strip nem checa o tipo, diferente do POST.
Impact: Entradas inválidas viram 500 em HTML ou dados corrompidos no banco.
Recommendation: Validadores por recurso na borda, usados por create e update, retornando 400 JSON → PB-13
Verified: yes (`POST /tasks {"priority":"x"}` → 500; `GET /tasks/search?priority=abc` → 500; `PUT /categories/1` com body `null` → 500; `POST /categories {"color":"notacolor-very-long"}` → 201)

### F-09 [MEDIUM] Generic Error Handling / No Central Handler
File: routes/task_routes.py:62, 137, 151-154, 204, 221-223, 236, routes/user_routes.py:87-90, 130, 149, routes/report_routes.py:186, 207, 221, utils/helpers.py:46, 49, 88, app.py:9-34
Catalog: AP-14
Description: `except:` puro e `except Exception` repetidos em cada handler. Não há `@app.errorhandler`, então 404, 405, 415 e 500 saem em HTML enquanto os erros de domínio saem em JSON `{"error": ...}`.
Impact: O formato de erro é inconsistente para os clientes e as falhas inesperadas são engolidas sem log.
Recommendation: Exceções de domínio + handler central JSON com log → PB-12
Verified: yes (`GET /nope` → 404 HTML; os 500 de F-08 vieram em HTML)

### F-10 [MEDIUM] N+1 Queries
File: routes/task_routes.py:41-57, 275-281, routes/user_routes.py:22, routes/report_routes.py:15-28, 53-56, 163
Catalog: AP-12
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` por task. `GET /users` faz `len(u.tasks)` lazy por usuário. `summary_report` faz uma query de tasks por usuário e 12 `COUNT` separados. `GET /categories` faz um `count()` por categoria.
Impact: São 1 + 2N queries em `/tasks`, e a latência cresce linearmente com o volume.
Recommendation: `selectinload`/`joinedload` e `GROUP BY` com agregação → PB-10
Verified: no

### F-11 [MEDIUM] Duplicated Code
File: routes/task_routes.py:17-39, 71-80, 110, 177, 284-287, 296, routes/user_routes.py:15-21, 61, 71, 106, 120, 162-180, routes/report_routes.py:19-22, 34-36, 67, 132-135, 151, models/task.py:39, 50-60, utils/helpers.py:21, 75, 110
Catalog: AP-16
Description: O cálculo de "overdue" aparece copiado 6 vezes, além de `Task.is_overdue()`, que não é usado. A serialização de task é refeita à mão (`task_routes.py:17-28`) em vez de usar `to_dict()`. A lista de status aparece 4 vezes, a regex de email 3 vezes, a lista de roles 2 vezes, e a taxa de conclusão e as contagens por status se repetem.
Impact: As correções precisam ser feitas em N lugares, e as cópias já divergem (o PUT valida o título de outra forma).
Recommendation: Métodos de domínio no model (`is_overdue`, serializers) e constantes num único módulo → PB-14
Verified: no

### F-12 [MEDIUM] Permissive CORS
File: app.py:15
Catalog: AP-18
Description: `CORS(app)` sem `origins` libera `*` para todas as rotas, inclusive as destrutivas e de escalada (F-02).
Impact: Qualquer site pode chamar a API a partir do navegador da vítima.
Recommendation: `CORS_ORIGINS` vindo da config/env → PB-01
Verified: no

### F-13 [MEDIUM] Deprecated API
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213
Catalog: AP-13
Description: `Model.query.get(id)` é legado no SQLAlchemy 2.x (instalado: 2.1.6). O restante de `Model.query.*` também é a Query API legada. `datetime.utcnow()` **não** está deprecated no Python 3.11.15 instalado (passa a estar no 3.12), então não foi contado.
Impact: Gera warnings em runtime e vai quebrar em upgrades futuros do SQLAlchemy.
Recommendation: `db.session.get(Model, id)` / `db.session.execute(db.select(...))` → PB-11
Verified: yes (`PYTHONWARNINGS=always` → `LegacyAPIWarning: The Query.get() method is considered legacy ...` no log)

### F-14 [MEDIUM] Mutable Global State (dead code)
File: services/notification_service.py:6, 31
Catalog: AP-09
Description: `self.notifications = []` acumula notificações em memória (`append`) sem limite. A severidade desceu de HIGH para MEDIUM porque o serviço nunca é instanciado (código morto).
Impact: Se o serviço for ligado como singleton, vaza memória e perde as notificações a cada restart ou entre instâncias.
Recommendation: Remover o serviço morto ou injetá-lo sem estado → PB-08
Verified: no

### F-15 [LOW] print as Logging
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, utils/helpers.py:39, 41, services/notification_service.py:21, 24
Catalog: AP-21
Description: `print(f"Task criada: ...")`, `print(f"ERRO: {str(e)}")` e similares no código da aplicação.
Impact: Não há níveis nem formato, e não dá para configurar os logs por ambiente.
Recommendation: `logging` / `app.logger` com nível vindo da config → PB-18
Verified: no

### F-16 [LOW] Dead Code and Unused Imports
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:1-116, services/notification_service.py:1-48
Catalog: AP-22
Description: Imports não usados: `os, sys, json` (app), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes) e `json` (task model). Em `utils/helpers.py`, nenhuma função é chamada e há 5 imports não usados. `NotificationService` nunca é importado.
Impact: Dá uma falsa impressão de regras centralizadas e aumenta o custo de leitura.
Recommendation: Remover o que não é usado e mover o que é útil para o lugar certo → PB-17
Verified: no

### F-17 [LOW] Magic Numbers and Strings
File: routes/task_routes.py:96, 99, 113, 167, 169, 182, routes/user_routes.py:64, 115, routes/report_routes.py:45, 129, 180, utils/helpers.py:110-116
Catalog: AP-19
Description: Limites de título `3`/`200`, prioridade `1`–`5`, senha `4`, janela de `7` dias, "alta prioridade" `<= 2` e a cor `'#000000'` aparecem como literais, enquanto as constantes de `helpers.py:110-116` não são usadas.
Impact: As regras ficam escondidas e sujeitas a divergir.
Recommendation: Constantes nomeadas num módulo de domínio → PB-16
Verified: no

### F-18 [LOW] Poor Naming
File: routes/report_routes.py:24-28, routes/task_routes.py:16, routes/user_routes.py:14, utils/helpers.py:25, 83
Catalog: AP-20
Description: Variáveis `p1`..`p5`, `t`, `u`, `c`, `cat`, `p` e `s` sem contexto.
Impact: Prejudica a leitura.
Recommendation: Nomes descritivos nos identificadores internos, sem mudar o contrato → PB-17
Verified: no

## Deprecated APIs
| Location | Deprecated API | Modern replacement | Evidence |
|----------|----------------|--------------------|----------|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` | `LegacyAPIWarning` observado; SQLAlchemy 2.1.6 instalado |
| routes/*.py (`Model.query.filter_by/all/count`) | Query API legada | `db.select(...)` + `db.session.execute/scalar` | SQLAlchemy 2.x (legado, sem warning) |

## Architecture Notes
- Current: Parcialmente em camadas. As rotas concentram HTTP, regras e queries, e o CRUD de categorias está em `report_routes.py`.
- Layers present but unused: `services/notification_service.py`, `utils/helpers.py`, `Task.validate_status/validate_priority/is_overdue`, `User.is_admin`
- Target: MVC. Haverá app factory + config via env, controllers por domínio, routes finas, models com regras de domínio e serialização segura, e error handler central.

Notas da verificação: o `DELETE /categories/<id>` **não** deixa órfãos (o SQLAlchemy fez `SET NULL` em `tasks.category_id`, confirmado), então não foi reportado como AP-11. Depois dos testes, `instance/tasks.db` foi restaurado a partir do backup e a app foi derrubada.

================================
Total: 18 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? **n** (usuário recusou; Fase 3 não executada)
