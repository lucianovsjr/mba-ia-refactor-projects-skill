# Playbook de Refatoração

Referência da **Fase 3**. Para cada anti-pattern do [catálogo](anti-patterns-catalog.md) há um padrão de transformação concreto com código **antes/depois**, em Python (Flask) e/ou JavaScript (Express). Para outras stacks, aplique a mesma ideia com os idiomas equivalentes.

## Índice

| ID | Padrão | Corrige |
|---|---|---|
| PB-01 | Extrair configuração para variáveis de ambiente | AP-01, AP-07, AP-18 |
| PB-02 | Queries parametrizadas | AP-02 |
| PB-03 | Quebrar God Class em camadas por domínio | AP-03 |
| PB-04 | Hash de senha com KDF e salt | AP-04 |
| PB-05 | Serialização por lista branca e logs sem dados sensíveis | AP-05 |
| PB-06 | Desabilitar endpoints perigosos, bloquear escalada de privilégio e assinar tokens | AP-06 |
| PB-07 | Mover regra de negócio da rota para o controller | AP-08 |
| PB-08 | App factory, composition root e injeção de dependência | AP-09, AP-10 |
| PB-09 | Transação por caso de uso e integridade referencial | AP-11 |
| PB-10 | Eliminar N+1 com JOIN / eager loading / agregação | AP-12 |
| PB-11 | Substituir APIs deprecated | AP-13 |
| PB-12 | Exceções de domínio e error handler central | AP-14 |
| PB-13 | Validação de entrada na borda | AP-15 |
| PB-14 | Extrair duplicação para uma fonte única | AP-16 |
| PB-15 | Callbacks → async/await | AP-17 |
| PB-16 | Constantes nomeadas | AP-19 |
| PB-17 | Renomear e remover código morto | AP-20, AP-22 |
| PB-18 | Logger no lugar de print/console.log | AP-21 |

## Ordem de aplicação

Siga a ordem do SKILL.md (§3.2). Depois de **cada grupo**, suba a aplicação e chame pelo menos um endpoint por domínio antes de continuar:

1. **Config:** PB-01
2. **Estrutura:** PB-08 → PB-03 → PB-07. Primeiro a factory e a conexão, depois o split por domínio, depois as regras movidas para os controllers.
3. **Segurança:** PB-02 → PB-04 → PB-05 → PB-06
4. **Integridade/performance:** PB-09 → PB-10
5. **Erros/validação:** PB-12 → PB-13 (e PB-15 em Node, junto com PB-12)
6. **Deprecated:** PB-11
7. **Qualidade:** PB-14 → PB-16 → PB-17 → PB-18

---

## PB-01 — Extrair configuração para variáveis de ambiente

**Corrige:** AP-01 (segredos hardcoded), AP-07 (debug em produção), AP-18 (CORS aberto).

**Passos:**
1. Crie o módulo de config que lê `os.environ` / `process.env`.
2. Os defaults servem **só para desenvolvimento** e não são os segredos originais. Gere um valor aleatório quando o segredo faltar, e `DEBUG` é `False` por padrão.
3. Substitua todas as referências literais pela config.
4. Crie o `.env.example` com as chaves sem valores reais.
5. Os segredos que só eram usados para nada (configs mortas) são removidos (PB-17).

**Antes (Python):**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
...
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois (Python):**
```python
# src/config/settings.py
import os
import secrets


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)  # aleatório em dev
    DEBUG = _bool(os.environ.get("FLASK_DEBUG"), default=False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = [o for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o]


settings = Settings()
```
```python
# src/app.py (trecho)
CORS(app, origins=settings.CORS_ORIGINS)
app.config["SECRET_KEY"] = settings.SECRET_KEY
```
```python
# app.py (raiz)
from src.app import create_app
from src.config.settings import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

**Antes (JavaScript):**
```js
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

**Depois (JavaScript):**
```js
// src/config/index.js
const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "", // obrigatório em produção
    databaseFile: process.env.DATABASE_FILE || ":memory:",
    logLevel: process.env.LOG_LEVEL || "info",
});

module.exports = config;
```
```bash
# .env.example
PORT=3000
PAYMENT_GATEWAY_KEY=
DATABASE_FILE=:memory:
LOG_LEVEL=info
```

> Não adicione `python-dotenv`/`dotenv` só para isso: ler o ambiente direto basta. Se o projeto já tiver a dependência, use-a para carregar o `.env`.

---

## PB-02 — Queries parametrizadas

**Corrige:** AP-02 (SQL Injection).

**Passos:**
1. Troque toda concatenação/interpolação por placeholders do driver: `?` (sqlite3), `%s` (psycopg2/pymysql), `$1` (pg), `:nome` (SQLAlchemy `text()`).
2. Para **filtros dinâmicos**, monte as listas `conditions` e `params` em paralelo.
3. Para `LIKE`, coloque o curinga no **parâmetro**, não no SQL.
4. Nomes de coluna e ordenação dinâmicos não aceitam placeholder: valide contra uma lista branca.

**Antes:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")

query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
if categoria:
    query += " AND categoria = '" + categoria + "'"
