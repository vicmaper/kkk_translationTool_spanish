@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if exist "KKK_Traduccion.exe" (start "" "KKK_Traduccion.exe" & exit /b 0)
set "PY=pythonw"
where pythonw >nul 2>&1
if errorlevel 1 set "PY=pyw"
start "" %PY% herramientas\kkk_gui.py
