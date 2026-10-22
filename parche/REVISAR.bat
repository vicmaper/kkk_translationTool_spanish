@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set "ARCH=%~1"
if not defined ARCH set "ARCH=datos\traduccion_es.tsv"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
%PY% herramientas\kkk_revisar.py "%ARCH%"
echo.
pause
