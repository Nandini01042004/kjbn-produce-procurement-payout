@echo off
echo ===================================================================
echo Starting KJBN Produce Procurement Engine (Local Bring-Up)
echo ===================================================================

echo [1/3] Running migrate and seed...
python backend\seed.py

echo [2/3] Starting backend FastAPI server on http://localhost:8000...
start cmd /k "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Starting frontend Vite dev server on http://localhost:5173...
start cmd /k "cd frontend && npm run dev"

echo All services launched!
echo UI: http://localhost:5173
echo API Docs: http://localhost:8000/docs
