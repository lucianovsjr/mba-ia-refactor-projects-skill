# Análise de Projeto — Heurísticas

Referência da **Fase 1** (e da Fase 3 para subir a aplicação). Mostra como identificar a stack, o banco, o domínio e a arquitetura de qualquer projeto de backend. Use **evidências do código**, nunca o nome da pasta.

---

## 1. Inventário de arquivos

**Inclua** o código-fonte da aplicação, os scripts de seed/migration e os arquivos de configuração escritos à mão.

**Exclua:**

| Tipo | Exemplos |
|---|---|
| Dependências | `node_modules/`, `.venv/`, `venv/`, `env/`, `vendor/`, `site-packages/` |
| Build/cache | `dist/`, `build/`, `out/`, `target/`, `__pycache__/`, `.pytest_cache/`, `.next/`, `coverage/` |
| VCS/ferramentas | `.git/`, `.idea/`, `.vscode/`, `.claude/` |
| Lockfiles | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `go.sum`, `composer.lock` |
| Dados/binários | `*.db`, `*.sqlite`, `*.sqlite3`, imagens, `*.log` |

Comando sugerido (portável, funciona em macOS e Linux):

```bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.mjs" -o -name "*.cjs" \
  -o -name "*.go" -o -name "*.java" -o -name "*.kt" -o -name "*.rb" -o -name "*.php" -o -name "*.cs" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" \
  -not -path "*/__pycache__/*" -not -path "*/.git/*" -not -path "*/.claude/*" \
  -not -path "*/dist/*" -not -path "*/build/*" | sort | xargs wc -l
```

Arquivos `__init__.py` vazios contam como arquivos, mas não somam linhas relevantes.

---

## 2. Detecção de linguagem

Decida pelo **manifesto** e confirme pela **extensão dominante** dos arquivos-fonte.

| Manifesto / arquivo | Linguagem | Onde ler a versão do runtime |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | Python | `python --version` / `.venv/bin/python --version`, `.python-version`, `pyproject` → `requires-python` |
| `package.json` | JavaScript (TypeScript se houver `tsconfig.json` ou arquivos `.ts`) | `node --version`, `engines.node`, `.nvmrc` |
| `go.mod` | Go | diretiva `go` em `go.mod` |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin | `<java.version>`, `sourceCompatibility` |
| `Gemfile` | Ruby | `.ruby-version` |
| `composer.json` | PHP | `require.php` |
| `*.csproj` | C# | `<TargetFramework>` |

---

## 3. Detecção de framework (e versão exata)

**Sinal primário:** a dependência no manifesto. **Confirmação:** o import no entry point.

| Linguagem | Dependência | Import / sinal no código | Framework |
|---|---|---|---|
| Python | `flask` | `from flask import Flask`, `Flask(__name__)` | Flask |
| Python | `django` | `manage.py`, `settings.py`, `urls.py` | Django |
| Python | `fastapi` | `FastAPI()`, `@app.get` | FastAPI |
| JS/TS | `express` | `require('express')`, `express()` | Express |
| JS/TS | `@nestjs/core` | `@Controller()`, `@Module()` | NestJS |
| JS/TS | `fastify` / `koa` / `hono` | `fastify()`, `new Koa()` | Fastify / Koa / Hono |
| Go | `gin-gonic/gin`, `labstack/echo`, `gofiber/fiber` | `gin.Default()` | Gin / Echo / Fiber |
| Java | `spring-boot-starter-web` | `@RestController` | Spring Boot |
| Ruby | `rails` / `sinatra` | `config/routes.rb` | Rails / Sinatra |
| PHP | `laravel/framework` | `routes/api.php` | Laravel |

**Versão exata:** a faixa declarada (`^4.18.2`, `>=3.0`) não é a versão em uso. Leia a versão **instalada**:

```bash
# Python (use o interpretador do virtualenv do projeto, se existir)
.venv/bin/pip show flask | grep -i ^version      # ou: pip list | grep -i flask
# Node
node -p "require('./node_modules/express/package.json').version"
# Dependências transitivas relevantes (ex.: ORM puxado por um plugin)
.venv/bin/pip show sqlalchemy | grep -i ^version
```

