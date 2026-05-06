# ============================================================
# ANDROMEDA — tests/test_api.py
# Tests de la capa FastAPI (Fase 3).
#
# Estrategia:
#   - El bot (OdooAIProV5) se reemplaza con un MagicMock vía
#     app.dependency_overrides[get_bot].
#   - Se usa FastAPI TestClient (starlette) — síncrono, sin uvicorn real.
#   - Cada clase de test es independiente. El mock se restaura al final.
# ============================================================

import pytest
from unittest.mock import MagicMock, patch

# ── Importaciones diferidas dentro de fixtures para evitar carga de PyTorch ──


# ═══════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def mock_bot():
    """
    Mock de OdooAIProV5.

    procesar_mensaje devuelve el tuple estándar:
        (historial_actualizado, tabla_html, status)
    """
    bot = MagicMock()
    bot.procesar_mensaje.return_value = (
        [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"},
        ],
        "",               # tabla_html vacía
        "✓ saludo (100%)",
    )
    bot.llm_activo = True
    bot.odoo = MagicMock()
    bot.odoo.conectado = False
    return bot


@pytest.fixture(scope="module")
def client(mock_bot):
    """
    TestClient con bot y autenticación sobreescritos por mocks.
    Sprint 1: /chat requiere JWT — se inyecta un payload de agente de prueba.
    Se limpia dependency_overrides al finalizar el módulo.
    """
    from fastapi.testclient import TestClient
    from app.api.main_api import app
    from app.api.dependencies import get_bot, get_usuario_autenticado

    _payload_test = {"sub": "test-uid", "rol": "agente", "empresa_id": "test-empresa-001"}

    app.dependency_overrides[get_bot] = lambda: mock_bot
    app.dependency_overrides[get_usuario_autenticado] = lambda: _payload_test
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════
# GET /health
# ═══════════════════════════════════════════════════════════

class TestHealthEndpoint:

    def test_health_retorna_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_status_ok(self, client):
        assert client.get("/health").json()["status"] == "ok"

    def test_health_incluye_version(self, client):
        data = client.get("/health").json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_incluye_nombre(self, client):
        assert client.get("/health").json()["nombre"] == "ANDROMEDA"

    def test_health_no_requiere_cuerpo(self, client):
        """GET /health no necesita autenticación ni body."""
        assert client.get("/health").status_code == 200

    def test_health_nombre_completo_ausente(self, client):
        """nombre_completo no forma parte del contrato de /health."""
        data = client.get("/health").json()
        # Verificamos que solo tenga las claves definidas en el contrato
        assert set(data.keys()) == {"status", "version", "nombre"}


# ═══════════════════════════════════════════════════════════
# GET /status
# ═══════════════════════════════════════════════════════════

class TestStatusEndpoint:

    def test_status_retorna_200(self, client):
        assert client.get("/status").status_code == 200

    def test_status_tiene_clave_bot(self, client):
        assert "bot" in client.get("/status").json()

    def test_status_bot_es_ready(self, client):
        assert client.get("/status").json()["bot"] == "ready"

    def test_status_tiene_clave_llm(self, client):
        data = client.get("/status").json()
        assert "llm" in data
        assert isinstance(data["llm"], bool)

    def test_status_tiene_clave_odoo(self, client):
        data = client.get("/status").json()
        assert "odoo" in data
        assert isinstance(data["odoo"], bool)

    def test_status_tiene_clave_version(self, client):
        assert "version" in client.get("/status").json()

    def test_status_llm_refleja_mock(self, client, mock_bot):
        mock_bot.llm_activo = True
        assert client.get("/status").json()["llm"] is True

    def test_status_odoo_refleja_mock(self, client, mock_bot):
        mock_bot.odoo.conectado = False
        assert client.get("/status").json()["odoo"] is False


# ═══════════════════════════════════════════════════════════
# POST /chat
# ═══════════════════════════════════════════════════════════

