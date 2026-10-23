================================
PHASE 3: REFACTORING COMPLETE
================================
Project: code-smells-project
Stack:   Python 3.11.15 + Flask 3.1.1 (SQLite / sqlite3 driver)
Date:    2026-10-23
Audit:   [audit-project-1.md](audit-project-1.md)

## New Project Structure
```
code-smells-project/
├── app.py                         # entry point fino: create_app() + app.run(HOST/PORT/DEBUG da config)
├── requirements.txt               # inalterado (flask, flask-cors; nenhuma dependência nova)
├── .env.example                   # variáveis esperadas, sem valores reais
├── README.md                      # como rodar / variáveis
└── src/
    ├── app.py                     # composition root: create_app(config) → logging, CORS, banco, error handlers, blueprints
    ├── config/settings.py         # Settings: lê o ambiente, defaults seguros (debug off, SECRET_KEY aleatória)
    ├── database/connection.py     # conexão por requisição (flask.g) + teardown + init_app
    ├── database/schema.py         # DDL, seed com senhas em hash, migração de senhas legadas, limpeza (reset)
    ├── models/produto_model.py    # SQL parametrizado de produtos (busca dinâmica, baixa de estoque atômica)
    ├── models/usuario_model.py    # SQL parametrizado de usuários
    ├── models/pedido_model.py     # pedidos/itens: JOIN único na listagem, agregação única no relatório
    ├── controllers/produto_controller.py   # casos de uso de produto (404, 409 se há pedidos)
    ├── controllers/usuario_controller.py   # cadastro (hash, email único, tipo fixo) e login (check_password_hash)
    ├── controllers/pedido_controller.py    # criação em transação, valida usuário/estoque, status + notificações
    ├── controllers/relatorio_controller.py # faixas de desconto e métricas
    ├── controllers/health_controller.py    # health sem segredos
    ├── controllers/admin_controller.py     # reset do banco em transação
    ├── views/{produto,usuario,pedido,relatorio,system,admin}_routes.py  # blueprints: só HTTP
    ├── views/serializers.py       # lista branca de campos (sem senha)
    ├── middlewares/error_handler.py  # AppError/HTTPException/Exception → JSON
    ├── middlewares/auth.py        # admin_required: flag ENABLE_ADMIN_ENDPOINTS + X-Admin-Token
    ├── services/notification_service.py  # "notificações" (log) isoladas
    └── utils/{constants,errors,validators}.py  # enums/limites, exceções de domínio, validação na borda
```

Arquivos removidos: `controllers.py`, `models.py`, `database.py`.

## Changes
| Achado | Playbook | O que foi feito |
|---|---|---|
| F-01 SQL Injection | PB-02 | Todas as queries com placeholders `?`; busca com listas de condições + params; LIKE com curinga no parâmetro |
| F-02 Admin sem auth | PB-06 | `/admin/query` removido; `/admin/reset-db` desligado por padrão (404), exige `ENABLE_ADMIN_ENDPOINTS=true` + `X-Admin-Token` |
| F-03 Dados sensíveis | PB-05 | Serializers por lista branca (sem `senha`); health sem `secret_key`/`db_path`/`debug`; logs sem email |
| F-04 Senhas em texto puro | PB-04 | werkzeug scrypt no cadastro e no seed; login busca por email + `check_password_hash`; senhas legadas convertidas no boot |
| F-05 Segredo hardcoded | PB-01 | `SECRET_KEY` via env (aleatória em dev); `.env.example` |
| F-06 Transação/integridade | PB-09 | Pedido em transação única (`with db:`), decremento atômico `WHERE estoque >= ?`, quantidade > 0, usuário existente; 404 para pedido inexistente; 409 ao excluir produto com pedidos |
| F-07 God Files | PB-03 | `models.py`/`controllers.py`/`database.py` divididos por camada e domínio, e depois removidos |
| F-08 Debug fixo | PB-01 | `DEBUG`/`HOST`/`PORT`/`DATABASE_PATH`/`APP_ENV` via env; debug off e host `127.0.0.1` por padrão |
| F-09 Regra no lugar errado | PB-07 | Regras (total, desconto, status, notificações) nos controllers/service; models só com dados |
| F-10 Conexão global | PB-08 | Conexão por requisição em `flask.g`, fechada no teardown; sem `global` nem `check_same_thread=False` |
| F-11 Sem factory/DI | PB-08 | `create_app(config)` como composition root; schema/seed rodam na factory, não no import de módulos |
| F-12 Validação | PB-13 | `validators.py` único para criar e atualizar, com checagem de tipo, enum, itens e email; body ausente → 400 |
| F-13 Erros genéricos | PB-12 | Exceções de domínio + error handler central em JSON; sem try/except repetido; 500 com mensagem genérica e stack no log |
| F-14 N+1 | PB-10 | Listagem de pedidos com 1 JOIN; relatório com 1 agregação; produtos do pedido lidos em 1 `IN (...)` |
| F-15 Duplicação | PB-14 | Serializers únicos; `listar_com_itens(usuario_id opcional)`; validador de produto compartilhado |
| F-16 CORS | PB-01 | CORS restrito a `CORS_ORIGINS` (default `localhost:3000`) |
| F-17 print | PB-18 | `logging` com `LOG_LEVEL`; notificações viram `notification_service` |
| F-18 Magic numbers | PB-16 | `constants.py` (`FAIXAS_DESCONTO`, `STATUS_PEDIDO`, `CATEGORIAS_VALIDAS`, limites, `APP_VERSION`) |
| F-19 Nomenclatura | PB-17 | `id` → `produto_id`/`usuario_id`; sem `cursor2`/`cursor3` |
| F-20 Imports mortos | PB-17 | Eliminados junto com os arquivos antigos (checagem AST: 0 imports não usados) |

