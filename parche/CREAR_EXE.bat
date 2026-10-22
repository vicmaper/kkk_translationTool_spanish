@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Crea KKK_Traduccion.exe (la ventana del parche sin necesitar Python).
echo   Solo hace falta para quien publica el parche. Necesita internet la 1a vez.
echo ============================================================
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
%PY% -m pip install --upgrade pyinstaller
%PY% -m PyInstaller --noconfirm --onefile --windowed --name KKK_Traduccion --paths herramientas --distpath . --workpath "%TEMP%\kkk_build" --specpath "%TEMP%\kkk_build" herramientas\kkk_gui.py
if exist KKK_Traduccion.exe (echo. & echo LISTO: KKK_Traduccion.exe) else (echo. & echo No se pudo crear el .exe. Toma foto de esta ventana.)
pause
