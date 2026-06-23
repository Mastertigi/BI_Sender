@echo off
REM ============================================================
REM  Gera o BI_Notify.exe (launcher da stack via Docker).
REM  Rode este .bat UMA vez na sua maquina Windows (duplo-clique
REM  ou no terminal). Requer Python 3.10+ instalado.
REM ============================================================
setlocal
cd /d "%~dp0"

echo [*] Instalando PyInstaller (se necessario)...
python -m pip install --quiet --upgrade pyinstaller || goto :erro

echo [*] Compilando BI_Notify.exe ...
python -m PyInstaller --onefile --console --name BI_Notify --distpath "%~dp0." --workpath "%~dp0build\_pyi" --specpath "%~dp0build" "%~dp0launcher\run.py" || goto :erro

echo.
echo [OK] Gerado: %~dp0BI_Notify.exe
echo     Deixe o BI_Notify.exe nesta pasta (ao lado do docker-compose.yml)
echo     e de um duplo-clique para subir tudo.
echo.
pause
exit /b 0

:erro
echo.
echo [X] Falha no build. Verifique se o Python esta instalado e no PATH.
pause
exit /b 1
