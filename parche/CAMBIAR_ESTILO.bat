@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo Cambia el cuadro de texto de tu juego YA PARCHADO (no necesitas el CSV).
set "JUEGO=%~1"
if not defined JUEGO set /p "JUEGO=Arrastra aqui la carpeta del juego y presiona Enter: "
set "JUEGO=%JUEGO:"=%"
echo.
echo Elige el cuadro de texto:
echo   1 = BARRA     barra hecha para el parche, de lado a lado (recomendado; cabe todo)
echo   2 = ABAJO     imagen original del panel del juego, acostada abajo (cabe todo)
echo   3 = ORIGINAL  panel original de pie, a un lado (5 mensajes largos se cortan)
set "EST=BARRA"
set /p "OPC=Numero: "
if "%OPC%"=="2" set "EST=ABAJO"
if "%OPC%"=="3" set "EST=ORIGINAL"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
echo Tarda varios minutos: no cierres la ventana.
%PY% herramientas\cambiar_estilo.py "%JUEGO%" %EST%
echo.
pause
