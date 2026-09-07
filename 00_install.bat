@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

where py >nul 2>nul
if not errorlevel 1 goto USE_PY
where python >nul 2>nul
if not errorlevel 1 goto USE_PYTHON

echo Python was not found.
echo Install Python 3 and enable "Add Python to PATH", then run this file again.
pause
exit /b 1

:USE_PY
set "PYCMD=py -3"
goto INSTALL

:USE_PYTHON
set "PYCMD=python"

:INSTALL
echo Installing required Python packages...
%PYCMD% -m pip install --upgrade requests openpyxl playwright
if errorlevel 1 goto INSTALL_FAIL

echo.
echo Installation completed successfully.
echo You do NOT need to run playwright install because this package uses Google Chrome.
pause
exit /b 0

:INSTALL_FAIL
echo.
echo Package installation failed.
echo Check that Python and pip are installed correctly.
pause
exit /b 1
