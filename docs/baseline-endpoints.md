# Baseline de Endpoints (antes da refatoração)

Inventário do comportamento original dos 3 projetos, capturado em 2026-10-23 sobre instâncias recém-iniciadas. Serve como contrato a ser preservado pela Fase 3 da skill `refactor-arch`.

- Scripts de verificação: [`scripts/smoke-test-project-{1,2,3}.sh`](../scripts)
- Corpos das respostas originais: [`scripts/baseline/project-{1,2,3}/`](../scripts/baseline)

```bash
# Exemplo (porta 5000 ocupada pelo AirPlay no macOS → usar porta alternativa)
BASE_URL=http://localhost:5001 ./scripts/smoke-test-project-1.sh
# Para salvar os corpos das respostas: OUT_DIR=<pasta> BASE_URL=... ./scripts/smoke-test-project-1.sh
```

Resultado da baseline: **P1 25/25 · P2 7/7 · P3 26/26**.

> **Exceção aceita ao contrato:** a remoção de dados sensíveis das respostas (ex.: `password`, `secret_key`) é uma correção de segurança esperada e não conta como quebra.

---

## Projeto 1 — code-smells-project (Python/Flask, E-commerce)

**Boot:** `rm -f loja.db && .venv/bin/flask --app app run --port 5001` (o banco é criado com seed no primeiro acesso: 10 produtos, 3 usuários).
**Envelope de resposta:** `{"dados": ..., "sucesso": true, "mensagem"?: ...}`; erros como `{"erro": "..."}`.

| Método | Rota | Body de exemplo | Status | Resposta |
|---|---|---|---|---|
| GET | `/` | — | 200 | `mensagem`, `versao`, mapa `endpoints` |
| GET | `/health` | — | 200 | `status`, `database`, `counts`, … (vaza `secret_key`, `db_path`) |
| GET | `/produtos` | — | 200 | `dados: [produto]` |
| GET | `/produtos/busca?q=&categoria=&preco_min=&preco_max=` | — | 200 | `dados`, `total` |
| GET | `/produtos/<id>` | — | 200 / 404 | `dados: produto` |
| POST | `/produtos` | `{"nome","descricao","preco","estoque","categoria"}` | 201 / 400 | `dados: {id}` |
| PUT | `/produtos/<id>` | `{"nome","preco","estoque","categoria"}` | 200 / 400 / 404 | `mensagem` |
| DELETE | `/produtos/<id>` | — | 200 / 404 | `mensagem` |
| GET | `/usuarios` | — | 200 | `dados: [usuario]` |
| GET | `/usuarios/<id>` | — | 200 / 404 | `dados: usuario` |
| POST | `/usuarios` | `{"nome","email","senha"}` | 201 / 400 | `dados: {id}` |
| POST | `/login` | `{"email":"joao@email.com","senha":"123456"}` | 200 / 401 | `dados: {id,nome,email,tipo}` |
| POST | `/pedidos` | `{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1}]}` | 201 / 400 | `dados: {pedido_id,total}` |
| GET | `/pedidos` | — | 200 | `dados: [pedido]` |
| GET | `/pedidos/usuario/<usuario_id>` | — | 200 | `dados: [pedido]` |
| PUT | `/pedidos/<pedido_id>/status` | `{"status":"aprovado"}` | 200 / 400 | `mensagem` |
| GET | `/relatorios/vendas` | — | 200 | `dados: {total_pedidos, faturamento_bruto, ticket_medio, …}` |
| POST | `/admin/query` | `{"sql":"SELECT ..."}` | 200 | executa SQL arbitrário |
| POST | `/admin/reset-db` | — | 200 | apaga todas as tabelas |

---

## Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS + checkout)

**Boot:** `npm start` (porta 3000, SQLite em memória com seed: 1 usuário, 2 cursos, 1 matrícula paga).
**Formato de resposta:** misto — JSON em sucesso, **texto puro** em erros e no DELETE.

| Método | Rota | Body de exemplo | Status | Resposta |
|---|---|---|---|---|
| POST | `/api/checkout` | `{"usr","eml","pwd","c_id":2,"card":"4111..."}` | 200 | `{"msg":"Sucesso","enrollment_id":N}` |
| POST | `/api/checkout` | cartão não iniciado em `4` | 400 | `Pagamento recusado` (texto) |
| POST | `/api/checkout` | campos faltando | 400 | `Bad Request` (texto) |
| POST | `/api/checkout` | `c_id` inexistente | 404 | `Curso não encontrado` (texto) |
| GET | `/api/admin/financial-report` | — | 200 | `[{course, revenue, students:[{student, paid}]}]` |
| DELETE | `/api/users/<id>` | — | 200 | texto `Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.` |

---

## Projeto 3 — task-manager-api (Python/Flask, Task Manager)

**Boot:** `.venv/bin/python seed.py && .venv/bin/flask --app app run --port 5002` (seed: 3 usuários, 4 categorias, 10 tasks).
**Formato de resposta:** objeto/lista direto, sem envelope; erros como `{"error": "..."}`.

| Método | Rota | Body de exemplo | Status | Resposta |
|---|---|---|---|---|
| GET | `/tasks` | — | 200 | `[task + overdue, user_name, category_name]` |
| GET | `/tasks/search?q=&status=&priority=&user_id=` | — | 200 | `[task]` |
| GET | `/tasks/stats` | — | 200 | `{total, pending, in_progress, done, cancelled, overdue, completion_rate}` |
| GET | `/tasks/<id>` | — | 200 / 404 | `task + overdue` |
| POST | `/tasks` | `{"title","description","priority","user_id","category_id","due_date":"YYYY-MM-DD","tags":[]}` | 201 / 400 / 404 | `task` |
| PUT | `/tasks/<id>` | `{"status":"done","priority":1}` | 200 / 400 / 404 | `task` |
| DELETE | `/tasks/<id>` | — | 200 / 404 | `{"message"}` |
| GET | `/users` | — | 200 | `[user + task_count]` |
| GET | `/users/<id>` | — | 200 / 404 | `user + tasks` (vaza hash `password`) |
| POST | `/users` | `{"name","email","password","role"}` | 201 / 400 / 409 | `user` |
| PUT | `/users/<id>` | `{"name"}` | 200 / 400 / 404 / 409 | `user` |
| DELETE | `/users/<id>` | — | 200 / 404 | `{"message"}` (apaga tasks do usuário) |
| GET | `/users/<id>/tasks` | — | 200 / 404 | `[task resumida + overdue]` |
| POST | `/login` | `{"email":"joao@email.com","password":"1234"}` | 200 / 401 / 403 | `{message, user, token}` |
| GET | `/reports/summary` | — | 200 | `overview`, `tasks_by_status`, `tasks_by_priority`, `overdue`, `recent_activity`, `user_productivity` |
| GET | `/reports/user/<id>` | — | 200 / 404 | `{user, statistics}` |
| GET | `/categories` | — | 200 | `[category + task_count]` |
| POST | `/categories` | `{"name","description","color"}` | 201 / 400 | `category` |
| PUT | `/categories/<id>` | `{"name"}` | 200 / 404 | `category` |
| DELETE | `/categories/<id>` | — | 200 / 404 | `{"message"}` |
