================================
PHASE 3: REFACTORING COMPLETE
================================
Project: task-manager-api
Stack:   Python 3.11.15 + Flask 3.0.0 (SQLite / Flask-SQLAlchemy 3.1.1 + SQLAlchemy 2.1.6)
Date:    2026-10-28
Mode:    `/refactor-arch --fase3 ../reports/audit-project-3.md` (entrada direta na Fase 3, sobre o código já refatorado)
Audit:   [audit-project-3.md](audit-project-3.md) (não alterado)
Previous run: [refactor-project-3.md](refactor-project-3.md)
Log:     [docs/logs/project-3-rerun-phase3.log](../docs/logs/project-3-rerun-phase3.log)

## Planning (§3.1)
O mapeamento tem uma linha por ação da `Recommendation`. Nesta execução, só a F-02 (b) estava pendente. As outras ações já estavam aplicadas e aparecem com o `arquivo:linha` que as comprova.

| Ação | Padrão | Estado antes desta execução |
|---|---|---|
| F-01 serializar sem `password` | PB-05 | já aplicada (models/user.py:27-36) |
| F-02 (a) ignorar `role`/`active` vindos do body | PB-06 | já aplicada (utils/validators.py:156, 160-174; controllers/user_controller.py:34) |
| **F-02 (b) token previsível → token assinado com `SECRET_KEY`** | PB-06 | **pendente** (utils/constants.py:24 `LOGIN_TOKEN_PREFIX = "fake-jwt-token-"`; controllers/user_controller.py:79) |
| F-02 (c) exigir autenticação nas rotas | — | remanescente (mvc-guidelines §5, Fora do escopo) |
| F-03 werkzeug + verificação do MD5 legado | PB-04 | já aplicada (models/user.py:40-51; controllers/user_controller.py:75-78) |
| F-04 config por env + `.env.example` | PB-01 | já aplicada (config/settings.py:19-32; .env.example) |
| F-05 controllers por domínio, métodos de domínio usados | PB-07 | já aplicada (controllers/*; utils/validators.py:56, 62; routes/serializers.py:7) |
| F-06 debug/host/porta pela config | PB-01 | já aplicada (app.py:39; config/settings.py:25-27) |
| F-07 desvincular tasks na mesma transação | PB-09 | já aplicada (controllers/category_controller.py:42-45); falso positivo já registrado |
| F-08 `create_app` + seed via factory | PB-08 | já aplicada (app.py:18; seed.py:13) |
| F-09 validadores na borda | PB-13 | já aplicada (utils/validators.py) |
| F-10 handler central em JSON | PB-12 | já aplicada (middlewares/error_handler.py:16-30) |
| F-11 eager loading / `GROUP BY` | PB-10 | já aplicada (models/task.py:81, 111-122; models/category.py:34-42; models/user.py:68-76) |
| F-12 `is_overdue`, serializers e constantes únicos | PB-14 | já aplicada (routes/serializers.py; models/task.py:60-71) |
| F-13 `db.session.get` / `db.select` / `datetime.now(timezone.utc)` | PB-11 | já aplicada (models/task.py:77; utils/dates.py:4-6) |
| F-14 `CORS_ORIGINS` | PB-01 | já aplicada (app.py:27; config/settings.py:31) |
| F-15 remover estado global do serviço morto | PB-08 | já aplicada (`services/` removido) |
| F-16 remover código morto, imports e dependências | PB-17 | já aplicada (`utils/helpers.py` removido; requirements.txt) |
| F-17 constantes de domínio | PB-16 | já aplicada (utils/constants.py) |
| F-18 logging no lugar de `print` | PB-18 | já aplicada (logger nos controllers; middlewares/error_handler.py:29) |
| F-19 nomes descritivos | PB-17 | já aplicada (controllers/report_controller.py) |

## New Project Structure
```
task-manager-api/
├── app.py                  # composition root: create_app() e execução direta
├── config/settings.py      # Settings lida do ambiente/.env (SECRET_KEY, DEBUG, HOST, PORT, DB, CORS, LOG_LEVEL)
├── database.py             # instância do SQLAlchemy e transaction()
├── seed.py                 # popula o banco via create_app()
├── .env.example            # variáveis esperadas, sem segredos (nota nova sobre a invalidação de tokens)
├── models/                 # Task, User, Category: entidades, consultas e regras de domínio
├── controllers/            # casos de uso: task, user, category, report (login(data, secret_key))
├── routes/                 # blueprints só com HTTP + serializers.py (a rota de login injeta a SECRET_KEY)
├── middlewares/error_handler.py  # respostas de erro centralizadas em JSON {"error": ...}
└── utils/
    ├── constants.py        # constantes de domínio (LOGIN_TOKEN_PREFIX removido)
    ├── dates.py, errors.py, validators.py
    └── tokens.py           # NOVO: issue_login_token(user_id, secret_key)
```

## Changes
- **F-02 (b) → aplicada nesta execução** (PB-06, "Token previsível → token assinado"):
  - `utils/tokens.py:6-8`: `issue_login_token(user_id, secret_key)` usa `itsdangerous.URLSafeTimedSerializer` com salt `"login-token"` e payload `{"uid": <id>}`, sem email, papel ou hash. O serializer grava o instante de emissão, então quem verificar o token pode aplicar `max_age`.
  - `controllers/user_controller.py:69, 80`: `login(data, secret_key)` devolve o token assinado.
  - `routes/user_routes.py:47`: a rota injeta `current_app.config['SECRET_KEY']`, então o controller continua sem importar o Flask.
  - `utils/constants.py`: o `LOGIN_TOKEN_PREFIX = "fake-jwt-token-"` foi removido.
  - `.env.example` e `README.md`: avisam que, sem `SECRET_KEY`, a chave aleatória de desenvolvimento invalida os tokens a cada restart.
  - Nenhuma dependência nova: o `itsdangerous` 2.2.0 já vem com o Flask, e o `requirements.txt` não mudou.
  - O projeto não ganhou função de verificação, porque nenhuma rota a chamaria (AP-22). A verificação foi feita só na validação.
- F-02 (c) → remanescente (§5 Fora do escopo: exigir autenticação nas rotas hoje públicas).
- F-01, F-02 (a), F-03 a F-19 → já aplicadas na execução anterior (veja o `arquivo:linha` de cada uma na tabela de Planning).

## Contract changes
nenhuma. O `POST /login` mantém 200/401/403 e as chaves `message`, `user` e `token`, e `token` continua sendo string; só o **valor** mudou (`fake-jwt-token-1` → `eyJ1aWQiOjF9.auI1NQ.tDIM…`). As mudanças de contrato da execução anterior continuam valendo, como descritas em [refactor-project-3.md](refactor-project-3.md#contract-changes).

## Validation
  ✓ Application boots without errors (`PORT=5002 SECRET_KEY=… .venv/bin/python -W always app.py`; o log não tem Traceback, Error nem warning de deprecated)
  ✓ All endpoints respond correctly (29/29 requisições da baseline batem: as 26 do `scripts/smoke-test-project-3.sh` mais `/`, `/health` e 404 de rota. As chaves de topo das 26 respostas são idênticas às da baseline)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (não sobrou nenhum `fake-jwt` nem `LOGIN_TOKEN_PREFIX`, e controllers/models/utils não importam o Flask. Ficaram só os `print()` de saída de CLI em `seed.py:96-99`, mantidos de propósito porque são a saída do script)
  ✓ All recommendations applied (20/21 ações; remanescentes: F-02 (c) exigir autenticação nas rotas, §5 Fora do escopo)

Prova de assinatura (snippet de validação do PB-06, com o `.venv` do projeto e `SECRET_KEY=validation-key`):
- ✓ o token emitido pelo `POST /login` é aceito com `max_age` de 24h e devolve `{"uid": 1}`;
- ✓ `fake-jwt-token-2` é rejeitado (`BadSignature`);
- ✓ o token com a assinatura adulterada é rejeitado;
- ✓ o token com o payload trocado para `{"uid": 2}` e a assinatura original é rejeitado;
- ✓ o mesmo token é rejeitado com outra `SECRET_KEY`.

O banco `instance/tasks.db` foi restaurado byte a byte (sha1 `80f283d0…`, igual ao backup) e a porta 5002 ficou livre.

## How to run
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                 # defina SECRET_KEY em produção (sem ela, os tokens caem a cada restart)
.venv/bin/python seed.py
PORT=5001 .venv/bin/python app.py    # no macOS a 5000 costuma estar ocupada pelo AirPlay
```
================================
