# Refactor Projects Skill

Skill `refactor-arch` para Claude Code que analisa, audita e refatora projetos legados para o padrão MVC, independente da stack.

## Desafio

A descrição completa do desafio está em [DESAFIO.md](./DESAFIO.md).

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

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt": 3 fases, regras gerais, formatos de saída
└── references/
    ├── project-analysis.md               # Análise de projeto (Fase 1 + como subir a app)
    ├── anti-patterns-catalog.md          # Catálogo de anti-patterns (Fase 2 + re-auditoria)
    ├── audit-report-template.md          # Template do relatório (Fase 2)
    ├── mvc-guidelines.md                 # Guidelines da arquitetura MVC alvo (Fase 3)
    └── refactoring-playbook.md           # Playbook de transformações antes/depois (Fase 3)
```

| Área de conhecimento exigida | Arquivo | Conteúdo principal |
|---|---|---|
| Análise de projeto | `project-analysis.md` | Manifestos e imports de 7 linguagens e 10+ frameworks; versão **instalada** vs declarada; detecção de banco e tabelas; classificação Monolítica / Parcialmente em camadas / Em camadas; verificação de **uso real** das camadas; como subir e sondar a app (porta ocupada, banco com estado, `timeout` ausente no macOS) |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` | **22 anti-patterns** (CRITICAL 6 · HIGH 5 · MEDIUM 7 · LOW 4), cada um com sinais de detecção, `grep` testado, exemplo, impacto e padrão do playbook; tabelas de **APIs deprecated** "obsoleto → moderno" para Python/Flask/SQLAlchemy e Node/Express |
| Template de relatório | `audit-report-template.md` | Formato exato (IDs `F-xx`, `File:` com linhas, `Catalog`, `Verified`), seções fixas de Deprecated APIs e Architecture Notes, exemplo preenchido com projeto fictício e checklist antes de imprimir |
| Guidelines de arquitetura | `mvc-guidelines.md` | Responsabilidades e limites de cada camada, regras de dependência, estrutura de pastas por stack, como adaptar um monolito e um projeto parcialmente em camadas, **mudanças de contrato permitidas** |
| Playbook de refatoração | `refactoring-playbook.md` | **18 padrões** (PB-01…PB-18) com código antes/depois em Python e JavaScript, mais a ordem de aplicação com validação após cada grupo |

### Decisões de design

1. **O SKILL.md conduz o processo; as referências guardam o conhecimento.** O SKILL.md diz *o que fazer e quando*, e cada fase indica qual referência ler *naquele momento*. Isso mantém o prompt curto (~170 linhas) e deixa o conhecimento de domínio editável sem mexer no fluxo.
2. **Saídas com formato fixo.** Os banners e rótulos são copiados do exemplo do desafio (`PHASE 1: PROJECT ANALYSIS`, `ARCHITECTURE AUDIT REPORT`, `PHASE 3: REFACTORING COMPLETE`). O texto da skill está em português e os rótulos em inglês.
3. **Nada é escrito antes da confirmação.** As Fases 1 e 2 são somente leitura (podem subir a app original para testar, restaurando o estado depois). O relatório é salvo **depois** da resposta do usuário, no caminho passado como argumento (`/refactor-arch ../reports/audit-project-1.md`).
4. **Evidência, não suposição.** Todo achado precisa de `arquivo:linha` lido na execução. A Fase 2 confirma os achados de alto impacto com a app rodando (`Verified: yes (...)`).
5. **A skill captura a própria baseline.** A Fase 1 inventaria os endpoints e a Fase 3 grava o comportamento original antes de mexer no código. A validação compara status e formato das respostas com essa baseline, então a skill não depende de testes externos e pode ser copiada para qualquer projeto.
6. **Contrato preservado, com exceções explícitas.** Paths, métodos, status e formato das respostas não mudam, a não ser por **correções de segurança e integridade**: remover dados sensíveis, desligar endpoints de SQL arbitrário, bloquear escalada de privilégio e rejeitar entradas que corrompem dados. Cada exceção é listada em `## Contract changes`. Exigir login nas rotas hoje públicas ficou **fora do escopo**, porque quebraria os clientes, e é registrado como recomendação.
7. **Adaptação ao ponto de partida.** Um monolito é reestruturado por completo. Num projeto parcialmente em camadas, a skill reaproveita o que já está no lugar certo, cria a camada que falta e remove ou passa a usar o código que existe sem ser usado.
8. **A skill não faz commit.** O humano revisa as mudanças e commita.

