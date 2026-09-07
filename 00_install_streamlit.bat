@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

where py >nul 2>nul
if not errorlevel 1 goto USE_PY
where python >nul 2>nul
if not errorlevel 1 goto USE_PYTHON

echo Python was not found.
pause
exit /b 1

:USE_PY
set "PYCMD=py -3"
goto INSTALL

:USE_PYTHON
set "PYCMD=python"

:INSTALL
%PYCMD% -m pip install -r requirements_streamlit.txt
if errorlevel 1 goto FAIL
echo.
echo Streamlit installation completed.
pause
exit /b 0

:FAIL
echo.
echo Installation failed.
pause
exit /b 1
