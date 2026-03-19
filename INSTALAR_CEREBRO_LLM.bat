@echo off
chcp 65001 >nul
title ANDROMEDA - Configurar Cerebro LLM

echo ============================================================
echo    ANDROMEDA - CONFIGURACIÓN DEL CEREBRO LLM (OLLAMA)
echo ============================================================
echo.

:: Verificar si Ollama está instalado
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama no está instalado.
    echo.
    echo Descargando Ollama...
    echo    Por favor, espera mientras se abre el navegador.
    echo.
    start https://ollama.ai/download
    echo.
    echo INSTRUCCIONES:
    echo    1. Descarga e instala Ollama desde la página web
    echo    2. Reinicia este script después de instalar
    echo.
    pause
    exit /b 1
)

echo Ollama está instalado.
echo.

:: Verificar si Ollama está corriendo
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo Iniciando Ollama...
    start /min ollama serve
    timeout /t 5 /nobreak >nul
)

echo Modelos disponibles:
ollama list

echo.
echo ============================================================
echo    INSTALANDO MODELO RECOMENDADO
echo ============================================================
echo.
echo El modelo recomendado es llama3.2 (2.5GB, muy rápido)
echo.

set /p install="¿Deseas instalar llama3.2? (S/N): "
if /i "%install%"=="S" (
    echo.
    echo Descargando llama3.2... Esto puede tardar unos minutos.
    echo.
    ollama pull llama3.2
    echo.
    echo Modelo instalado correctamente.
) else (
    echo.
    echo Puedes instalar un modelo manualmente con:
    echo    ollama pull llama3.2
    echo    ollama pull mistral
    echo    ollama pull phi3
)

echo.
echo ============================================================
echo    CONFIGURACIÓN COMPLETADA
echo ============================================================
echo.
echo El cerebro LLM está listo para usar.
echo.
echo Para iniciar ANDROMEDA:
echo    1. Asegúrate de que Ollama esté corriendo
echo    2. Ejecuta: python main.py web
echo.
echo Comandos útiles de Ollama:
echo    ollama list        - Ver modelos instalados
echo    ollama pull [modelo] - Descargar modelo
echo    ollama run [modelo]  - Probar modelo
echo    ollama serve       - Iniciar servidor
echo.

pause