cursor.execute(query)
```

**Depois:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

conditions, params = [], []
if termo:
    conditions.append("(nome LIKE ? OR descricao LIKE ?)")
    like = f"%{termo}%"
    params += [like, like]
if categoria:
    conditions.append("categoria = ?")
    params.append(categoria)
if preco_min is not None:
    conditions.append("preco >= ?")
    params.append(preco_min)

sql = "SELECT * FROM produtos"
if conditions:
    sql += " WHERE " + " AND ".join(conditions)
cursor.execute(sql, params)
```

**JavaScript (sqlite3/pg):**
```js
// Antes
db.all("SELECT * FROM courses WHERE title = '" + title + "'", cb);
// Depois
await db.all("SELECT * FROM courses WHERE title = ?", [title]);
```

---

## PB-03 — Quebrar God Class em camadas por domínio

**Corrige:** AP-03.

**Passos:**
1. Liste os **domínios** (tabelas/entidades) e, para cada função/método do God File, classifique-a como *dados*, *regra* ou *HTTP*.
2. Crie `models/<dominio>_model`, `controllers/<dominio>_controller` e `routes/<dominio>_routes` (veja `mvc-guidelines.md` §3).
3. Mova domínio por domínio, ajustando os imports, e suba a app a cada domínio movido.
4. Apague o arquivo original quando ele estiver vazio.

**Antes (um `models.py` com 3 domínios):**
```python
# models.py
def get_produto_por_id(id): ...           # SQL de produto
def criar_pedido(usuario_id, itens):      # SQL + regra de estoque + cálculo de total
    ...
def relatorio_vendas():                   # SQL + faixas de desconto
    ...
def login_usuario(email, senha): ...      # SQL de usuário
```

**Depois:**
```
src/models/produto_model.py      → buscar_por_id, listar, buscar, inserir, atualizar, remover
src/models/pedido_model.py       → inserir_pedido, inserir_item, listar_com_itens
src/models/usuario_model.py      → buscar_por_email, inserir, listar
src/controllers/pedido_controller.py  → criar_pedido (valida, calcula total, chama models em transação)
src/controllers/relatorio_controller.py → relatorio_vendas (faixas de desconto)
src/views/pedido_routes.py       → POST /pedidos → pedido_controller.criar_pedido
```

**Antes (JavaScript, classe que faz tudo):**
```js
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { /* CREATE TABLE + seed */ }
    setupRoutes(app) { app.post('/api/checkout', (req, res) => { /* regra + SQL */ }); }
}
```

**Depois:**
```js
// src/database/connection.js  → createDatabase(), initSchema(db), seed(db)
// src/models/courseModel.js   → createCourseModel(db) { findActiveById, findAll }
// src/controllers/checkoutController.js → createCheckoutController({ userModel, courseModel, ... })
// src/routes/checkoutRoutes.js → router.post('/checkout', asyncHandler(...))
// src/app.js                   → composition root
```

---

## PB-04 — Hash de senha com KDF e salt

**Corrige:** AP-04.

**Passos:**
1. Use um KDF lento com salt: `werkzeug.security` (já vem com Flask), `hashlib.scrypt`, `crypto.scrypt` (Node), bcrypt ou argon2.
2. Faça a comparação em tempo constante (o `check_password_hash` / `crypto.timingSafeEqual` já cuida disso).
3. O **login passa a buscar o usuário pelo email** e verifica o hash em código. Nunca compare a senha no SQL.
4. Atualize o **seed** para gravar hashes.
5. **Bancos existentes com senhas antigas:** se o banco for recriado no boot ou pelo seed, basta o seed novo. Se houver dados persistidos, aceite o formato legado no login e regrave com o hash novo (*rehash on login*), documentando essa decisão.

**Antes (Python):**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**Depois (Python):**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

**Antes (Python, SQL puro):**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

**Depois:**
```python
row = usuario_model.buscar_por_email(email)
if row is None or not check_password_hash(row["senha"], senha):
    raise UnauthorizedError("Email ou senha inválidos")
```

**Antes (JavaScript):**
```js
function badCrypto(pwd) {
    let hash = "";
    for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    return hash.substring(0, 10);
}
```

**Depois (JavaScript):**
```js
// src/utils/crypto.js
const crypto = require('node:crypto');
const KEY_LENGTH = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derived = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
    return `scrypt$${salt}$${derived}`;
}

function verifyPassword(password, stored) {
    const [scheme, salt, expected] = String(stored).split('$');
    if (scheme !== 'scrypt' || !salt || !expected) return false;
    const derived = crypto.scryptSync(password, salt, KEY_LENGTH);
    const expectedBuf = Buffer.from(expected, 'hex');
    return expectedBuf.length === derived.length && crypto.timingSafeEqual(derived, expectedBuf);
}

module.exports = { hashPassword, verifyPassword };
```

---

## PB-05 — Serialização por lista branca e logs sem dados sensíveis

**Corrige:** AP-05.

