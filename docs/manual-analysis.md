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

---

## Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

**Arquivos analisados:** `src/app.js` (14 linhas), `src/AppManager.js` (141), `src/utils.js` (25), ~180 linhas no total.
**Stack:** Node.js 20, Express 4.22.1, sqlite3 5.1.7 (banco em memória).
**Arquitetura atual:** uma única classe `AppManager` cria a conexão, define o schema, insere o seed, registra as rotas e executa as regras de checkout, pagamento e relatório. `utils.js` mistura configuração com segredos, cache global e "criptografia".

**Resumo:** CRITICAL: 5 · HIGH: 4 · MEDIUM: 4 · LOW: 3 → **16 achados**

| # | Severidade | Problema | Local |
|---|---|---|---|
| 2.1 | CRITICAL | Credenciais de produção hardcoded (banco, gateway de pagamento, SMTP) | `src/utils.js:1-7` |
| 2.2 | CRITICAL | Número do cartão e chave do gateway escritos no log | `src/AppManager.js:45` |
| 2.3 | CRITICAL | "Hash" de senha caseiro e trivialmente colidível; senhas padrão e em texto puro | `src/utils.js:17-23`, `src/AppManager.js:18, 68` |
| 2.4 | CRITICAL | Ausência de autenticação e autorização (checkout em nome de terceiros, rotas admin abertas) | `src/AppManager.js:40, 73-75, 80, 131` |
| 2.5 | CRITICAL | God Class `AppManager`: DB, schema, seed, rotas e regras no mesmo lugar | `src/AppManager.js:4-139` |
| 2.6 | HIGH | Checkout com 3 escritas encadeadas sem transação; erro do audit log ignorado | `src/AppManager.js:50-61` |
| 2.7 | HIGH | Regra de negócio no handler da rota e acoplamento sem DI | `src/AppManager.js:7, 43-75`, `src/app.js:8-10` |
| 2.8 | HIGH | Estado global mutável exportado (cache sem limite, contador nunca atualizado) | `src/utils.js:9-15, 25` |
| 2.9 | HIGH | Exclusão de usuário deixa matrículas e pagamentos órfãos e ignora erros | `src/AppManager.js:131-137` |
| 2.10 | MEDIUM | Queries N+1 no relatório financeiro, com ordem não determinística | `src/AppManager.js:83-127` |
| 2.11 | MEDIUM | Callback hell e uso de API legada baseada em callbacks (deprecated) | `src/AppManager.js:37-77, 83-128`, `src/AppManager.js:1` |
| 2.12 | MEDIUM | Erros engolidos, respostas em texto puro e status HTTP incorretos; sem handler central | `src/AppManager.js:35, 38, 41, 48, 51, 55, 57, 70, 92-93, 104-106, 133-135` |
| 2.13 | MEDIUM | Validação de entrada ausente | `src/AppManager.js:29-35, 46` |
| 2.14 | LOW | Magic numbers e strings | `src/AppManager.js:46, 68`, `src/utils.js:6, 19-22` |
| 2.15 | LOW | Nomenclatura ruim e código morto | `src/AppManager.js:29-33`, `src/utils.js:2-5, 10, 17`, `src/app.js:13` |
| 2.16 | LOW | `console.log` como mecanismo de log | `src/utils.js:13`, `src/app.js:13`, `src/AppManager.js:45` |

### Detalhamento e justificativas

**2.1 [CRITICAL] Credenciais hardcoded.** O objeto `config` contém `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (chave **live**) e `smtpUser` (`src/utils.js:1-7`).
*Por que importa:* os segredos de produção ficam versionados no git e qualquer pessoa com acesso ao repositório pode usá-los.

**2.2 [CRITICAL] Dados de cartão no log.** `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (`src/AppManager.js:45`). **Comprovado:** o log do servidor registra `Processando cartão 4000000000000000 na chave pk_live_1234567890abcdef`.
*Por que importa:* viola o PCI-DSS (o PAN completo não pode ser logado) e espalha a chave do gateway em qualquer agregador de logs.

