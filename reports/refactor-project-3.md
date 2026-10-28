================================
PHASE 3: REFACTORING COMPLETE
================================
Project: task-manager-api
Stack:   Python 3.11.15 + Flask 3.0.0 (SQLite / Flask-SQLAlchemy 3.1.1 + SQLAlchemy 2.1.6, API `select` 2.0)
Date:    2026-10-23
Audit:   [audit-project-3.md](audit-project-3.md)

## New Project Structure
```
task-manager-api/
├── app.py                      # composition root: create_app() (config, logging, CORS, db, error handler, blueprints, create_all) + __main__
├── database.py                 # db = SQLAlchemy() + transaction() (commit/rollback por caso de uso)
├── seed.py                     # popula o banco via create_app()
├── requirements.txt            # sem marshmallow/requests; SQLAlchemy fixado em >=2.0,<2.2
├── .env.example                # SECRET_KEY, FLASK_DEBUG, HOST, PORT, DATABASE_URL, CORS_ORIGINS, LOG_LEVEL
├── config/settings.py          # Settings lendo env/.env, com defaults seguros de dev
├── models/                     # Task, User, Category: ORM, consultas (select 2.0, sem N+1) e regras de domínio
│   ├── task.py                 #   is_overdue/overdue_clause, is_valid_status/priority, completion_rate, count_by, stats_by_user
│   ├── user.py                 #   to_dict sem password, hash werkzeug (scrypt) + verificação do MD5 legado
│   └── category.py
├── controllers/                # casos de uso (sem Flask)
│   ├── task_controller.py
│   ├── user_controller.py      #   bloqueio de role/active do body, rehash no login
│   ├── category_controller.py  #   exclusão desvincula as tasks na mesma transação
│   └── report_controller.py
├── routes/                     # Views: só HTTP
│   ├── task_routes.py, user_routes.py, category_routes.py, report_routes.py, system_routes.py
│   └── serializers.py          #   formatos compostos (overdue, user_name, task_count...)
├── middlewares/error_handler.py  # AppError/HTTPException/Exception → {"error": ...}
└── utils/
    ├── constants.py            # status, prioridades, limites, roles, janela de 7 dias
    ├── errors.py               # ValidationError, NotFoundError, ConflictError, Unauthorized/Forbidden
    ├── validators.py           # validação na borda (create/update/search/login)
    └── dates.py                # utcnow() sem datetime.utcnow
Removidos: services/ (código morto), utils/helpers.py
```

## Changes
- **F-01:** `User.to_dict()` passou a serializar por lista branca, sem `password`.
- **F-02:** `role` e `active` vindos do body de `POST /users` e `PUT /users` agora são ignorados, e todo cadastro nasce com `role: "user"`. O código morto `is_admin()` foi removido.
- **F-03:** o hash da senha passou a ser `werkzeug` (scrypt com salt). Hashes MD5 legados são verificados com `hmac.compare_digest` e regravados no primeiro login válido.
- **F-04 / F-06 / F-14:** criei `config/settings.py` e o `.env.example`. A `SECRET_KEY` vem do ambiente (ou é aleatória), o debug fica desligado por padrão, host/porta vêm da env e o CORS é restrito a `CORS_ORIGINS`. As credenciais SMTP saíram junto com o serviço morto.
- **F-05:** criei `controllers/` por domínio. As rotas ficaram com 2 a 4 linhas, e as categorias ganharam o próprio blueprint. Os métodos de domínio que existiam e não eram usados agora são a fonte única.
- **F-07:** era um falso positivo, já corrigido no relatório de auditoria. A desvinculação das tasks agora é explícita e transacional.
- **F-08:** `create_app()` virou o composition root, `create_all()` não roda mais no import e o seed usa a factory.
- **F-09:** os validadores ficam na borda, reaproveitando as mensagens originais. Agora há checagem de tipo de `priority`, título, tags, ids e query params, além de validação de cor, nome e email.
- **F-10:** os `except:` puros foram removidos. Há um handler central em JSON, com log de erros inesperados, e `transaction()` faz rollback.
- **F-11:** usei `joinedload` e `GROUP BY` nas consultas. Queries por requisição: `/tasks` 21 → 1, `/users` 4 → 1, `/categories` 5 → 1, `/reports/summary` ~17 → 10 (agora fixo, sem crescer com o volume), `/tasks/stats` 6 → 3.
- **F-12 / F-17:** o cálculo de "atrasado", as listas de status/roles e a taxa de conclusão ficaram num lugar só, e os literais viraram constantes em `utils/constants.py`.
- **F-13:** `Query.get` foi trocado por `session.get`, a Query API por `db.select`, e `datetime.utcnow` por `utils.dates.utcnow`. Nenhum warning com `PYTHONWARNINGS=always`.
- **F-15 / F-16:** apaguei `services/` e `utils/helpers.py`, os imports não usados e as dependências `marshmallow`/`requests`. O pyflakes está limpo.
- **F-18:** os `print` viraram `logging`, com o nível vindo de `LOG_LEVEL` (o `print` só ficou no seed, que é CLI).
- **F-19:** nomes internos descritivos (`p1..p5` → `PRIORITY_LABELS`, `d`/`u`/`t` → nomes reais).