Se as dependências não estiverem instaladas, informe a versão declarada e indique `(declarada; não instalada)`. Atenção às **dependências sem pin**: uma lib resolvida transitivamente numa versão major nova (ex.: SQLAlchemy 2.x via Flask-SQLAlchemy) muda quais APIs estão deprecated.

**Dependências de runtime:** liste as do manifesto, excluindo as de desenvolvimento (`devDependencies`, `[dev]`, `pytest`, `eslint`).

---

## 4. Detecção do banco de dados

| Sinal | Banco / camada de acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(...)` | SQLite, driver puro (SQL à mão) |
| `require('sqlite3')`, `new sqlite3.Database(':memory:')` | SQLite **em memória**, driver puro (callbacks) |
| `better-sqlite3`, `node:sqlite` | SQLite, driver síncrono |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | ORM SQLAlchemy (engine pela URI: `sqlite:///`, `postgresql://`, `mysql://`) |
| `psycopg2`, `pg`, `mysql2`, `pymysql` | PostgreSQL / MySQL, driver puro |
| `mongoose`, `pymongo` | MongoDB |
| `prisma`, `sequelize`, `typeorm`, `knex` | ORM/query builder Node |
| `gorm` | ORM Go |

**Tabelas/coleções:** colete-as de:
1. DDL inline: `CREATE TABLE <nome>` (grep `CREATE TABLE`).
2. Models do ORM: `__tablename__ = '...'`, `class X(db.Model)`, `mongoose.model('X', ...)`, `@Entity`.
3. Migrations: `migrations/`, `alembic/versions/`, `prisma/schema.prisma`.

Registre também **onde a conexão é criada** (variável global? factory? injeção?) e **onde o schema e o seed rodam** (no import? no boot? em script separado?), porque isso alimenta os achados de estado global e de efeitos colaterais.

---

## 5. Inferência do domínio

1. Liste as entidades (tabelas/models) e os recursos das rotas (`/produtos`, `/api/checkout`, `/tasks`).
2. Agrupe-as em um domínio de negócio conhecido. Exemplos:
   - produtos + pedidos + usuários → **E-commerce**
   - cursos + matrículas + pagamentos → **LMS / plataforma de cursos com checkout**
   - tasks + categorias + usuários + relatórios → **Task Manager**
3. Escreva em uma linha: `<tipo de API> — <entidades principais>`. Use o idioma do próprio código para os nomes das entidades.

---

## 6. Mapeamento da arquitetura atual

### 6.1 Onde estão as rotas

| Framework | Padrões de declaração de rota (grep) |
|---|---|
| Flask | `@app.route(`, `@<bp>.route(`, `app.add_url_rule(`, `Blueprint(`, `register_blueprint(` |
| FastAPI | `@app.get(`, `@router.post(`, `include_router(` |
| Django | `path(`, `re_path(` em `urls.py` |
| Express | `app.get(`, `app.post(`, `router.put(`, `app.delete(`, `app.use('/prefixo', router)` |
| NestJS | `@Get(`, `@Post(`, `@Controller('prefixo')` |
| Spring | `@GetMapping`, `@PostMapping`, `@RequestMapping` |

Monte o path completo somando os prefixos (`url_prefix` do Blueprint, `app.use('/api', router)`). Para cada rota, registre método, path, handler e `arquivo:linha`.

### 6.2 Quem faz o quê

Para cada arquivo-fonte, marque quais responsabilidades ele carrega:

| Responsabilidade | Sinais |
|---|---|
| Roteamento/HTTP | declaração de rotas, leitura de `request`/`req`, `jsonify`/`res.json` |
| Regra de negócio | cálculos, validações de domínio, transições de status, decisões (`if status == ...`) |
| Acesso a dados | SQL, chamadas de ORM (`.query`, `.execute`, `db.run`, `session.add`) |
| Configuração | chaves, URIs, portas, flags de debug |
| Formatação | montagem manual de dicionários/objetos de resposta |
| Infra | envio de e-mail, logging, cache |

Um arquivo com **3 ou mais** dessas responsabilidades é candidato a God Class/God File.

### 6.3 Uso real das camadas

Pastas não provam arquitetura. Para cada camada existente (`services/`, `utils/`, `helpers/`, `models/`), verifique **se ela é importada e chamada**:

```bash
# Ex.: para cada símbolo público definido em services/ ou utils/, procure usos fora do próprio arquivo
grep -rn "NomeDaClasseOuFuncao" --include="*.py" . | grep -v "def NomeDaClasseOuFuncao\|class NomeDaClasseOuFuncao"
```