**2.3 [CRITICAL] Criptografia caseira de senha.** `badCrypto` converte a senha para base64, pega os 2 primeiros caracteres, repete e corta em 10 (`src/utils.js:17-23`). O resultado depende só do início da senha. **Comprovado:** `senhaforte`, `senha123` e `sen` geram o mesmo valor `c2c2c2c2c2`. O loop de 10.000 iterações não acrescenta segurança. O seed grava a senha `'123'` em texto puro (`src/AppManager.js:18`), e um checkout sem `pwd` cria o usuário com a senha padrão `"123456"` (`src/AppManager.js:68`).
*Por que importa:* senhas diferentes colidem e o valor é reversível, então o "hash" não protege nada.

**2.4 [CRITICAL] Sem autenticação nem autorização.** No checkout, quando o email já existe, o fluxo segue com `user.id` **sem verificar a senha** (`src/AppManager.js:40, 73-75`). **Comprovado:** um checkout com `eml: leonan@fullcycle.com.br` e `pwd: "errada"` retorna `Sucesso` e cria a matrícula na conta do Leonan. `GET /api/admin/financial-report` (`80`) e `DELETE /api/users/:id` (`131`) não têm nenhum controle de acesso.
*Por que importa:* qualquer pessoa pode fazer compras em nome de terceiros, ler dados financeiros e apagar usuários.

**2.5 [CRITICAL] God Class.** `AppManager` abre a conexão (`7`), cria as tabelas e o seed (`10-23`), registra todas as rotas (`25-138`) e implementa checkout, pagamento, cadastro de usuário e relatório dentro dos handlers. Não existe nenhuma camada de model, controller ou config.
*Por que importa:* nada pode ser testado ou reutilizado de forma isolada, e qualquer mudança passa pelo mesmo arquivo.

**2.6 [HIGH] Checkout sem transação.** Matrícula, pagamento e audit log são 3 `INSERT`s encadeados, sem `BEGIN`/`COMMIT`/`ROLLBACK` (`src/AppManager.js:50-61`). Se o pagamento falhar, a matrícula já gravada permanece. O erro do audit log é ignorado (`57`), e a resposta de sucesso é enviada de qualquer forma.
*Por que importa:* pode haver aluno matriculado sem pagamento registrado, ou compra sem trilha de auditoria.

**2.7 [HIGH] Regra de negócio no handler e acoplamento.** A aprovação do pagamento (`cc.startsWith("4")`, `46`), a criação implícita de usuário (`66-72`) e a orquestração de matrícula estão dentro do callback da rota. A conexão é criada no construtor (`7`) e `app.js` instancia tudo diretamente (`src/app.js:8-10`), sem injeção de dependência.
*Por que importa:* não é possível trocar o gateway ou o banco, nem testar a regra de checkout sem HTTP e sem SQLite.

**2.8 [HIGH] Estado global mutável.** `globalCache` cresce sem limite a cada checkout (`src/utils.js:9, 12-15`). `totalRevenue` é declarado, nunca atualizado e exportado como valor primitivo (`10, 25`), então quem importa recebe uma cópia congelada.
*Por que importa:* gera vazamento de memória, estado compartilhado entre requisições e comportamento imprevisível em múltiplas instâncias.

**2.9 [HIGH] Integridade na exclusão.** `DELETE /api/users/:id` remove só a linha de `users`, ignora o `err` e sempre responde 200, inclusive para IDs inexistentes (`src/AppManager.js:131-137`). As tabelas não têm `FOREIGN KEY` (`12-16`). **Comprovado:** `DELETE /api/users/999` retorna 200, e depois de `DELETE /api/users/1` o relatório financeiro lista os alunos como `"Unknown"`.
*Por que importa:* sobram dados órfãos, o relatório fica corrompido e o cliente recebe uma resposta enganosa. A própria mensagem de resposta admite o problema.

