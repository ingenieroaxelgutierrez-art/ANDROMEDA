# ============================================================
# ANDROMEDA v5.0 - IA Predictiva Empresarial para Odoo
# Advanced Neural Data Resource for Operations, 
# Management & Enterprise Decision Analytics
# ============================================================
# Sin APIs externas, 100% local y gratuito
# ============================================================

"""
ANDROMEDA  - IA Predictiva Empresarial para Odoo.

Estructura del proyecto:
    app/        - Configuración y punto de entrada
    core/       - Lógica principal (bot, cerebro)
    models/     - Conexión a Odoo y modelos
    services/   - Servicios (NLP, análisis, predicción)
    views/      - Interfaces y reportes
    utils/      - Utilidades

Uso básico:
    # Iniciar desde línea de comandos:
    python main.py web      # Interfaz web
    python main.py consola  # Modo consola
    bot.conectar()
    respuesta = bot.procesar("¿Cuántas ventas hay hoy?")
    print(respuesta.mensaje)

Para interfaz web:
    python -m ODOO_BOT_PRO.interfaz_gradio
"""

__version__ = "1.0.0"
__author__ = "Axel Gutierrez"
