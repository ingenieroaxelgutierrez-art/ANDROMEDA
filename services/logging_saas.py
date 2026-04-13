# ============================================================
# ANDROMEDA — services.logging_saas
# Logging Comportamental SaaS (Fase 4)
#
# Registra métricas de uso por empresa:
#   - Número de consultas y tipo (ventas, inventario, etc.)
#   - Tiempos de respuesta promedio
#   - Tasa de errores
#   - Distribución temporal (por día)
#   - Rotación automática de logs (>ROTACION_DIAS días)
#
# Diseño:
#   - Tolerante a fallos: NUNCA lanza excepción al llamador.
#   - Escrituras asíncronas-safe: no bloquea el pipeline principal.
#   - Datos en la misma BD SaaS (SesionLog) — sin dependencias externas.
# ============================================================

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("andromeda.logging_saas")

ROTACION_DIAS: int = 30   # Logs más antiguos que esto se eliminan automáticamente


# ── Registro de Consultas ─────────────────────────────────────────────────────

def registrar_consulta(
    empresa_id: Optional[str],
    accion: str,
    duracion_ms: int,
    exito: bool,
    tipo_consulta: Optional[str] = None,
    session_id: Optional[str] = None,
    usuario_id: Optional[str] = None,
    error_msg: Optional[str] = None,
) -> None:
    """
    Persiste una consulta en SesionLog.

    Tolerante a fallos: si la BD no está disponible, solo registra
    el warning en el logger local y retorna sin lanzar excepción.
    El pipeline principal NO debe verse afectado por fallos de logging.

    Args:
        empresa_id:    ID de la empresa que originó la consulta.
        accion:        Tipo de acción (``"chat"``, ``"reporte"``, ``"configuracion"``).
        duracion_ms:   Duración total del procesamiento en milisegundos.
        exito:         ``True`` si la consulta terminó correctamente.
        tipo_consulta: Subtipo semántico (``"ventas"``, ``"inventario"``, etc.).
        session_id:    ID de sesión del usuario.
        usuario_id:    ID del usuario (si está autenticado).
        error_msg:     Mensaje de error (solo si ``exito=False``).
    """
    try:
        from models.db_saas import get_session, SesionLog, inicializar_db
        inicializar_db()
        session = get_session()
        try:
            log = SesionLog(
                empresa_id=empresa_id,
                usuario_id=usuario_id,
                session_id=session_id,
                timestamp=datetime.now(timezone.utc),
                accion=accion,
                tipo_consulta=tipo_consulta,
                resultado="ok" if exito else "error",
                duracion_ms=duracion_ms,
                error_msg=error_msg[:500] if error_msg else None,
            )
            session.add(log)
            session.commit()
        except Exception as ex:
            session.rollback()
            logger.warning("Error guardando SesionLog: %s", ex)
        finally:
            session.close()
    except Exception as ex:
        logger.warning("registrar_consulta falló silenciosamente: %s", ex)


# ── Rotación de Logs ──────────────────────────────────────────────────────────

def rotar_logs_antiguos(dias: int = ROTACION_DIAS) -> int:
    """
    Elimina registros de SesionLog con más de ``dias`` días de antigüedad.

    Debe invocarse periódicamente (p.ej. en el evento ``startup`` de FastAPI
    o mediante un scheduler externo) para evitar crecimiento indefinido de la BD.

    Returns:
        Número de registros eliminados. Retorna 0 ante cualquier error.
    """
    try:
        from models.db_saas import get_session, SesionLog, inicializar_db
        inicializar_db()
        corte = datetime.now(timezone.utc) - timedelta(days=dias)
        session = get_session()
        try:
            eliminados: int = (
                session.query(SesionLog)
                .filter(SesionLog.timestamp < corte)
                .delete(synchronize_session=False)
            )
            session.commit()
            if eliminados:
                logger.info("Rotación de logs: %d registros eliminados (>%dd)", eliminados, dias)
            return eliminados
        except Exception as ex:
            session.rollback()
            logger.warning("Error rotando logs: %s", ex)
            return 0
        finally:
            session.close()
    except Exception as ex:
        logger.warning("rotar_logs_antiguos falló: %s", ex)
        return 0


