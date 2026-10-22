@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set "JUEGO=%~1"
if not defined JUEGO set /p "JUEGO=Ruta de la carpeta del juego (la que tiene data1.dat): "
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
%PY% herramientas\extraer.py "%JUEGO%"
echo.
pause
