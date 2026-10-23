#!/usr/bin/env bash
# Smoke test — code-smells-project (Python/Flask, E-commerce)
# Pré-condição: banco recém-criado (apague loja.db antes de subir a app).
# Uso: BASE_URL=http://localhost:5001 ./scripts/smoke-test-project-1.sh
set -u
source "$(dirname "$0")/lib.sh"
BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "code-smells-project @ $BASE_URL"

check index            GET    /                         200
check health           GET    /health                   200

check produtos_list    GET    /produtos                 200
check produtos_busca   GET    "/produtos/busca?q=mouse&categoria=informatica&preco_min=10&preco_max=500" 200
check produto_get      GET    /produtos/1               200
check produto_404      GET    /produtos/9999            404
check produto_create   POST   /produtos                 201 '{"nome":"Produto Teste","descricao":"Desc","preco":10.5,"estoque":5,"categoria":"livros"}'
check produto_400      POST   /produtos                 400 '{"nome":"X"}'
check produto_update   PUT    /produtos/2               200 '{"nome":"Mouse Atualizado","preco":99.9,"estoque":40,"categoria":"informatica"}'
check produto_delete   DELETE /produtos/10              200

check usuarios_list    GET    /usuarios                 200
check usuario_get      GET    /usuarios/1               200
check usuario_404      GET    /usuarios/9999            404
check usuario_create   POST   /usuarios                 201 '{"nome":"Novo","email":"novo@email.com","senha":"abc123"}'
check login_ok         POST   /login                    200 '{"email":"joao@email.com","senha":"123456"}'
check login_401        POST   /login                    401 '{"email":"joao@email.com","senha":"errada"}'

check pedido_create    POST   /pedidos                  201 '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1},{"produto_id":3,"quantidade":2}]}'
check pedido_400       POST   /pedidos                  400 '{"usuario_id":2,"itens":[]}'
check pedidos_list     GET    /pedidos                  200
check pedidos_usuario  GET    /pedidos/usuario/2        200
check pedido_status    PUT    /pedidos/1/status         200 '{"status":"aprovado"}'
check pedido_status400 PUT    /pedidos/1/status         400 '{"status":"invalido"}'

check relatorio_vendas GET    /relatorios/vendas        200

check admin_query      POST   /admin/query              200 '{"sql":"SELECT COUNT(*) AS total FROM produtos"}'
check admin_reset      POST   /admin/reset-db           200

summary