**Passos:**
1. Cada entidade exposta tem um serializer com os **campos permitidos** listados explicitamente.
2. Remova `password`/`senha`/hash, segredos, caminhos internos e flags de debug das respostas.
3. Nos logs, mascare os dados sensíveis (cartão → só os 4 últimos dígitos) e nunca logue segredos.
4. Registre cada campo removido em `## Contract changes`.

**Antes:**
```python
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email,
            "password": self.password, "role": self.role}
```
```python
return jsonify({"status": "ok", "secret_key": "minha-chave-super-secreta-123", "db_path": "loja.db"})
```

**Depois:**
```python
PUBLIC_USER_FIELDS = ("id", "name", "email", "role", "active", "created_at")

def to_dict(self):
    data = {
        "id": self.id, "name": self.name, "email": self.email,
        "role": self.role, "active": self.active, "created_at": str(self.created_at),
    }
    return {k: data[k] for k in PUBLIC_USER_FIELDS}
```
```python
return jsonify({"status": "ok", "database": "connected", "counts": counts, "versao": APP_VERSION})
```

**Antes (JavaScript):**
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

**Depois:**
```js
const maskCard = (card) => `**** **** **** ${String(card).slice(-4)}`;
logger.info(`Processando pagamento com cartão ${maskCard(card)}`);
```

---

## PB-06 — Desabilitar endpoints perigosos, bloquear escalada de privilégio e assinar tokens

**Corrige:** AP-06. Siga os limites de `mvc-guidelines.md` §5: corrija sem tornar obrigatório o login de rotas que hoje são públicas.

**Passos:**
1. Os endpoints que executam SQL/código arbitrário ou apagam o banco ficam **desligados por padrão** e só são habilitados com `ENABLE_ADMIN_ENDPOINTS=true` **e** o header `X-Admin-Token` igual a `ADMIN_TOKEN` (env). O endpoint de SQL arbitrário pode simplesmente ser **removido**.
2. Campos de privilégio (`role`, `tipo`, `is_admin`, `active`) vindos do body em rotas públicas são **ignorados** (ficam com o default) ou exigem o token de admin.
3. Fluxos que agem em nome de um usuário existente **verificam a credencial** antes (por exemplo, checkout com email já cadastrado exige a senha correta → 401).
4. Tokens falsos ou previsíveis emitidos pelo login (`'fake-jwt-token-' + id`, id em base64, timestamp) são **substituídos por um token assinado** com a `SECRET_KEY` da config. Veja "Token previsível → token assinado" abaixo.
5. Liste em `## Contract changes` o que mudou nas respostas (passos 1–3). A troca do token do passo 4 **não** é mudança de contrato e vai só em `## Changes`. Registre "exigir autenticação nas rotas" como recomendação remanescente.

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json().get("sql", ""))
    ...
```

**Depois:**
```python
# src/middlewares/auth.py
import hmac
from functools import wraps
from flask import request
from src.config.settings import settings
from src.utils.errors import ForbiddenError, NotFoundError


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not settings.ENABLE_ADMIN_ENDPOINTS:
            raise NotFoundError("Recurso não encontrado")
        token = request.headers.get("X-Admin-Token", "")
        if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)
    return wrapper
```
```python
# src/views/admin_routes.py — o /admin/query (SQL arbitrário) foi removido
@admin_bp.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database():
    admin_controller.reset_database()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
```

**Mass assignment, antes:**
```python
role = data.get('role', 'user')
user.role = role
```

**Depois:**
```python
user.role = DEFAULT_ROLE  # papel não é definido pelo próprio usuário na criação pública
```

**JavaScript (checkout em nome de terceiro), depois:**
```js
const existing = await userModel.findByEmail(email);
if (existing && !verifyPassword(password ?? '', existing.pass)) {
    throw new UnauthorizedError('Credenciais inválidas');
}
```

### Token previsível → token assinado

Um token montado a partir do id (`'fake-jwt-token-' + id`) pode ser forjado para qualquer usuário. A troca **não quebra contrato**: o token é opaco para o cliente, que só o guarda e o reenvia. O endpoint de login continua com o mesmo status, as mesmas chaves e o campo `token` continua sendo string; só o **valor** muda. Exigir o token nas rotas é outra coisa e continua fora do escopo (§5).

**Regras:**
- Assine com a `SECRET_KEY` do módulo de config (PB-01), nunca com uma chave literal, e use um `salt`/propósito próprio para o token de login.
- **Injete a chave.** O módulo de tokens recebe a chave como parâmetro e não importa config nem framework. A rota lê a chave da config da app (`current_app.config["SECRET_KEY"]`, `config.secretKey`) e a repassa ao controller. Assim o controller continua sem importar o framework HTTP (`mvc-guidelines.md`), e a função funciona com qualquer config: factory, testes ou outra chave.
- O payload leva só o id do usuário. Nada de email, papel, senha ou hash.
- O token carrega o instante de emissão (o `URLSafeTimedSerializer` já inclui; em Node, `iat`), para que quem o verificar aplique uma expiração com constante nomeada (`max_age`).
- Use o que a stack já traz: em Flask, `itsdangerous` (dependência do próprio Flask, sem pacote novo no manifesto); em Node, `crypto` nativo com HMAC-SHA256. Não adicione uma biblioteca de JWT só para isso.
- Não crie no projeto uma função de verificação que nenhuma rota chama (seria código morto, AP-22). Verifique o token no passo de validação (§3.3) com o snippet abaixo.
- Remova a constante/prefixo do token antigo e qualquer código que só existia para montá-lo.
- Documente no `.env.example` que, sem `SECRET_KEY` definida, a chave aleatória de desenvolvimento invalida os tokens a cada restart.

**Antes (Python):**
```python
def login(data):
    ...
    return user, 'fake-jwt-token-' + str(user.id)
