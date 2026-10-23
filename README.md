# Refactor Projects Skill

Skill `refactor-arch` para Claude Code que analisa, audita e refatora projetos legados para o padrão MVC, independente da stack.

## Desafio

A descrição completa do desafio está em [DESAFIO.md](./DESAFIO.md). O plano de execução está em [PLANO.md](./PLANO.md).

## Sumário

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

---

## A) Análise Manual

Antes de criar a skill, li o código dos 3 projetos e testei cada suspeita contra a aplicação rodando. As tabelas abaixo resumem os achados, de CRITICAL a LOW. O detalhamento completo, com evidências e linhas exatas, está em [`docs/manual-analysis.md`](docs/manual-analysis.md). O inventário de endpoints usado como baseline está em [`docs/baseline-endpoints.md`](docs/baseline-endpoints.md).

**Escala de severidade** (definida no [desafio](DESAFIO.md#definição-de-severidades)):
- **CRITICAL:** segurança ou arquitetura que expõe dados ou quebra totalmente a separação de responsabilidades.
- **HIGH:** violação forte de MVC ou SOLID.
- **MEDIUM:** padronização, duplicação ou performance.
- **LOW:** legibilidade.

### Visão geral

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|:-:|:-:|:-:|:-:|:-:|
| code-smells-project | Python 3.11 + Flask 3.1.1 + sqlite3 | 5 | 4 | 5 | 3 | **17** |
| ecommerce-api-legacy | Node.js 20 + Express 4.22 + sqlite3 | 5 | 4 | 4 | 3 | **16** |
| task-manager-api | Python 3.11 + Flask 3.0 + Flask-SQLAlchemy | 3 | 3 | 6 | 3 | **15** |

Os achados marcados com ✔ foram **comprovados com requisições reais**. Os demais vêm da leitura do código.

### Projeto 1 — code-smells-project (E-commerce)

Monolito em 4 arquivos. `models.py` mistura SQL, regras e formatação de 3 domínios. O banco é acessado por uma conexão global e as queries são montadas por concatenação de strings.

| # | Severidade | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 1.1 | CRITICAL | SQL Injection em praticamente todas as queries ✔ | `models.py:28, 47-50, 57-61, 92, 109-111, 126-129, 140, 174, 279-281, 289-297` (+ outras) | `{"email": "admin@loja.com' --"}` loga como Admin sem senha. Também quebra entradas legítimas com apóstrofo. |
| 1.2 | CRITICAL | `/admin/query` (SQL arbitrário) e `/admin/reset-db` sem autenticação | `app.py:47-57, 59-78` | Qualquer cliente lê, altera ou apaga o banco inteiro com uma requisição. |
| 1.3 | CRITICAL | `SECRET_KEY` hardcoded e devolvida pelo `/health` ✔ | `app.py:7`, `controllers.py:285-289` | O segredo fica versionado no git e é publicado por um endpoint público. |
| 1.4 | CRITICAL | Senhas em texto puro, retornadas pela API ✔ | `database.py:76-78`, `models.py:83, 99, 126-129` | `GET /usuarios/1` retorna `"senha": "admin123"`. |
| 1.5 | CRITICAL | God Module: dados, regras e formatação de 3 domínios | `models.py:1-314` | Nada é testável isoladamente, e qualquer mudança afeta tudo. |
| 1.6 | HIGH | `debug=True` com servidor exposto em `0.0.0.0` | `app.py:8, 88` | O debugger do Werkzeug exposto na rede permite execução remota de código. |
| 1.7 | HIGH | Conexão global mutável compartilhada entre threads; schema e seed dentro de `get_db()` | `database.py:4-10, 14-84` | Condições de corrida, e não dá para injetar outro banco em testes. |
| 1.8 | HIGH | Pedido sem transação nem validação de integridade ✔ | `models.py:133-169` | `quantidade: -5` gera total negativo e **aumenta** o estoque. Aceita usuário inexistente. |
| 1.9 | HIGH | Regra de negócio espalhada e acoplamento direto (sem DI) | `controllers.py:2-3, 52-54, 208-210, 242-250`, `models.py:256-262` | Não há um lugar único para cada regra, e testar exige banco real. |
| 1.10 | MEDIUM | Queries N+1 na listagem de pedidos | `models.py:171-201, 203-233` | São 1 + P + P·I queries por chamada. |
| 1.11 | MEDIUM | `except Exception` em cada função, vazando o erro interno ✔ | `controllers.py` (todas as funções) | O erro de sintaxe do SQLite chega ao cliente, e não há handler central. |
| 1.12 | MEDIUM | Validação ausente ou inconsistente entre criar e atualizar | `controllers.py:43-54 vs 81-90, 153-158, 169-170` | Entradas inválidas viram 500 ou dados corrompidos. |
| 1.13 | MEDIUM | Código duplicado (mapeamento de linhas, listagens de pedido) | `models.py:12-21/31-40/304-313, 171-201 vs 203-233` | As correções precisam ser replicadas, e as cópias já divergiram. |
| 1.14 | MEDIUM | CORS aberto para qualquer origem | `app.py:9` | Somado ao 1.2, qualquer site pode chamar os endpoints administrativos. |
| 1.15 | LOW | `print` como log, inclusive com email (PII) | `controllers.py:8, 57, 161, 179, 208-210, …` | Não há níveis de log, e dados pessoais vazam no log. |
| 1.16 | LOW | Magic numbers (faixas de desconto, limites, listas) | `models.py:257-262`, `controllers.py:47-52, 242` | Regras de negócio ficam escondidas em literais. |
| 1.17 | LOW | `id` sombreando o builtin, `cursor2`/`cursor3`, imports não usados | `controllers.py:14, 56, 64`, `models.py:2, 187-192`, `database.py:2` | Prejudica a leitura. |

**APIs deprecated:** nenhuma encontrada. Flask 3.1 e flask-cors 5 são usados com APIs atuais.

### Projeto 2 — ecommerce-api-legacy (LMS com checkout)

Uma única classe `AppManager` cria o banco, define schema e seed, registra as rotas e executa checkout, pagamento e relatórios em callbacks aninhados. `utils.js` concentra segredos, cache global e uma "criptografia" caseira.

| # | Severidade | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 2.1 | CRITICAL | Credenciais de produção hardcoded (banco, gateway `pk_live`, SMTP) | `src/utils.js:1-7` | Os segredos de produção ficam versionados no repositório. |
| 2.2 | CRITICAL | Número do cartão e chave do gateway escritos no log ✔ | `src/AppManager.js:45` | Viola o PCI-DSS e espalha a chave do gateway pelos logs. |
| 2.3 | CRITICAL | "Hash" de senha caseiro que colide; senhas padrão e em texto puro ✔ | `src/utils.js:17-23`, `src/AppManager.js:18, 68` | `senhaforte`, `senha123` e `sen` geram o mesmo valor, `c2c2c2c2c2`. |
| 2.4 | CRITICAL | Checkout não verifica a senha de um usuário existente; rotas admin abertas ✔ | `src/AppManager.js:73-75, 80, 131` | É possível comprar na conta de outra pessoa, ler o financeiro e apagar usuários. |
| 2.5 | CRITICAL | God Class `AppManager` | `src/AppManager.js:4-139` | Banco, rotas e regras no mesmo lugar, sem nenhuma camada. |
| 2.6 | HIGH | Matrícula, pagamento e auditoria sem transação | `src/AppManager.js:50-61` | Pode haver aluno matriculado sem pagamento registrado. |
| 2.7 | HIGH | Regra de pagamento no handler e acoplamento sem DI | `src/AppManager.js:7, 43-75`, `src/app.js:8-10` | Não dá para testar ou trocar o gateway ou o banco. |
| 2.8 | HIGH | Estado global mutável (cache sem limite, `totalRevenue` congelado) | `src/utils.js:9-15, 25` | Vazamento de memória e estado compartilhado entre requisições. |
| 2.9 | HIGH | DELETE de usuário deixa órfãos e sempre responde 200 ✔ | `src/AppManager.js:131-137` | O relatório passa a listar alunos "Unknown", e o ID 999 inexistente também recebe 200. |
| 2.10 | MEDIUM | N+1 no relatório financeiro, com ordem não determinística ✔ | `src/AppManager.js:83-127` | São 1 + C + 2·E queries, e a ordem da resposta muda a cada chamada. |
| 2.11 | MEDIUM | Callback hell e API legada de callbacks do `sqlite3` (deprecated) | `src/AppManager.js:1, 37-77, 83-128` | Até 6 níveis de aninhamento. O driver traz dependência deprecated (`@npmcli/move-file`). O moderno é `async/await` com Promises ou `node:sqlite`. |
| 2.12 | MEDIUM | Erros engolidos, texto puro como `text/html`, sem handler central ✔ | `src/AppManager.js:35-70, 92-93, 133-135` | Uma falha de query em `92-93` derruba o processo, e as respostas são inconsistentes. |
| 2.13 | MEDIUM | Validação ausente (email, cartão, tipos) ✔ | `src/AppManager.js:29-35, 46` | O cartão `"4"` é aprovado. |
| 2.14 | LOW | Magic numbers e strings (`"4"`, `"123456"`, `10000`, porta) | `src/AppManager.js:46, 68`, `src/utils.js:6, 19-22` | Regras escondidas e configuração fixa no código. |
| 2.15 | LOW | Nomes `u`/`e`/`p`/`cc`/`badCrypto` e configs nunca usadas | `src/AppManager.js:29-33`, `src/utils.js:2-5, 10` | Prejudica a leitura. |
| 2.16 | LOW | `console.log` como log | `src/utils.js:13`, `src/app.js:13` | Não há níveis nem mascaramento de dados. |

### Projeto 3 — task-manager-api (Task Manager)

Projeto **parcialmente organizado** (`models/`, `routes/`, `services/`, `utils/`), mas falta a camada de controllers. As rotas concentram validação, regras e queries, enquanto `services/`, a maior parte de `utils/` e os métodos de domínio dos models **não são usados**.

| # | Severidade | Problema | Arquivo:linha | Por que é relevante |
|---|---|---|---|---|
| 3.1 | CRITICAL | SECRET_KEY, senha SMTP e URI do banco hardcoded | `app.py:11, 13`, `services/notification_service.py:7-10` | Os segredos ficam versionados, sem configuração por ambiente. |
| 3.2 | CRITICAL | Senha com MD5 sem salt, e o hash é retornado pela API ✔ | `models/user.py:21, 29, 32`, `routes/user_routes.py:33, 85, 129, 209` | A resposta traz `md5("1234")`, que se reverte instantaneamente. |
| 3.3 | CRITICAL | Sem autenticação nem autorização; token falso; `role` aceito do body ✔ | `routes/user_routes.py:52, 71-72, 119-125, 210` | Um cliente anônimo cria um admin e promove outro usuário a admin. |
| 3.4 | HIGH | Rotas "gordas", sem controllers; camadas existentes abandonadas | `routes/task_routes.py:11-299`, `routes/report_routes.py:12-155` | A organização é só aparente, e as regras não são testáveis. |
| 3.5 | HIGH | App global sem factory; `create_all()` no import | `app.py:9-31`, `seed.py:2` | Não dá para testar com outro banco, e o import tem efeito colateral. |
| 3.6 | HIGH | `debug=True` com servidor exposto em `0.0.0.0` | `app.py:34` | O debugger do Werkzeug exposto na rede permite execução remota de código. |
| 3.7 | MEDIUM | N+1 em `/tasks`, `/users`, `/reports/summary` e `/categories` | `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:15-28, 53-68, 159-164` | `GET /tasks` faz 1 + 2N queries. |
| 3.8 | MEDIUM | **APIs deprecated:** `Query.get()` (16×) e `datetime.utcnow()` (22×) ✔ | `routes/*.py`, `models/*.py`, `seed.py` | O SQLAlchemy 2.1 emite `LegacyAPIWarning`. O moderno é `db.session.get()` e `datetime.now(timezone.utc)`. |
| 3.9 | MEDIUM | 12 `except:` genéricos, e erros de tipo viram 500 em HTML ✔ | `routes/*.py`, `utils/helpers.py:46, 49, 88` | `"priority": "alta"` derruba o `POST /tasks` com uma página HTML de erro. |
| 3.10 | MEDIUM | Regra de "overdue" copiada 6×, validações duplicadas e divergentes | `routes/task_routes.py:30-39, 71-80, 96-114 vs 166-184` (+ outras) | `Task.is_overdue()` existe e é ignorado. |
| 3.11 | MEDIUM | Validação ausente ou fraca (cor, body vazio, senha de 4 caracteres) | `routes/report_routes.py:180, 196-202`, `routes/user_routes.py:64, 102-103` | Dados inválidos chegam ao banco ou viram 500. |
| 3.12 | MEDIUM | CORS aberto | `app.py:15` | Somado ao 3.3, qualquer site pode operar a API. |
| 3.13 | LOW | Código morto: `NotificationService`, helpers, constantes e imports não usados | `services/`, `utils/helpers.py`, `app.py:7`, `routes/task_routes.py:7` | Dá a falsa impressão de que as regras estão centralizadas. |
| 3.14 | LOW | Magic numbers, apesar de as constantes existirem em `helpers.py:110-116` | `routes/task_routes.py:113, 182`, `routes/report_routes.py:24-28, 45, 129` | Mudar uma regra exige caçar literais. |
| 3.15 | LOW | `print` como log | `routes/task_routes.py:149, 153, 219, 234`, `routes/user_routes.py:83, 89, 147` | Sem observabilidade. |

### O que a análise ensinou para a skill

- **Padrões recorrentes nas 3 stacks:** segredos hardcoded, falta de autenticação, senha mal protegida, God Class ou rotas "gordas", N+1, error handling genérico, magic numbers e `print`/`console.log` como log. Esses padrões viram o núcleo do catálogo de anti-patterns.
- **A detecção precisa olhar comportamento, não só estrutura.** O projeto 3 "parece" organizado em pastas, mas as camadas não são usadas. A skill precisa verificar *quem chama quem*, não só se as pastas existem.
- **APIs deprecated dependem da versão instalada.** O `Query.get()` só emite warning porque o SQLAlchemy resolvido é o 2.x. A Fase 1 precisa ler as versões reais das dependências.
- **A refatoração precisa preservar contratos.** Os smoke tests de `scripts/` são a régua de validação da Fase 3. A única mudança aceita no contrato é a remoção de dados sensíveis das respostas.

---

## B) Construção da Skill

_Em construção (Tasks 6–11)._

## C) Resultados

_Em construção (Tasks 12–15)._

## D) Como Executar

_Em construção (Task 16)._