class TestChatEndpoint:

    def test_chat_retorna_200(self, client):
        assert client.post("/chat", json={"mensaje": "Hola"}).status_code == 200

    def test_chat_contiene_respuesta(self, client):
        data = client.post("/chat", json={"mensaje": "Hola"}).json()
        assert "respuesta" in data
        assert len(data["respuesta"]) > 0

    def test_chat_respuesta_es_del_asistente(self, client):
        data = client.post("/chat", json={"mensaje": "Hola"}).json()
        assert "¡Hola!" in data["respuesta"]

    def test_chat_contiene_session_id(self, client):
        data = client.post("/chat", json={"mensaje": "test"}).json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_chat_session_id_personalizado_se_conserva(self, client):
        sid = "sesion-test-abc-123"
        data = client.post("/chat", json={"mensaje": "test", "session_id": sid}).json()
        assert data["session_id"] == sid

    def test_chat_session_id_autogenerado_es_uuid(self, client):
        """Sin session_id, el servidor genera uno automáticamente."""
        import uuid
        data = client.post("/chat", json={"mensaje": "test"}).json()
        # Debe ser parseable como UUID
        uuid.UUID(data["session_id"])  # lanza ValueError si no es UUID válido

    def test_chat_contiene_timestamp(self, client):
        data = client.post("/chat", json={"mensaje": "test"}).json()
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # formato ISO 8601

    def test_chat_contiene_historial(self, client):
        data = client.post("/chat", json={"mensaje": "Hola"}).json()
        assert "historial" in data
        assert isinstance(data["historial"], list)
        assert len(data["historial"]) >= 1

    def test_chat_contiene_status(self, client):
        data = client.post("/chat", json={"mensaje": "Hola"}).json()
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_chat_contiene_tabla_html(self, client):
        data = client.post("/chat", json={"mensaje": "Hola"}).json()
        assert "tabla_html" in data

    def test_chat_pasa_historial_previo_al_bot(self, client, mock_bot):
        """El router debe pasar el historial recibido al método del bot."""
        mock_bot.procesar_mensaje.reset_mock()
        historial_previo = [{"role": "user", "content": "Pregunta anterior"}]
        client.post("/chat", json={"mensaje": "Nueva pregunta", "historial": historial_previo})
        call = mock_bot.procesar_mensaje.call_args
        historial_recibido = call.kwargs.get("historial") or (
            call.args[1] if len(call.args) > 1 else []
        )
        assert historial_recibido == historial_previo

    def test_chat_pasa_mensaje_al_bot(self, client, mock_bot):
        mock_bot.procesar_mensaje.reset_mock()
        client.post("/chat", json={"mensaje": "consulta especifica"})
        call = mock_bot.procesar_mensaje.call_args
        mensaje_recibido = call.kwargs.get("mensaje") or (
            call.args[0] if call.args else ""
        )
        assert mensaje_recibido == "consulta especifica"

    def test_chat_mensaje_vacio_retorna_422(self, client):
        assert client.post("/chat", json={"mensaje": ""}).status_code == 422

    def test_chat_mensaje_demasiado_largo_retorna_422(self, client):
        assert client.post("/chat", json={"mensaje": "x" * 2001}).status_code == 422

    def test_chat_sin_body_retorna_422(self, client):
        assert client.post("/chat").status_code == 422

    def test_chat_empresa_id_opcional(self, client):
        resp = client.post("/chat", json={"mensaje": "test", "empresa_id": "empresa-001"})
        assert resp.status_code == 200

    def test_chat_historial_ausente_es_lista_vacia(self, client, mock_bot):
        """Si no se envía historial, el bot recibe lista vacía."""
        mock_bot.procesar_mensaje.reset_mock()
        client.post("/chat", json={"mensaje": "sin historial"})
        call = mock_bot.procesar_mensaje.call_args
        # Usar sentinel para detectar clave ausente (evita falsy-trap con list vacía)
        _sentinel = object()
        historial_recibido = call.kwargs.get("historial", _sentinel)
        if historial_recibido is _sentinel:
            historial_recibido = call.args[1] if len(call.args) > 1 else None
        assert historial_recibido == []

    def test_chat_error_interno_retorna_500(self, client, mock_bot):
        """Excepción del bot → HTTP 500 con detalle."""
        mock_bot.procesar_mensaje.side_effect = RuntimeError("Error de prueba")
        try:
            resp = client.post("/chat", json={"mensaje": "test error"})
            assert resp.status_code == 500
            assert "Error procesando mensaje" in resp.json().get("detail", "")
        finally:
            # Restaurar siempre, aunque el assert falle
            mock_bot.procesar_mensaje.side_effect = None
            mock_bot.procesar_mensaje.return_value = (
                [
                    {"role": "user", "content": "Hola"},
                    {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"},
                ],
                "",
                "✓ saludo (100%)",
            )


# ═══════════════════════════════════════════════════════════
# GET /reportes
# ═══════════════════════════════════════════════════════════

class TestReportesEndpoint:

    def test_listar_reportes_200(self, client):
        assert client.get("/reportes").status_code == 200

    def test_listar_reportes_tiene_tipos(self, client):
        data = client.get("/reportes").json()
        assert "tipos" in data
        assert isinstance(data["tipos"], list)
        assert len(data["tipos"]) > 0

    def test_listar_reportes_tiene_total(self, client):
        data = client.get("/reportes").json()
        assert "total" in data
        assert data["total"] == len(data["tipos"])

    def test_listar_reportes_cada_tipo_tiene_campos(self, client):
        for tipo in client.get("/reportes").json()["tipos"]:
            assert "id" in tipo
            assert "nombre" in tipo
            assert "descripcion" in tipo

    def test_listar_reportes_incluye_ventas(self, client):
        ids = {t["id"] for t in client.get("/reportes").json()["tipos"]}
        assert "ventas" in ids

    def test_listar_reportes_incluye_inventario(self, client):
        ids = {t["id"] for t in client.get("/reportes").json()["tipos"]}
        assert "inventario" in ids

    def test_generar_reporte_valido_200(self, client):
        assert client.post("/reportes/generar", json={"tipo": "ventas"}).status_code == 200

    def test_generar_reporte_tiene_tipo(self, client):
        data = client.post("/reportes/generar", json={"tipo": "ventas"}).json()
        assert data["tipo"] == "ventas"

    def test_generar_reporte_tiene_timestamp(self, client):
        data = client.post("/reportes/generar", json={"tipo": "inventario"}).json()
        assert "timestamp" in data

    def test_generar_reporte_tiene_mensaje(self, client):
        data = client.post("/reportes/generar", json={"tipo": "finanzas"}).json()
        assert "mensaje" in data
        assert len(data["mensaje"]) > 0

    def test_generar_reporte_tipo_invalido_422(self, client):
        resp = client.post("/reportes/generar", json={"tipo": "tipo_inexistente"})
        assert resp.status_code == 422

    def test_generar_reporte_tipo_invalido_incluye_detalle(self, client):
        data = client.post("/reportes/generar", json={"tipo": "xyz"}).json()
        assert "detail" in data

    def test_generar_reporte_sin_body_422(self, client):
        assert client.post("/reportes/generar").status_code == 422


# ═══════════════════════════════════════════════════════════
# Schemas — validación pura (sin HTTP)
# ═══════════════════════════════════════════════════════════

class TestSchemas:

    def test_mensaje_request_con_defaults(self):
        from app.api.schemas import MensajeRequest
        req = MensajeRequest(mensaje="Hola")
        assert req.mensaje == "Hola"
        assert req.session_id is None
        assert req.empresa_id is None
        assert req.historial == []

    def test_mensaje_request_con_historial(self):
        from app.api.schemas import MensajeRequest
        hist = [{"role": "user", "content": "test"}]
        req = MensajeRequest(mensaje="Nueva consulta", historial=hist)
        assert req.historial == hist

    def test_mensaje_request_vacio_lanza_error(self):
        from app.api.schemas import MensajeRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MensajeRequest(mensaje="")

    def test_mensaje_request_demasiado_largo_lanza_error(self):
        from app.api.schemas import MensajeRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MensajeRequest(mensaje="x" * 2001)

    def test_respuesta_api_instanciable(self):
        from app.api.schemas import RespuestaAPI
        r = RespuestaAPI(
            respuesta="OK",
            tabla_html="",
            status="✓ test",
            session_id="abc-123",
            historial=[],
            timestamp="2026-04-06T00:00:00",
        )
        assert r.respuesta == "OK"
        assert r.session_id == "abc-123"

    def test_generar_reporte_request_valido(self):
        from app.api.schemas import GenerarReporteRequest
        req = GenerarReporteRequest(tipo="ventas")
        assert req.tipo == "ventas"
        assert req.parametros == {}

    def test_generar_reporte_request_con_params(self):
        from app.api.schemas import GenerarReporteRequest
        req = GenerarReporteRequest(tipo="ventas", parametros={"periodo": "2026-Q1"})
        assert req.parametros["periodo"] == "2026-Q1"

    def test_tipo_reporte_instanciable(self):
        from app.api.schemas import TipoReporte
        t = TipoReporte(id="ventas", nombre="Ventas", descripcion="Reporte de ventas")
        assert t.id == "ventas"


# ═══════════════════════════════════════════════════════════
# Middleware — integración (verificar que los requests se loguean)
# ═══════════════════════════════════════════════════════════

class TestMiddlewareLogging:

    def test_middleware_no_rompe_health(self, client):
        """El middleware de logging no debe alterar la respuesta."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_middleware_no_rompe_chat(self, client):
        resp = client.post("/chat", json={"mensaje": "Hola"})
        assert resp.status_code == 200

    def test_middleware_schema_logging(self):
        """Verifica que el módulo de middleware sea importable y tenga la función."""
        from app.api.middlewares.logging import log_requests_middleware
        import asyncio
        assert callable(log_requests_middleware)
