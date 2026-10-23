# Catálogo de Anti-patterns

Referência da **Fase 2** (auditoria) e da **re-auditoria da Fase 3**. Cada entrada traz a severidade padrão, os **sinais de detecção** (o que procurar, inclusive com grep), um exemplo curto, o impacto e o padrão de correção no [playbook](refactoring-playbook.md).

## Como usar

1. Para cada arquivo-fonte, percorra **todas** as entradas. Os comandos `grep` servem para achar candidatos; **confirme lendo o código** antes de registrar. Rode-os a partir da raiz do projeto, acrescentando `--exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv`, e mantenha as aspas em `--include="*.py"` (sem elas o zsh expande o glob e o comando falha). No zsh, variáveis **não** são divididas em palavras: `F="a b"; grep x $F` procura um arquivo chamado `a b`. Escreva os caminhos direto no comando, ou use `--include`.
2. **Quando não der para ter certeza pela leitura** (comportamento implícito de ORM/framework, cascatas, defaults de serialização), confirme com a app rodando antes de registrar, ou deixe de fora. Um falso positivo custa trabalho na Fase 3 e tira a credibilidade do relatório.
3. Registre o `arquivo:linha` exato de cada ocorrência. Agrupe ocorrências do mesmo anti-pattern em um único achado.
4. **Ajuste de severidade:** a severidade da tabela é o padrão. Suba um nível quando a ocorrência for explorável sem autenticação ou afetar dinheiro/dados pessoais; desça um nível quando o código for morto ou inalcançável. Justifique o ajuste na descrição.
5. Os sinais estão escritos para Python e JavaScript/TypeScript; traduza-os para o idioma da stack detectada (Go, Java, Ruby, PHP...).

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis ou violam completamente a separação de responsabilidades |
| **HIGH** | Fortes violações de MVC/SOLID que dificultam muito manutenção e testes: regra de negócio no controller/rota, acoplamento sem DI, estado global mutável |
| **MEDIUM** | Padronização, duplicação, performance moderada (N+1), middlewares inadequados, validação ausente, APIs deprecated |
| **LOW** | Legibilidade, nomenclatura, magic numbers, logs com `print` |

## Índice

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP-01 | Credenciais e segredos hardcoded | CRITICAL | PB-01 |
| AP-02 | SQL Injection | CRITICAL | PB-02 |
| AP-03 | God Class / God File | CRITICAL | PB-03 |
| AP-04 | Armazenamento inseguro de senhas | CRITICAL | PB-04 |
| AP-05 | Exposição de dados sensíveis (respostas e logs) | CRITICAL | PB-05 |
| AP-06 | Operações sensíveis sem autenticação/autorização | CRITICAL | PB-06 |
| AP-07 | Modo debug / configuração de desenvolvimento em produção | HIGH | PB-01 |
| AP-08 | Regra de negócio na rota/controller (*fat controller*) | HIGH | PB-07 |
| AP-09 | Estado global mutável | HIGH | PB-08 |
| AP-10 | Acoplamento forte sem injeção de dependência | HIGH | PB-08 |
| AP-11 | Operação multi-etapa sem transação / sem integridade referencial | HIGH | PB-09 |
| AP-12 | Queries N+1 | MEDIUM | PB-10 |
| AP-13 | Uso de API deprecated | MEDIUM | PB-11 |
| AP-14 | Tratamento de erro genérico / ausência de handler central | MEDIUM | PB-12 |
| AP-15 | Validação de entrada ausente ou inconsistente | MEDIUM | PB-13 |
| AP-16 | Código duplicado | MEDIUM | PB-14 |
| AP-17 | Callback hell | MEDIUM | PB-15 |
| AP-18 | CORS permissivo | MEDIUM | PB-01 |
| AP-19 | Magic numbers e strings | LOW | PB-16 |
| AP-20 | Nomenclatura ruim | LOW | PB-17 |
| AP-21 | `print` / `console.log` como mecanismo de log | LOW | PB-18 |
| AP-22 | Código morto e imports não usados | LOW | PB-17 |

---