# ── Métricas Agregadas ────────────────────────────────────────────────────────

def obtener_metricas(
    empresa_id: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Agrega métricas de SesionLog para una empresa (o globalmente).

    Sin ``empresa_id`` → métricas globales de todas las empresas.
    Con ``empresa_id`` → métricas filtradas para esa empresa.

    Args:
        empresa_id: Filtrar por empresa. ``None`` = todas.
        desde:      Inicio del período (default: últimos 30 días).
        hasta:      Fin del período (default: ahora).

    Returns:
        Dict con:
        - ``total_consultas``, ``consultas_ok``, ``consultas_error``
        - ``tasa_error`` (porcentaje)
        - ``duracion_promedio_ms``
        - ``por_tipo`` (dict tipo → count)
        - ``por_dia`` (dict fecha-iso → count)
        - ``empresas_activas`` (solo en modo global)
        - ``periodo`` (desde/hasta en ISO 8601)
    """
    desde = desde or (datetime.now(timezone.utc) - timedelta(days=30))
    hasta = hasta or datetime.now(timezone.utc)

    try:
        from models.db_saas import get_session, SesionLog, inicializar_db
        inicializar_db()
        session = get_session()
        try:
            query = session.query(SesionLog).filter(
                SesionLog.timestamp >= desde,
                SesionLog.timestamp <= hasta,
            )
            if empresa_id:
                query = query.filter(SesionLog.empresa_id == empresa_id)

            registros: List[SesionLog] = query.all()

            if not registros:
                return _metricas_vacias(empresa_id, desde, hasta)

            total: int = len(registros)
            ok: int = sum(1 for r in registros if r.resultado == "ok")
            error: int = total - ok
            duraciones: List[int] = [r.duracion_ms for r in registros if r.duracion_ms is not None]
            promedio_ms: int = int(sum(duraciones) / len(duraciones)) if duraciones else 0

            # Distribución por tipo de consulta
            por_tipo: Dict[str, int] = {}
            for r in registros:
                t = r.tipo_consulta or "desconocido"
                por_tipo[t] = por_tipo.get(t, 0) + 1

            # Distribución por día
            por_dia: Dict[str, int] = {}
            for r in registros:
                dia = (
                    r.timestamp.strftime("%Y-%m-%d")
                    if r.timestamp
                    else "desconocido"
                )
                por_dia[dia] = por_dia.get(dia, 0) + 1

            # Empresas activas (solo en modo global — conteo real desde tabla Empresa)
            empresas_activas: int = 0
            if not empresa_id:
                try:
                    from models.db_saas import Empresa
                    empresas_activas = session.query(Empresa).filter(Empresa.activa == True).count()
                except Exception:
                    empresas_activas = len({r.empresa_id for r in registros if r.empresa_id})

            return {
                "empresa_id": empresa_id,
                "periodo": {
                    "desde": desde.isoformat(),
                    "hasta": hasta.isoformat(),
                },
                "total_consultas": total,
                "consultas_ok": ok,
                "consultas_error": error,
                "tasa_error": round(error / total * 100, 2) if total else 0.0,
                "duracion_promedio_ms": promedio_ms,
                "por_tipo": por_tipo,
                "por_dia": por_dia,
                "empresas_activas": empresas_activas,  # int: número de empresas con actividad
            }
        finally:
            session.close()
    except Exception as ex:
        logger.warning("obtener_metricas falló: %s", ex)
        return _metricas_vacias(empresa_id, desde, hasta)


def _metricas_vacias(
    empresa_id: Optional[str],
    desde: Optional[datetime],
    hasta: Optional[datetime],
) -> Dict[str, Any]:
    return {
        "empresa_id": empresa_id,
        "periodo": {
            "desde": desde.isoformat() if desde else None,
            "hasta": hasta.isoformat() if hasta else None,
        },
        "total_consultas": 0,
        "consultas_ok": 0,
        "consultas_error": 0,
        "tasa_error": 0.0,
        "duracion_promedio_ms": 0,
        "por_tipo": {},
        "por_dia": {},
        "empresas_activas": 0,
    }
