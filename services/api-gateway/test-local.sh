#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Building gateway image..."
docker compose build gateway

echo "==> Starting stack..."
docker compose up -d

cleanup() {
  echo "==> Tearing down..."
  docker compose down
}
trap cleanup EXIT

echo "==> Waiting for gateway..."
for i in $(seq 1 30); do
  if curl -sf "http://localhost:3000/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> GET /health"
curl -sf "http://localhost:3000/health" | head -c 400
echo ""

echo "==> GET /metrics (first lines)"
curl -sf "http://localhost:3000/metrics" | head -n 8
echo ""

echo "==> Smoke test OK"
