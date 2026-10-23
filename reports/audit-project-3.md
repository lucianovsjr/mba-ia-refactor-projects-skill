================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.11.15 + Flask 3.0.0 (SQLite / Flask-SQLAlchemy 3.1.1 + SQLAlchemy 2.1.6)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-10-23

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 7 | LOW: 4

| ID | Severity | Finding | Catalog | Location |
|----|----------|---------|---------|----------|
| F-01 | CRITICAL | Exposição de hash de senha nas respostas | AP-05 | models/user.py:21 |
| F-02 | CRITICAL | Escalada de privilégio / token falso | AP-06 | routes/user_routes.py:52, 71-78 |
| F-03 | CRITICAL | Senhas com MD5 sem salt | AP-04 | models/user.py:27-32 |
| F-04 | CRITICAL | Segredos hardcoded | AP-01 | app.py:13 |
| F-05 | HIGH | Fat controller e camadas abandonadas | AP-08 | routes/task_routes.py:11-63 |
| F-06 | HIGH | Debug ligado e exposto na rede | AP-07 | app.py:34 |
| F-07 | HIGH | Exclusão de categoria deixa tasks órfãs | AP-11 | routes/report_routes.py:211-223 |
| F-08 | HIGH | App global sem factory, efeitos no import | AP-10 | app.py:9-31 |
| F-09 | MEDIUM | Validação de entrada ausente/inconsistente | AP-15 | routes/task_routes.py:113, 182 |
| F-10 | MEDIUM | `except:` genérico e sem handler central | AP-14 | routes/task_routes.py:62 |
| F-11 | MEDIUM | Queries N+1 | AP-12 | routes/task_routes.py:41-57 |
| F-12 | MEDIUM | Código duplicado | AP-16 | routes/task_routes.py:30-39 |
| F-13 | MEDIUM | APIs deprecated | AP-13 | routes/task_routes.py:42 |
| F-14 | MEDIUM | CORS permissivo | AP-18 | app.py:15 |
| F-15 | MEDIUM | Estado global mutável (em código morto) | AP-09 | services/notification_service.py:6 |
| F-16 | LOW | Código morto e imports/dependências não usados | AP-22 | services/notification_service.py:1-48 |
| F-17 | LOW | Magic numbers e strings | AP-19 | routes/task_routes.py:96-113 |
| F-18 | LOW | `print` como log | AP-21 | routes/task_routes.py:149 |
| F-19 | LOW | Nomenclatura ruim | AP-20 | routes/report_routes.py:24-28 |

## Findings

### F-01 [CRITICAL] Exposição de dados sensíveis (hash de senha nas respostas)
File: models/user.py:16-25, routes/user_routes.py:33, 85-86, 129, 209
Catalog: AP-05
Description: `User.to_dict()` inclui `'password': self.password`, e esse dicionário é devolvido em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. Todas essas rotas são públicas.
Impact: Qualquer cliente obtém o hash MD5 de qualquer usuário, que é revertido em segundos (veja F-03).
Recommendation: Serializar por lista branca, sem `password` → PB-05
Verified: yes (`GET /users/1` e `POST /login` retornaram `"password":"81dc9bdb52d04dc20036dbd8313ed055"`, o MD5 de "1234")

### F-02 [CRITICAL] Operações sensíveis sem autorização: escalada de privilégio e token falso
File: routes/user_routes.py:52, 71-78, 119-125, 134-151, 210, models/user.py:34-38
Catalog: AP-06
Description: `POST /users` aceita `role` do body (inclusive `admin`) sem autenticação. `PUT /users/<id>` aceita `role` e `active`. `DELETE /users/<id>` apaga o usuário e as tasks dele sem nenhuma verificação. O login devolve `'fake-jwt-token-' + str(user.id)`, que é previsível. `User.is_admin()` existe, mas nunca é chamado.
Impact: Qualquer pessoa vira administrador, reativa contas desativadas ou apaga usuários. O "token" pode ser forjado para qualquer id.
Recommendation: Ignorar campos de privilégio (`role`/`active`) vindos de rotas públicas, ou seja, bloquear a escalada. Trocar o token previsível por um token assinado com `SECRET_KEY`. Registrar como recomendação a exigência de autenticação nas rotas destrutivas → PB-06
Verified: yes (`POST /users {"role":"admin",...}` → 201 com `"role":"admin"`)

