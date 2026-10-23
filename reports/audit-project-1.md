================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.11.15 + Flask 3.1.1 (SQLite / sqlite3 driver)
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-23

## Summary
CRITICAL: 7 | HIGH: 4 | MEDIUM: 5 | LOW: 4

| ID | Severity | Finding | Catalog | Location |
|----|----------|---------|---------|----------|
| F-01 | CRITICAL | SQL Injection | AP-02 | models.py:109-111 |
| F-02 | CRITICAL | Endpoints administrativos sem autenticação (SQL arbitrário, reset) | AP-06 | app.py:59-78 |
| F-03 | CRITICAL | Exposição de dados sensíveis | AP-05 | controllers.py:285-289 |
| F-04 | CRITICAL | Senhas em texto puro | AP-04 | models.py:109-111 |
| F-05 | CRITICAL | Segredo hardcoded | AP-01 | app.py:7 |
| F-06 | CRITICAL | Pedido sem transação / sem integridade | AP-11 | models.py:133-169 |
| F-07 | CRITICAL | God Files | AP-03 | models.py:1-314 |
| F-08 | HIGH | Debug / config de desenvolvimento fixos | AP-07 | app.py:8, 88 |
| F-09 | HIGH | Regra de negócio no model e no controller | AP-08 | models.py:256-262 |
| F-10 | HIGH | Conexão global mutável | AP-09 | database.py:4-11 |
| F-11 | HIGH | Acoplamento forte sem app factory / DI | AP-10 | app.py:6 |
| F-12 | MEDIUM | Validação de entrada ausente ou inconsistente | AP-15 | controllers.py:169-170 |
| F-13 | MEDIUM | Tratamento de erro genérico, sem handler central | AP-14 | controllers.py:10-12 |
| F-14 | MEDIUM | Queries N+1 | AP-12 | models.py:203-233 |
| F-15 | MEDIUM | Código duplicado | AP-16 | models.py:12-21 |
| F-16 | MEDIUM | CORS permissivo | AP-18 | app.py:9 |
| F-17 | LOW | `print` como log | AP-21 | controllers.py:8 |
| F-18 | LOW | Magic numbers e strings | AP-19 | models.py:257-262 |
| F-19 | LOW | Nomenclatura ruim | AP-20 | models.py:187, 191 |
| F-20 | LOW | Imports não usados | AP-22 | models.py:2 |

## Findings

### F-01 [CRITICAL] SQL Injection
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299
Catalog: AP-02
Description: Todas as queries são montadas por concatenação, por exemplo `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` no login e `" AND (nome LIKE '%" + termo + "%' ..."` na busca. Strings vindas do body (nome, descricao, categoria, email, senha, status) entram direto no SQL.
Impact: Permite burlar o login, ler e escrever qualquer dado do banco, e quebra entradas legítimas com apóstrofo (ex.: "Monitor 27''"). Explorável sem autenticação.
Recommendation: Usar placeholders `?` com os parâmetros separados em todas as queries; filtros dinâmicos da busca com lista de condições e lista de parâmetros → PB-02
Verified: yes (`POST /login` com `{"email":"admin@loja.com' --","senha":"x"}` → 200 "Login OK" como Admin)

### F-02 [CRITICAL] Endpoints administrativos sem autenticação (SQL arbitrário, reset)
File: app.py:47-57, 59-78
Catalog: AP-06
Description: `POST /admin/query` executa qualquer SQL recebido em `dados.get("sql")` e faz commit. `POST /admin/reset-db` apaga as 4 tabelas. Nenhum dos dois exige autenticação. O relatório financeiro (`/relatorios/vendas`, app.py:28) e a mudança de status de pedido (app.py:26) também são públicos.
Impact: Qualquer cliente lê as senhas e altera ou destrói o banco inteiro com uma única requisição.
Recommendation: Remover `/admin/query`. Desabilitar `/admin/reset-db` por padrão e habilitá-lo só por flag de ambiente + token. Para o relatório e o status, registrar autenticação como recomendação → PB-06
Verified: yes (`POST /admin/query {"sql":"SELECT email, senha FROM usuarios"}` → 200 com as 3 senhas em texto puro)