**2.10 [MEDIUM] N+1 no relatório.** Para cada curso há 1 query de matrículas (`92`), e para cada matrícula mais 2 queries, de usuário e de pagamento (`104, 106`): no total, 1 + C + 2·E queries. O agrupamento é feito com contadores manuais (`coursesPending`, `enrPending`). **Comprovado:** a ordem dos cursos na resposta muda entre execuções (Docker aparece antes de Clean Architecture), porque depende da ordem em que os callbacks terminam.
*Por que importa:* a latência cresce com o volume e a saída não é determinística. Um único `JOIN` com `GROUP BY` resolveria.

**2.11 [MEDIUM] Callback hell e API legada.** São até 6 níveis de callbacks aninhados (`37-77`, `83-128`), com o truque `const self = this` (`26`) para acessar `this.lastID`. O driver `sqlite3` é usado no estilo de callback anterior às Promises, com `.verbose()` (modo de debug) em produção (`1`). O `npm install` desse driver também traz dependência transitiva marcada como **deprecated** (`@npmcli/move-file@1.1.2`, via `sqlite3 → node-gyp`).
*Recomendação moderna:* `async/await` sobre um wrapper com Promises (`util.promisify` ou `sqlite`/`better-sqlite3`), ou o módulo nativo `node:sqlite` em Node ≥ 22.5.
*Por que importa:* o fluxo fica difícil de ler e propaga erros mal, como mostra o item 2.12.

**2.12 [MEDIUM] Error handling.** Vários `err` são ignorados ou mal tratados. Em `92-93`, se a query falhar, `enrollments.length` lança `TypeError` e **derruba o processo**. Em `104-106` e `133`, os erros são ignorados. As respostas de erro são texto puro servido como `text/html` (`35, 38, 41, 48, 51, 55, 70`), enquanto as de sucesso são JSON. Qualquer erro na busca do curso vira 404 (`38`). Não há middleware de erro nem handler para rotas inexistentes.
*Por que importa:* os clientes não conseguem tratar erros de forma uniforme, e uma falha de banco pode derrubar o servidor.

**2.13 [MEDIUM] Validação ausente.** Só há um teste de presença dos campos (`35`). `pwd` é opcional e não há validação de formato de email, de cartão (número, tamanho, Luhn) nem de tipo de `c_id`. **Comprovado:** o cartão `"4"` é aprovado e gera matrícula paga.
*Por que importa:* aceita dados inválidos e cria pagamentos "aprovados" falsos.

**2.14 [LOW] Magic numbers e strings.** O prefixo `"4"` decide a aprovação (`46`). A senha padrão é `"123456"` (`68`). A porta `3000` está fixa (`src/utils.js:6`), assim como os valores `10000`, `2` e `10` do "hash" (`19-22`). Os status `'PAID'` e `'DENIED'` aparecem como literais espalhados.
*Por que importa:* esconde regras de negócio e dificulta a configuração por ambiente.

**2.15 [LOW] Nomenclatura e código morto.** As variáveis `u`, `e`, `p`, `cid` e `cc` não dizem nada (`src/AppManager.js:29-33`), assim como os campos de API `usr`, `eml`, `pwd` e `c_id`. Os nomes `badCrypto`, `AppManager` e `"Frankenstein LMS"` (`src/app.js:13`) também não ajudam. `dbUser`, `dbPass`, `smtpUser` e `totalRevenue` nunca são usados (`src/utils.js:2-5, 10`). Usa-se `let` onde caberia `const`.
*Por que importa:* prejudica a leitura e esconde intenção.

**2.16 [LOW] `console.log` como log.** Os logs não têm nível nem estrutura (`src/utils.js:13`, `src/app.js:13`, `src/AppManager.js:45`).
*Por que importa:* não é possível filtrar por severidade nem mascarar campos sensíveis (ver 2.2).
