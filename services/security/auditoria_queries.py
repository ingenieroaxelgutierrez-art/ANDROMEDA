# ANDROMEDA - Auditoría de Queries Odoo (Log SIEM)
# Autor: KAIROS-SYNERGY
# Descripción: Logging estructurado de queries ejecutadas contra Odoo, compatible SIEM.
# Minimalista, extensible y sin sobreingeniería.

import json
import os
from datetime import datetime
from threading import Lock

# Ruta del log (puede moverse a config si se requiere)
LOG_PATH = os.path.join(os.path.dirname(__file__), '../../logs/queries_odoo.log')
_lock = Lock()

class AuditoriaQueries:
    """
    Logger estructurado para registrar queries ejecutadas contra Odoo.
    Cada registro es un JSON en una línea (formato SIEM-friendly).
    """
    def __init__(self, log_path: str = LOG_PATH):
        self.log_path = os.path.abspath(log_path)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def registrar_query(self, *, usuario: str, modelo_odoo: str, filtros: dict, campos: list, registros_retornados: int, duracion_ms: int, hash_prompt: str = None, nivel: str = "INFO"):
        registro = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "usuario": usuario,
            "modelo_odoo": modelo_odoo,
            "filtros": filtros,
            "campos": campos,
            "registros_retornados": registros_retornados,
            "duracion_ms": duracion_ms,
            "hash_prompt": hash_prompt,
            "nivel": nivel
        }
        linea = json.dumps(registro, ensure_ascii=False)
        with _lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(linea + "\n")

# Ejemplo de uso (eliminar en producción)
if __name__ == "__main__":
    auditor = AuditoriaQueries()
    auditor.registrar_query(
        usuario="test_user",
        modelo_odoo="sale.order",
        filtros={"state": "sale"},
        campos=["name", "amount_total"],
        registros_retornados=10,
        duracion_ms=123,
        hash_prompt="abc123",
        nivel="INFO"
    )
    print(f"Registro escrito en {auditor.log_path}")
