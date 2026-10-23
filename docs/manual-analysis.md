# Análise Manual dos Projetos

Achados identificados por leitura do código e por testes contra a aplicação rodando. Cada achado traz severidade (escala do [DESAFIO.md](../DESAFIO.md#definição-de-severidades)), localização exata e justificativa. Os achados estão ordenados de CRITICAL a LOW.

---

## Projeto 1 — code-smells-project (Python/Flask, E-commerce)

**Arquivos analisados:** `app.py` (88 linhas), `controllers.py` (292), `models.py` (314), `database.py` (86), ~780 linhas no total.
**Arquitetura atual:** monolito em 4 arquivos. `app.py` mistura roteamento, endpoints administrativos e acesso a banco. `controllers.py` faz validação, regra de negócio e "notificações". `models.py` concentra SQL, regras e formatação de 3 domínios (produtos, usuários, pedidos).

**Resumo:** CRITICAL: 5 · HIGH: 4 · MEDIUM: 5 · LOW: 3 → **17 achados**

| # | Severidade | Problema | Local |
|---|---|---|---|
| 1.1 | CRITICAL | SQL Injection em praticamente todas as queries | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297` |
| 1.2 | CRITICAL | Endpoints administrativos sem autenticação: SQL arbitrário e reset do banco | `app.py:47-57`, `app.py:59-78` |
| 1.3 | CRITICAL | Credenciais hardcoded e expostas pela API | `app.py:7`, `controllers.py:285-289` |
| 1.4 | CRITICAL | Senhas em texto puro, retornadas pela API | `database.py:76-78`, `models.py:83, 99, 109-111, 126-129` |
| 1.5 | CRITICAL | God Module: `models.py` concentra dados, regras e formatação de 3 domínios | `models.py:1-314` |
| 1.6 | HIGH | Modo debug ligado e servidor exposto em `0.0.0.0` | `app.py:8`, `app.py:88` |
| 1.7 | HIGH | Conexão global mutável compartilhada entre threads, com schema e seed dentro de `get_db()` | `database.py:4-10`, `database.py:14-84` |
| 1.8 | HIGH | Criação de pedido sem transação e sem validação de integridade | `models.py:133-169`, `controllers.py:195-201` |
| 1.9 | HIGH | Regra de negócio e efeitos colaterais espalhados em controllers e models, com acoplamento direto (sem DI) | `controllers.py:2-3, 52-54, 208-210, 242-250`, `models.py:256-262` |
| 1.10 | MEDIUM | Queries N+1 na listagem de pedidos | `models.py:171-201`, `models.py:203-233`, `models.py:139-141 + 154-156` |
| 1.11 | MEDIUM | Tratamento de erro genérico em cada função, vazando detalhes internos; sem handler central | `controllers.py:10-12, 21-22, 60-62, 95-96, …` (todas as funções), `app.py:77-78` |
| 1.12 | MEDIUM | Validação de entrada ausente ou inconsistente | `controllers.py:43-50 vs 81-90`, `153-158`, `169-170`, `239-240`, `models.py:144` |
| 1.13 | MEDIUM | Código duplicado (mapeamento de linhas, listagem de pedidos, validação de produto) | `models.py:12-21 / 31-40 / 304-313`, `models.py:79-86 / 95-102`, `models.py:171-201 vs 203-233`, `controllers.py:28-46 vs 72-90` |
| 1.14 | MEDIUM | CORS liberado para qualquer origem | `app.py:9` |
| 1.15 | LOW | `print` usado como log, inclusive com PII (email) | `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`, `app.py:55, 83-86` |
| 1.16 | LOW | Magic numbers e strings | `models.py:257-262`, `controllers.py:47-50, 52, 242`, `controllers.py:285-286` |
| 1.17 | LOW | Nomenclatura ruim e imports não usados | `controllers.py:14, 56, 64, 98, 160` (`id`), `models.py:187-192` (`cursor2`, `cursor3`), `models.py:2`, `database.py:2` |

### Detalhamento e justificativas

**1.1 [CRITICAL] SQL Injection.** Todas as queries com parâmetros são montadas por concatenação de strings, por exemplo `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (`models.py:109-111`). **Comprovado:** `POST /login` com `{"email": "admin@loja.com' --", "senha": "x"}` autentica como **Admin** sem a senha. Também quebra entradas legítimas: criar o produto `"Livro D'Ávila"` retorna 500 com erro de sintaxe SQL.
*Por que importa:* permite bypass de autenticação, leitura e alteração arbitrária do banco. É a falha de segurança mais grave do projeto.

**1.2 [CRITICAL] Endpoints administrativos abertos.** `POST /admin/query` executa qualquer SQL vindo no body (`app.py:59-78`). `POST /admin/reset-db` apaga todas as tabelas (`app.py:47-57`). Nenhum dos dois tem autenticação, e ambos acessam o banco direto na camada de roteamento.
*Por que importa:* qualquer cliente pode ler senhas, alterar preços ou destruir os dados com uma única requisição.

**1.3 [CRITICAL] Credenciais hardcoded e expostas.** `SECRET_KEY = "minha-chave-super-secreta-123"` está fixa no código (`app.py:7`). O `GET /health` devolve essa mesma chave, além de `db_path`, `debug` e `ambiente` (`controllers.py:285-289`).
*Por que importa:* a chave fica versionada no git e é publicada por um endpoint público, o que permite forjar sessões e assinaturas.

**1.4 [CRITICAL] Senhas em texto puro.** O seed grava senhas legíveis (`database.py:76-78`), `criar_usuario` persiste a senha sem hash (`models.py:126-129`) e o login compara texto puro direto no SQL (`models.py:109-111`). `GET /usuarios` e `GET /usuarios/<id>` retornam o campo `senha` (`models.py:83, 99`). **Comprovado:** `GET /usuarios/1` retorna `"senha": "admin123"`.
*Por que importa:* um vazamento do banco ou da API expõe as credenciais de todos os usuários.

**1.5 [CRITICAL] God Module.** `models.py` (314 linhas) contém SQL, regras de negócio (cálculo de total, baixa de estoque, faixas de desconto), formatação de resposta e lógica de 3 domínios diferentes. Não há camadas: tudo é função solta que acessa a conexão global.
*Por que importa:* não é possível testar nada isoladamente, e qualquer mudança em um domínio arrisca quebrar os outros.

**1.6 [HIGH] Debug em produção.** `app.config["DEBUG"] = True` (`app.py:8`) e `app.run(host="0.0.0.0", debug=True)` (`app.py:88`). O próprio `/health` declara `"ambiente": "producao"`.
*Por que importa:* o debugger do Werkzeug exposto na rede permite execução remota de código e mostra stack traces.

**1.7 [HIGH] Estado global mutável.** `db_connection` é uma variável global única, aberta com `check_same_thread=False` e compartilhada por todas as requisições (`database.py:4-10`). `get_db()` ainda cria o schema e insere o seed (`database.py:14-84`), misturando conexão, migração e dados iniciais.
*Por que importa:* a conexão compartilhada entre threads gera condições de corrida. Também não dá para injetar outro banco em testes, e o caminho `loja.db` é fixo (`database.py:5`).

**1.8 [HIGH] Pedido sem transação e sem integridade.** `criar_pedido` verifica o estoque em um loop (`models.py:139-146`), insere o pedido (`148-152`) e depois, em outro loop, insere os itens e decrementa o estoque (`154-166`). Não há transação explícita nem rollback: uma exceção no meio deixa o pedido incompleto. O estoque também não é revalidado no UPDATE (condição de corrida). **Comprovado:** `usuario_id: 999` (inexistente) gera o pedido com sucesso (201). `quantidade: -5` gera um pedido com total **negativo** (`-29999.95`) e o estoque do produto **sobe** de 10 para 15.
*Por que importa:* gera dados financeiros e de estoque inconsistentes.

**1.9 [HIGH] Regra de negócio fora do lugar e acoplamento.** Os controllers importam `models` e `get_db` diretamente (`controllers.py:2-3`), sem injeção de dependência. Regras de domínio estão nos controllers: categorias válidas (`52-54`), transições de status (`242`) e "notificações" de email, SMS e push simuladas com `print` (`208-210, 247-250`). A regra de desconto está no model (`models.py:256-262`). O `health_check` faz SQL direto no controller (`controllers.py:266-274`).
*Por que importa:* não existe um lugar único para cada regra. Testar exige banco real, e trocar a persistência exige mexer em tudo.

**1.10 [MEDIUM] N+1.** `get_todos_pedidos` e `get_pedidos_usuario` fazem 1 query por pedido para buscar os itens, e mais 1 query por item para buscar o nome do produto (`models.py:187-193`, `219-225`). `criar_pedido` busca cada produto duas vezes (`140` e `155`).
*Por que importa:* com P pedidos de I itens, são 1 + P + P·I queries, e a latência cresce de forma linear.

**1.11 [MEDIUM] Error handling genérico.** Cada função de controller tem `try/except Exception as e: return jsonify({"erro": str(e)}), 500`. Não existe handler centralizado. **Comprovado:** a mensagem de erro do SQLite (`near "Ávila": syntax error`) chega ao cliente.
*Por que importa:* expõe detalhes internos, transforma erros de validação (ex.: `preco` como string) em 500 e duplica código em todas as funções.

**1.12 [MEDIUM] Validação ausente ou inconsistente.** O `atualizar_produto` não valida tamanho do nome nem categoria, ao contrário do `criar_produto` (`controllers.py:43-54 vs 81-90`). Não há checagem de tipo em `preco` e `estoque`. `criar_usuario` não valida formato de email nem força da senha, nem verifica duplicidade (`153-158`). `login` e `atualizar_status_pedido` chamam `dados.get` sem checar se `dados` é `None`, o que dá 500 com body vazio (`169-170`, `239-240`). `quantidade` dos itens não é validada (`models.py:144`).
*Por que importa:* entradas inválidas viram erros 500 ou dados corrompidos.

**1.13 [MEDIUM] Duplicação.** O mapeamento `row → dict` de produto aparece 3 vezes (`models.py:12-21, 31-40, 304-313`) e o de usuário 2 vezes (`79-86, 95-102`). `get_pedidos_usuario` e `get_todos_pedidos` são praticamente idênticos (`171-201` vs `203-233`). A validação de produto está copiada entre criar e atualizar (`controllers.py:28-46` vs `72-90`).
*Por que importa:* as correções precisam ser replicadas em vários lugares, e as cópias já divergiram (ver 1.12).

**1.14 [MEDIUM] CORS aberto.** `CORS(app)` sem restrição de origem (`app.py:9`).
*Por que importa:* combinado com 1.2, qualquer site pode chamar os endpoints administrativos a partir do navegador da vítima.

**1.15 [LOW] `print` como log.** São mais de 15 `print` espalhados, sem nível nem formato. Alguns registram emails de usuários (`controllers.py:161, 179, 182`).
*Por que importa:* não há como filtrar ou desligar logs, e dados pessoais vazam nos logs.

**1.16 [LOW] Magic numbers e strings.** Faixas de desconto `10000/5000/1000` e `0.1/0.05/0.02` (`models.py:257-262`). Limites de nome `2/200` (`controllers.py:47-50`). Listas de categorias e status inline (`52`, `242`). Versão `"1.0.0"` repetida (`controllers.py:285`, `app.py:35`).
*Por que importa:* regras de negócio ficam escondidas e são difíceis de alterar de forma consistente.

**1.17 [LOW] Nomenclatura e imports.** O parâmetro `id` sombreia o builtin do Python (`controllers.py:14, 56, 64, 98, 160`). As variáveis `cursor2` e `cursor3` não dizem nada (`models.py:187-192`). Há imports não usados: `sqlite3` (`models.py:2`) e `os` (`database.py:2`). Nomes em português e inglês misturados (`get_todos_produtos`).
*Por que importa:* prejudica a leitura e esconde intenção.

**APIs deprecated:** nenhuma identificada. O projeto usa Flask 3.1.1 e flask-cors 5.0.1 com APIs atuais (`add_url_rule`, `jsonify`, `sqlite3` padrão).
