# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em MVC
(`src/models`, `src/controllers`, `src/views`).

## Como rodar

```bash
pip install -r requirements.txt
python app.py                       # ou: flask --app app run
```

A aplicação sobe em `http://127.0.0.1:5000` (porta configurável por `PORT`; no macOS a 5000 costuma estar
ocupada pelo AirPlay, use por exemplo `PORT=5001 python app.py`). O banco SQLite (`DATABASE_PATH`, padrão
`loja.db`) é criado no boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

Veja `.env.example` para todas as variáveis. `SECRET_KEY` é obrigatória em produção. O endpoint
`POST /admin/reset-db` só responde com `ENABLE_ADMIN_ENDPOINTS=true` e o header `X-Admin-Token`
igual a `ADMIN_TOKEN`.