### F-03 [CRITICAL] Armazenamento inseguro de senhas
File: models/user.py:3, 27-32, routes/user_routes.py:64-65, 115-116
Catalog: AP-04
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()`, sem salt. `check_password` compara com `==`, que não é tempo constante. O tamanho mínimo da senha é 4.
Impact: Um vazamento do banco (ou F-01) expõe as senhas por rainbow table. Senhas iguais geram hashes iguais.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`, com verificação dos hashes MD5 legados no login para não quebrar o seed → PB-04
Verified: yes (o hash retornado para a senha "1234" é o MD5 público `81dc9bdb...`)

### F-04 [CRITICAL] Credenciais e segredos hardcoded
File: app.py:11, 13, services/notification_service.py:7-10
Catalog: AP-01
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` e a URI do banco estão fixas no código. `NotificationService` tem `email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'` literais.
Impact: Os segredos estão versionados no git e não há configuração por ambiente. A chave fixa permite forjar qualquer token assinado com ela.
Recommendation: Módulo `config.py` lendo do ambiente (python-dotenv já é dependência), mais um `.env.example` → PB-01
Verified: no

### F-05 [HIGH] Regra de negócio nas rotas e camadas abandonadas
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299, routes/user_routes.py:42-90, 92-132, routes/report_routes.py:12-101, 103-155, 157-223, models/task.py:38-60, models/user.py:34-38, utils/helpers.py:57-108
Catalog: AP-08
Description: Os handlers fazem parsing, validação de domínio, consultas ORM, cálculo de atraso e estatísticas e montagem da resposta, com até ~90 linhas cada. `Task.validate_status`, `validate_priority` e `is_overdue`, `User.is_admin` e `utils.helpers.process_task_data` existem, mas nunca são chamados, e a mesma lógica aparece copiada nas rotas. O CRUD de categorias está em `report_routes.py`, no módulo de outro domínio.
Impact: Não há um lugar único para cada regra, os testes exigem HTTP e banco, e as regras já divergem: `process_task_data` faz strip e aceita `dd/mm/YYYY`, as rotas não.
Recommendation: Criar `controllers/` por domínio (task, user, category, report), passar a usar os métodos de domínio dos models e deixar as rotas só com HTTP → PB-07
Verified: no

### F-06 [HIGH] Modo debug em produção
File: app.py:34
Catalog: AP-07
Description: `app.run(debug=True, host='0.0.0.0', port=5000)`: debug, host e porta fixos no código.
Impact: Com `python app.py`, o debugger do Werkzeug fica exposto na rede, o que permite execução remota de código.
Recommendation: Ler debug/host/porta da config/env, com debug desligado por padrão → PB-01
Verified: no

### F-07 [HIGH] Exclusão sem integridade referencial
File: routes/report_routes.py:211-223, models/task.py:13-14, 20-21
Catalog: AP-11
Description: `DELETE /categories/<id>` apaga a categoria sem tratar as tasks que a referenciam. As FKs não têm `ondelete` e o SQLite não as aplica sem `PRAGMA foreign_keys`, então as tasks ficam com `category_id` apontando para uma categoria inexistente.
Impact: Registros órfãos. `GET /categories` e os relatórios ficam inconsistentes.
Recommendation: Na mesma transação, desvincular as tasks (`category_id = NULL`) antes de apagar a categoria → PB-09
Verified: no — **Correção (Fase 3): falso positivo.** A baseline mostrou que, após `DELETE /categories/4`, `GET /tasks/4` devolve `category_id: null`: o `backref` do SQLAlchemy já anula a FK dos filhos ao apagar o pai, sem deixar órfãos. Na refatoração, a desvinculação ficou explícita no controller (`Task.unassign_category`), na mesma transação, sem mudança de contrato.

### F-08 [HIGH] Acoplamento forte sem app factory
File: app.py:9-31, seed.py:2, routes/task_routes.py:2, routes/user_routes.py:2, routes/report_routes.py:2
Catalog: AP-10
Description: `app = Flask(__name__)` é criado no nível do módulo, com config fixa, e `db.create_all()` roda no import (app.py:30-31). `seed.py` importa a app global. As rotas importam `db` direto e acessam a sessão.
Impact: Importar `app` já cria o schema. Não é possível subir a app com outra config, como um banco de teste.
Recommendation: `create_app(config)` como composition root. O seed passa a usar a factory → PB-08
Verified: no