## Contract changes
- `GET /usuarios`, `GET /usuarios/<id>`: campo `senha` removido de cada usuário
- `GET /health`: removidos `secret_key`, `db_path` e `debug`; `ambiente` vem de `APP_ENV` (default `"development"`, antes `"producao"` fixo)
- `POST /admin/query`: removido → 404 JSON
- `POST /admin/reset-db`: 404 por padrão; 403 sem token válido; 200 só com flag + token
- `POST /login`: payload de SQL injection agora → 401; sem body → 400 (antes 500)
- `POST /pedidos`: quantidade ≤ 0 → 400; `usuario_id` inexistente → 404; itens malformados → 400 (antes 201 ou 500)
- `PUT /pedidos/<id>/status`: pedido inexistente → 404 (antes 200)
- `DELETE /produtos/<id>`: produto com pedidos → 409 (antes 200, deixando itens órfãos)
- `POST /usuarios`: email duplicado → 409; email com formato inválido → 400
- `POST`/`PUT /produtos`: `preco`/`estoque` de tipo errado → 400 (antes 500); o PUT passa a validar nome e categoria como o POST
- `GET /produtos/busca`: `preco_min`/`preco_max` não numérico → 400 (antes 500)
- Rotas inexistentes / método não permitido: 404/405 em JSON `{"erro", "sucesso": false}` (antes HTML)

## Validation
- ✓ Application boots without errors: `python app.py` com `PORT=5001`, e também `flask --app app run`; sem Traceback nem DeprecationWarning com `PYTHONWARNINGS=always`
- ✓ All endpoints respond correctly: 34/49 requisições da baseline idênticas; as 15 diferenças são as mudanças de contrato acima:
  - 12 diretas;
  - 3 em cascata (`GET /pedidos`, `GET /pedidos/usuario/2`, `GET /relatorios/vendas`), que só diferem porque a baseline havia aceitado os 2 pedidos corrompidos agora rejeitados. Confirmado: a resposta é igual à baseline sem os pedidos 2 e 3.
- ✓ Zero CRITICAL/HIGH anti-patterns remaining

Verificações extras:
- **Rollback:** pedido com o mesmo produto duas vezes estourando o estoque → 400, estoque inalterado (8) e nenhum pedido criado
- **Senhas antigas:** banco antigo com senha em texto puro → convertida para scrypt no boot, e o login continua funcionando
- **Admin:** com o endpoint ligado, sem token → 403; token válido → 200
- **SQL injection:** payload na busca tratado como texto (200, lista vazia)
- **Validação/conflitos:** email duplicado → 409; `preco_min=abc` → 400; método não permitido → 405 JSON

### Remaining (MEDIUM/LOW) e recomendações
- **MEDIUM:** schema sem `FOREIGN KEY`; a integridade é garantida só na aplicação, porque alterar o schema de bancos existentes exige migração.
- **LOW:** senhas das contas de exemplo do seed aparecem como literais em `src/database/schema.py`. Elas são gravadas com hash e são necessárias para as contas demo.
- **Fora do escopo** (exigiria decisão de produto / quebraria clientes):
  - autenticação em `GET /relatorios/vendas` e `PUT /pedidos/<id>/status`;
  - devolução de estoque no cancelamento de pedido;
  - servidor WSGI de produção (gunicorn) no lugar do servidor de desenvolvimento.

## How to run
```bash
.venv/bin/pip install -r requirements.txt
export SECRET_KEY=<valor forte>        # obrigatória em produção
PORT=5001 python app.py                # ou: flask --app app run --port 5001
```
- O seed roda automaticamente no primeiro boot (`DATABASE_PATH`, default `loja.db`).
- Opcionais: `FLASK_DEBUG`, `HOST`, `APP_ENV`, `CORS_ORIGINS`, `LOG_LEVEL`, `ENABLE_ADMIN_ENDPOINTS` + `ADMIN_TOKEN` (veja `.env.example`).
- No macOS a porta 5000 costuma estar ocupada pelo AirPlay; use `PORT=5001`.
- Padrões que mudaram: host agora é `127.0.0.1` (antes `0.0.0.0`) e CORS restrito; ajuste `HOST`/`CORS_ORIGINS` se clientes acessarem por outra máquina ou origem.
================================
