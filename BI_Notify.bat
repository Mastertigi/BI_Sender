@echo off
REM ============================================================
REM  BI Notify — sobe TODA a stack (Docker) sem precisar compilar.
REM  Duplo-clique aqui. Requer Docker Desktop em execucao e Python 3.10+.
REM  (Equivale ao BI_Notify.exe, mas roda o launcher direto com o Python.)
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [X] Python nao encontrado no PATH. Instale o Python 3.10+ e tente de novo.
    pause
    exit /b 1
)

python "%~dp0launcher\run.py"
pause