```

**Depois (Python):**
```python
# src/utils/tokens.py
from itsdangerous import URLSafeTimedSerializer

LOGIN_TOKEN_SALT = "login-token"


def issue_login_token(user_id, secret_key):
    """Token opaco para o cliente, assinado com a SECRET_KEY: não dá para forjá-lo para outro id."""
    return URLSafeTimedSerializer(secret_key, salt=LOGIN_TOKEN_SALT).dumps({"uid": user_id})
```
```python
# src/controllers/user_controller.py (trecho)
from src.utils.tokens import issue_login_token

def login(data, secret_key):
    ...
    return user, issue_login_token(user.id, secret_key)
```
```python
# src/routes/user_routes.py (trecho): a rota injeta a chave da config da app
from flask import current_app

@user_bp.route("/login", methods=["POST"])
def login():
    user, token = user_controller.login(request.get_json(silent=True), current_app.config["SECRET_KEY"])
    return jsonify({"message": "Login realizado com sucesso", "user": user.to_dict(), "token": token}), 200
```

**Validação (§3.3), sem deixar código de verificação no projeto:**
```python
# rode com o interpretador do projeto; SECRET_KEY = a mesma usada para subir a app
from itsdangerous import BadSignature, URLSafeTimedSerializer

LOGIN_TOKEN_MAX_AGE = 60 * 60 * 24  # segundos
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="login-token")
assert serializer.loads(token, max_age=LOGIN_TOKEN_MAX_AGE) == {"uid": 1}   # token do POST /login
for forged in ("fake-jwt-token-2", token[:-2] + "xx"):
    try:
        serializer.loads(forged)
        raise AssertionError("token forjado aceito")
    except BadSignature:
        pass                                                                 # rejeitado, como esperado
```
Confira também que o mesmo token é rejeitado com outra `SECRET_KEY`.

**Antes (JavaScript):**
```js
res.json({ message: 'Login realizado', token: `fake-jwt-token-${user.id}` });
```

**Depois (JavaScript):**
```js
// src/utils/tokens.js
const crypto = require('crypto');

const sign = (payload, secretKey) =>
    crypto.createHmac('sha256', secretKey).update(payload).digest('base64url');

function issueLoginToken(userId, secretKey) {
    const payload = Buffer.from(JSON.stringify({ uid: userId, iat: Date.now() })).toString('base64url');
    return `${payload}.${sign(payload, secretKey)}`;
}

module.exports = { issueLoginToken };
```
```js
// src/routes/userRoutes.js (trecho): a rota injeta a chave da config
router.post('/login', async (req, res) => {
    const { user, token } = await userController.login(req.body, config.secretKey);
    res.json({ message: 'Login realizado', user, token });
});
```
Na validação, recalcule `sign(payload, secretKey)` e compare com `crypto.timingSafeEqual` (buffers do mesmo tamanho), checando `iat` contra a expiração.

---

## PB-07 — Mover regra de negócio da rota para o controller

**Corrige:** AP-08.

**Passos:**
1. O handler passa a ter 3 passos: **extrair** os dados do request → **chamar** um método do controller → **serializar** e responder.
2. Toda decisão de domínio (validação de regra, cálculo, cascata, notificação) vai para o controller, que lança exceções de domínio em vez de devolver `(json, status)`.
3. Em projetos parcialmente em camadas, **use os métodos de domínio já existentes** (`task.is_overdue()`) e apague as cópias inline.

**Antes:**
```python
@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        data = task.to_dict()
        if task.due_date:
            if task.due_date < datetime.utcnow():
                if task.status != 'done' and task.status != 'cancelled':
                    data['overdue'] = True
                ...
        return jsonify(data), 200
    else:
        return jsonify({'error': 'Task não encontrada'}), 404
```

**Depois:**
```python
# controllers/task_controller.py
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")
    return task

# routes/task_routes.py
@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_controller.get_task(task_id)
    return jsonify(serialize_task(task)), 200   # serialize_task usa task.is_overdue()
```

**JavaScript, antes:**
```js
app.post('/api/checkout', (req, res) => {
    let status = cc.startsWith("4") ? "PAID" : "DENIED";
    if (status === "DENIED") return res.status(400).send("Pagamento recusado");
    this.db.run("INSERT INTO enrollments ...", ...);
});
```

**Depois:**
```js
// src/routes/checkoutRoutes.js
router.post('/checkout', asyncHandler(async (req, res) => {
    const result = await checkoutController.checkout(req.body);
    res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
}));

