@echo off
echo Starting Alt-F4 Waypoint with Docker Compose...
echo.

REM Check if docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed or not in your PATH.
    echo Please install Docker Desktop to run this repository.
    pause
    exit /b 1
)

REM Build and start containers
echo Stopping any existing containers and removing volumes...
docker compose down -v

echo.
echo Building the images...
docker compose build

echo.
echo Starting the containers...
docker compose up -d

echo.
echo =======================================================
echo Waypoint has been started successfully!
echo.
echo Frontend URL:        http://localhost:3000
echo Backend API URL:     http://localhost:8000/api/v1
echo Backend Health:      http://localhost:8000/health
echo =======================================================
echo.
echo To view logs, you can run: docker compose logs -f
echo To stop the app, you can run: docker compose down
echo.
pause