### F-03 [CRITICAL] Exposição de dados sensíveis
File: controllers.py:285-289, models.py:83, 99, controllers.py:161, 179, 182
Catalog: AP-05
Description: `GET /health` devolve `secret_key`, `db_path`, `debug` e `ambiente`. `GET /usuarios` e `GET /usuarios/<id>` serializam o campo `senha`. Os logs gravam o email do usuário na criação e no login (com sucesso ou com falha).
Impact: A chave de assinatura e as senhas de todos os usuários ficam acessíveis a qualquer cliente, e os logs passam a conter PII.
Recommendation: Serializar usuários por lista branca (sem `senha`), tirar segredos e configuração do `/health` e não logar emails → PB-05
Verified: yes (`GET /health` → `"secret_key":"minha-chave-super-secreta-123"`; `GET /usuarios/1` → `"senha":"admin123"`)

### F-04 [CRITICAL] Senhas em texto puro
File: database.py:75-83, models.py:109-111, 126-129
Catalog: AP-04
Description: O seed grava `admin123`, `123456` e `senha123` sem hash. `criar_usuario` insere a senha como veio do request, e o login compara `senha = '<valor>'` no próprio SQL.
Impact: Um vazamento do banco, trivial via F-01/F-02, expõe todas as senhas.
Recommendation: `werkzeug.security.generate_password_hash` na gravação e no seed; `check_password_hash` (tempo constante) no login, buscando o usuário só pelo email → PB-04
Verified: yes (via `/admin/query`, que retornou as senhas em texto puro)

### F-05 [CRITICAL] Segredo hardcoded
File: app.py:7, controllers.py:289
Catalog: AP-01
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está versionado, e o mesmo literal se repete na resposta do `/health`.
Impact: A chave fica no git, sem rotação nem configuração por ambiente, o que permite forjar sessões e cookies assinados.
Recommendation: Ler `SECRET_KEY` do ambiente num módulo de config e criar `.env.example` sem valores reais → PB-01
Verified: yes (vazada por `GET /health`, veja F-03)

### F-06 [CRITICAL] Pedido sem transação / sem integridade
File: models.py:133-169, 144, 163-166, 65-70, 275-283, controllers.py:245-252
Catalog: AP-11
Description: `criar_pedido` faz o INSERT do pedido, os INSERTs dos itens e os UPDATEs de estoque na conexão global compartilhada, sem transação nem rollback. O estoque é validado na l.144 e decrementado só depois (l.163-166), sem condição atômica. Quantidade negativa e `usuario_id` inexistente são aceitos. `deletar_produto` deixa `itens_pedido` órfãos. `atualizar_status_pedido` responde sucesso para pedido inexistente, e o cancelamento não devolve o estoque. A severidade foi elevada de HIGH para CRITICAL porque o problema afeta dinheiro e estoque e é explorável sem autenticação.
Impact: Pedidos com total negativo, estoque inflado, registros órfãos e relatórios financeiros corrompidos. Escritas pendentes de uma requisição que falhou podem ser commitadas pela requisição seguinte.
Recommendation: Uma transação por caso de uso (`with conn:`); `UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?`; exigir quantidade > 0; verificar que usuário e pedido existem (404) → PB-09
Verified: yes (`POST /pedidos {"usuario_id":999,"itens":[{"produto_id":1,"quantidade":-3}]}` → 201, total -17999.97, estoque do produto 1 de 10 para 13)

### F-07 [CRITICAL] God Files
File: models.py:1-314, controllers.py:1-292, database.py:7-86
Catalog: AP-03
Description: `models.py` (314 linhas) reúne SQL, serialização, cálculo de total, baixa de estoque e faixas de desconto de produtos, usuários, pedidos e relatório. `controllers.py` cobre os 3 domínios e ainda executa SQL direto no `health_check` (l.266-274). `database.py` junta conexão, DDL e seed.
Impact: Nada pode ser testado isoladamente, qualquer mudança afeta tudo e um domínio esconde o outro.
Recommendation: Separar por camada e por domínio: `models/{produto,usuario,pedido}_model.py`, `controllers/*_controller.py`, `routes/*_routes.py`, e um módulo de database só com conexão + schema/seed → PB-03
Verified: no

