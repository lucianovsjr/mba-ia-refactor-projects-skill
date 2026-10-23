#!/usr/bin/env bash
# Helpers compartilhados pelos smoke tests.
# Uso: source lib.sh; check <nome> <METHOD> <path> <status_esperado> [json_body]
# Variáveis: BASE_URL (obrigatória), OUT_DIR (opcional — salva o corpo de cada resposta)

PASS=0
FAIL=0

check() {
  local name="$1" method="$2" path="$3" expected="$4" body="${5:-}"
  local tmp status
  tmp="$(mktemp)"

  if [[ -n "$body" ]]; then
    status=$(curl -s -o "$tmp" -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" -d "$body" "$BASE_URL$path")
  else
    status=$(curl -s -o "$tmp" -w "%{http_code}" -X "$method" "$BASE_URL$path")
  fi

  if [[ -n "${OUT_DIR:-}" ]]; then
    mkdir -p "$OUT_DIR"
    cp "$tmp" "$OUT_DIR/$name.json"
  fi

  if [[ "$status" == "$expected" ]]; then
    PASS=$((PASS + 1))
    printf "  ✓ %-6s %-40s %s\n" "$method" "$path" "$status"
  else
    FAIL=$((FAIL + 1))
    printf "  ✗ %-6s %-40s %s (esperado %s) %s\n" "$method" "$path" "$status" "$expected" "$(head -c 120 "$tmp")"
  fi
  rm -f "$tmp"
}

summary() {
  echo "--------------------------------"
  echo "  $PASS passed | $FAIL failed"
  [[ "$FAIL" -eq 0 ]]
}
