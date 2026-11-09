@echo off
setlocal
cd /d "%~dp0"
set "INSTALLED_FILE=%LOCALAPPDATA%\FIFA15LocalFUT\installed-game.txt"
if exist "%INSTALLED_FILE%" (
  set /p "GAME="<"%INSTALLED_FILE%"
  if exist "%GAME%\ADMIN_MENU.cmd" (
    call "%GAME%\ADMIN_MENU.cmd"
    exit /b %errorlevel%
  )
)
set "PY=%~dp0payload\runtime\python\python.exe"
if exist "%PY%" goto run
where py >nul 2>nul && set "PY=py -3" && goto run
where python >nul 2>nul && set "PY=python" && goto run
echo Python was not found. Run INSTALL_PREREQUISITES.cmd first.
pause
exit /b 1
:run
start "FIFA 15 Local FUT Admin" %PY% "%~dp0payload\localfut15\admin_menu.py"