## CRITICAL

### AP-01 — Credenciais e segredos hardcoded

**Severidade:** CRITICAL · **Playbook:** PB-01

**Sinais de detecção:**
- Atribuição literal a chaves de configuração sensíveis: `SECRET_KEY`, `password`, `pass`, `pwd`, `token`, `api_key`, `apiKey`, `secret`, `private_key`, `dbPass`, `smtp`, `gateway`.
- Strings com cara de segredo: prefixos `sk_`, `pk_live_`, `AKIA`, `ghp_`, JWTs (`eyJ...`), URIs com usuário e senha (`postgres://user:pass@`).
- Objetos/dicionários `config` com segredos inline, e construtores de serviço que recebem a senha literal (ex.: `self.email_password = '...'`).
- Ausência de `os.environ` / `os.getenv` / `process.env` para esses valores.

```bash
grep -rnE "(SECRET|PASS|PWD|TOKEN|API_?KEY|PRIVATE|GATEWAY|SMTP)[A-Z_]*['\"]?\]?\s*[:=]\s*['\"][^'\"]+['\"]" -i --include="*.py" --include="*.js" --include="*.ts" .
grep -rnE "pk_live_|sk_live_|AKIA[0-9A-Z]{16}|://[^/ ]+:[^@ ]+@" .
```

**Exemplo:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_..." };
```

**Impacto:** o segredo fica versionado no git e se espalha a cada clone, sem rotação possível e sem configuração por ambiente.
**Recomendação:** mova para variáveis de ambiente lidas por um módulo de config, com `.env.example` sem valores reais.

---

### AP-02 — SQL Injection

**Severidade:** CRITICAL · **Playbook:** PB-02

**Sinais de detecção:**
- Uma string de SQL (`SELECT|INSERT|UPDATE|DELETE|WHERE`) montada com `+`, f-string, `%`, `.format()` ou template literal `${}` contendo uma variável vinda de request ou de parâmetro de função.
- `cursor.execute(query)` / `db.run(query)` / `db.query(query)` onde `query` foi concatenada antes, por exemplo em filtros dinâmicos (`query += " AND campo = '" + valor + "'"`).
- Endpoint que executa SQL recebido do cliente (`cursor.execute(request.json["sql"])`), o caso extremo (veja também AP-06).
- `LIKE '%" + termo + "%'`.

```bash
grep -rnE "(execute|run|all|get|query)\s*\(\s*f?['\"].*(SELECT|INSERT|UPDATE|DELETE).*['\"]\s*\+" -i .
grep -rnE "f['\"].*(SELECT|INSERT|UPDATE|DELETE).*\{" -i --include="*.py" .
grep -rnE "\`.*(SELECT|INSERT|UPDATE|DELETE).*\\$\{" -i --include="*.js" --include="*.ts" .
# Concatenação quebrada em várias linhas: fragmentos de string colados a variáveis com "+"
grep -rnE "['\"]\s*\+\s*(str\()?[A-Za-z_]|[A-Za-z_)\]]\s*\+\s*['\"]\s*(,|\)|AND|OR|WHERE|'|$)" --include="*.py" --include="*.js" --include="*.ts" .
```
Os dois últimos padrões trazem falsos positivos (concatenação de mensagens); considere só os que estão dentro de um `execute`/`run`/`query` ou de uma variável de query.

**Não é injeção:** placeholders (`?`, `%s`, `:nome`, `$1`) com os valores passados separadamente, e métodos de ORM (`filter_by`, `.like(f'%{q}%')` do SQLAlchemy, porque o valor vira um bind param).

**Exemplo:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

**Impacto:** bypass de login (`' --`), leitura e alteração arbitrária do banco. Também quebra entradas legítimas que contêm apóstrofo.
**Recomendação:** use queries parametrizadas sempre. Para filtros dinâmicos, monte a lista de condições com placeholders e a lista de parâmetros em paralelo.

---

### AP-03 — God Class / God File

**Severidade:** CRITICAL · **Playbook:** PB-03

