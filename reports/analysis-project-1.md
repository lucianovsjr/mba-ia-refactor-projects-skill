================================
PHASE 1: PROJECT ANALYSIS
================================
Project: code-smells-project
Date:    2026-10-23
Note:    Análise do código **original** (antes da refatoração da Fase 3). Linhas e arquivos citados referem-se a essa versão.

```
Language:      Python 3.11.15 (.venv)
Framework:     Flask 3.1.1 (instalada = declarada `flask==3.1.1`; Werkzeug 3.1.9)
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Database:      SQLite (arquivo `loja.db`) via driver puro `sqlite3`, SQL escrito à mão
Domain:        API de E-commerce: produtos, usuários (login), pedidos/itens, relatório de vendas
Architecture:  Monolítica — 4 arquivos sem fronteiras: `models.py` concentra SQL + regras de 3 domínios, `controllers.py` faz HTTP + validação + SQL direto, `database.py` mistura conexão global + schema + seed
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Entry point:   app.py (python app.py, porta 5000)
Endpoints:     19 rotas
```

## Inventário de arquivos-fonte
| Arquivo | Linhas | Responsabilidades |
|---|---|---|
| `app.py` | 88 | Criação da app e config fixa (SECRET_KEY, DEBUG), CORS, registro das rotas, rotas `/`, `/admin/reset-db` e `/admin/query` inline (com SQL), bloco `__main__` |
| `controllers.py` | 292 | Handlers HTTP dos 3 domínios, validação, "notificações" com `print`, SQL direto no `health_check` |
| `models.py` | 314 | SQL (concatenado) de produtos, usuários e pedidos, serialização, cálculo de total, baixa de estoque, faixas de desconto |
| `database.py` | 86 | Conexão global (`check_same_thread=False`), DDL e seed com senhas em texto puro |

Excluídos: `.venv/`, `__pycache__/`, `.claude/`, `loja.db`, `README.md`, `requirements.txt` (manifesto, lido para dependências).

## Banco de dados
- Conexão criada em `database.py:7-11`, em variável global, na primeira chamada a `get_db()`.
- Schema (`CREATE TABLE IF NOT EXISTS`) e seed rodam como efeito colateral dessa primeira chamada (`database.py:14-84`).
- Seed: 10 produtos e 3 usuários (`admin@loja.com`, `joao@email.com`, `maria@email.com`) com senhas em texto puro.
- Sem chaves estrangeiras declaradas; `usuario_id`, `pedido_id` e `produto_id` são FKs só lógicas.

## Arquitetura atual
- **Entry point:** `app.py`; rotas registradas com `app.add_url_rule` (`app.py:11-30`) e `@app.route` (`app.py:32, 47, 59`).
- **Regra de negócio:** espalhada entre `controllers.py` (validações, categorias, status, notificações) e `models.py` (total do pedido, estoque, descontos).
- **Acesso a dados:** `models.py`, e também `controllers.py:266-274` e `app.py:49-55, 66-76`.
- **Uso das camadas:** `app.py` → `controllers` → `models` → `database`; todas usadas, mas sem fronteiras (controllers e app também falam direto com o banco).
- **Config:** literais em `app.py:7-8, 88` e `database.py:5`; nenhuma leitura de variável de ambiente.

## Inventário de endpoints (contrato)
```
GET     /                                   -> index                    app.py:32
POST    /admin/reset-db                     -> reset_database           app.py:47
POST    /admin/query                        -> executar_query           app.py:59
GET     /produtos                           -> listar_produtos          controllers.py:5   (app.py:11)
GET     /produtos/busca                     -> buscar_produtos          controllers.py:111 (app.py:12)
GET     /produtos/<int:id>                  -> buscar_produto           controllers.py:14  (app.py:13)
POST    /produtos                           -> criar_produto            controllers.py:24  (app.py:14)
PUT     /produtos/<int:id>                  -> atualizar_produto        controllers.py:64  (app.py:15)
DELETE  /produtos/<int:id>                  -> deletar_produto          controllers.py:98  (app.py:16)
GET     /usuarios                           -> listar_usuarios          controllers.py:128 (app.py:18)
GET     /usuarios/<int:id>                  -> buscar_usuario           controllers.py:136 (app.py:19)
POST    /usuarios                           -> criar_usuario            controllers.py:146 (app.py:20)
POST    /login                              -> login                    controllers.py:167 (app.py:21)
POST    /pedidos                            -> criar_pedido             controllers.py:188 (app.py:23)
GET     /pedidos                            -> listar_todos_pedidos     controllers.py:229 (app.py:24)
GET     /pedidos/usuario/<int:usuario_id>   -> listar_pedidos_usuario   controllers.py:222 (app.py:25)
PUT     /pedidos/<int:pedido_id>/status     -> atualizar_status_pedido  controllers.py:237 (app.py:26)
GET     /relatorios/vendas                  -> relatorio_vendas         controllers.py:257 (app.py:28)
GET     /health                             -> health_check             controllers.py:264 (app.py:30)
```

## Como subir
```bash
.venv/bin/pip install -r requirements.txt
python app.py            # porta 5000 fixa, host 0.0.0.0, debug=True
```
- **Bloqueio:** a porta 5000 está ocupada pelo AirPlay Receiver (`ControlCenter`) no macOS, então `python app.py` não sobe.
- **Alternativa sem alterar arquivos:** `flask --app app run --port 5001`. O seed continua acontecendo, porque roda de forma lazy no primeiro request.
- `loja.db` é criado no diretório de trabalho e está no `.gitignore` (`*.db`).
================================
