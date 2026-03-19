# ============================================================
# ANDROMEDA - Configuración Centralizada de Logging
# ============================================================

import logging
import logging.handlers
import os
import re

# Directorio de logs
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.path.join(_BASE_DIR, 'logs')
os.makedirs(_LOG_DIR, exist_ok=True)

_LOG_FILE = os.path.join(_LOG_DIR, 'andromeda.log')


class FiltroCredenciales(logging.Filter):
    """Filtra credenciales sensibles de los mensajes de log."""

    _PATRONES = [
        (re.compile(r'(password|passwd|pwd|token|api_key|secret)["\']?\s*[:=]\s*["\']?[^\s,\}"\']+'
                     , re.IGNORECASE), r'\1=***REDACTED***'),
        # Patrón genérico para tokens hexadecimales de 40 chars (SHA1/API keys)
        (re.compile(r'\b[a-f0-9]{40}\b'), '***REDACTED_TOKEN***'),
        # Patrón genérico para emails
        (re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'), '***USER***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for patron, reemplazo in self._PATRONES:
            msg = patron.sub(reemplazo, msg)
        record.msg = msg
        record.args = ()
        return True


def configurar_logging(nivel: int = logging.INFO) -> None:
    """
    Configura logging centralizado para ANDROMEDA.

    - Archivo rotativo: logs/andromeda.log (5 MB, 3 backups)
    - Consola: solo WARNING+
    - Filtro de credenciales en ambos handlers
    """
    root_logger = logging.getLogger()

    # Evitar configurar doble
    if root_logger.handlers:
        return

    root_logger.setLevel(nivel)

    formato = logging.Formatter(
        '%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    filtro = FiltroCredenciales()

    # Handler archivo rotativo
    fh = logging.handlers.RotatingFileHandler(
        _LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding='utf-8'
    )
    fh.setLevel(nivel)
    fh.setFormatter(formato)
    fh.addFilter(filtro)
    root_logger.addHandler(fh)

    # Handler consola (solo warnings+)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formato)
    ch.addFilter(filtro)
    root_logger.addHandler(ch)

    # Silenciar librerías ruidosas
    logging.getLogger('odoorpc').setLevel(logging.WARNING)
    logging.getLogger('odoorpc.rpc.jsonrpclib').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(nombre: str) -> logging.Logger:
    """Obtiene un logger con el nombre del módulo."""
    return logging.getLogger(nombre)
