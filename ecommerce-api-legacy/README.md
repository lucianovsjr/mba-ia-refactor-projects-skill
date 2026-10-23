# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

Requer Node.js >= 20.17.

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

Todas são opcionais (veja `.env.example`):

| Variável | Default | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DATABASE_FILE` | `:memory:` | Arquivo SQLite (`:memory:` reinicia a cada boot) |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |
| `ADMIN_TOKEN` | vazio | Se definido, `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Admin-Token` |

## Estrutura

```
src/
├── app.js          # entry point
├── server.js       # composition root (buildApp)
├── config/         # leitura de variáveis de ambiente
├── database/       # conexão, transações, schema e seed
├── models/         # acesso a dados por domínio
├── controllers/    # casos de uso
├── routes/         # rotas HTTP
├── services/       # gateway de pagamento simulado
├── middlewares/    # error handler e guarda admin
└── utils/          # constantes, erros, validação, hash de senha, logger
```