**Sinais de detecção:**
- Um arquivo/classe com **3 ou mais responsabilidades** (veja `project-analysis.md` §6.2): rotas + SQL + regra de negócio + config/seed.
- Funções de **vários domínios** (produtos, pedidos, usuários) no mesmo módulo de "models" ou "manager".
- Uma classe que abre a conexão, cria o schema, insere o seed **e** registra as rotas (`initDb()` + `setupRoutes(app)`).
- Arquivos acima de ~300 linhas misturando camadas, ou um único método acima de ~50 linhas com SQL e regras.
- Nomes genéricos: `AppManager`, `Utils`, `Helper`, `Manager`, `models.py` sem pacote.

**Exemplo:** `models.py` com 314 linhas contendo SQL, cálculo de desconto, baixa de estoque e formatação para produtos, usuários e pedidos.

**Impacto:** é impossível testar algo isoladamente, qualquer mudança afeta tudo e há conflito constante entre quem mexe no código.
**Recomendação:** separe por camada (model / controller / route) **e** por domínio (`produto_model`, `pedido_controller`...).

---

### AP-04 — Armazenamento inseguro de senhas

**Severidade:** CRITICAL · **Playbook:** PB-04

**Sinais de detecção:**
- A senha é gravada como veio do request (`INSERT ... senha` com o valor cru) e comparada em texto puro (`WHERE senha = ?`, `user.pass === pwd`).
- Hash rápido sem salt: `hashlib.md5`, `hashlib.sha1`, `hashlib.sha256(pwd)` puro, `crypto.createHash('md5'|'sha1')`.
- "Criptografia" caseira: base64, inversão, loops que concatenam substrings (`badCrypto`), XOR.
- Senhas padrão (`pwd || "123456"`) e seeds com senha em texto puro.
- Comparação de hash com `==` (timing attack) em vez de `hmac.compare_digest` / `crypto.timingSafeEqual`.

```bash
grep -rnE "md5|sha1|createHash\(|base64|b64encode|btoa\(" --include="*.py" --include="*.js" --include="*.ts" .
grep -rnE "senha|password|pass|pwd" --include="*.py" --include="*.js" . | grep -iE "insert|==|===|where"
```

**Impacto:** um vazamento do banco expõe todas as senhas (MD5 se reverte com rainbow tables em segundos), e um hash caseiro gera colisões.
**Recomendação:** use um KDF lento com salt: `werkzeug.security.generate_password_hash` (scrypt/pbkdf2), `hashlib.scrypt`, `crypto.scrypt`, bcrypt ou argon2. Verifique em tempo constante.

---

### AP-05 — Exposição de dados sensíveis (respostas e logs)

**Severidade:** CRITICAL · **Playbook:** PB-05

**Sinais de detecção:**
- `to_dict()` / serializadores / `SELECT *` mapeados direto para a resposta incluindo `password`, `senha`, `pass`, `hash`, `token`, `secret`.
- Endpoints de health/debug/info que retornam `secret_key`, `db_path`, `debug`, variáveis de ambiente ou stack traces.
- Logs (`print`, `console.log`, `logger.info`) com número de cartão, CVV, senha, token, chave de API ou PII (email, CPF) sem mascaramento.
- Mensagens de erro que devolvem `str(e)` com detalhes internos (veja também AP-14).

```bash
grep -rnE "['\"](password|senha|pass|secret_key|token)['\"]\s*:" --include="*.py" --include="*.js" .
grep -rnE "(print|console\.log|logger\.\w+)\(.*(card|cartao|cc|cvv|senha|password|token|key)" -i .
```

**Impacto:** hashes e segredos ficam acessíveis a qualquer cliente da API, e dados de cartão nos logs violam o PCI-DSS.
**Recomendação:** use serialização por **lista branca** de campos, mascare dados sensíveis nos logs e retire segredos e configuração dos endpoints públicos. *É uma mudança de contrato permitida (veja `mvc-guidelines.md` §5); liste-a no resumo da Fase 3.*

---

### AP-06 — Operações sensíveis sem autenticação/autorização

**Severidade:** CRITICAL · **Playbook:** PB-06

