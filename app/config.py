# ============================================================
# ANDROMEDA - Configuración Global
# ============================================================

import os
import json
import logging
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Silenciar logging de odoorpc que expone credenciales en DEBUG
logging.getLogger('odoorpc.rpc.jsonrpclib').setLevel(logging.WARNING)
logging.getLogger('odoorpc').setLevel(logging.WARNING)


@dataclass
class ConfiguracionOdoo:
    """Configuración de conexión a Odoo."""
    url: str
    db: str
    usuario: str
    password: str
    
    @classmethod
    def desde_json(cls, ruta: str) -> 'ConfiguracionOdoo':
        """Carga configuración desde archivo JSON."""
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(
            url=data.get('url', ''),
            db=data.get('db', ''),
            usuario=data.get('usuario', ''),
            password=data.get('password', '')
        )
    
    @classmethod
    def default(cls) -> 'ConfiguracionOdoo':
        """Carga configuración desde variables de entorno."""
        return cls(
            url=os.getenv('ODOO_URL', ''),
            db=os.getenv('ODOO_DB', ''),
            usuario=os.getenv('ODOO_USER', ''),
            password=os.getenv('ODOO_PASSWORD', '')
        )


class Config:
    """Configuración global de ANDROMEDA."""
    
    # Rutas base
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    
    # Archivos
    MEMORIA_BOT_PATH = os.path.join(DATA_DIR, 'memoria_bot.json')
    LOGO_PATH = os.path.join(ASSETS_DIR, 'logo.png')
    
    # Versión
    VERSION = "1.0.0"
    NOMBRE = "ANDROMEDA"
    NOMBRE_COMPLETO = "Advanced Neural Data Resource for Operations, Management & Enterprise Decision Analytics"
    
    # Configuración NLP
    USAR_SPACY = True
    USAR_EMBEDDINGS = False
    MODELO_SPACY = "es_core_news_sm"
    
    # Configuración de servidor
    GRADIO_SERVER_NAME = "127.0.0.1"
    GRADIO_SERVER_PORT = 7860
    GRADIO_SHARE = False
    
    @classmethod
    def crear_directorios(cls):
        """Crea los directorios necesarios si no existen."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        os.makedirs(cls.ASSETS_DIR, exist_ok=True)
