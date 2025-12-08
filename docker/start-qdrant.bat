@echo off
echo Starting Qdrant Vector Database...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Start Qdrant
docker-compose up -d

REM Wait for startup
echo Waiting for Qdrant to be ready...
timeout /t 5 /nobreak >nul

REM Check status
curl -s http://localhost:6333/ >nul 2>&1
if errorlevel 1 (
    echo Qdrant may still be starting up...
    echo Check status: docker-compose ps
    echo View logs: docker-compose logs qdrant
) else (
    echo Qdrant is running!
    echo.
    echo Dashboard: http://localhost:6333/dashboard
    echo API Docs: http://localhost:6333/docs
    echo HTTP API: http://localhost:6333
    echo.
    echo To stop: docker-compose stop
    echo To view logs: docker-compose logs -f qdrant
)

pause