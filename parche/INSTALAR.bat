@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set "JUEGO=%~1"
if not defined JUEGO (
  echo Arrastra la carpeta del juego encima de este archivo, o escribe la ruta aqui.
  echo Ejemplo: C:\Games\KajiriKamuiKagura   ^(la carpeta que tiene data1.dat y malie.exe^)
  set /p "JUEGO=Ruta del juego: "
)
echo.
echo Elige el cuadro de texto:
echo   1 = BARRA     barra hecha para el parche, de lado a lado (recomendado; cabe todo)
echo   2 = ABAJO     imagen original del panel del juego, acostada abajo (cabe todo)
echo   3 = ORIGINAL  panel original de pie, a un lado (5 mensajes largos se cortan)
set "EST=BARRA"
set /p "OPC=Numero (Enter = 1): "
if "%OPC%"=="2" set "EST=ABAJO"
if "%OPC%"=="3" set "EST=ORIGINAL"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
%PY% herramientas\armar.py "%JUEGO%" --estilo %EST%
echo.
pause
