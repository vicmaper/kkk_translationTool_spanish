@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
set "ARCH=%~1"
if not defined ARCH set "ARCH=mi_traduccion.csv"
echo Traduccion a integrar: "%ARCH%"
set /p "JUEGO=Ruta de la carpeta del juego (la que tiene data1.dat): "
echo.
echo Elige el cuadro de texto:
echo   1 = BARRA     barra hecha para el parche, de lado a lado (recomendado; cabe todo)
echo   2 = ABAJO     imagen original del panel del juego, acostada abajo (cabe todo)
echo   3 = ORIGINAL  panel original de pie, a un lado (5 mensajes largos se cortan)
set "EST=BARRA"
set /p "OPC=Numero (Enter = 1): "
if "%OPC%"=="2" set "EST=ABAJO"
if "%OPC%"=="3" set "EST=ORIGINAL"
echo.
echo [1/2] Revisando el formato...
%PY% herramientas\kkk_revisar.py "%ARCH%" --sin-abrir > "%TEMP%\kkk_revision.txt"
type "%TEMP%\kkk_revision.txt"
findstr /c:"LISTO PARA INTEGRAR" "%TEMP%\kkk_revision.txt" >nul
if errorlevel 1 (
  echo.
  echo No se integra: corrige las filas de *_FILAS_CON_ERROR.csv y vuelve a intentar.
  pause & exit /b 1
)
for %%F in ("%ARCH%") do set "CORR=%%~dpnF_CORREGIDO%%~xF"
echo.
echo [2/2] Integrando "%CORR%" en el juego...
%PY% herramientas\armar.py "%JUEGO%" --tsv "%CORR%" --estilo %EST%
echo.
pause
