# ============================================================
# ANDROMEDA — app.api.routers.reportes
# GET  /reportes           — catálogo de reportes disponibles
# POST /reportes/generar   — genera un reporte delegando al bot
# ============================================================

import re
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    GenerarReporteRequest,
    ListaReportes,
    ReporteGenerado,
    TipoReporte,
)
from app.api.dependencies import get_bot

router = APIRouter(prefix="/reportes", tags=["reportes"])

# Catálogo estático de tipos de reporte soportados por el bot.
# Actualizar cuando se añadan nuevos agentes especializados.
_TIPOS_REPORTE: List[TipoReporte] = [
    TipoReporte(
        id="ventas",
        nombre="Reporte de Ventas",
        descripcion="Análisis de ventas por período: totales, por vendedor, por producto.",
    ),
    TipoReporte(
        id="inventario",
        nombre="Reporte de Inventario",
        descripcion="Stock actual, movimientos y alertas de reposición.",
    ),
    TipoReporte(
        id="finanzas",
        nombre="Reporte Financiero",
        descripcion="Ingresos, gastos, balance y KPIs financieros.",
    ),
    TipoReporte(
        id="clientes",
        nombre="Reporte de Clientes",
        descripcion="CRM: clientes activos, potenciales y análisis de comportamiento.",
    ),
    TipoReporte(
        id="compras",
        nombre="Reporte de Compras",
        descripcion="Órdenes de compra, proveedores y análisis de costos.",
    ),
]

_TIPOS_VALIDOS = {t.id for t in _TIPOS_REPORTE}

# Regex para detectar rutas de archivo en la respuesta del bot
_RE_ARCHIVO = re.compile(r'[\w/\\.\-]+\.(xlsx|pdf|html)', re.IGNORECASE)


@router.get("", response_model=ListaReportes, summary="Listar tipos de reporte")
def listar_reportes() -> ListaReportes:
    """Retorna el catálogo de reportes disponibles en el sistema."""
    return ListaReportes(tipos=_TIPOS_REPORTE, total=len(_TIPOS_REPORTE))


@router.post("/generar", response_model=ReporteGenerado, summary="Generar reporte")
def generar_reporte(request: GenerarReporteRequest, bot=Depends(get_bot)) -> ReporteGenerado:
    """
    Genera un reporte del tipo solicitado delegando la lógica al bot.

    El bot interpreta un mensaje en lenguaje natural construido a partir
    del ``tipo`` y los ``parametros``.  Si el bot genera un archivo, su
    ruta se incluye en ``archivo``; de lo contrario es ``null``.
    """
    if request.tipo not in _TIPOS_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Tipo de reporte inválido: '{request.tipo}'. "
                f"Tipos válidos: {sorted(_TIPOS_VALIDOS)}"
            ),
        )

    # Construir mensaje natural para el pipeline NLP del bot
    mensaje_reporte = f"Genera un reporte de {request.tipo}"
    params = request.parametros or {}
    if params.get("periodo"):
        mensaje_reporte += f" del {params['periodo']}"

    try:
        historial, _tabla_html, _status = bot.procesar_mensaje(
            mensaje=mensaje_reporte,
            historial=[],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando reporte: {exc}",
        ) from exc

    # Intentar extraer ruta de archivo de la respuesta del bot
    archivo = None
    for entry in reversed(historial):
        content = entry.get("content", "")
        if isinstance(content, str):
            match = _RE_ARCHIVO.search(content)
            if match:
                archivo = match.group(0)
                break

    return ReporteGenerado(
        tipo=request.tipo,
        archivo=archivo,
        mensaje=f"Reporte '{request.tipo}' procesado correctamente.",
        timestamp=datetime.now().isoformat(),
    )
