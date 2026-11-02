@echo off
setlocal
echo Stopping Nazi AI services on localhost...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=8000,5173; foreach($port in $ports){$connections=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue;foreach($connection in $connections){$process=Get-CimInstance Win32_Process -Filter ('ProcessId = '+$connection.OwningProcess) -ErrorAction SilentlyContinue;if($process -and ($process.CommandLine -match 'uvicorn|vite|npm')){& taskkill.exe /PID $connection.OwningProcess /T /F 2>$null | Out-Null}}}"
echo Done. If a server window remains open, close it manually.
pause
