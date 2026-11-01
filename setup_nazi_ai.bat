@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo        NAZI AI - WINDOWS SETUP
echo ==========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
  echo Python Launcher was not found. Install Python 3.11 or newer first.
  pause
  exit /b 1
)

py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 or newer was not found. Install Python 3.11+, then run this file again.
  pause
  exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
  echo Node.js was not found. Install Node.js 20 LTS or newer first.
  pause
  exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
  echo Creating Python environment...
  py -3 -m venv backend\.venv
  if errorlevel 1 goto failed
)

echo Installing backend dependencies...
call "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
call "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed

if not exist "backend\.env" (
  copy "backend\.env.example" "backend\.env" >nul
  echo Created backend\.env. Add your private AI API key and model there.
)

echo Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 goto failed

echo.
echo Setup completed.
echo Next: run start_nazi_ai.bat from the project folder.
pause
exit /b 0

:failed
echo.
echo Setup failed. Check the error above and try again.
pause
exit /b 1
