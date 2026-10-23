#!/usr/bin/env bash
# Smoke test — ecommerce-api-legacy (Node.js/Express, LMS + checkout)
# Pré-condição: app recém-iniciada (banco em memória com seed).
# Uso: BASE_URL=http://localhost:3000 ./scripts/smoke-test-project-2.sh
set -u
source "$(dirname "$0")/lib.sh"
BASE_URL="${BASE_URL:-http://localhost:3000}"

echo "ecommerce-api-legacy @ $BASE_URL"

check checkout_ok       POST   /api/checkout                200 '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
check checkout_existing POST   /api/checkout                200 '{"usr":"Leonan","eml":"leonan@fullcycle.com.br","pwd":"123","c_id":2,"card":"4111222233334444"}'
check checkout_denied   POST   /api/checkout                400 '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
check checkout_400      POST   /api/checkout                400 '{"usr":"João"}'
check checkout_404      POST   /api/checkout                404 '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":999,"card":"4111222233334444"}'

check financial_report  GET    /api/admin/financial-report  200

check user_delete       DELETE /api/users/1                 200

summary
