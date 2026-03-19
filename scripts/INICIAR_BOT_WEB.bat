@echo off
REM ============================================================
REM ANDROMEDA v5.0 - Interfaz Web (Gradio)
REM ============================================================

echo.
echo ============================================================
echo         ANDROMEDA v5.0 - Interfaz Web
echo ============================================================
echo.
echo Iniciando servidor web...
echo La interfaz se abrira automaticamente en tu navegador.
echo.
echo Para detener: Presiona Ctrl+C
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

python main.py web

pause
