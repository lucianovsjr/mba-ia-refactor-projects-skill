# Guidelines de Arquitetura — MVC Alvo

Referência da **Fase 3**. Define a arquitetura que a refatoração deve produzir: as camadas, a responsabilidade de cada uma, as regras de dependência e a estrutura de pastas para cada stack.

> Em APIs HTTP não há templates HTML, então a **View** é a camada de apresentação HTTP: as **rotas** (mapeamento URL/método → controller) e os **serializers/presenters**, que transformam entidades em JSON.

---

## 1. Camadas e responsabilidades

| Camada | Responsabilidade | Pode | Não pode |
|---|---|---|---|
| **Config** | Centralizar configurações lidas do ambiente | Ler `os.environ` / `process.env`, definir defaults seguros de dev, expor um objeto de config | Ter segredos reais; ser alterada em runtime |
| **Database / infra de dados** | Criar e fornecer a conexão/sessão; schema e seed | Abrir a conexão por app/requisição, oferecer helper de transação | Conter regras de negócio; rodar efeitos colaterais no import |
| **Models** | Representar entidades e encapsular o **acesso a dados** de um domínio | SQL parametrizado ou ORM, mapear linha → entidade, métodos de domínio puros (ex.: `is_overdue()`) | Ler `request`/`req`, devolver respostas HTTP, conhecer status codes |
| **Controllers** | Orquestrar **casos de uso**: validar a regra de negócio, coordenar models e serviços, controlar transações | Chamar models e serviços, lançar exceções de domínio, devolver dados (dict/objeto) | Ler `request` diretamente, montar respostas HTTP, escrever SQL |
| **Views / Routes** | Traduzir HTTP ↔ controller | Declarar rotas, extrair path/query/body, chamar **um** método de controller, serializar, escolher o status de sucesso | Ter regra de negócio, acessar o banco, decidir fluxos de domínio |
| **Serializers / Presenters** (parte da View) | Converter entidades em JSON com **lista branca** de campos | Formatar datas e listas, omitir campos sensíveis | Consultar o banco |
| **Middlewares** | Preocupações transversais | Error handler central, validação comum, CORS, logging de requisição, guarda de rotas admin | Ter regra de negócio de um domínio específico |
| **Services** (opcional) | Integrações externas e infraestrutura usadas pelos controllers | E-mail, gateway de pagamento, filas, cache, sempre injetados | Ser chamados direto pelas rotas; acessar `request` |
| **Entry point / Composition root** | Montar a aplicação | Criar a app (factory), carregar a config, instanciar e injetar dependências, registrar rotas e middlewares, iniciar o servidor | Ter rotas ou regras inline |

### Fluxo de uma requisição

```
HTTP → Route (View) → Controller → Model → DB
                 ↘ Validator      ↘ Service (e-mail, pagamento)
HTTP ← Serializer ← Controller (dados ou exceção de domínio)
        ↑
   Error handler (middleware) traduz exceções → status + JSON
```

---

## 2. Regras de dependência

1. **A dependência vai sempre para dentro:** Routes → Controllers → Models/Services → Database/Config. Nunca no sentido inverso: um model jamais importa uma rota ou um controller.
2. **Só as Routes conhecem o framework HTTP** (`request`, `jsonify`, `req`, `res`). Controllers e models devem funcionar num teste unitário sem servidor.
3. **Erros sobem como exceções de domínio** (`NotFoundError`, `ValidationError`, `ConflictError`, `BusinessRuleError`). O error handler central decide o status HTTP e o formato do corpo.
4. **Uma fonte de verdade por regra:** constantes, validações e cálculos de domínio vivem em um único lugar (model/controller/módulo de constantes) e são reutilizados.
5. **Dependências injetadas:** a conexão, a config e os serviços chegam por parâmetro, construtor ou contexto da app. Não há singletons globais mutáveis.
6. **Sem efeitos colaterais no import:** criar tabelas, rodar seed e abrir conexões acontece dentro da factory/boot, nunca no topo de um módulo.

