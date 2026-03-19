@echo off
REM ============================================================
REM ANDROMEDA v5.0 - Modo Consola (Chat)
REM ============================================================

echo.
echo ============================================================
echo         ANDROMEDA v5.0 - Modo Consola
echo ============================================================
echo.

cd /d "%~dp0"
cd ..

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python main.py consola

pause