### Anti-patterns do catálogo e por quê

Os 22 itens saíram da análise manual (seção A). Todo achado dos 3 projetos se encaixa em algum item, e cada item foi escrito de forma genérica, sem nomes de arquivos dos projetos.

| Severidade | Anti-patterns | Por que estão no catálogo |
|---|---|---|
| CRITICAL | AP-01 segredos hardcoded · AP-02 SQL Injection · AP-03 God Class · AP-04 senha insegura · AP-05 dados sensíveis em respostas/logs · AP-06 operação sensível sem autenticação | Apareceram nos 3 projetos (AP-01, AP-04, AP-05) ou são os de maior dano (bypass de login, SQL arbitrário, escalada para admin). O desafio exige credenciais, SQLi e God Class como CRITICAL |
| HIGH | AP-07 debug em produção · AP-08 fat controller / camadas abandonadas · AP-09 estado global · AP-10 acoplamento sem DI · AP-11 sem transação/integridade | São as violações de MVC/SOLID da definição de HIGH. AP-08 inclui o sinal "camadas que existem mas não são usadas", para pegar projetos que parecem organizados |
| MEDIUM | AP-12 N+1 · **AP-13 APIs deprecated** · AP-14 error handling genérico · AP-15 validação · AP-16 duplicação · AP-17 callback hell · AP-18 CORS aberto | Problemas de padronização e performance da definição de MEDIUM. AP-13 é obrigatório no desafio e traz tabelas por stack, considerando a **versão instalada** |
| LOW | AP-19 magic numbers · AP-20 nomenclatura · AP-21 `print` como log · AP-22 código morto | Legibilidade, presente nos 3 projetos |

### Como a skill é agnóstica de tecnologia

- **Detecção por evidência:** linguagem e framework saem do manifesto e dos imports, nunca do nome da pasta. A referência cobre Python, JS/TS, Go, Java/Kotlin, Ruby, PHP e C#.
- **Sinais de detecção por conceito**, com variantes por stack: por exemplo, "query montada com `+`/f-string/template literal" e "callback com `err` ignorado".
- **Layouts alvo por stack** (Flask, Express, mais referências para Django, FastAPI, NestJS e Spring) e exemplos antes/depois em Python **e** JavaScript no playbook.
- **Nenhum caminho dos projetos no SKILL.md.** A mesma pasta foi copiada sem alteração para os 3 projetos (`diff -r` idêntico).

### Desafios encontrados e como foram resolvidos

| Desafio | Solução |
|---|---|
| A porta 5000 está ocupada pelo AirPlay no macOS e o `python app.py` original falha | A referência ensina a detectar o problema (`lsof`) e a subir com `flask run --port` **sem alterar código** nas Fases 1–2. A skill detectou o bloqueio sozinha no P1 e no P3 |
| "Preservar contrato" impediria corrigir `/admin/query` (SQL arbitrário) | Defini uma lista fechada de mudanças de contrato permitidas para segurança e integridade, que precisam ser declaradas no resumo |
| Os `grep` do catálogo falhavam no zsh (`--include=*.py` sem aspas → *no matches found*) | Coloquei aspas em todos os comandos e testei cada um nos 3 projetos. Também corrigi o regex de segredos, que não pegava `config["KEY"] = "..."`, e criei um padrão para SQL concatenado em várias linhas |
| Falso positivo no P3: a skill reportou "categoria apagada deixa órfãos", mas o SQLAlchemy já anula a FK | A própria skill percebeu na Fase 3, pela baseline. Na iteração (Task 15), acrescentei ao catálogo um bloco "Não é órfão" que exige confirmação dinâmica com ORM, e formalizei como marcar falsos positivos no relatório |
| A skill atualizou o `sqlite3` de 5 para 6 no P2, o que exige Node ≥ 20.17 | Regra nova no SKILL.md: atualizar para nova versão major só para corrigir um achado, conferindo o runtime e declarando o requisito no manifesto |
| Express 4 não captura erros de handlers async | O playbook (PB-12) traz o `asyncHandler`, que a skill usou no P2 |

