@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "$r=Join-Path $env:LOCALAPPDATA 'FIFA15LocalFUT\runtime_ports.json'; if(Test-Path $r){try{$p=(Get-Content $r -Raw|ConvertFrom-Json).server_pid; if($p){Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue}}catch{}}; Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -like '*localfut15*server.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>nul
del /q "%LOCALAPPDATA%\FIFA15LocalFUT\runtime_ports.json" >nul 2>nul
if /i not "%~1"=="/quiet" (
  echo FIFA 15 Local FUT server stopped.
  pause
)
endlocal
