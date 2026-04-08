# ============================================================
# ANDROMEDA — views.gradio_cliente
# Interfaz Gradio como CLIENTE HTTP del backend FastAPI.
#
# Uso:
#   1. Iniciar el backend:
#        uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload
#   2. Iniciar este cliente:
#        python views/gradio_cliente.py
#
# Variables de entorno:
#   ANDROMEDA_API_URL  — URL base de la API (default: http://127.0.0.1:8000)
#
# Diferencia con interfaz_v5.py (modo directo):
#   - Este cliente NO instancia OdooAIProV5 localmente.
#   - Toda la lógica de negocio corre en el proceso FastAPI separado.
#   - Gradio puede detenerse sin afectar al backend.
# ============================================================

import os
import sys
from typing import Any, Dict, List, Tuple

# Raíz del proyecto en sys.path
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import requests
import gradio as gr

from app.config import Config

# ── Configuración del backend ────────────────────────────────────────────────
FASTAPI_URL: str = os.getenv("ANDROMEDA_API_URL", "http://127.0.0.1:8000")
_CHAT_ENDPOINT: str = f"{FASTAPI_URL}/chat"
_HEALTH_ENDPOINT: str = f"{FASTAPI_URL}/health"
_TIMEOUT_CHAT: int = 60   # segundos máximos esperando respuesta del bot
_TIMEOUT_HEALTH: int = 3  # segundos para el ping de salud


# ── Utilidades ───────────────────────────────────────────────────────────────

def _verificar_backend() -> Tuple[bool, str]:
    """
    Hace un GET /health al backend para verificar disponibilidad.

    Returns:
        (disponible, mensaje_legible)
    """
    try:
        resp = requests.get(_HEALTH_ENDPOINT, timeout=_TIMEOUT_HEALTH)
        if resp.status_code == 200:
            data = resp.json()
            nombre = data.get("nombre", "ANDROMEDA")
            version = data.get("version", "?")
            return True, f"✅ Backend activo — {nombre} v{version} en {FASTAPI_URL}"
        return False, f"⚠️ Backend respondió HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, (
            f"❌ Backend no disponible en {FASTAPI_URL}.  "
            f"Iniciar con:  uvicorn app.api.main_api:app --port 8000"
        )
    except Exception as exc:  # red timeout, DNS, etc.
        return False, f"❌ Error verificando backend: {exc}"


def _llamar_chat(
    mensaje: str,
    historial: List[Dict[str, Any]],
    session_id: str,
) -> Tuple[List[Dict[str, Any]], str, str, str]:
    """
    POST /chat al backend FastAPI.

    Returns:
        (historial_actualizado, tabla_html, status, session_id)
    """
    if not mensaje.strip():
        return historial, "", "✓ Listo", session_id

    payload: Dict[str, Any] = {
        "mensaje": mensaje,
        "session_id": session_id or None,
        "historial": historial or [],
    }

    try:
        resp = requests.post(_CHAT_ENDPOINT, json=payload, timeout=_TIMEOUT_CHAT)
        resp.raise_for_status()
        data = resp.json()
        return (
            data.get("historial", historial),
            data.get("tabla_html", ""),
            data.get("status", ""),
            data.get("session_id", session_id),
        )
    except requests.exceptions.ConnectionError:
        msg = f"❌ No se puede conectar al backend en {FASTAPI_URL}. ¿Está iniciado?"
    except requests.exceptions.Timeout:
        msg = "⏳ El backend tardó demasiado en responder. Intenta de nuevo."
    except requests.exceptions.HTTPError as exc:
        msg = f"❌ Error HTTP {exc.response.status_code}: {exc.response.text[:200]}"
    except Exception as exc:
        msg = f"❌ Error inesperado: {exc}"

    historial_error = list(historial)
    historial_error.append({"role": "user", "content": mensaje})
    historial_error.append({"role": "assistant", "content": msg})
    return historial_error, "", "❌ Error", session_id


# ── Interfaz Gradio ──────────────────────────────────────────────────────────

def construir_interfaz() -> gr.Blocks:
    """Construye y retorna el bloque Gradio del cliente API."""
    backend_ok, backend_msg = _verificar_backend()

    with gr.Blocks(title=f"{Config.NOMBRE} — Cliente API") as demo:

        gr.Markdown(f"# {Config.NOMBRE}\n*{Config.NOMBRE_COMPLETO}*")
        gr.Markdown(f"> **Modo:** Cliente HTTP — toda la lógica corre en `{FASTAPI_URL}`")

        estado_backend = gr.Markdown(backend_msg)  # noqa: F841

        # Estado de sesión (no visible al usuario)
        session_id_state = gr.State("")
        historial_state = gr.State([])

        chatbot = gr.Chatbot(
            label="Conversación",
            type="messages",
            height=520,
        )

        with gr.Row():
            mensaje_input = gr.Textbox(
                label="",
                placeholder="Escribe tu consulta sobre Odoo…",
                scale=9,
                lines=1,
            )
            enviar_btn = gr.Button("Enviar", variant="primary", scale=1)

        tabla_output = gr.HTML(label="Datos tabulares")
        status_output = gr.Textbox(label="Estado del pipeline", interactive=False)

        def _responder(
            mensaje: str,
            historial: List[Dict],
            session_id: str,
        ):
            historial_nuevo, tabla, status, new_sid = _llamar_chat(
                mensaje, historial, session_id
            )
            # Gradio type="messages" espera lista de dicts {role, content}
            chat_messages = [
                {"role": e.get("role", "user"), "content": e.get("content", "")}
                for e in historial_nuevo
            ]
            return chat_messages, tabla, status, historial_nuevo, new_sid, ""

        _outputs = [
            chatbot,
            tabla_output,
            status_output,
            historial_state,
            session_id_state,
            mensaje_input,
        ]
        _inputs = [mensaje_input, historial_state, session_id_state]

        enviar_btn.click(fn=_responder, inputs=_inputs, outputs=_outputs)
        mensaje_input.submit(fn=_responder, inputs=_inputs, outputs=_outputs)

    return demo


if __name__ == "__main__":
    demo = construir_interfaz()
    demo.launch(
        server_name=Config.GRADIO_SERVER_NAME,
        server_port=7861,   # Puerto diferente al modo directo (7860)
        share=Config.GRADIO_SHARE,
    )