> Os relatórios `reports/audit-project-{1,2,3}.md` foram gerados com a versão da skill anterior aos ajustes da Task 15. Para comprovar os ajustes, **reexecutei as Fases 1–2 da versão final sobre o código original do P3** (git worktree no commit `12a317f`, respondendo `n` na confirmação): [`reports/audit-project-3-rerun.md`](reports/audit-project-3-rerun.md). Resultado: **18 achados, sem o falso positivo**. A skill testou o `DELETE /categories` com a app rodando e registrou que "não deixa órfãos (o SQLAlchemy fez `SET NULL`)". Os outros 18 achados válidos continuam lá, nenhum arquivo foi modificado, e o `datetime.utcnow()` deixou de ser contado como deprecated porque o Python instalado é o 3.11, enquanto a depreciação vale a partir do 3.12 (a regra de "versão instalada" do catálogo).

---

## C) Resultados

### Resumo das auditorias (Fase 2)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Análise manual | Deprecated |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| [code-smells-project](reports/audit-project-1.md) | 7 | 4 | 5 | 4 | **20** | 17 (todos cobertos) | Nenhuma nas versões instaladas (verificado com warnings ligados) |
| [ecommerce-api-legacy](reports/audit-project-2.md) | 5 | 6 | 5 | 4 | **20** | 16 (todos cobertos + 1 novo) | API de callbacks do `sqlite3` + 7 dependências transitivas deprecated |
| [task-manager-api](reports/audit-project-3.md) | 4 | 4¹ | 7 | 4 | **19** | 15 (todos cobertos) | `Query.get()` (16×, `LegacyAPIWarning`), Query API legada, `datetime.utcnow()` |

¹ Inclui o F-07, falso positivo corrigido pela própria skill na Fase 3 (18 achados válidos). A [reexecução com a versão final da skill](reports/audit-project-3-rerun.md) chegou a 4 · 3 · 7 · 4 = **18**, sem o falso positivo.

**Achado que a skill encontrou e a análise manual não:** no P2, `POST /api/checkout` com `"card": 4111` (número em vez de string) lança `TypeError` dentro de um callback e **derruba o processo**, um DoS sem autenticação.

Saídas completas de cada fase: `reports/analysis-project-N.md` (Fase 1), `reports/audit-project-N.md` (Fase 2) e `reports/refactor-project-N.md` (Fase 3).

### Estrutura antes × depois

**Projeto 1 — code-smells-project** (monolito → MVC completo)

```
ANTES                                DEPOIS
app.py          (88)                 app.py                      # entry point fino → create_app()
controllers.py  (292)                .env.example
models.py       (314)                src/
database.py     (86)                 ├── app.py                  # composition root
                                     ├── config/settings.py
                                     ├── database/{connection,schema}.py
                                     ├── models/{produto,usuario,pedido}_model.py
                                     ├── controllers/{produto,usuario,pedido,relatorio,health,admin}_controller.py
                                     ├── views/{produto,usuario,pedido,relatorio,system,admin}_routes.py + serializers.py
                                     ├── middlewares/{error_handler,auth}.py
                                     ├── services/notification_service.py
                                     └── utils/{constants,errors,validators}.py
```

**Projeto 2 — ecommerce-api-legacy** (God Class → MVC completo)

```
ANTES                                DEPOIS
src/app.js         (14)              src/app.js                  # entry point → buildApp() + listen
src/AppManager.js  (141)             src/server.js               # composition root
src/utils.js       (25)              src/config/index.js
                                     src/database/connection.js  # wrapper Promise + transaction()
                                     src/models/{user,course,enrollment,report}Model.js
                                     src/controllers/{checkout,report,user}Controller.js
                                     src/routes/{checkout,admin,user}Routes.js
                                     src/services/paymentService.js
                                     src/middlewares/{errorHandler,adminGuard}.js
                                     src/utils/{constants,errors,crypto,logger,validators}.js
                                     .env.example
```

**Projeto 3 — task-manager-api** (parcialmente em camadas → MVC, reaproveitando o existente)

