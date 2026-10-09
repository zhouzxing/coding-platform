#!/usr/bin/env bash
# One-shot start: launches backend (FastAPI on :8001) + frontend (Vite on :5173)
set -e

cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Backend
if [ ! -d app/.venv ]; then
  echo "[start] Creating backend venv..."
  (cd app && python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt)
fi

echo "[start] Starting backend on :$BACKEND_PORT"
(cd app && .venv/bin/uvicorn app:app --host 127.0.0.1 --port "$BACKEND_PORT" --log-level info) &
BACKEND_PID=$!

# Frontend
if [ ! -d web/node_modules ]; then
  echo "[start] Installing frontend deps..."
  (cd web && npm install)
fi

echo "[start] Starting frontend on :$FRONTEND_PORT"
(cd web && npm run dev -- --port "$FRONTEND_PORT" --host 127.0.0.1) &
FRONTEND_PID=$!

echo
echo "============================================================"
echo " Coding Platform is up:"
echo "   Backend  : http://127.0.0.1:$BACKEND_PORT  (API + /api/health)"
echo "   Frontend : http://127.0.0.1:$FRONTEND_PORT  (React app)"
echo "============================================================"
echo
echo "Ctrl-C to stop."
wait -n $BACKEND_PID $FRONTEND_PID || true
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