**Sinais de detecção:**
- Rotas administrativas ou destrutivas (`/admin/*`, `reset`, `DELETE /users/:id`, relatórios financeiros) sem nenhum decorator/middleware de autenticação.
- Endpoint que executa SQL ou código vindo do cliente (`/admin/query`, `eval`, `exec`).
- *Mass assignment* de privilégio: `role`, `is_admin`, `active`, `tipo` aceitos direto do body na criação/edição.
- Token falso ou previsível (`'fake-jwt-token-' + id`) e verificações como `is_admin()` que existem mas nunca são chamadas.
- Fluxo que age em nome de um usuário existente identificado só pelo email, sem verificar a senha (ex.: checkout).

```bash
grep -rnE "route\(['\"]/admin|['\"]/api/admin|reset|/query" --include="*.py" --include="*.js" .
grep -rnE "get\(['\"](role|is_admin|tipo|active)['\"]|body\.(role|isAdmin)" --include="*.py" --include="*.js" .
```

**Impacto:** qualquer pessoa pode destruir dados, ler informações financeiras, virar administrador ou comprar em nome de terceiros.
**Recomendação:** remova os endpoints que executam SQL/código arbitrário, proteja as rotas administrativas, ignore campos de privilégio vindos do body e verifique as credenciais antes de agir em nome de alguém.

---

## HIGH

### AP-07 — Modo debug / configuração de desenvolvimento em produção

**Severidade:** HIGH · **Playbook:** PB-01

**Sinais de detecção:**
- `debug=True`, `app.config["DEBUG"] = True`, `app.run(debug=True, host="0.0.0.0")`.
- `sqlite3.verbose()`, `NODE_ENV` ignorado, `ENV = "production"` declarado junto com debug ligado.
- Porta, host e URI de banco fixos no código.

```bash
grep -rnE "debug\s*=\s*True|DEBUG['\"]?\]?\s*=\s*True|\.verbose\(\)|host\s*=\s*['\"]0\.0\.0\.0" .
```

**Impacto:** o debugger do Werkzeug exposto na rede permite **execução remota de código**, mostra stack traces ao cliente e impede a configuração por ambiente.
**Recomendação:** debug, host e porta passam a vir de env/config, com debug desligado por padrão.

---

### AP-08 — Regra de negócio na rota/controller (*fat controller*)

**Severidade:** HIGH · **Playbook:** PB-07

**Sinais de detecção:**
- Handlers de rota com mais de ~30 linhas, ou que fazem **ao mesmo tempo** parsing do request, validação de domínio, queries/ORM, cálculos e montagem da resposta.
- Decisões de negócio dentro do handler: aprovação de pagamento (`card.startsWith("4")`), transições de status, cálculos de desconto, cascatas de exclusão, "notificações" com `print`.
- Regras de negócio dentro do *model* de acesso a dados, misturadas com SQL (faixas de desconto no meio das queries).
- **Camadas abandonadas:** `services/`, `helpers/` ou métodos de domínio (`is_overdue()`, `validate_status()`) que existem mas não são chamados, enquanto a mesma lógica está copiada nas rotas.

**Impacto:** não há um lugar único para cada regra, testar exige HTTP e banco, e as regras divergem entre as rotas.
**Recomendação:** as rotas só traduzem HTTP ↔ controller, o controller orquestra a regra de negócio e o model só acessa dados. Reaproveite e ligue as camadas existentes.

---

### AP-09 — Estado global mutável

**Severidade:** HIGH · **Playbook:** PB-08

**Sinais de detecção:**
- Uma conexão de banco em variável global de módulo (`db_connection = None` + `global db_connection`), especialmente com `check_same_thread=False`.
- Caches/contadores globais (`let globalCache = {}`, `let totalRevenue = 0`) modificados por requisições, sem limite de tamanho.
- Listas em atributo de instância singleton que acumulam dados (`self.notifications.append`).
- Exportação de primitivos mutáveis (`module.exports = { totalRevenue }`, que exporta uma cópia congelada).

