# ============================================================
# ANDROMEDA — app.api.routers.chat
# POST /chat — pipeline principal usuario → respuesta
# ============================================================

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import MensajeRequest, RespuestaAPI
from app.api.dependencies import get_bot

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=RespuestaAPI, summary="Procesar mensaje")
def procesar_chat(request: MensajeRequest, bot=Depends(get_bot)) -> RespuestaAPI:
    """
    Recibe un mensaje del usuario y retorna la respuesta del bot.

    **Diseño stateless:** el cliente es responsable de mantener y enviar
    el historial completo en cada request.  El servidor procesa, actualiza
    el historial y lo devuelve.

    **Fase 4 — Multi-empresa:** si se provee ``empresa_id``, el comportamiento
    se registra en SesionLog asociado a esa empresa.

    Flujo interno:
    1. Extrae ``historial`` y ``session_id`` del request.
    2. Si el historial está vacío y existe contexto previo en BD → lo restaura.
    3. Llama a ``OdooAIProV5.procesar_mensaje(mensaje, historial)``.
    4. Persiste el historial actualizado en BD por session_id.
    5. Registra la consulta en SesionLog (métricas SaaS).
    6. Retorna ``RespuestaAPI`` con historial actualizado.
    """
    session_id: str = request.session_id or str(uuid.uuid4())
    historial: List[Dict[str, Any]] = list(request.historial or [])
    empresa_id: str | None = request.empresa_id
    t_inicio = time.perf_counter()

    # ── Restaurar contexto de sesión desde BD si el cliente no lo envió ──────
    if not historial and session_id:
        historial = _cargar_contexto_sesion(session_id)

    exito = True
    error_msg: str | None = None

    try:
        historial_actualizado, tabla_html, status = bot.procesar_mensaje(
            mensaje=request.mensaje,
            historial=historial,
        )
    except Exception as exc:
        exito = False
        error_msg = str(exc)
        duracion_ms = int((time.perf_counter() - t_inicio) * 1000)
        _registrar_log(empresa_id, session_id, duracion_ms, False, error_msg=error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando mensaje: {exc}",
        ) from exc

    duracion_ms = int((time.perf_counter() - t_inicio) * 1000)

    # ── Extraer última respuesta del asistente ────────────────────────────────
    respuesta: str = ""
    for entry in reversed(historial_actualizado):
        if entry.get("role") == "assistant":
            respuesta = str(entry.get("content", ""))
            break

    # ── Validar respuesta antes de enviar al cliente (evita alucinaciones) ────
    try:
        from utils.validador_respuestas import obtener_validador
        validador = obtener_validador()
        resultado_val = validador.validar(
            respuesta=respuesta,
            consulta_original=request.mensaje,
            accion=_inferir_tipo_consulta(status or ""),
            confianza_previa=1.0,
        )
        if resultado_val.accion_correctiva in ('reemplazada', 'rechazada') and resultado_val.respuesta_validada:
            respuesta = resultado_val.respuesta_validada
            # Actualizar el historial con la respuesta limpia
            for entry in reversed(historial_actualizado):
                if entry.get("role") == "assistant":
                    entry["content"] = respuesta
                    break
    except Exception:
        pass  # Validación no bloquea el flujo

    # ── Inferir tipo de consulta desde el status devuelto por el bot ─────────
    tipo_consulta = _inferir_tipo_consulta(status or "")

    # ── Persistir contexto y registrar métricas ───────────────────────────────
    _guardar_contexto_sesion(session_id, empresa_id, historial_actualizado)
    _registrar_log(
        empresa_id, session_id, duracion_ms, exito,
        tipo_consulta=tipo_consulta, error_msg=error_msg
    )

    return RespuestaAPI(
        respuesta=respuesta,
        tabla_html=tabla_html or "",
        status=status or "",
        session_id=session_id,
        historial=historial_actualizado,
        timestamp=datetime.now().isoformat(),
    )


# ── Helpers internos ─────────────────────────────────────────────────────────

def _cargar_contexto_sesion(session_id: str) -> List[Dict[str, Any]]:
    """Carga el historial almacenado para session_id. Tolerante a fallos."""
    try:
        from models.db_saas import get_session, SesionContexto, inicializar_db
        inicializar_db()
        db = get_session()
        try:
            ctx = db.query(SesionContexto).filter(
                SesionContexto.session_id == session_id
            ).first()
            return ctx.get_historial() if ctx else []
        finally:
            db.close()
    except Exception:
        return []


def _guardar_contexto_sesion(
    session_id: str,
    empresa_id: str | None,
    historial: List[Dict[str, Any]],
) -> None:
    """Persiste el historial actualizado en SesionContexto. Tolerante a fallos."""
    try:
        from models.db_saas import get_session, SesionContexto, inicializar_db
        from datetime import timezone
        inicializar_db()
        db = get_session()
        try:
            ctx = db.query(SesionContexto).filter(
                SesionContexto.session_id == session_id
            ).first()
            if ctx:
                ctx.set_historial(historial)
                ctx.ultima_actividad = datetime.now(timezone.utc)
            else:
                ctx = SesionContexto(
                    session_id=session_id,
                    empresa_id=empresa_id,
                    creado_en=datetime.now(timezone.utc),
                    ultima_actividad=datetime.now(timezone.utc),
                )
                ctx.set_historial(historial)
                db.add(ctx)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass


def _registrar_log(
    empresa_id: str | None,
    session_id: str,
    duracion_ms: int,
    exito: bool,
    tipo_consulta: str | None = None,
    error_msg: str | None = None,
) -> None:
    """Registra la consulta en SesionLog vía logging_saas. Tolerante a fallos."""
    try:
        from services.logging_saas import registrar_consulta
        registrar_consulta(
            empresa_id=empresa_id,
            accion="chat",
            duracion_ms=duracion_ms,
            exito=exito,
            tipo_consulta=tipo_consulta,
            session_id=session_id,
            error_msg=error_msg,
        )
    except Exception:
        pass


def _inferir_tipo_consulta(status: str) -> str | None:
    """Extrae el dominio semántico del status del pipeline (e.g. 'ventas')."""
    if not status:
        return None
    status_lower = status.lower()
    dominios = [
        "ventas", "inventario", "finanzas", "crm", "compras",
        "pdv", "predicciones", "estadistica", "rrhh", "diagnostico",
        "matematicas", "manuales", "llm",
    ]
    for dominio in dominios:
        if dominio in status_lower:
            return dominio
    return "otro"

