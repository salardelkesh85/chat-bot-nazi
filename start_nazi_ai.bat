@echo off
setlocal
set "ROOT=%~dp0"

if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
  echo Run setup_nazi_ai.bat first.
  pause
  exit /b 1
)
if not exist "%ROOT%frontend\node_modules" (
  echo Frontend packages are missing. Run setup_nazi_ai.bat first.
  pause
  exit /b 1
)
if not exist "%ROOT%backend\.env" (
  copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
  echo Created backend\.env. Add your API settings before chatting.
)

start "NAZI AI Backend" cmd /k "cd /d ""%ROOT%backend"" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
start "NAZI AI Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm run dev -- --host 127.0.0.1"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:5173"