### F-08 [HIGH] Debug / config de desenvolvimento fixos
File: app.py:8, 88, controllers.py:286-288
Catalog: AP-07
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` expõem o debugger do Werkzeug na rede. Porta, host e caminho do banco (`database.py:5`) são fixos. O `/health` declara `"ambiente": "producao"` junto com `"debug": True`.
Impact: O debugger permite execução remota de código e envia stack traces ao cliente; não há configuração por ambiente. A porta fixa 5000 também conflita com o AirPlay do macOS.
Recommendation: `DEBUG`, `HOST`, `PORT` e `DATABASE_PATH` vindos de variáveis de ambiente, com debug desligado por padrão → PB-01
Verified: no (`python app.py` não sobe por conflito na porta 5000)

### F-09 [HIGH] Regra de negócio no model e no controller
File: models.py:256-262, 139-146, controllers.py:52-54, 208-210, 242, 247-250
Catalog: AP-08
Description: As faixas de desconto do relatório e o cálculo do total do pedido estão no meio do SQL do model. As categorias válidas e as transições de status estão inline no controller. As "notificações" de e-mail, SMS e push e as de aprovação e cancelamento são `print` no controller, e o cancelamento promete devolver o estoque sem fazê-lo.
Impact: Nenhuma regra tem um lugar único, testar exige HTTP e banco, e as regras já divergem (criar valida a categoria, atualizar não).
Recommendation: Rotas só com HTTP, controllers com as regras (total, desconto, status, notificação) e models só com acesso a dados → PB-07
Verified: no

### F-10 [HIGH] Conexão global mutável
File: database.py:4-11
Catalog: AP-09
Description: `db_connection = None` + `global db_connection` + `sqlite3.connect(..., check_same_thread=False)` faz todas as threads e requisições compartilharem uma única conexão.
Impact: Condições de corrida, transações de requisições diferentes misturadas (veja F-06) e testes que interferem entre si.
Recommendation: Uma conexão por requisição em `flask.g`, fechada no `teardown_appcontext` → PB-08
Verified: no

### F-11 [HIGH] Acoplamento forte sem app factory / DI
File: app.py:6-30, controllers.py:3, 266, models.py:1, database.py:7-86
Catalog: AP-10
Description: A app é criada no import (`app = Flask(__name__)`) com config fixa. Controllers e models importam `get_db` diretamente. Schema e seed rodam como efeito colateral da primeira chamada a `get_db()`.
Impact: Não dá para trocar o banco ou a config em testes, e importar um módulo já altera o banco.
Recommendation: `create_app(config)` como composition root, registrando os blueprints, a conexão por app context e um `init_db` explícito → PB-08
Verified: no

### F-12 [MEDIUM] Validação de entrada ausente ou inconsistente
File: controllers.py:169-170, 239-240, 43-50, 64-90, 195-201, 153-158
Catalog: AP-15
Description: `login` e `atualizar_status_pedido` chamam `dados.get` sem checar se o body é `None`. `preco < 0` é comparado sem checar o tipo. `atualizar_produto` não valida o tamanho do nome nem a categoria, que `criar_produto` valida. Os itens do pedido não são validados (`produto_id`/`quantidade` ausentes, quantidade ≤ 0), e o formato do email não é verificado.
Impact: Entradas ruins viram 500 e dados inválidos chegam ao banco.
Recommendation: Funções de validação por recurso na borda, compartilhadas entre criar e atualizar, respondendo 400 → PB-13
Verified: yes (`POST /login` sem body → 500; `POST /produtos {"preco":"10",...}` → 500 "'<' not supported...")

### F-13 [MEDIUM] Tratamento de erro genérico, sem handler central
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Catalog: AP-14
Description: Cada handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`. Não há `@app.errorhandler`, e os 404/405 de rota inexistente saem em HTML.
Impact: Detalhes internos vazam para o cliente (mensagens do sqlite, `KeyError`) e o formato de erro é inconsistente.
Recommendation: Exceções de domínio + `register_error_handler` central em JSON, com log do erro inesperado e mensagem genérica para o cliente → PB-12
Verified: yes (`POST /pedidos` com item sem `quantidade` → 500 `{"erro":"'quantidade'"}`)

