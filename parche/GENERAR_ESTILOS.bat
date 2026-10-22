@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo   Crea los 3 estilos de cuadro de texto (BARRA, ABAJO, ORIGINAL)
echo   a partir de un data3.dat YA PARCHADO. Los deja en la carpeta "mis_estilos".
echo   (Para cambiar el estilo del juego directamente usa CAMBIAR_ESTILO.bat o la ventana.)
echo ============================================================
set "ARCH=%~1"
if not defined ARCH set /p "ARCH=Arrastra aqui tu data3.dat y presiona Enter: "
set "ARCH=%ARCH:"=%"
if not exist "%ARCH%" (echo No encontre: %ARCH% & pause & exit /b 1)
for %%F in ("%ARCH%") do set "JUEGO=%%~dpF."
mkdir mis_estilos 2>nul
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
echo Tarda varios minutos: no cierres la ventana.
%PY% herramientas\generar_estilos.py "%ARCH%" "%CD%\mis_estilos" --alto 150 --juego "%JUEGO%"
echo.
echo Para usar uno: copia mis_estilos\data3_ESTILO.dat a la carpeta del juego con el nombre data3.dat.
pause