// src/controllers/checkoutController.js
async checkout({ usr, eml, pwd, c_id, card }) {
    validateCheckoutInput({ usr, eml, c_id, card });
    const course = await courseModel.findActiveById(c_id);
    if (!course) throw new NotFoundError('Curso não encontrado');
    const status = paymentService.charge(card, course.price);   // regra isolada no service
    if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError('Pagamento recusado');
    return enrollmentModel.enrollWithPayment({ userId, courseId: course.id, amount: course.price, status });
}
```

---

## PB-08 — App factory, composition root e injeção de dependência

**Corrige:** AP-09 (estado global), AP-10 (acoplamento).

**Passos:**
1. Crie `create_app(config)` (Flask) ou `buildApp(deps)` (Express). Tudo que hoje roda no import (criação de tabelas, seed, conexão) passa a rodar dentro dela.
2. A conexão de banco é **por requisição/app context** (Flask: `g` + `teardown_appcontext`) ou criada uma vez no composition root e **injetada** nos models (Node).
3. Controllers e models recebem as dependências por parâmetro/factory, não por import de estado global.
4. Caches/contadores globais sem uso são removidos. Se forem usados, ganham escopo e limite.
5. Os scripts auxiliares (`seed.py`) usam `create_app()`.

**Antes (Python):**
```python
# database.py
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
        # CREATE TABLE ... + seed
    return db_connection
```

**Depois (Python):**
```python
# src/database/connection.py
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        create_schema(get_db())
        seed_if_empty(get_db())
```
```python
# src/app.py
def create_app(config=settings):
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=config.CORS_ORIGINS)
    connection.init_app(app)
    register_error_handlers(app)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    return app
```

**Flask-SQLAlchemy (app global com `create_all()` no import), depois:**
```python
def create_app(config=settings):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
    db.init_app(app)
    register_error_handlers(app)
    for bp in (task_bp, user_bp, report_bp):
        app.register_blueprint(bp)
    with app.app_context():
        db.create_all()
    return app
```
```python
# seed.py
from app import app          # app = create_app() no app.py raiz
with app.app_context():
    ...
```

**Antes (JavaScript):**
```js
let globalCache = {};
let totalRevenue = 0;
const manager = new AppManager();   // abre o banco no construtor
manager.initDb();
manager.setupRoutes(app);
```

**Depois (JavaScript):**
```js
// src/app.js — composition root
const express = require('express');
const config = require('./config');
const { createDatabase, initSchema } = require('./database/connection');
const { createUserModel } = require('./models/userModel');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createCheckoutRoutes } = require('./routes/checkoutRoutes');
const { errorHandler, notFound } = require('./middlewares/errorHandler');

async function buildApp() {
    const db = createDatabase(config.databaseFile);
    await initSchema(db);
    const userModel = createUserModel(db);
    // ... demais models
    const checkoutController = createCheckoutController({ db, userModel /* ... */ });

    const app = express();
    app.use(express.json());
    app.use('/api', createCheckoutRoutes(checkoutController));
    app.use(notFound);
    app.use(errorHandler);
    return app;
}

if (require.main === module) {
    buildApp().then((app) => app.listen(config.port, () => logger.info(`Servidor na porta ${config.port}`)));
}

module.exports = { buildApp };
```

---

## PB-09 — Transação por caso de uso e integridade referencial

**Corrige:** AP-11.

**Passos:**
1. Todas as escritas de um caso de uso ficam numa transação única, com rollback em qualquer exceção.
2. **Valide antes de escrever:** existência das referências (usuário, produto), quantidades > 0, estoque suficiente.
3. Use um decremento atômico com condição (`... WHERE estoque >= ?`) e verifique `rowcount`/`changes`.
4. Na exclusão do pai: remova ou trate os filhos na mesma transação (ou use `ON DELETE CASCADE` com `PRAGMA foreign_keys = ON`), e responda 404 se o pai não existir.

**Antes (Python):**
```python
for item in itens:
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
    ...
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - " + str(item["quantidade"]) + ...)
db.commit()
```

**Depois (Python):**
```python
def criar_pedido(usuario_id, itens):
    db = get_db()
    if usuario_model.buscar_por_id(db, usuario_id) is None:
        raise NotFoundError("Usuário não encontrado")
    for item in itens:
        if item["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")

    with db:  # sqlite3: commit no sucesso, rollback em exceção
        total = 0
        produtos = produto_model.buscar_por_ids(db, [i["produto_id"] for i in itens])
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise NotFoundError(f"Produto {item['produto_id']} não encontrado")
            total += produto["preco"] * item["quantidade"]
        pedido_id = pedido_model.inserir(db, usuario_id, total)
        for item in itens:
            pedido_model.inserir_item(db, pedido_id, item, produtos[item["produto_id"]]["preco"])
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise BusinessRuleError(f"Estoque insuficiente para {produtos[item['produto_id']]['nome']}")
    return {"pedido_id": pedido_id, "total": total}
```
```python
# produto_model.py
def baixar_estoque(db, produto_id, quantidade):
    cur = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cur.rowcount == 1