## Contract changes
- `password` (hash) foi removido das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
- `role` e `active` enviados no body de `POST /users` e `PUT /users/<id>` agora são ignorados. Antes era possível virar `admin` e reativar contas.
- Entradas inválidas que davam 500/415 em HTML agora dão 400 em JSON:
  - `priority` não inteira em `POST/PUT /tasks`;
  - `?priority=abc` e `?user_id=abc` em `/tasks/search`;
  - `PUT /categories/<id>` sem JSON.
- Há validações novas que respondem 400:
  - cor fora de `#RRGGBB`, nome vazio em `PUT /users` e `PUT /categories`;
  - email sem domínio com ponto (`a@b`), tags que não sejam string/lista de strings, título ou ids de tipo errado.
- 404 de rota inexistente, 405 e 500 inesperado agora saem em JSON `{"error": ...}`, e não mais em HTML.

## Validation
  ✓ Application boots without errors (`python app.py` e `flask --app app run`, com `PYTHONWARNINGS=always`: nenhum warning nem traceback no log)
  ✓ All endpoints respond correctly (43/52 requisições da baseline batem em status, tipo e formato, e os valores das respostas de leitura são idênticos. As 9 diferenças são as mudanças de contrato listadas acima)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining, com uma ressalva que é limite da regra §5 das guidelines, e não uma correção que deixei de fazer:
     - o AP-06 residual continua: as rotas destrutivas (`DELETE /users`, `/tasks`, `/categories`) seguem públicas e o token do login segue previsível (`fake-jwt-token-<id>`). Nenhuma rota usa esse token, mas exigir autenticação ou trocar o mecanismo de login quebraria todos os clientes, então fica como recomendação;
       > **Nota (2026-10-28):** a parte do token foi corrigida na reexecução da Fase 3 ([refactor-project-3-rerun-2.md](refactor-project-3-rerun-2.md)). O `fake-jwt-token-<id>` virou um token assinado com a `SECRET_KEY`, sem mudança de contrato. Só a exigência de autenticação nas rotas continua como recomendação (§5 Fora do escopo).
     - LOW: a senha mínima continua com 4 caracteres, para manter o contrato e as senhas do seed. A recomendação é subir esse limite.

Verificações extras:
- `seed.py` roda num banco de teste e cria 3 usuários, 4 categorias e 10 tasks.
- Uma senha com hash MD5 legado faz login, é regravada em `scrypt:` e o login seguinte também funciona. Senha errada → 401.
- Um usuário novo (hash scrypt) faz login → 200.
- O banco `instance/tasks.db` foi restaurado ao estado original depois de cada rodada.

## How to run
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env              # opcional; em produção defina SECRET_KEY
.venv/bin/python seed.py
PORT=5001 .venv/bin/python app.py # ou: .venv/bin/flask --app app run --port 5001
```
Nenhuma variável de ambiente é obrigatória em dev. No macOS, a porta 5000 está ocupada pelo AirPlay.
================================
