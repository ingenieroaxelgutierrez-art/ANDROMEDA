#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================
# ANDROMEDA  - Punto de Entrada Principal
# Advanced Neural Data Resource for Operations, 
# Management & Enterprise Decision Analytics
# ============================================================

import os
import sys
import argparse

# Asegurar que el directorio raíz está en el path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.config import Config
from app.logging_config import configurar_logging, get_logger

# Inicializar logging al arrancar
configurar_logging()
logger = get_logger('andromeda.main')


def iniciar_web() -> None:
    """Iniciar la interfaz web con Gradio."""
    logger.info("Iniciando ANDROMEDA - Interfaz Web")
    print("=" * 60)
    print("      ANDROMEDA - Interfaz Web")
    print("=" * 60)
    
    Config.crear_directorios()
    
    from views.interfaz_v5 import OdooAIProV5, CSS_PRO_V5
    
    bot = OdooAIProV5()
    app = bot.crear_interfaz()
    
    app.launch(
        server_name=Config.GRADIO_SERVER_NAME,
        server_port=Config.GRADIO_SERVER_PORT,
        share=Config.GRADIO_SHARE,
        inbrowser=True,
        css=CSS_PRO_V5
    )


def iniciar_consola() -> None:
    """Iniciar el bot en modo consola."""
    logger.info("Iniciando ANDROMEDA - Modo Consola")
    print("=" * 60)
    print("      ANDROMEDA - Modo Consola")
    print("=" * 60)
    
    Config.crear_directorios()
    
    from core.bot_principal import OdooBotPro
    from app.config import ConfiguracionOdoo
    
    config = ConfiguracionOdoo.default()
    bot = OdooBotPro(config, modo_verbose=True)
    
    print("\n¡Bot listo! Escribe 'salir' para terminar.\n")
    
    while True:
        try:
            consulta = input("Tú: ").strip()
            if consulta.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego!")
                break
            if not consulta:
                continue
                
            respuesta = bot.procesar(consulta)
            print(f"\nBot: {respuesta.mensaje}\n")
            
        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
            break
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            print(f"Error: {e}")


def main() -> None:
    """Función principal con argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='ANDROMEDA  - IA Predictiva Empresarial para Odoo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Ejemplos de uso:
        python main.py web      # Iniciar interfaz web (Gradio)
        python main.py consola  # Iniciar modo consola
        python main.py --help   # Mostrar esta ayuda
        """
    )
    
    parser.add_argument(
        'modo',
        nargs='?',
        default='web',
        choices=['web', 'consola', 'console'],
        help='Modo de ejecución: web (default) o consola'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=7860,
        help='Puerto para la interfaz web (default: 7860)'
    )
    
    parser.add_argument(
        '--share', '-s',
        action='store_true',
        help='Crear enlace público compartido (Gradio)'
    )
    
    args = parser.parse_args()
    
    # Aplicar configuración de argumentos
    if args.port:
        Config.GRADIO_SERVER_PORT = args.port
    if args.share:
        Config.GRADIO_SHARE = True
    
    # Ejecutar según el modo
    if args.modo in ['consola', 'console']:
        iniciar_consola()
    else:
        iniciar_web()


if __name__ == '__main__':
    main() 