```

**JavaScript:**
```js
// src/database/connection.js
async function transaction(db, work) {
    await db.run('BEGIN');
    try {
        const result = await work();
        await db.run('COMMIT');
        return result;
    } catch (err) {
        await db.run('ROLLBACK');
        throw err;
    }
}
```
```js
// enrollmentModel.enrollWithPayment
return transaction(db, async () => {
    const { lastID: enrollmentId } = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]);
    await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
        [`Checkout curso ${courseId} por ${userId}`]);
    return { enrollmentId };
});
```

> Com o `sqlite3` do Node usando **uma única conexão**, duas transações concorrentes se misturam. Serialize os casos de uso transacionais (uma fila/mutex simples no helper `transaction`) ou use `better-sqlite3`.

**Exclusão com filhos (JavaScript):**
```js
async deleteUser(id) {
    const user = await userModel.findById(id);
    if (!user) throw new NotFoundError('Usuário não encontrado');
    await transaction(db, async () => {
        await paymentModel.deleteByUser(id);
        await enrollmentModel.deleteByUser(id);
        await userModel.delete(id);
    });
}
```

---

## PB-10 — Eliminar N+1 com JOIN / eager loading / agregação

**Corrige:** AP-12.

**Passos:**
1. Troque a query dentro do loop por **uma** query com `JOIN` (ou `IN (...)`) e agrupe em memória.
2. No ORM, use `joinedload`/`selectinload` ou subquery de contagem.
3. Troque vários `COUNT` separados por um `GROUP BY`.
4. **Preserve a ordem e o formato** da resposta original. Se a original não tinha ordem estável, use `ORDER BY` pela chave primária.

**Antes (SQL puro):**
```python
cursor.execute("SELECT * FROM pedidos")
for row in cursor.fetchall():
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois:**
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(pr.nome, 'Desconhecido') AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id, i.id
""").fetchall()

pedidos = {}
for r in rows:
    pedido = pedidos.setdefault(r["id"], {
        "id": r["id"], "usuario_id": r["usuario_id"], "status": r["status"],
        "total": r["total"], "criado_em": r["criado_em"], "itens": [],
    })
    if r["produto_id"] is not None:
        pedido["itens"].append({
            "produto_id": r["produto_id"], "produto_nome": r["produto_nome"],
            "quantidade": r["quantidade"], "preco_unitario": r["preco_unitario"],
        })
return list(pedidos.values())
```

**ORM (SQLAlchemy), antes:**
```python
for t in Task.query.all():
    user = User.query.get(t.user_id)
    cat = Category.query.get(t.category_id)
```

**Depois:**
```python
from sqlalchemy.orm import joinedload

tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
).scalars().all()
for t in tasks:
    user_name = t.user.name if t.user else None
```

**Contagens, antes → depois:**
```python
pending = Task.query.filter_by(status='pending').count()
done = Task.query.filter_by(status='done').count()
# ...
```
```python
from sqlalchemy import func

counts = dict(db.session.execute(
    db.select(Task.status, func.count()).group_by(Task.status)
).all())
pending = counts.get('pending', 0)
```

**JavaScript (relatório com callbacks aninhados), depois:**
```js
const rows = await db.all(`
    SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id`);
const report = new Map();
for (const r of rows) {
    if (!report.has(r.course_id)) report.set(r.course_id, { course: r.title, revenue: 0, students: [] });
    if (r.student === null && r.amount === null) continue;   // curso sem matrículas
    const entry = report.get(r.course_id);
    if (r.status === PAYMENT_STATUS.PAID) entry.revenue += r.amount;
    entry.students.push({ student: r.student ?? 'Unknown', paid: r.amount ?? 0 });
}
return [...report.values()];
```

---

## PB-11 — Substituir APIs deprecated

**Corrige:** AP-13. Use a tabela do catálogo (AP-13) para ver o equivalente de cada API.

**Passos:**
1. Substitua **todas** as ocorrências (procure com grep; os números do relatório indicam quantas são).
2. Fixe no manifesto a versão das dependências que mudaram o comportamento (ex.: `SQLAlchemy>=2.0,<2.2`).
3. Valide subindo a app com os warnings ligados (`PYTHONWARNINGS=always`, `node --trace-deprecation`): o log não pode mais mostrar `DeprecationWarning`/`LegacyAPIWarning`.

**SQLAlchemy `Query.get()`:**
```python
# Antes
task = Task.query.get(task_id)
# Depois
task = db.session.get(Task, task_id)
```

**`datetime.utcnow()`:**
```python
# Antes
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if t.due_date < datetime.utcnow(): ...

# Depois
from datetime import datetime, timezone

def utcnow():
    """UTC naive, compatível com as colunas DateTime sem timezone já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
if t.due_date < utcnow(): ...
```
> Mantenha *naive* (sem `tzinfo`) quando as colunas e os dados existentes forem naive: comparar aware com naive gera `TypeError`. A saída em JSON fica idêntica à original.

**Node `new Buffer` e `res.send(status, body)`:**
```js
// Antes
const b = new Buffer(pwd);
res.send(404, 'Não encontrado');
// Depois
const b = Buffer.from(pwd);
res.status(404).send('Não encontrado');
```

**Driver `sqlite3` só com callbacks → wrapper com Promises:**
```js
// src/database/connection.js
const sqlite3 = require('sqlite3');   // sem .verbose() em produção

