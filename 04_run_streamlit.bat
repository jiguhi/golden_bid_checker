@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

where py >nul 2>nul
if not errorlevel 1 goto RUN_PY
where python >nul 2>nul
if not errorlevel 1 goto RUN_PYTHON

echo Python was not found.
pause
exit /b 1

:RUN_PY
py -3 -m streamlit run streamlit_app.py
goto END

:RUN_PYTHON
python -m streamlit run streamlit_app.py

:END
pause