```bash
grep -rnE "^\s*global\s+\w+|^(let|var)\s+\w+\s*=\s*(\{\}|\[\]|0)" --include="*.py" --include="*.js" .
```

**Impacto:** condições de corrida, vazamento de memória, testes que interferem entre si e comportamento diferente com várias instâncias.
**Recomendação:** crie a conexão por requisição ou por *app context*, ou injete-a. Cache só com escopo e limite definidos, ou removido se não for usado.

---

### AP-10 — Acoplamento forte sem injeção de dependência

**Severidade:** HIGH · **Playbook:** PB-08

**Sinais de detecção:**
- Controllers/handlers que importam e chamam diretamente o módulo do banco (`from database import get_db`) ou instanciam dependências (`new sqlite3.Database(...)`, `NotificationService()`) dentro do código de negócio.
- A aplicação é criada no nível do módulo (`app = Flask(__name__)`) **sem app factory**, com config fixa e efeitos colaterais no import (`db.create_all()`, seed, conexão).
- Scripts auxiliares (seed, CLI) que importam a app global.
- Não há composition root: as dependências não são montadas num único ponto de entrada.

**Impacto:** não é possível substituir o banco ou um serviço em testes, e importar um módulo já altera o banco.
**Recomendação:** use uma app factory (`create_app(config)`) ou uma função `buildApp(deps)` como composition root, e passe as dependências por parâmetro ou construtor.

---

### AP-11 — Operação multi-etapa sem transação / sem integridade referencial

**Severidade:** HIGH · **Playbook:** PB-09

**Sinais de detecção:**
- Uma sequência de `INSERT`/`UPDATE` relacionados (pedido + itens + estoque; matrícula + pagamento + auditoria) sem `BEGIN`/`COMMIT`/`ROLLBACK`, `with conn:`, `session.begin()` ou `db.serialize` + transação.
- Retorno antecipado (`return {"erro": ...}`) ou erro no meio do fluxo depois de escritas já feitas.
- Estoque/saldo validado num passo e decrementado em outro, sem condição atômica (`UPDATE ... SET estoque = estoque - ? WHERE estoque >= ?`).
- `DELETE` de uma entidade pai sem tratar os filhos (sem `FOREIGN KEY ... ON DELETE`, sem cascade), com o erro ignorado e sucesso sempre retornado.
- Quantidades/valores negativos aceitos em operações financeiras ou de estoque.
- FK lógica (ex.: `usuario_id`) aceita sem verificar se o registro existe.

**Não é órfão (evite falso positivo):** com ORM, a exclusão do pai pode já tratar os filhos. No SQLAlchemy, um `relationship`/`backref` sem `cascade="all, delete-orphan"` faz `UPDATE filho SET fk = NULL` ao apagar o pai pela sessão (`db.session.delete(pai)`), então não sobra referência quebrada. Comportamento equivalente aparece em `onDelete: 'SET NULL'` (Sequelize/TypeORM) e em `ON DELETE CASCADE/SET NULL` com FKs ativas. **Antes de reportar órfãos num projeto com ORM, confirme dinamicamente**: apague um pai com filhos na app original e consulte um filho. Só registre o achado se a FK continuar apontando para o registro removido. Exclusão via SQL puro (`DELETE FROM ...` / `query.delete()` em massa) ignora esse comportamento e continua sendo achado.

**Impacto:** dados financeiros e de estoque inconsistentes, registros órfãos e relatórios corrompidos.
**Recomendação:** use uma transação única por caso de uso, com rollback em qualquer falha, verifique existência e limites antes de escrever e trate os filhos na exclusão.

---

## MEDIUM

### AP-12 — Queries N+1

**Severidade:** MEDIUM · **Playbook:** PB-10

**Sinais de detecção:**
- Uma query (ou chamada de ORM que dispara query) **dentro de um loop** sobre o resultado de outra query: `for row in rows: cursor.execute(...)`, `courses.forEach(c => db.all(...))`.
- No ORM: `Model.query.get(x.fk_id)` dentro do loop, acesso a relacionamento lazy (`len(u.tasks)`, `t.user.name`) para cada item, `.count()` por item.
- Vários `COUNT(*)` separados que poderiam ser um único `GROUP BY`.
- Cursores numerados (`cursor2`, `cursor3`) são um indício forte.