function createDatabase(file) {
    const raw = new sqlite3.Database(file);
    return {
        run: (sql, params = []) => new Promise((resolve, reject) =>
            raw.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            })),
        get: (sql, params = []) => new Promise((resolve, reject) =>
            raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)))),
        all: (sql, params = []) => new Promise((resolve, reject) =>
            raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)))),
        close: () => new Promise((resolve, reject) => raw.close((err) => (err ? reject(err) : resolve()))),
    };
}
```

---

## PB-12 — Exceções de domínio e error handler central

**Corrige:** AP-14.

**Passos:**
1. Crie as exceções de domínio com status associado (`ValidationError` 400, `UnauthorizedError` 401, `ForbiddenError` 403, `NotFoundError` 404, `ConflictError` 409, `BusinessRuleError` 400/422).
2. Registre **um** handler central que converte as exceções de domínio no JSON do formato **já usado pelo projeto** (`{"erro": ...}`, `{"error": ...}`, ou texto se a baseline for texto) e trata 404 de rota e 500 genérico (logando o stack, mas respondendo com uma mensagem genérica).
3. Remova os `try/except` repetidos dos handlers. Troque `except:` puro por exceções específicas onde realmente for preciso capturar algo.
4. Em Express 4, envolva os handlers async com `asyncHandler`, porque o Express 4 não captura promises rejeitadas.

**Antes (Python):**
```python
def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Depois (Python):**
```python
# src/utils/errors.py
class AppError(Exception):
    status_code = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404
```
```python
# src/middlewares/error_handler.py
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"erro": err.description, "sucesso": False}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```
```python
# src/views/produto_routes.py
@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    produto = produto_controller.buscar_produto(produto_id)   # lança NotFoundError
    return jsonify({"dados": produto, "sucesso": True}), 200
```

**Depois (JavaScript):**
```js
// src/utils/errors.js
class AppError extends Error {
    constructor(message, statusCode = 400) { super(message); this.statusCode = statusCode; }
}
class NotFoundError extends AppError { constructor(m) { super(m, 404); } }
class ValidationError extends AppError { constructor(m) { super(m, 400); } }
module.exports = { AppError, NotFoundError, ValidationError };

// src/middlewares/errorHandler.js
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

function notFound(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

function errorHandler(err, req, res, _next) {
    if (err instanceof AppError) {
        // Preserva o contrato: a baseline respondia texto puro nos erros deste endpoint
        return res.status(err.statusCode).type('text/plain').send(err.message);
    }
    logger.error(err);
    return res.status(500).type('text/plain').send('Erro interno');
}

module.exports = { asyncHandler, notFound, errorHandler };
```

---

## PB-13 — Validação de entrada na borda

**Corrige:** AP-15.

**Passos:**
1. Crie **um** validador por recurso/operação, usado por criar **e** atualizar (com modo parcial no update).
2. Cheque o body ausente/não objeto, os tipos (`isinstance(x, (int, float))` sem aceitar `bool`), as faixas, os enums e os formatos (email, data, cor, cartão).
3. Lance `ValidationError` com a **mesma mensagem** da baseline quando ela existir.
4. Reutilize os validadores que já existem em `utils/` em vez de criar novos.

**Antes:**
```python
dados = request.get_json()
if "preco" not in dados: ...
if preco < 0: ...                 # TypeError se preco for "abc"
```

**Depois:**
```python
# src/utils/validators.py
from src.utils.constants import CATEGORIAS_VALIDAS, NOME_MIN, NOME_MAX
from src.utils.errors import ValidationError


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def require_json_object(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")
    return data


def validar_produto(data):
    data = require_json_object(data)
    for campo, msg in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"),
                       ("estoque", "Estoque é obrigatório")):
        if campo not in data:
            raise ValidationError(msg)
    if not _is_number(data["preco"]) or data["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    if not isinstance(data["estoque"], int) or data["estoque"] < 0:
        raise ValidationError("Estoque não pode ser negativo")
    nome = str(data["nome"])
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    categoria = data.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")
    return {"nome": nome, "descricao": data.get("descricao", ""), "preco": data["preco"],
            "estoque": data["estoque"], "categoria": categoria}
```

**JavaScript:**
```js
function validateCheckoutInput({ usr, eml, c_id, card }) {
    if (!usr || !eml || !c_id || !card) throw new ValidationError('Bad Request');
    if (!EMAIL_REGEX.test(eml)) throw new ValidationError('Bad Request');
    if (!/^\d{13,19}$/.test(String(card))) throw new ValidationError('Bad Request');
}
```

---

## PB-14 — Extrair duplicação para uma fonte única

**Corrige:** AP-16.

**Passos:**
1. Mapeamentos `row → dict` repetidos viram uma função `row_to_<entidade>(row)`.
2. Funções quase idênticas viram uma função com parâmetro (filtro opcional).
3. Regras copiadas viram um método de domínio ou uma função utilitária, e todas as cópias passam a chamá-lo.