### F-09 [MEDIUM] Validação de entrada ausente ou inconsistente
File: routes/task_routes.py:96-100, 113, 166-169, 182, 261, 264, routes/report_routes.py:173-180, 196-202, routes/user_routes.py:61, 102-103, 124-125
Catalog: AP-15
Description: `priority` é comparada sem checar o tipo (`"5" < 1` → TypeError). `int()` é aplicado direto nos query params da busca. O título não tem checagem de tipo. `PUT /categories` usa `request.get_json()` sem checar e sem validar a cor (`is_valid_color` existe e não é usado). `PUT /users` aceita nome vazio e `active` não booleano. A regex de email aceita `a@b`.
Impact: Entradas ruins viram 500 em HTML, e dados inválidos chegam ao banco.
Recommendation: Validadores por recurso na borda, os mesmos para criar e atualizar, respondendo 400 em JSON → PB-13
Verified: yes (`POST /tasks {"priority":"5"}` → 500 HTML; `GET /tasks/search?priority=abc` → 500; `PUT /categories/1` sem JSON → 415 HTML)

### F-10 [MEDIUM] Tratamento de erro genérico e sem handler central
File: routes/task_routes.py:62-63, 137, 151-154, 204, 221-223, 236, routes/user_routes.py:87-90, 130, 149, routes/report_routes.py:186, 207, 221, utils/helpers.py:46, 49, 88, app.py:9-31
Catalog: AP-14
Description: Há `except:` puro em 12 pontos e nenhum `@app.errorhandler`. Erros não tratados e 404/405/415 do Flask saem em HTML, enquanto os erros da app saem como `{'error': ...}`.
Impact: O cliente recebe formatos inconsistentes, e exceções reais (inclusive `KeyboardInterrupt`) são engolidas sem log.
Recommendation: Exceções de domínio mais um handler central em JSON, com log do erro inesperado → PB-12
Verified: yes (os 500 de F-09 vieram como página HTML "Internal Server Error")

### F-11 [MEDIUM] Queries N+1
File: routes/task_routes.py:41-57, 275-281, routes/user_routes.py:22, routes/report_routes.py:15-30, 53-56, 159-163
Catalog: AP-12
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task. `GET /users` acessa `u.tasks`, que é lazy, por usuário. O summary faz 13 `count()` separados mais uma query de tasks por usuário. `GET /categories` faz um `count()` por categoria.
Impact: 1 + 2N queries em `/tasks`, e a latência cresce com o volume.
Recommendation: Eager loading (`selectinload`/`joinedload`) e `GROUP BY` com agregação → PB-10
Verified: yes (o log mostrou 10 `LegacyAPIWarning` em task_routes.py:42 e 10 em :51 numa única chamada a `GET /tasks` com 10 tasks)

### F-12 [MEDIUM] Código duplicado
File: routes/task_routes.py:17-39, 71-80, 110, 177, 284-287, 296, routes/user_routes.py:61, 106, 162-180, routes/report_routes.py:34-36, 67, 132-135, 151, models/task.py:50-60
Catalog: AP-16
Description: O cálculo de "atrasado" aparece copiado 6 vezes, embora já exista `Task.is_overdue()`. A serialização da task é refeita à mão em vez de usar `to_dict()`. A lista de status, a regex de email e o cálculo de completion rate se repetem.
Impact: Cada correção precisa ser feita em N lugares, e as cópias tendem a divergir.
Recommendation: Usar `Task.is_overdue()`, serializers únicos e constantes compartilhadas → PB-14
Verified: no

### F-13 [MEDIUM] Uso de API deprecated
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213, models/task.py:15-16, 52, models/user.py:14, models/category.py:11
Catalog: AP-13
Description: `Model.query.get(id)` emite `LegacyAPIWarning` no SQLAlchemy 2.1.6 instalado. Todo o acesso usa a Query API legada (`Model.query.filter_by`). `datetime.utcnow()` aparece em 26 pontos e é deprecated a partir do Python 3.12.
Impact: Warnings em runtime e quebra em upgrades. `utcnow()` devolve datetime *naive*.
Recommendation: `db.session.get(Model, id)` e `db.select(...)`; `datetime.now(timezone.utc)` → PB-11
Verified: yes (`PYTHONWARNINGS=always`: `LegacyAPIWarning: The Query.get() method is considered legacy`)

### F-14 [MEDIUM] CORS permissivo
File: app.py:15
Catalog: AP-18
Description: `CORS(app)` sem `origins` responde `Access-Control-Allow-Origin: *` em todas as rotas, inclusive nas destrutivas.
Impact: Qualquer site pode chamar a API pelo navegador do usuário, o que agrava F-02.
Recommendation: Origens lidas de `CORS_ORIGINS` na config → PB-01
Verified: no

