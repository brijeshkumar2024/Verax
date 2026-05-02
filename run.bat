@echo off
echo ======================================
echo  VERAX Project Launcher
echo ======================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/4] Setting up Python virtual environment...
cd /d "%~dp0backend"
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
echo       Done.

echo [2/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install
echo       Done.

echo.
echo ======================================
echo  Starting servers...
echo ======================================
echo.

REM Start backend server in background
start "VERAX Backend" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend server
start "VERAX Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ======================================
echo  Servers started!
echo  - Backend: http://localhost:8000
echo  - Frontend: http://localhost:3000
echo ======================================
echo.
echo Press any key to exit this window...
pause >nul
