================================
PHASE 1: PROJECT ANALYSIS
================================
Project: task-manager-api
Date:    2026-10-23
Note:    Análise do código **original** (antes da refatoração da Fase 3). Linhas e arquivos citados referem-se a essa versão.

```
Language:      Python 3.11.15 (.venv)
Framework:     Flask 3.0.0 (declarada ==3.0.0, instalada 3.0.0) · Werkzeug 3.1.9 · SQLAlchemy 2.1.6 (transitiva, sem pin)
Dependencies:  flask, flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (não usada), requests 2.31.0 (não usada), python-dotenv 1.0.0 (não usada)
Database:      SQLite (instance/tasks.db) via ORM Flask-SQLAlchemy
Domain:        API de Task Manager: tasks, usuários, categorias e relatórios
Architecture:  Parcialmente em camadas — existem models/, routes/, services/ e utils/, mas as rotas concentram validação, regra e queries; services/, utils/helpers.py e os métodos de domínio dos models não são usados
Source files:  15 files analyzed (~1158 lines) + requirements.txt
DB tables:     users, categories, tasks
Entry point:   app.py (python seed.py && python app.py, porta 5000)
Endpoints:     22 rotas
```

## Inventário de arquivos-fonte
| Arquivo | Linhas | Responsabilidades |
|---|---|---|
| `app.py` | 34 | Criação global da app Flask, config literal (URI, `SECRET_KEY`), `CORS(app)`, registro dos blueprints, rotas `/` e `/health`, `db.create_all()` no import, `app.run(debug=True, host='0.0.0.0', port=5000)` |
| `database.py` | 3 | Instância global `db = SQLAlchemy()` |
| `models/__init__.py` | 3 | Reexporta `Task`, `User`, `Category` |
| `models/task.py` | 60 | Model `tasks`, `to_dict()`, `validate_status`/`validate_priority`/`is_overdue` (nunca chamados) |
| `models/user.py` | 38 | Model `users`, `to_dict()` com `password`, hash MD5 (`set_password`/`check_password`), `is_admin` (nunca chamado) |
| `models/category.py` | 21 | Model `categories`, `to_dict()` |
| `routes/task_routes.py` | 299 | 7 rotas de tasks: HTTP, validação, queries ORM, cálculo de atraso, estatísticas, serialização manual, `print` |
| `routes/user_routes.py` | 211 | 7 rotas de usuários + login: HTTP, validação, queries, cascata de exclusão, token falso |
| `routes/report_routes.py` | 223 | 2 rotas de relatórios + CRUD de categorias (4 rotas): HTTP, agregações, queries |
| `services/notification_service.py` | 48 | Envio de e-mail SMTP com credenciais literais e lista em memória (nunca importado) |
| `utils/helpers.py` | 116 | Helpers de formatação/validação e constantes (quase todos nunca usados) |
| `seed.py` | 99 | Limpa e popula o banco importando a `app` global |
| `routes/__init__.py`, `services/__init__.py`, `utils/__init__.py` | 1 cada | Vazios |

Excluídos: `.venv/`, `__pycache__/`, `.git/`, `.claude/`, `instance/tasks.db`. `requirements.txt` (manifesto) e `README.md` foram lidos, mas não contam como código-fonte.

## Banco de dados
- `db = SQLAlchemy()` global em `database.py:3`, ligado à app em `app.py:16`; URI fixa `sqlite:///tasks.db` (`app.py:11`), que o Flask-SQLAlchemy 3 resolve para `instance/tasks.db`.
- Schema criado por `db.create_all()` no import de `app.py` (`app.py:30-31`).
- Seed separado em `seed.py` (3 usuários com senhas MD5 `1234`/`abcd`/`pass`, 4 categorias, 10 tasks); precisa ser rodado antes do primeiro boot.
- FKs `tasks.user_id → users.id` e `tasks.category_id → categories.id` declaradas sem `ondelete`; o SQLite não as aplica (sem `PRAGMA foreign_keys`).
- `instance/` e `*.db` estão no `.gitignore`.

## Arquitetura atual
- **Entry point:** `app.py`; rotas em 3 blueprints sem prefixo (`task_bp`, `user_bp`, `report_bp`) mais 2 rotas inline em `app.py`.
- **Regra de negócio:** nos handlers das rotas (cálculo de atraso, estatísticas, validações, cascata de exclusão de usuário).
- **Acesso a dados:** Query API do Flask-SQLAlchemy direto nos handlers (`Model.query.get/filter_by/count`).
- **Uso das camadas:** `app.py` → `routes/*` → `models/*` + `database.db`. `services/notification_service.py` nunca é importado; de `utils/helpers.py`, só `format_date` e `calculate_percentage` são importados (`routes/report_routes.py:7`), e nem eles são chamados; os métodos de domínio `Task.validate_status/validate_priority/is_overdue` e `User.is_admin` nunca são chamados.
- **Config:** literais em `app.py:11-13, 34` e `services/notification_service.py:7-10`; nenhuma leitura de variável de ambiente.

## Inventário de endpoints (contrato)
```
GET     /                       -> index              app.py:26
GET     /health                 -> health             app.py:22
GET     /tasks                  -> get_tasks          routes/task_routes.py:11
GET     /tasks/<id>             -> get_task           routes/task_routes.py:65
POST    /tasks                  -> create_task        routes/task_routes.py:85
PUT     /tasks/<id>             -> update_task        routes/task_routes.py:156
DELETE  /tasks/<id>             -> delete_task        routes/task_routes.py:225
GET     /tasks/search           -> search_tasks       routes/task_routes.py:240
GET     /tasks/stats            -> task_stats         routes/task_routes.py:273
GET     /users                  -> get_users          routes/user_routes.py:10
GET     /users/<id>             -> get_user           routes/user_routes.py:27
POST    /users                  -> create_user        routes/user_routes.py:42
PUT     /users/<id>             -> update_user        routes/user_routes.py:92
DELETE  /users/<id>             -> delete_user        routes/user_routes.py:134
GET     /users/<id>/tasks       -> get_user_tasks     routes/user_routes.py:153
POST    /login                  -> login              routes/user_routes.py:185
GET     /reports/summary        -> summary_report     routes/report_routes.py:12
GET     /reports/user/<id>      -> user_report        routes/report_routes.py:103
GET     /categories             -> get_categories     routes/report_routes.py:157
POST    /categories             -> create_category    routes/report_routes.py:167
PUT     /categories/<id>        -> update_category    routes/report_routes.py:190
DELETE  /categories/<id>        -> delete_category    routes/report_routes.py:211
```

## Como subir
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
.venv/bin/python app.py          # porta 5000 fixa, debug=True
```
- **Bloqueio:** a porta 5000 está ocupada pelo AirPlay Receiver (`ControlCenter`) no macOS. Alternativa sem modificar código: `.venv/bin/flask --app app run --port 5001` (o `db.create_all()` roda no import, então nada do bloco `__main__` é necessário).
- Nenhuma variável de ambiente obrigatória.
- O banco em arquivo guarda o estado dos testes: faça backup de `instance/tasks.db` antes e restaure depois (ou rode `seed.py` de novo).
================================
