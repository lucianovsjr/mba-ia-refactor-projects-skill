#!/usr/bin/env bash
# Smoke test — task-manager-api (Python/Flask, Task Manager)
# Pré-condição: rodar `python seed.py` antes de subir a app.
# Uso: BASE_URL=http://localhost:5002 ./scripts/smoke-test-project-3.sh
# Opcional: SECRET_KEY=<a mesma da app> também confere a assinatura do token do login,
# com o itsdangerous do .venv do projeto (ou do interpretador em PYTHON).
# As checagens de token (F-02) falham de propósito no código original, que devolve
# o previsível `fake-jwt-token-<id>`. As demais valem para o original e o refatorado.
set -u
source "$(dirname "$0")/lib.sh"
BASE_URL="${BASE_URL:-http://localhost:5000}"
PYTHON="${PYTHON:-$(dirname "$0")/../task-manager-api/.venv/bin/python}"

echo "task-manager-api @ $BASE_URL"

login_token() {
  curl -s -X POST -H "Content-Type: application/json" \
    -d '{"email":"joao@email.com","password":"1234"}' "$BASE_URL/login" \
    | sed -nE 's/.*"token": ?"([^"]*)".*/\1/p'
}

not_predictable() {
  [[ -n "$1" && ! "$1" =~ ^fake-jwt-token-[0-9]+$ ]]
}

# Aceita o token emitido para o usuário 1 e rejeita um forjado e um adulterado.
signature_valid() {
  "$PYTHON" -I -c '
import sys
from itsdangerous import BadSignature, URLSafeTimedSerializer

key, token = sys.argv[1], sys.argv[2]
serializer = URLSafeTimedSerializer(key, salt="login-token")
try:
    if serializer.loads(token, max_age=60 * 60 * 24) != {"uid": 1}:
        sys.exit(1)
except BadSignature:
    sys.exit(1)
for forged in ("fake-jwt-token-1", token[:-1] + ("A" if token[-1] != "A" else "B")):
    try:
        serializer.loads(forged)
        sys.exit(1)
    except BadSignature:
        pass
' "$SECRET_KEY" "$1"
}

check tasks_list       GET    /tasks                    200
check tasks_search     GET    "/tasks/search?q=login&status=in_progress" 200
check tasks_stats      GET    /tasks/stats              200
check task_get         GET    /tasks/1                  200
check task_404         GET    /tasks/9999               404
check task_create      POST   /tasks                    201 '{"title":"Nova task","description":"Desc","priority":2,"user_id":1,"category_id":1,"due_date":"2030-01-01","tags":["a","b"]}'
check task_400         POST   /tasks                    400 '{"title":"ab"}'
check task_update      PUT    /tasks/2                  200 '{"status":"done","priority":1}'
check task_delete      DELETE /tasks/3                  200

check users_list       GET    /users                    200
check user_get         GET    /users/1                  200
check user_404         GET    /users/9999               404
check user_create      POST   /users                    201 '{"name":"Ana","email":"ana@email.com","password":"segredo","role":"user"}'
check user_409         POST   /users                    409 '{"name":"Ana","email":"ana@email.com","password":"segredo"}'
check user_update      PUT    /users/2                  200 '{"name":"Maria S."}'
check user_tasks       GET    /users/1/tasks            200
check login_ok         POST   /login                    200 '{"email":"joao@email.com","password":"1234"}'
check login_401        POST   /login                    401 '{"email":"joao@email.com","password":"errada"}'

TOKEN="$(login_token)"
assert "token do login não é previsível"   not_predictable "$TOKEN"
if [[ -n "${SECRET_KEY:-}" ]]; then
  assert "token assinado com a SECRET_KEY"  signature_valid "$TOKEN"
fi

check report_summary   GET    /reports/summary          200
check report_user      GET    /reports/user/1           200
check report_user_404  GET    /reports/user/9999        404

check categories_list  GET    /categories               200
check category_create  POST   /categories               201 '{"name":"QA","description":"Testes","color":"#123456"}'
check category_update  PUT    /categories/1             200 '{"name":"Backend API"}'
check category_delete  DELETE /categories/5             200

check user_delete      DELETE /users/3                  200

summary
