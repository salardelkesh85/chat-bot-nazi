@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"

if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
  echo Run setup_nazi_ai.bat first.
  pause
  exit /b 1
)
if not exist "%ROOT%frontend\node_modules\vite\bin\vite.js" (
  echo Frontend dependencies are missing. Run setup_nazi_ai.bat first.
  pause
  exit /b 1
)
if not exist "%ROOT%backend\.env" (
  copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
  if errorlevel 1 (
    echo Could not create backend\.env.
    pause
    exit /b 1
  )
)

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:8000/api/health | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
  echo Backend already running on port 8000. Reusing it.
) else (
  echo Starting Nazi AI backend...
  start "NAZI AI Backend" /D "%ROOT%backend" cmd /k ""%ROOT%backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

echo Waiting for backend health check...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 40;$i++){try{$r=Invoke-RestMethod -TimeoutSec 2 'http://127.0.0.1:8000/api/health';if($r.status -eq 'ok'){$ok=$true;break}}catch{};Start-Sleep -Seconds 1};if($ok){exit 0}else{exit 1}"
if errorlevel 1 (
  echo [ERROR] Backend did not become ready within 40 seconds.
  echo Check the NAZI AI Backend window for the error.
  pause
  exit /b 1
)

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:5173 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
  echo Frontend already running on port 5173. Reusing it.
) else (
  echo Starting Nazi AI frontend...
  start "NAZI AI Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"
)

echo Waiting for frontend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 30;$i++){try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:5173';if($r.StatusCode -eq 200){$ok=$true;break}}catch{};Start-Sleep -Seconds 1};if($ok){exit 0}else{exit 1}"
if errorlevel 1 (
  echo [ERROR] Frontend did not become ready within 30 seconds.
  echo Check the NAZI AI Frontend window for the error.
  pause
  exit /b 1
)

echo.
echo Nazi AI is ready. Opening your local app...
start "" "http://127.0.0.1:5173"
echo.
echo Keep the backend and frontend windows open while using Nazi AI.
echo To stop both servers, run stop_nazi_ai.bat.
exit /b 0