```
ANTES                                DEPOIS
app.py                               app.py                      # create_app() (antes: app global + create_all no import)
database.py                          database.py                 # + transaction()
seed.py                              seed.py                     # usa a factory
models/{task,user,category}.py       models/{task,user,category}.py   # mantidos: + regras de domínio, sem password, sem N+1
routes/task_routes.py   (299)        routes/task_routes.py  (46) # só HTTP
routes/user_routes.py   (211)        routes/user_routes.py
routes/report_routes.py (223)        routes/report_routes.py + category_routes.py + system_routes.py + serializers.py
services/notification_service.py ✗   controllers/{task,user,category,report}_controller.py   # camada criada
utils/helpers.py                 ✗   config/settings.py
                                     middlewares/error_handler.py
                                     utils/{constants,errors,validators,dates}.py
                                     .env.example
(✗ = código morto removido)
```

### Validação independente

Além da validação feita pela própria skill, validei cada projeto por fora com os smoke tests de [`scripts/`](scripts) e com a [baseline](docs/baseline-endpoints.md) capturada antes da refatoração:

| Verificação | P1 | P2 | P3 |
|---|---|---|---|
| Boot sem erros / sem warnings de deprecated | ✅ | ✅ (`--trace-deprecation`) | ✅ (`PYTHONWARNINGS=always`) |
| Smoke test | ✅ 25/25¹ | ✅ 7/7 | ✅ 26/26 |
| Formato das respostas igual à baseline | 20/25 (5 = mudanças aprovadas) | 6/7 (1 = texto do DELETE) | 22/26 (4 = `password` removido) + valores de leitura idênticos |
| Ataques da análise manual bloqueados | SQLi no login → 401; quantidade negativa → 400 | compra em nome de terceiro → 401; `card` numérico → 400 sem derrubar o processo | criar admin anônimo → `role: user`; `priority: "alta"` → 400 JSON |
| Greps do catálogo no código novo | 0 SQL concatenado, 0 `print`, 0 segredos | 0 SQL concatenado, 0 `console.*` fora do logger | 0 `Query.get`, 0 `utcnow`, 0 `except:` |

¹ Script ajustado só nos 2 endpoints admin (`/admin/query` removido, `/admin/reset-db` desligado por padrão), mudanças de contrato aprovadas.

**Logs das aplicações rodando após a refatoração:** [`docs/logs/project-1-run.log`](docs/logs/project-1-run.log), [`project-2-run.log`](docs/logs/project-2-run.log) e [`project-3-run.log`](docs/logs/project-3-run.log). Cada log traz o boot e a saída do smoke test.

### Checklist de validação

| Fase | Item | P1 | P2 | P3 |
|---|---|:-:|:-:|:-:|
| 1 | Linguagem detectada corretamente | ✅ | ✅ | ✅ |
| 1 | Framework detectado corretamente | ✅ | ✅ | ✅ |
| 1 | Domínio da aplicação descrito corretamente | ✅ | ✅ | ✅ |
| 1 | Número de arquivos analisados condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| 2 | Relatório segue o template definido nos arquivos de referência | ✅ | ✅ | ✅ |
| 2 | Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| 2 | Findings ordenados por severidade (CRITICAL → LOW) | ✅ | ✅ | ✅ |
| 2 | Mínimo de 5 findings identificados | ✅ 20 | ✅ 20 | ✅ 19 |
| 2 | Detecção de APIs deprecated incluída (se aplicável) | ✅ (nenhuma) | ✅ | ✅ |
| 2 | Skill pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| 3 | Estrutura de diretórios segue padrão MVC | ✅ | ✅ | ✅ |
| 3 | Configuração extraída para módulo de config (sem hardcoded) | ✅ | ✅ | ✅ |
| 3 | Models criados para abstrair dados | ✅ | ✅ | ✅ |
| 3 | Views/Routes separadas para visualização ou roteamento | ✅ | ✅ | ✅ |
| 3 | Controllers concentram o fluxo da aplicação | ✅ | ✅ | ✅ |
| 3 | Error handling centralizado | ✅ | ✅ | ✅ |
| 3 | Entry point claro | ✅ | ✅ | ✅ |
| 3 | Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| 3 | Endpoints originais respondem corretamente | ✅ | ✅ | ✅ |

**Critérios de aceite:** Fase 1 detecta a stack (3/3) · Fase 2 com ≥ 5 findings (3/3) · Fase 2 com ≥ 1 CRITICAL/HIGH (3/3) · aplicação funciona após a refatoração (3/3).