**Impacto:** o número de queries cresce com o volume (1 + N, ou 1 + N + N·M), e com isso a latência.
**Recomendação:** use `JOIN` + agrupamento em memória, `IN (...)` em lote, eager loading (`joinedload`/`selectinload`) ou `GROUP BY` com agregação.

---

### AP-13 — Uso de API deprecated

**Severidade:** MEDIUM · **Playbook:** PB-11

**Sinais de detecção:** compare o código com a tabela abaixo **considerando a versão instalada** (Fase 1). Sempre que possível, confirme rodando a app com os warnings ligados (`PYTHONWARNINGS=always`, `node --trace-deprecation`) e procurando `DeprecationWarning`, `LegacyAPIWarning` ou `DEP0xxx` no log.

#### Python / Flask / SQLAlchemy

| Deprecated / legado | Desde | Equivalente moderno |
|---|---|---|
| `Model.query.get(id)` / `session.query(M).get(id)` | SQLAlchemy 2.0 (`LegacyAPIWarning`) | `db.session.get(Model, id)` / `db.get_or_404(Model, id)` |
| `Model.query.filter_by(...).all()` (Query API legada) | SQLAlchemy 2.0 (legado) | `db.session.execute(db.select(Model).filter_by(...)).scalars().all()` |
| `engine.execute(sql)` / `conn.execute("texto")` | removido no SQLAlchemy 2.0 | `with engine.connect() as c: c.execute(text(sql), params)` |
| `from sqlalchemy.ext.declarative import declarative_base` | SQLAlchemy 2.0 | `class Base(DeclarativeBase): ...` |
| `datetime.utcnow()` / `datetime.utcfromtimestamp()` | Python 3.12 | `datetime.now(timezone.utc)` / `datetime.fromtimestamp(ts, timezone.utc)` |
| `@app.before_first_request` | removido no Flask 2.3 | código de inicialização em `create_app()` / `with app.app_context():` |
| `flask.json.JSONEncoder` / `app.json_encoder` | removido no Flask 2.3 | `app.json = CustomJSONProvider(app)` |
| `from werkzeug.security import safe_str_cmp` | removido no Werkzeug 2.1 | `hmac.compare_digest` |
| `flask._app_ctx_stack` / `_request_ctx_stack` | Flask 2.2 | `flask.g`, `flask.current_app` |
| `logger.warn(...)` | Python 3.3 | `logger.warning(...)` |
| `pkg_resources`, `distutils`, `imp` | setuptools / Python 3.12 | `importlib.metadata`, `importlib` |

#### Node.js / Express

| Deprecated / legado | Desde | Equivalente moderno |
|---|---|---|
| `new Buffer(x)` | Node 10 (DEP0005) | `Buffer.from(x)` / `Buffer.alloc(n)` |
| `res.send(status, body)` / `res.json(status, obj)` | Express 4 (removido no 5) | `res.status(code).json(obj)` |
| `req.param('x')` | Express 4 (removido no 5) | `req.params.x` / `req.query.x` / `req.body.x` |
| `app.del(...)` | Express 4 (removido no 5) | `app.delete(...)` |
| `res.sendfile()` | Express 4 | `res.sendFile()` |
| `require('body-parser')` só para JSON/urlencoded | Express 4.16 | `express.json()` / `express.urlencoded()` |
| `crypto.createCipher()` / `createDecipher()` | Node 10 (DEP0106) | `crypto.createCipheriv()` com IV aleatório |
| `url.parse()` | Node 11 (legado) | `new URL(str, base)` |
| `fs.exists()` | Node 1 (DEP0034) | `fs.existsSync()` / `fs.promises.access()` |
| `util.isArray()` e afins (`util.is*`) | Node 4/22 (DEP0044) | `Array.isArray()`, `typeof` |
| `querystring` | legado | `URLSearchParams` |
| `String.prototype.substr()` | legado (Annex B) | `slice()` / `substring()` |
| Driver de banco só com callbacks (ex.: `sqlite3` com `db.get(sql, cb)`), Mongoose < 7 com callbacks | API legada; o `sqlite3@5` traz dependências transitivas deprecated (`npm install` avisa) | wrapper com Promises (`util.promisify`, pacote `sqlite`), `better-sqlite3`, `node:sqlite` (Node ≥ 22.5), ou `async/await` com o driver moderno |