### F-14 [MEDIUM] Queries N+1
File: models.py:203-233, 171-201, 155, 239-254, controllers.py:268-274
Catalog: AP-12
Description: `get_todos_pedidos` e `get_pedidos_usuario` fazem uma query de itens por pedido e uma de produto por item (`cursor2`/`cursor3`). `criar_pedido` relê o preço de cada produto, e o relatório roda 5 agregações separadas.
Impact: 1 + N + N·M queries por listagem, e a latência cresce com o volume de dados.
Recommendation: `JOIN pedidos/itens_pedido/produtos` agrupado em memória, e um único `SELECT COUNT/SUM ... CASE` no relatório → PB-10
Verified: no

### F-15 [MEDIUM] Código duplicado
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233, controllers.py:28-50, 72-90
Catalog: AP-16
Description: O mapeamento `row → dict` de produto aparece 3 vezes, e o de usuário 2 vezes. `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo filtro. A validação de produto está copiada entre criar e atualizar e já diverge.
Impact: Cada correção precisa ser feita em N lugares, e as cópias divergem (veja F-12).
Recommendation: Um serializer único por entidade, uma listagem de pedidos com filtro opcional e um validador compartilhado → PB-14
Verified: no

### F-16 [MEDIUM] CORS permissivo
File: app.py:9
Catalog: AP-18
Description: `CORS(app)` sem `origins` libera todas as origens, inclusive para os endpoints de F-02.
Impact: Qualquer site pode chamar a API a partir do navegador da vítima.
Recommendation: Origens permitidas lidas de `CORS_ORIGINS` no ambiente → PB-01
Verified: no

### F-17 [LOW] `print` como log
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, 83-86
Catalog: AP-21
Description: Logs e "notificações" são feitos com `print` ("ERRO:", "ENVIANDO EMAIL", "NOTIFICAÇÃO").
Impact: Não há níveis nem controle por ambiente, e PII acaba logada (veja F-03).
Recommendation: `logging` com nível vindo da config → PB-18
Verified: no

### F-18 [LOW] Magic numbers e strings
File: models.py:257-262, controllers.py:47-50, 52, 242, app.py:36, controllers.py:285
Catalog: AP-19
Description: As faixas de desconto (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`), os limites do nome (`2`, `200`), as listas de categorias e de status e a versão `"1.0.0"` aparecem como literais repetidos.
Impact: As regras ficam escondidas e mudá-las exige caçar literais pelo código.
Recommendation: Constantes nomeadas num módulo de domínio → PB-16
Verified: no

### F-19 [LOW] Nomenclatura ruim
File: models.py:187, 191, 219, 223, 24, 54, 65, 89, controllers.py:14, 56, 64, 98, 136, 160
Catalog: AP-20
Description: Há cursores numerados (`cursor2`/`cursor3`), e `id` é usado como parâmetro e variável local, sombreando o builtin.
Impact: A leitura fica prejudicada e a intenção do código, escondida.
Recommendation: Nomes descritivos (`produto_id`, `novo_id`) nos identificadores internos, mantendo o contrato HTTP → PB-17
Verified: no

### F-20 [LOW] Imports não usados
File: models.py:2, database.py:2
Catalog: AP-22
Description: `import sqlite3` em `models.py` e `import os` em `database.py` nunca são referenciados.
Impact: Ruído no código e uma falsa dependência.
Recommendation: Remover → PB-17
Verified: no

## Deprecated APIs
| Location | Deprecated API | Modern replacement | Evidence |
|----------|----------------|--------------------|----------|
| — | None detected for the installed versions (Python 3.11.15, Flask 3.1.1, Werkzeug 3.1.9, flask-cors 5.0.1, sqlite3 stdlib) | — | App original rodada com `PYTHONWARNINGS=always`, sem nenhum DeprecationWarning no log |

## Architecture Notes
- Current: Monolítica — `models.py` concentra o SQL e as regras de 3 domínios; `controllers.py` mistura HTTP, validação e SQL; `database.py` mistura conexão global, schema e seed
- Layers present but unused: none (as 3 camadas são usadas, mas sem fronteiras entre elas)
- Target: MVC — app factory + config via env, models por domínio com SQL parametrizado, controllers com as regras, routes (blueprints) só com HTTP, error handler central

================================
Total: 20 findings
================================
User response: y (prosseguir para a Fase 3)
