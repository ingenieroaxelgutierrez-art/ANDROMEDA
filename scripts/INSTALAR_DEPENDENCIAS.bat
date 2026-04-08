@echo off
REM ============================================================
REM ANDROMEDA v5.0 - Instalador
REM ============================================================
REM Crea entorno virtual e instala todas las dependencias
REM ============================================================

echo.
echo ============================================================
echo        ANDROMEDA v5.0 - Instalador de Dependencias
echo ============================================================
echo.

cd /d "%~dp0"
cd ..

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.8+ desde python.org
    pause
    exit /b 1
)

echo [1/5] Creando entorno virtual...
if not exist ".venv" (
    python -m venv .venv
    echo     Entorno virtual creado en .venv
) else (
    echo     Entorno virtual ya existe
)

echo.
echo [2/5] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo [3/5] Actualizando pip...
python -m pip install --upgrade pip

echo.
echo [4/5] Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

echo.
echo [5/5] Descargando modelo de espanol para spaCy...
python -m spacy download es_core_news_sm

echo.
echo ============================================================
echo        INSTALACION COMPLETADA
echo ============================================================
echo.
echo Estructura del proyecto:
echo   app/       - Configuracion
echo   core/      - Logica principal
echo   models/    - Conexion a Odoo
echo   services/  - NLP, Analisis, Prediccion
echo   views/     - Interfaz y reportes
echo   utils/     - Utilidades
echo.
echo Para iniciar el bot:
echo   - Interfaz Web:    scripts/INICIAR_BOT_WEB.bat
echo   - Linea Comandos:  scripts/INICIAR_BOT_CONSOLA.bat
echo   - Directamente:    python main.py web
echo.
pause