**Também conta:** `npm install`/`pip install` emitindo avisos `deprecated` para dependências diretas, e dependências **sem pin** que resolvem para uma major nova em que a API usada virou legada.

**Impacto:** warnings no runtime e quebra em upgrades. No caso de datas, `utcnow()` devolve datetime *naive* e gera bugs de fuso horário.
**Recomendação:** substitua cada ocorrência pelo equivalente moderno e fixe as versões no manifesto.

---

### AP-14 — Tratamento de erro genérico / ausência de handler central

**Severidade:** MEDIUM · **Playbook:** PB-12

**Sinais de detecção:**
- `except:` puro ou `except Exception as e: return {"erro": str(e)}, 500` repetido em cada função.
- Callbacks com `err` ignorado (`(err, row) => { ... }` sem `if (err)`), ou acesso a resultado sem checar o erro (`rows.length` depois de uma query que falhou, que derruba o processo).
- Nenhum `@app.errorhandler` / `app.register_error_handler` / middleware `(err, req, res, next)`, e nenhum handler de 404.
- Respostas de erro em formatos diferentes (texto puro × JSON, `erro` × `error`), erros de validação virando 500 em HTML e status errados (falha de banco respondida como 404).

```bash
grep -rnE "except\s*:|except Exception" --include="*.py" .
grep -rnE "\(err[,)]" --include="*.js" . | grep -v "if (err"
```

**Impacto:** vaza detalhes internos, os clientes não conseguem tratar erros e o servidor pode cair.
**Recomendação:** crie exceções de domínio e um handler central que traduza cada uma para status + JSON padronizado, com log do erro inesperado e mensagem genérica para o cliente.

---

### AP-15 — Validação de entrada ausente ou inconsistente

**Severidade:** MEDIUM · **Playbook:** PB-13

**Sinais de detecção:**
- `request.get_json()` / `req.body` usado sem checar `None`/tipo (`dados.get(...)` com body vazio → `AttributeError`).
- Comparações numéricas sem checar o tipo (`if preco < 0` quando `preco` pode ser string → `TypeError` → 500).
- Validação diferente entre criar e atualizar o mesmo recurso.
- Sem validação de formato (email, cartão, cor, data), de faixa (quantidade > 0) ou de enum (status, categoria).
- Validadores que existem em `utils/` mas não são chamados.

**Impacto:** dados inválidos chegam ao banco e entradas ruins viram 500.
**Recomendação:** valide uma única vez, na borda (schema/função de validação por recurso, usada por criar e atualizar), e devolva 400 com mensagem clara.

---

### AP-16 — Código duplicado

**Severidade:** MEDIUM · **Playbook:** PB-14

**Sinais de detecção:**
- O mesmo mapeamento `row → dict` / serialização repetido em várias funções.
- Funções quase idênticas que diferem só num filtro (`listar_todos_pedidos` × `listar_pedidos_usuario`).
- A mesma regra copiada em várias rotas (cálculo de "atrasado", listas de status, regex de email), às vezes já divergente.
- Blocos de validação copiados entre handlers.

**Impacto:** correções precisam ser feitas em N lugares e as cópias divergem.
**Recomendação:** extraia uma função/método único (serializer, método de domínio, constante) e reutilize-o.

---

### AP-17 — Callback hell

**Severidade:** MEDIUM · **Playbook:** PB-15

**Sinais de detecção:**
- Três ou mais níveis de callbacks aninhados, e contadores manuais para saber quando todos os callbacks terminaram (`pending--; if (pending === 0) res.json(...)`).
- `const self = this` para acessar o contexto dentro de `function(err) { this.lastID }`.
- Ordem de resposta não determinística, porque depende da ordem em que os callbacks terminam.