### F-15 [MEDIUM] Estado global mutável
File: services/notification_service.py:6, 31-36
Catalog: AP-09
Description: `self.notifications` é uma lista em memória, sem limite, que acumula notificações. A severidade cai de HIGH para MEDIUM porque a classe nunca é instanciada (código morto).
Impact: Se o serviço for ligado, haverá vazamento de memória e estado perdido entre processos.
Recommendation: Remover, junto com o serviço morto (F-16) → PB-08
Verified: no

### F-16 [LOW] Código morto e imports/dependências não usados
File: services/notification_service.py:1-48, utils/helpers.py:2-7, 9-116, app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, requirements.txt:4-6
Catalog: AP-22
Description: `NotificationService` nunca é importado. Das funções e constantes de `utils/helpers.py`, só `format_date` e `calculate_percentage` são importadas (report_routes.py:7), e nem elas são chamadas. Há imports não usados: `os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `json` (report_routes, models/task). `marshmallow`, `requests` e `python-dotenv` não são usados.
Impact: Dá a falsa impressão de que as regras estão centralizadas e mantém dependências desnecessárias.
Recommendation: Remover o que é morto e passar a usar as constantes e helpers úteis → PB-17
Verified: no

### F-17 [LOW] Magic numbers e strings
File: routes/task_routes.py:96-99, 104, 110, 113, 177, 182, routes/user_routes.py:52, 64, 71, 115, 120, routes/report_routes.py:24-28, 45, 129, utils/helpers.py:110-116
Catalog: AP-19
Description: Os limites 3/200 do título, a faixa de prioridade 1-5, o tamanho mínimo de senha 4, a janela de 7 dias, o `priority <= 2` para "alta prioridade" e as listas de status/roles aparecem como literais. Constantes equivalentes estão definidas em `utils/helpers.py:110-116`, mas não são usadas.
Impact: As regras ficam escondidas e divergem facilmente.
Recommendation: Constantes de domínio num único módulo → PB-16
Verified: no

### F-18 [LOW] `print` como mecanismo de log
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, utils/helpers.py:39, 41, services/notification_service.py:21, 24
Catalog: AP-21
Description: Eventos e erros são registrados com `print(...)`, por exemplo `print(f"ERRO: {str(e)}")`.
Impact: Não há níveis nem como configurar a saída, e o detalhe dos erros se perde.
Recommendation: `logging` / `app.logger` com nível vindo da config → PB-18
Verified: no

### F-19 [LOW] Nomenclatura ruim
File: routes/report_routes.py:24-28, models/category.py:14, routes/task_routes.py:16, 51, routes/user_routes.py:14, routes/report_routes.py:161
Catalog: AP-20
Description: Há variáveis `p1`..`p5` para contagens por prioridade, `d` para o dicionário serializado e `t`, `u`, `c` e `cat` como variáveis de laço em blocos longos.
Impact: Prejudica a leitura e esconde a intenção do código.
Recommendation: Nomes descritivos nos identificadores internos, sem tocar nas chaves do contrato → PB-17
Verified: no

## Deprecated APIs
| Location | Deprecated API | Modern replacement | Evidence |
|----------|----------------|--------------------|----------|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` | `LegacyAPIWarning` observado no log (SQLAlchemy 2.1.6 instalada) |
| routes/*.py (todas as consultas), seed.py:11-13 | Query API legada (`Model.query.filter_by/all/count`) | `db.session.execute(db.select(...)).scalars()` / `db.session.scalar(select(func.count()))` | Legada no SQLAlchemy 2.x |
| models/task.py:15-16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; seed.py:66-74; utils/helpers.py:38; services/notification_service.py:35 | `datetime.utcnow()` | `datetime.now(timezone.utc)` | Deprecated no Python 3.12 (o runtime atual é 3.11.15, ainda sem warning) |

## Architecture Notes
- Current: Parcialmente em camadas — `models/` e `routes/` separados, mas as rotas concentram validação, regra e queries; as categorias ficam em `report_routes.py`
- Layers present but unused: `services/notification_service.py`, `utils/helpers.py` (validações e constantes), métodos de domínio `Task.validate_status/validate_priority/is_overdue`, `User.is_admin`
- Target: MVC — `config.py` + `create_app()`, models com regras de domínio e serialização segura, `controllers/` por domínio, routes (blueprints) só com HTTP e error handler central em JSON

================================
Total: 19 findings
================================
User response: Siga (prosseguir para a Fase 3)