### Observações sobre o comportamento em stacks diferentes

- **Python/Flask monolítico (P1):** a skill separou os domínios pelas tabelas e foi a única execução que precisou de um guarda de admin (`ENABLE_ADMIN_ENDPOINTS` + `X-Admin-Token`). Converteu as senhas em texto puro de bancos antigos no boot.
- **Node/Express (P2):** a skill teve o cuidado de **manter as respostas de erro em texto puro**, como na baseline, e os nomes de campo do body (`usr`, `eml`, `c_id`), renomeando só os identificadores internos. O ponto mais delicado foi a concorrência numa conexão SQLite única: a skill encontrou uma leitura suja nos próprios testes e serializou as transações. Também foi a única execução que atualizou uma dependência para nova versão major (`sqlite3` 5 → 6). No P3 houve só remoção de dependências não usadas e o pin do SQLAlchemy.
- **Python/Flask parcialmente em camadas (P3):** a skill **não reescreveu** o projeto. Manteve os models e as rotas, criou a camada de controllers, passou a usar os métodos de domínio que eram ignorados e apagou só o código morto. Os valores das respostas de leitura ficaram idênticos aos originais. Foi a execução com o falso positivo, o que motivou o ajuste do catálogo.
- **Em todas:** a pausa da Fase 2 foi respeitada, os ataques reproduzidos na análise manual foram confirmados dinamicamente na Fase 2 e bloqueados na Fase 3, e as limitações que exigiriam decisão de produto (autenticação obrigatória, token real) ficaram como recomendação, sem quebrar clientes.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude` no PATH)
- Python 3.11+ (projetos 1 e 3)
- Node.js ≥ 20.17 (projeto 2, por causa do `sqlite3` 6.x usado após a refatoração)
- `curl` (validação)

> **macOS:** a porta 5000 costuma estar ocupada pelo AirPlay Receiver. Use `PORT=5001`/`5002` como nos exemplos abaixo, ou desative o AirPlay Receiver em Ajustes do Sistema.

### Executar a skill

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto. O argumento opcional é o caminho onde o relatório da Fase 2 será salvo (padrão: `reports/audit-report.md` dentro do projeto).

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch ../reports/audit-project-1.md"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch ../reports/audit-project-2.md"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch ../reports/audit-project-3.md"
```

Em cada execução, a skill imprime a Fase 1, imprime o relatório da Fase 2 e **para** em `Proceed with refactoring (Phase 3)? [y/n]`. Revise o relatório e responda `y` para refatorar. No fim, ela imprime `PHASE 3: REFACTORING COMPLETE` com o checklist de validação.

> Para rodar a skill de novo sobre o código **original**, use um commit anterior à refatoração (por exemplo, `git worktree add /tmp/p3-original 12a317f`). Este repositório já contém o código refatorado.

### Validar a refatoração

Suba cada projeto refatorado e rode o smoke test correspondente, a partir da raiz do repositório:

```bash
# Projeto 1 — o banco é recriado com seed no primeiro boot
cd code-smells-project && python -m venv .venv && .venv/bin/pip install -r requirements.txt
rm -f loja.db && PORT=5001 .venv/bin/python app.py &
cd .. && BASE_URL=http://localhost:5001 ./scripts/smoke-test-project-1.sh      # esperado: 25 passed

# Projeto 2 — banco em memória, seed no boot
cd ecommerce-api-legacy && npm install && npm start &
cd .. && BASE_URL=http://localhost:3000 ./scripts/smoke-test-project-2.sh      # esperado: 7 passed

# Projeto 3 — rode o seed antes do boot
cd task-manager-api && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py && PORT=5002 .venv/bin/python app.py &
cd .. && BASE_URL=http://localhost:5002 ./scripts/smoke-test-project-3.sh      # esperado: 26 passed
```

Para comparar o corpo das respostas com o comportamento original, rode o smoke test com `OUT_DIR=<pasta>` e compare com [`scripts/baseline/project-N/`](scripts/baseline). As diferenças esperadas estão em `## Contract changes` de cada `reports/refactor-project-N.md`.

Cada projeto também tem `.env.example` com as variáveis opcionais (`SECRET_KEY`, `PORT`, `CORS_ORIGINS`, `LOG_LEVEL`...).
