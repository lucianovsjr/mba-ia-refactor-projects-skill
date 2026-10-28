# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC (veja `../reports/audit-project-3.md`).

## Estrutura

```
app.py              # composition root: create_app() + execução direta
config/settings.py  # configuração via variáveis de ambiente (.env opcional)
database.py         # instância do SQLAlchemy e helper transaction()
models/             # entidades, consultas e regras de domínio (Task, User, Category)
controllers/        # casos de uso por domínio
routes/             # blueprints (só HTTP) e serializers
middlewares/        # error handler central (respostas {"error": ...})
utils/              # constantes, exceções de domínio, validadores, datas
seed.py             # popula o banco usando create_app()
```

## Como rodar

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # opcional; ajuste SECRET_KEY, PORT, CORS_ORIGINS...
.venv/bin/python seed.py
.venv/bin/python app.py         # ou: .venv/bin/flask --app app run
```

A aplicação sobe em `http://127.0.0.1:5000` (configurável por `HOST`/`PORT`; no macOS a 5000 costuma estar ocupada pelo AirPlay, use `PORT=5001`). O `seed.py` recria os dados de exemplo no SQLite (`instance/tasks.db`) — **rode-o antes do primeiro boot**. Em produção, defina `SECRET_KEY`; sem ela uma chave aleatória é gerada a cada boot, e os tokens de login (assinados com essa chave) deixam de valer a cada restart. O modo debug só liga com `FLASK_DEBUG=true`.
