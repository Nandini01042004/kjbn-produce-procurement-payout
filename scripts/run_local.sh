#!/usr/bin/env bash
set -e

echo "==================================================================="
echo "Starting KJBN Produce Procurement Engine (Local Bring-Up)"
echo "==================================================================="

echo "[1/3] Running migrate and seed..."
python3 backend/seed.py

echo "[2/3] Starting backend FastAPI server on http://localhost:8000..."
(cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

echo "[3/3] Starting frontend Vite dev server on http://localhost:5173..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "All services running!"
echo "UI: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