**Antes:**
```python
def get_todos_pedidos():
    cursor.execute("SELECT * FROM pedidos")
    ...  # 30 linhas
def get_pedidos_usuario(usuario_id):
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = " + str(usuario_id))
    ...  # as mesmas 30 linhas
```

**Depois:**
```python
def listar_com_itens(db, usuario_id=None):
    sql, params = BASE_PEDIDOS_SQL, []
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        params.append(usuario_id)
    sql += " ORDER BY p.id, i.id"
    return _agrupar_itens(db.execute(sql, params).fetchall())
```

**Regra copiada, antes → depois:**
```python
# em 6 lugares
if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled'): ...
```
```python
# models/task.py — fonte única
def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES
```

---

## PB-15 — Callbacks → async/await

**Corrige:** AP-17. Pré-requisito: o wrapper com Promises do PB-11.

**Passos:**
1. Troque os callbacks aninhados por `await` sequencial.
2. Use `Promise.all` para consultas independentes, ou elimine-as com JOIN (PB-10).
3. Remova os contadores manuais (`pending--`) e o `const self = this`.
4. Os erros vão para o handler central via `asyncHandler`.

**Antes:**
```js
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    if (err || !course) return res.status(404).send("Curso não encontrado");
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        if (err) return res.status(500).send("Erro DB");
        this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
            let enrId = this.lastID;
            self.db.run("INSERT INTO payments ...", [enrId, ...], function (err) { /* ... */ });
        });
    });
});
```

**Depois:**
```js
async checkout(input) {
    const course = await courseModel.findActiveById(input.c_id);
    if (!course) throw new NotFoundError('Curso não encontrado');
    const userId = await resolveUser(input);
    const { enrollmentId } = await enrollmentModel.enrollWithPayment({
        userId, courseId: course.id, amount: course.price, status: PAYMENT_STATUS.PAID,
    });
    return { enrollmentId };
}
```

---

## PB-16 — Constantes nomeadas

**Corrige:** AP-19.

**Passos:**
1. Crie `utils/constants` (ou `config` para os valores que mudam por ambiente).
2. Substitua cada literal com significado de negócio pela constante.
3. Se já existirem constantes não usadas, **passe a usá-las** em vez de criar novas.

**Antes:**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```

**Depois:**
```python
# src/utils/constants.py
FAIXAS_DESCONTO = (   # (faturamento mínimo exclusivo, percentual)
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
```
```python
def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0
```

**JavaScript:**
```js
// Antes
let status = cc.startsWith("4") ? "PAID" : "DENIED";
// Depois
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
const APPROVED_CARD_PREFIX = '4';   // regra do gateway simulado
const status = card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
```

---

## PB-17 — Renomear e remover código morto

**Corrige:** AP-20, AP-22.

**Passos:**
1. Renomeie os identificadores **internos** obscuros (`u`, `cc`, `cursor2`, `id` → `produto_id`). **Nunca renomeie** os campos do contrato HTTP (`usr`, `eml`, `c_id` no body ficam como estão: desestruture com alias).
2. Remova os imports não usados, as funções e constantes que nunca são chamadas, as configs não lidas e os arquivos que ficaram vazios.
3. Antes de apagar, confirme com grep que não há uso, **inclusive em scripts** (seed, CLI).

**Antes:**
```js
let u = req.body.usr;
let e = req.body.eml;
let cc = req.body.card;
```
```python
import os, sys, json, datetime   # só datetime é usado
```

**Depois:**
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;
```
```python
from datetime import datetime
```

---

## PB-18 — Logger no lugar de print/console.log

**Corrige:** AP-21.

**Passos:**
1. Configure um logger com o nível vindo da config.
2. Troque cada `print`/`console.log` pelo nível adequado (`info` para eventos, `warning` para recusas, `exception`/`error` em falhas).
3. Não logue PII nem segredos (PB-05).
4. "Notificações" simuladas com `print` viram uma chamada a um service de notificação injetado, que pode continuar só logando.
5. Mantenha o `print` em scripts CLI (seed) se for a saída esperada do script.

**Antes:**
```python
print("Usuário criado: " + email)
print("ENVIANDO EMAIL: Pedido " + str(pedido_id) + " criado para usuario " + str(usuario_id))
```

**Depois:**
```python
# src/app.py
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# src/controllers/usuario_controller.py
logger = logging.getLogger(__name__)
logger.info("Usuário criado id=%s", usuario_id)

# src/services/notification_service.py
def pedido_criado(self, pedido_id, usuario_id):
    logger.info("Notificação de pedido criado enviada pedido_id=%s usuario_id=%s", pedido_id, usuario_id)
```

**JavaScript (sem dependência nova):**
```js
// src/utils/logger.js
const config = require('../config');
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const threshold = LEVELS[config.logLevel] ?? LEVELS.info;

const log = (level) => (...args) => {
    if (LEVELS[level] <= threshold) console[level === 'debug' ? 'log' : level](`[${level.toUpperCase()}]`, ...args);
};

module.exports = { error: log('error'), warn: log('warn'), info: log('info'), debug: log('debug') };
```