---

## 3. Estrutura de pastas alvo

### 3.1 Python / Flask

```
<projeto>/
├── app.py                      # entry point fino: from src.app import create_app; app = create_app()
├── requirements.txt            # dependências com versão fixa
├── .env.example                # variáveis esperadas, sem valores reais
├── seed.py                     # (se existir) usa create_app(), não a app global
└── src/
    ├── __init__.py
    ├── app.py                  # composition root: create_app(config) → registra blueprints, middlewares, db
    ├── config/
    │   └── settings.py         # class Settings: lê os.environ com defaults de dev
    ├── database/
    │   └── connection.py       # init_db(app), get_db(), transaction(); schema/seed
    ├── models/
    │   └── <dominio>_model.py  # acesso a dados de UM domínio
    ├── controllers/
    │   └── <dominio>_controller.py
    ├── views/                  # (ou routes/) — blueprints por domínio
    │   ├── <dominio>_routes.py
    │   └── serializers.py
    ├── middlewares/
    │   ├── error_handler.py    # register_error_handlers(app)
    │   └── auth.py             # guarda de rotas admin (quando aplicável)
    ├── services/               # (opcional) integrações externas
    └── utils/
        ├── constants.py        # enums/limites de domínio
        ├── errors.py           # exceções de domínio
        └── validators.py       # validação de entrada reutilizável
```

**Por que manter um `app.py` fino na raiz:** os comandos de boot existentes (`python app.py` e `flask --app app run`) continuam funcionando. O `app.py` raiz só importa `create_app`, expõe `app` e, no bloco `__main__`, chama `app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)`.

### 3.2 Node.js / Express

```
<projeto>/
├── package.json                # "main"/"start" apontando para o entry point
├── .env.example
└── src/
    ├── app.js                  # entry point: carrega config, chama buildApp(), app.listen(config.port)
    ├── server.js               # (opcional) buildApp(deps): cria express(), middlewares, rotas — testável
    ├── config/
    │   └── index.js            # lê process.env com defaults de dev
    ├── database/
    │   └── connection.js       # abre a conexão, helpers async (run/get/all), transaction(), schema/seed
    ├── models/
    │   └── <dominio>Model.js   # acesso a dados de UM domínio (async/await)
    ├── controllers/
    │   └── <dominio>Controller.js
    ├── routes/                 # Views: um Router por domínio
    │   └── <dominio>Routes.js
    ├── middlewares/
    │   ├── errorHandler.js     # (err, req, res, next) + notFound
    │   └── adminGuard.js       # (quando aplicável)
    ├── services/               # (opcional) pagamento, e-mail
    └── utils/
        ├── constants.js
        ├── errors.js
        └── crypto.js           # hash de senha com crypto.scrypt
```

Mantenha o caminho do entry point declarado em `package.json` (`main`, `scripts.start`). Se ele mudar, atualize o `package.json`.

### 3.3 Outras stacks

Siga a convenção idiomática do framework, mantendo as mesmas camadas: Django (`models.py`, `views.py`, `urls.py`, `services.py` por app), FastAPI (`routers/`, `schemas/`, `services/`, `models/`), NestJS (`*.controller.ts`, `*.service.ts`, `*.entity.ts` por módulo), Spring (`controller/`, `service/`, `repository/`, `config/`).

---

## 4. Adaptando ao ponto de partida

### 4.1 Monolito (um ou poucos arquivos misturando tudo)

1. Crie a estrutura completa da §3.
2. Separe **por domínio** (identifique-os pelas tabelas/entidades) e **por camada**: o SQL de produtos vai para `produto_model`, as regras para `produto_controller` e as rotas para `produto_routes`.
3. Os arquivos antigos são **removidos** depois da migração, e o entry point original vira o entry point fino.

### 4.2 Projeto parcialmente em camadas

Não reescreva o que já está no lugar certo. **Complete e conserte**:

