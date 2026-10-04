@echo off
echo ===================================================
echo Starting Waypoint Application Stack
echo ===================================================

echo [1/3] Starting PostgreSQL (Docker)...
docker-compose up -d

echo.
echo [2/3] Starting Backend Server (FastAPI)...
start cmd /k "cd apps\backend && title Waypoint Backend && uvicorn app.main:app --reload --port 8000"

echo.
echo [3/3] Starting Frontend Server (Vite)...
start cmd /k "cd apps\frontend && title Waypoint Frontend && npm run dev"

echo.
echo ===================================================
echo All systems are starting in separate windows!
echo Backend API will be at: http://localhost:8000
echo Frontend will be at:    http://localhost:5173
echo ===================================================
pause
