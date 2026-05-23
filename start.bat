@echo off
echo ============================================
echo  PortalAI - Starting all services...
echo ============================================

echo [1/3] Starting Portaldot local node (WSL)...
start "Portaldot Node" wsl -d Ubuntu -e bash -c "cd ~/portaldot-node/portaldot-testnet-ubuntu && ./portaldot_dev --dev --alice --rpc-external --ws-external"

echo Waiting 10s for node to initialize...
timeout /t 10 /nobreak >nul

echo [2/3] Starting backend (FastAPI)...
start "PortalAI Backend" cmd /k "cd /d C:\Users\Administrator\Desktop\Hackthon\backend && python -m uvicorn main:app --reload --port 8000"

echo Waiting 6s for backend to start...
timeout /t 6 /nobreak >nul

echo Checking backend health...
:check_backend
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo   Backend not ready yet, waiting 3s...
    timeout /t 3 /nobreak >nul
    goto check_backend
)
echo   Backend OK!

echo [3/3] Starting frontend (Next.js)...
start "PortalAI Frontend" cmd /k "cd /d C:\Users\Administrator\Desktop\Hackthon\frontend && npm run dev"

echo.
echo Waiting for frontend to compile (this may take 30-60 seconds)...
echo Please watch the "PortalAI Frontend" window for the "Ready" message.
echo.

:check_frontend
timeout /t 5 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    echo   Still compiling... 
    goto check_frontend
)
echo   Frontend OK!

echo.
echo ============================================
echo  All services are ready!
echo  - Node:     ws://127.0.0.1:9944
echo  - Backend:  http://localhost:8000
echo  - Frontend: http://localhost:3000
echo ============================================

start http://localhost:3000
echo Browser opened. Enjoy PortalAI!
pause