**Impacto:** é difícil de ler, propaga erros mal e gera condições de corrida e resultados em ordem aleatória.
**Recomendação:** use `async/await` sobre APIs com Promises, `Promise.all` para paralelismo e `try/catch` encaminhando para o handler central.

---

### AP-18 — CORS permissivo

**Severidade:** MEDIUM · **Playbook:** PB-01

**Sinais de detecção:** `CORS(app)` sem `origins`, `app.use(cors())` sem opções, `Access-Control-Allow-Origin: *` em API com operações sensíveis.

**Impacto:** qualquer site pode chamar a API a partir do navegador do usuário, o que é especialmente grave quando combinado com AP-06.
**Recomendação:** leia as origens permitidas da config (env), com default restrito ou explícito para desenvolvimento.

---

## LOW

### AP-19 — Magic numbers e strings

**Severidade:** LOW · **Playbook:** PB-16

**Sinais de detecção:**
- Literais numéricos com significado de negócio: faixas de desconto (`10000`, `0.1`), limites (`2`, `200`, `5`), janelas de tempo (`7` dias), prefixos (`"4"` aprova cartão).
- Listas de enum inline repetidas (`["pendente", "aprovado", ...]`).
- Constantes definidas em algum módulo mas **não usadas**, enquanto os literais continuam espalhados.

**Impacto:** as regras ficam escondidas e mudá-las exige caçar literais em vários lugares.
**Recomendação:** use constantes nomeadas ou enums num módulo de domínio/config.

---

### AP-20 — Nomenclatura ruim

**Severidade:** LOW · **Playbook:** PB-17

**Sinais de detecção:**
- Nomes de uma letra ou abreviados sem contexto (`u`, `e`, `p`, `cc`, `cid`), numerados (`cursor2`, `cursor3`) ou enganosos (`badCrypto`, `AppManager`).
- Parâmetros que sombreiam builtins (`id`, `type`, `list`, `input` em Python).
- Mistura de idiomas no mesmo domínio (`get_todos_produtos`), ou `let`/`var` onde caberia `const`.

**Impacto:** prejudica a leitura e esconde a intenção do código.
**Recomendação:** use nomes descritivos e um único idioma por camada. **Não renomeie campos do contrato HTTP** (body/resposta): renomeie só os identificadores internos.

---

### AP-21 — `print` / `console.log` como mecanismo de log

**Severidade:** LOW · **Playbook:** PB-18

**Sinais de detecção:** `print(` / `console.log(` em código de aplicação (fora de scripts CLI/seed), mensagens como `"ERRO: "`, `"ENVIANDO EMAIL"`, `"[LOG]"`.

```bash
grep -rnE "^\s*print\(|console\.(log|error)\(" --include="*.py" --include="*.js" . | grep -v -E "seed|migrate"
```

**Impacto:** não há níveis, formato nem como desligar os logs por ambiente, e o risco de logar dados sensíveis cresce (veja AP-05).
**Recomendação:** use o logger padrão da stack (`logging`, `app.logger`, ou um logger mínimo em Node) com nível vindo da config.

---

### AP-22 — Código morto e imports não usados

**Severidade:** LOW · **Playbook:** PB-17

**Sinais de detecção:**
- Imports nunca referenciados (`import os, sys, json`).
- Funções, classes, constantes e serviços definidos e nunca chamados (verifique com grep do nome fora da definição).
- Variáveis de config declaradas e não lidas, e endpoints/rotinas comentados.

```bash
# Python: candidatos a import não usado
python -m pyflakes . 2>/dev/null || grep -rnE "^import |^from .* import " --include="*.py" .
```

**Impacto:** dá uma falsa impressão de que as regras estão centralizadas, aumenta o custo de leitura e mantém dependências desnecessárias.
**Recomendação:** remova o que não é usado, ou **passe a usar** o que deveria estar sendo usado (por exemplo, a rota chamar o método de domínio que já existe), e então apague a cópia.