| Situação encontrada | Ação |
|---|---|
| `models/` com ORM correto | **Manter**. Remover campos sensíveis do `to_dict()` (ou criar um serializer) e trocar APIs deprecated |
| `routes/` com regra de negócio e queries | Criar `controllers/` e **mover** a lógica para eles. As rotas ficam finas |
| Métodos de domínio nos models que não são usados (`is_overdue`, `validate_*`) | **Passar a usar** no controller e apagar as cópias inline das rotas |
| `services/` existente mas nunca chamado | Manter como camada de serviço **injetada nos controllers**, se fizer sentido para o domínio, ou remover. Os segredos vão para a config |
| `utils/helpers.py` com validações/constantes ignoradas | Mover para `utils/validators.py` / `utils/constants.py` e **usar**, ou apagar o que for morto |
| `app.py` com app global e `create_all()` no import | Converter em `create_app()`. Mover `create_all()`/seed para dentro da factory |
| Pastas na raiz (`models/`, `routes/`) | Pode manter na raiz, adicionando `controllers/`, `config/` e `middlewares/` ao lado, se mover tudo para `src/` exigir mexer em todos os imports sem ganho. Seja consistente |

### 4.3 Em qualquer caso

- Os **nomes** de arquivo seguem o domínio e o idioma do projeto (`produto_controller.py` num projeto em português, `task_controller.py` num em inglês).
- Um controller por domínio; separe em mais de um quando passar de ~300 linhas.
- Scripts auxiliares (seed, migrations) usam a factory/config, nunca a app global.

---

## 5. Contrato público e mudanças permitidas

**Regra:** paths, métodos, status codes e formato das respostas (chaves de topo, envelope, tipo de conteúdo) permanecem **idênticos** aos da baseline. Isso inclui manter respostas que hoje são texto puro, se a baseline for texto puro, para não quebrar clientes. A padronização vale para os **novos** erros tratados pelo handler central.

**Exceções permitidas (correções de segurança), que precisam ser listadas em `## Contract changes`:**

| Correção | Exemplo |
|---|---|
| Remover dados sensíveis das respostas | tirar `senha`/`password`/hash do JSON de usuário; tirar `secret_key`/`db_path` do health |
| Desabilitar endpoints que executam SQL/código arbitrário ou destroem dados | `/admin/query`, `/admin/reset-db`: removidos, ou habilitados só com `ENABLE_ADMIN_ENDPOINTS=true` **e** um token de admin vindo da env (padrão: desligado → 404/403) |
| Bloquear escalada de privilégio | ignorar `role`/`is_admin`/`tipo` vindos do body de criação pública; exigir credencial válida antes de agir em nome de um usuário existente |
| Rejeitar entradas que corrompem dados | quantidades negativas, IDs de referência inexistentes → 400/404 em vez de 201 |
| Responder erro onde a baseline mentia | `DELETE` de recurso inexistente → 404 em vez de 200 |

**Fora do escopo** (registre como recomendação remanescente, não implemente): exigir autenticação nas rotas comuns que hoje são públicas, ou trocar o mecanismo de login/token. Isso quebraria todos os clientes existentes e exige decisão de produto.

---

## 6. Checklist da arquitetura final

- [ ] Existe um módulo de config e nenhum segredo/URI/porta fixa no código
- [ ] Existem models por domínio, só com acesso a dados (SQL parametrizado/ORM)
- [ ] As Views/Routes só fazem HTTP: nenhuma query e nenhuma regra de negócio nos handlers
- [ ] Os controllers concentram os casos de uso e não importam o framework HTTP
- [ ] O error handler é centralizado e responde em JSON a exceções de domínio e 404/500
- [ ] Há um entry point claro / composition root, e nenhum efeito colateral no import
- [ ] Não há estado global mutável, e as dependências são injetadas
- [ ] Os arquivos antigos foram removidos e não sobrou código morto nem import não usado
- [ ] Os comandos de boot e seed documentados funcionam
