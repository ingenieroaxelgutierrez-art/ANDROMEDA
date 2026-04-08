# ============================================================
# ANDROMEDA — app.api.routers.salud
# Endpoints de salud e infraestructura.
# GET /health  — disponibilidad del servidor (no requiere bot)
# GET /status  — estado del bot, LLM y conexión Odoo
# ============================================================

from fastapi import APIRouter, Depends
from app.config import Config
from app.api.dependencies import get_bot

router = APIRouter(tags=["salud"])


@router.get("/health", summary="Salud del servidor")
def health() -> dict:
    """
    Retorna 200 si el servidor está activo.

    No instancia ni utiliza el bot: este endpoint debe responder
    incluso mientras el bot se está inicializando.
    """
    return {
        "status": "ok",
        "version": Config.VERSION,
        "nombre": Config.NOMBRE,
    }


@router.get("/status", summary="Estado del bot y conexiones")
def status(bot=Depends(get_bot)) -> dict:
    """
    Estado operativo del bot, el LLM y la conexión Odoo.

    - ``bot``: ``"ready"`` cuando el singleton está inicializado.
    - ``llm``: ``true`` si el cerebro LLM está activo y respondiendo.
    - ``odoo``: ``true`` si la sesión Odoo está autenticada.
    """
    llm_activo: bool = bool(getattr(bot, "llm_activo", False))
    odoo_conectado: bool = bool(getattr(getattr(bot, "odoo", None), "conectado", False))

    return {
        "bot": "ready",
        "llm": llm_activo,
        "odoo": odoo_conectado,
        "version": Config.VERSION,
    }
