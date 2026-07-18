@echo off
echo ========================================
echo  Starting System...
echo ========================================

echo [1/3] Starting backend server (port 8080)...
start "backend" /B python run.py

echo [2/3] Starting frontend server (port 5173)...
cd frontend
start "frontend" /B npm run dev
cd ..

echo [3/3] Waiting for services...
timeout /t 6 /nobreak >nul

echo Opening browser...
start http://localhost:5173

echo ========================================
echo  Services started!
echo  Backend: http://localhost:8080
echo  Frontend: http://localhost:5173
echo ========================================
pause