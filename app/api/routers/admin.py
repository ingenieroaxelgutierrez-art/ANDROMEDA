# ============================================================
# ANDROMEDA — app.api.routers.admin
# Dashboard de Métricas SaaS (Fase 4)
#
# Rutas:
#   GET /admin/metricas              — métricas globales o por empresa
#   GET /admin/metricas/{empresa_id} — métricas específicas de empresa
# ============================================================

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from app.api.schemas import MetricasSaaS
from services.logging_saas import obtener_metricas

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/metricas", response_model=MetricasSaaS, summary="Métricas globales SaaS")
def metricas_globales(
    empresa_id: Optional[str] = Query(
        default=None,
        description="ID de empresa. Omitir para métricas globales.",
    ),
    dias: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Ventana de tiempo en días hacia atrás.",
    ),
) -> MetricasSaaS:
    """
    Retorna métricas de comportamiento SaaS para el período solicitado.

    - Sin ``empresa_id`` → métricas globales de todas las empresas.
    - Con ``empresa_id`` → métricas filtradas para esa empresa.
    - ``dias`` controla la ventana temporal (default: 30 días).

    Métricas incluidas:
    - Total de consultas, OK vs Error, tasa de error
    - Duración promedio de respuesta en ms
    - Distribución por tipo de consulta (ventas, inventario, etc.)
    - Distribución por día
    - Empresas activas (solo en modo global)
    """
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    hasta = datetime.now(timezone.utc)
    datos = obtener_metricas(empresa_id=empresa_id, desde=desde, hasta=hasta)
    return MetricasSaaS(**datos)


@router.get(
    "/metricas/{empresa_id}",
    response_model=MetricasSaaS,
    summary="Métricas por empresa",
)
def metricas_empresa(
    empresa_id: str,
    dias: int = Query(default=30, ge=1, le=365),
) -> MetricasSaaS:
    """
    Métricas de comportamiento para una empresa específica.
    Equivalente a ``GET /admin/metricas?empresa_id={empresa_id}``.
    """
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    hasta = datetime.now(timezone.utc)
    datos = obtener_metricas(empresa_id=empresa_id, desde=desde, hasta=hasta)
    return MetricasSaaS(**datos)
