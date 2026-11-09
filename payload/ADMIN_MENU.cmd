@echo off
setlocal
cd /d "%~dp0"
where pyw.exe >nul 2>nul && start "" pyw -3 "%~dp0localfut15\admin_menu.py" && exit /b 0
where pythonw.exe >nul 2>nul && start "" pythonw "%~dp0localfut15\admin_menu.py" && exit /b 0
where py.exe >nul 2>nul && start "FIFA 15 Local FUT Admin" py -3 "%~dp0localfut15\admin_menu.py" && exit /b 0
where python.exe >nul 2>nul && start "FIFA 15 Local FUT Admin" python "%~dp0localfut15\admin_menu.py" && exit /b 0
echo Python was not found. Run INSTALL_PREREQUISITES.cmd first.
pause
