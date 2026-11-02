@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo          NAZI AI - WINDOWS SETUP
echo ==========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python Launcher was not found.
  echo Install Python 3.11 or 3.12 from python.org and enable Add Python to PATH.
  goto failed
)
set "PYTHON_LAUNCHER="
py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_LAUNCHER=py -3.12"
if not defined PYTHON_LAUNCHER (
  py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,11) else 1)" >nul 2>&1
  if not errorlevel 1 set "PYTHON_LAUNCHER=py -3.11"
)
if not defined PYTHON_LAUNCHER (
  echo [ERROR] Python 3.11 or 3.12 was not found.
  echo Detected Python installations:
  py -0p
  goto failed
)
echo Using %PYTHON_LAUNCHER% for the backend environment.

if exist "backend\.venv\Scripts\python.exe" (
  "backend\.venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,13) else 1)" >nul 2>&1
  if errorlevel 1 (
    echo Removing an old virtual environment with an unsupported Python version...
    rmdir /s /q "backend\.venv"
    if exist "backend\.venv" goto failed
  )
)

where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js 20 LTS or 22 LTS is required.
  goto failed
)
node -e "const v=process.versions.node.split('.').map(Number);process.exit(v[0]>=20?0:1)" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js 20 or newer is required. Install Node.js LTS and retry.
  goto failed
)

if not exist "backend\.venv\Scripts\python.exe" (
  echo [1/5] Creating Python virtual environment...
  %PYTHON_LAUNCHER% -m venv backend\.venv
  if errorlevel 1 goto failed
)

echo [2/5] Installing backend dependencies...
call "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
call "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed

if not exist "backend\.env" (
  copy "backend\.env.example" "backend\.env" >nul
  if errorlevel 1 goto failed
  echo Created backend\.env. Choose a local Ollama model or configure an API provider.
)

echo [3/5] Preparing local data folders...
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\data\media" mkdir "backend\data\media"
if not exist "backend\data\backups" mkdir "backend\data\backups"

echo [4/5] Installing pinned frontend dependencies...
cd /d "%~dp0frontend"
call npm install --no-audit --no-fund
if errorlevel 1 goto failed

echo [5/5] Verifying Python modules and frontend packages...
cd /d "%~dp0"
call "backend\.venv\Scripts\python.exe" -m compileall -q backend\app
if errorlevel 1 goto failed
if not exist "frontend\node_modules\vite\bin\vite.js" goto failed

echo.
echo ==========================================
echo SETUP COMPLETE
echo Next: double-click start_nazi_ai.bat
echo ==========================================
pause
exit /b 0

:failed
echo.
echo [ERROR] Setup did not complete. Read the message above.
echo Check your internet connection and installed Python/Node versions.
pause
exit /b 1