Métodos de domínio nos models que nunca são chamados enquanto a mesma lógica aparece copiada nas rotas são um sinal forte de "camadas abandonadas".

### 6.4 Classificação

| Classificação | Critério |
|---|---|
| **Monolítica** | Rotas, regra de negócio e acesso a dados no mesmo arquivo/classe, ou divididos em poucos arquivos sem fronteiras (ex.: "controllers" que fazem SQL, "models" com regras de 3 domínios) |
| **Parcialmente em camadas** | Existem pastas/camadas separadas, mas ao menos uma responsabilidade está no lugar errado (rotas com regra de negócio e queries) ou alguma camada existe sem ser usada |
| **Em camadas (MVC)** | Rotas só fazem HTTP → controllers orquestram → models acessam dados; config isolada; error handling central |

Justifique a classificação em uma linha citando os arquivos (ex.: "Monolítica — 4 arquivos; `models.py` concentra SQL e regras de 3 domínios").

---

## 7. Subindo a aplicação

### 7.1 Descobrir o comando

| Stack | Instalação | Start | Onde está a porta |
|---|---|---|---|
| Python/Flask | `python -m venv .venv && .venv/bin/pip install -r requirements.txt` | `python app.py` (bloco `__main__`) ou `flask --app <módulo> run` | `app.run(port=...)`, `FLASK_RUN_PORT` |
| Python/FastAPI | idem | `uvicorn <módulo>:app` | `--port` |
| Node/Express | `npm install` (ou `npm ci` com lockfile) | `npm start` (`scripts.start`) ou `node <main>` | `app.listen(...)`, `process.env.PORT` |

Procure também por **passos obrigatórios**: scripts de seed (`seed.py`, `npm run seed`), migrations e variáveis de ambiente lidas no boot (`os.environ[...]`, `process.env.X` sem default). Leia o README do projeto, se houver.

### 7.2 Bloqueios comuns

- **Porta ocupada.** Verifique com `lsof -nP -iTCP:<porta> -sTCP:LISTEN`. No macOS, a **porta 5000 costuma estar ocupada pelo AirPlay Receiver** (`ControlCenter`). Se a porta estiver fixa no código original, não altere o código nas Fases 1 e 2: use uma alternativa que não modifique arquivos, como `flask --app app run --port 5001` (no Flask o bloco `__main__` não roda, então execute manualmente qualquer inicialização que ele faça) ou `PORT=3001 npm start` se a app ler `PORT`. Depois da refatoração, a porta deve vir da config/env.
- **Banco com estado.** Bancos em arquivo (`*.db`) guardam as alterações dos seus testes. Antes da baseline, recrie o estado inicial (apague o arquivo, se ele for recriado com seed no boot, ou rode o script de seed). Faça o mesmo no fim.
- **Banco em memória.** Ele é reiniciado a cada boot, então reinicie a app entre a baseline e a validação.

### 7.3 Rodar em background e esperar ficar pronta

O macOS não tem o comando `timeout`. Use background + PID:

```bash
<comando de start> > /tmp/app.log 2>&1 &
APP_PID=$!
for i in $(seq 1 20); do curl -s -o /dev/null "http://localhost:<porta>/" && break; sleep 0.5; done
# ... requisições ...
kill $APP_PID
```

Considere a app "de pé" quando qualquer requisição HTTP receber resposta (mesmo 404). Confira o log de inicialização em busca de `Traceback`, `Error`, `Address already in use` ou warnings de deprecated.

### 7.4 Sondar os endpoints

Para cada rota do inventário, monte uma requisição representativa a partir do próprio handler: campos lidos do body (`request.get_json()`, `req.body.x`), query params (`request.args`, `req.query`) e IDs existentes no seed. Registre:

```bash
curl -s -o /tmp/resp.json -w "%{http_code}" -X POST -H "Content-Type: application/json" \
  -d '{"campo":"valor"}' http://localhost:<porta>/rota
```

Inclua, por recurso, um caso de sucesso e, quando fizer sentido, um 404 ou 400. Execute as operações destrutivas por último. A resposta original define o contrato: status code, tipo de conteúdo (JSON vs texto) e chaves de topo do corpo.
