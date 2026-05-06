# ============================================================
# ANDROMEDA — tests.test_saas
# Tests Fase 4 — Logging SaaS + Multi-Empresa
#
# Cobertura:
#   - models/db_saas.py: cifrado, ORM, CRUD, sesión contexto
#   - models/odoo_versions.py: mapa de versiones, adaptación de campos
#   - services/logging_saas.py: registro, rotación, métricas
#   - app/api/routers/configuracion.py: CRUD /configuracion
#   - app/api/routers/admin.py: GET /admin/metricas
#   - app/api/routers/chat.py: integración SaaS (contexto + métricas)
#   - app/api/dependencies.py: get_db, pool de conectores
# ============================================================

import os
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# ── Configuración de BD en memoria para tests ────────────────────────────────

@pytest.fixture(autouse=True)
def _db_en_memoria(tmp_path):
    """
    Fuerza una BD SQLite temporal por cada test.
    Resetea el motor global para garantizar aislamiento total.
    """
    db_path = str(tmp_path / "test_saas.db")
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    os.environ.setdefault("SECRET_KEY", "andromeda-test-secret-key-12345")

    import models.db_saas as _mod
    _mod.resetear_db()
    _mod.inicializar_db()

    yield

    _mod.resetear_db()
    os.environ.pop("DB_URL", None)


# ============================================================
# 1. CIFRADO DE CREDENCIALES
# ============================================================

class TestCifrado:
    def test_cifrar_y_descifrar_roundtrip(self):
        from models.db_saas import cifrar_credencial, descifrar_credencial
        original = "mi_password_super_segura"
        cifrado = cifrar_credencial(original)
        assert cifrado != original
        assert descifrar_credencial(cifrado) == original

    def test_cifrado_produce_string_diferente_cada_vez(self):
        """Fernet usa IV aleatorio: dos cifrados del mismo texto producen tokens distintos."""
        from models.db_saas import cifrar_credencial
        p1 = cifrar_credencial("password")
        p2 = cifrar_credencial("password")
        assert p1 != p2  # IV distinto

    def test_descifrar_con_clave_incorrecta_falla(self):
        from models.db_saas import cifrar_credencial
        from cryptography.fernet import Fernet, InvalidToken
        cifrado = cifrar_credencial("secreto")
        # Intentar descifrar con una clave distinta
        import base64, hashlib
        otra_clave = base64.urlsafe_b64encode(hashlib.sha256(b"clave_distinta").digest())
        f = Fernet(otra_clave)
        with pytest.raises((InvalidToken, Exception)):
            f.decrypt(cifrado.encode())

    def test_cifrado_de_cadena_vacia(self):
        from models.db_saas import cifrar_credencial, descifrar_credencial
        assert descifrar_credencial(cifrar_credencial("")) == ""

    def test_cifrado_de_unicode(self):
        from models.db_saas import cifrar_credencial, descifrar_credencial
        texto = "contraseña_con_ñ_y_émojis_🔐"
        assert descifrar_credencial(cifrar_credencial(texto)) == texto


# ============================================================
# 2. MODELO Empresa
# ============================================================

class TestEmpresa:
    def _crear_empresa(self, session, nombre="ACME Corp"):
        from models.db_saas import Empresa
        e = Empresa(
            id=str(uuid.uuid4()),
            nombre=nombre,
            odoo_url="https://acme.odoo.com",
            odoo_db="acme_db",
            odoo_usuario="admin",
            version_odoo=17,
            tipo_erp="odoo",
            activa=True,
            creado_en=datetime.now(timezone.utc),
        )
        e.set_password("secret_password")
        session.add(e)
        session.commit()
        session.refresh(e)
        return e

    def test_crear_empresa_persiste(self):
        from models.db_saas import get_session, Empresa
        session = get_session()
        try:
            e = self._crear_empresa(session)
            assert e.id is not None
            assert e.nombre == "ACME Corp"
            assert e.activa is True
        finally:
            session.close()

    def test_password_no_se_guarda_en_texto_plano(self):
        from models.db_saas import get_session
        session = get_session()
        try:
            e = self._crear_empresa(session)
            assert "secret_password" not in (e.odoo_clave_cifrada or "")
        finally:
            session.close()

    def test_get_password_retorna_texto_plano(self):
        from models.db_saas import get_session
        session = get_session()
        try:
            e = self._crear_empresa(session)
            assert e.get_password() == "secret_password"
        finally:
            session.close()

    def test_to_dict_no_incluye_password(self):
        from models.db_saas import get_session
        session = get_session()
        try:
            e = self._crear_empresa(session)
            d = e.to_dict()
            assert "odoo_password" not in d
            assert "odoo_clave_cifrada" not in d
        finally:
            session.close()

    def test_to_dict_include_credentials(self):
        from models.db_saas import get_session
        session = get_session()
        try:
            e = self._crear_empresa(session)
            d = e.to_dict(include_credentials=True)
            assert d["odoo_password"] == "secret_password"
        finally:
            session.close()

    def test_soft_delete(self):
        from models.db_saas import get_session, Empresa
        session = get_session()
        try:
            e = self._crear_empresa(session)
            eid = e.id
            e.activa = False
            session.commit()
            resultado = session.query(Empresa).filter(
                Empresa.id == eid, Empresa.activa == True
            ).first()
            assert resultado is None
        finally:
            session.close()

    def test_multiples_empresas(self):
        from models.db_saas import get_session, Empresa
        session = get_session()
        try:
            for i in range(3):
                self._crear_empresa(session, nombre=f"Empresa {i}")
            count = session.query(Empresa).filter(Empresa.activa == True).count()
            assert count == 3
        finally:
            session.close()


# ============================================================
# 3. MODELO Usuario
# ============================================================

class TestUsuario:
    def _crear_empresa_y_usuario(self, session):
        from models.db_saas import Empresa, Usuario
        e = Empresa(
            id=str(uuid.uuid4()),
            nombre="Corp X",
            odoo_url="https://x.odoo.com",
            odoo_db="x_db",
            odoo_usuario="admin",
            odoo_clave_cifrada="placeholder",
            version_odoo=17,
            tipo_erp="odoo",
            activa=True,
        )
        session.add(e)
        session.flush()

        u = Usuario(
            id=str(uuid.uuid4()),
            nombre="Juan Pérez",
            email=f"juan_{uuid.uuid4().hex[:6]}@corp.com",
            empresa_id=e.id,
            rol="agente",
            activo=True,
        )
        session.add(u)
        session.commit()
        return e, u

    def test_crear_usuario(self):
        from models.db_saas import get_session
        session = get_session()
        try:
            e, u = self._crear_empresa_y_usuario(session)
            assert u.id is not None
            assert u.empresa_id == e.id
            assert u.rol == "agente"
        finally:
            session.close()

    def test_to_dict_usuario(self):
        from models.db_saas import get_session
        session = get_session()
        try:
            _, u = self._crear_empresa_y_usuario(session)
            d = u.to_dict()
            assert "id" in d
            assert "email" in d
            assert "empresa_id" in d
        finally:
            session.close()

    def test_roles_validos(self):
        from models.db_saas import get_session, Empresa, Usuario
        session = get_session()
        try:
            e = Empresa(
                id=str(uuid.uuid4()),
                nombre="RolTest",
                odoo_url="https://test.odoo.com",
                odoo_db="db",
                odoo_usuario="usr",
                odoo_clave_cifrada="x",
                version_odoo=17,
                tipo_erp="odoo",
                activa=True,
            )
            session.add(e)
            session.flush()
            for rol in ["admin", "agente", "usuario"]:
                u = Usuario(
                    id=str(uuid.uuid4()),
                    nombre=f"User {rol}",
                    email=f"{rol}_{uuid.uuid4().hex[:6]}@test.com",
                    empresa_id=e.id,
                    rol=rol,
                )
                session.add(u)
            session.commit()
        finally:
            session.close()


# ============================================================
# 4. SesionLog y SesionContexto
# ============================================================

class TestSesionLog:
    def test_crear_sesion_log(self):
        from models.db_saas import get_session, SesionLog
        session = get_session()
        try:
            log = SesionLog(
                session_id=str(uuid.uuid4()),
                accion="chat",
                tipo_consulta="ventas",
                resultado="ok",
                duracion_ms=250,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(log)
            session.commit()
            assert log.id is not None
        finally:
            session.close()

    def test_sesion_contexto_roundtrip(self):
        from models.db_saas import get_session, SesionContexto
        session = get_session()
        try:
            historial = [
                {"role": "user", "content": "¿Cuánto se vendió?"},
                {"role": "assistant", "content": "Se vendieron 1000 unidades."},
            ]
            ctx = SesionContexto(
                session_id=str(uuid.uuid4()),
                empresa_id=None,
                creado_en=datetime.now(timezone.utc),
            )
            ctx.set_historial(historial)
            session.add(ctx)
            session.commit()

            recuperado = ctx.get_historial()
            assert len(recuperado) == 2
            assert recuperado[0]["role"] == "user"
        finally:
            session.close()

    def test_sesion_contexto_json_invalido_retorna_lista_vacia(self):
        from models.db_saas import SesionContexto
        ctx = SesionContexto()
        ctx.historial_json = "no_es_json_valido{{"
        assert ctx.get_historial() == []


# ============================================================
# 5. MAPA DE VERSIONES ODOO
# ============================================================

class TestOdooVersiones:
    def test_adaptar_campos_v14_renombra_move_type(self):
        from models.odoo_versions import adaptar_campos
        campos = ["move_type", "name", "amount_total"]
        resultado = adaptar_campos("account.move", campos, version=14)
        assert "type" in resultado
        assert "move_type" not in resultado
        assert "name" in resultado
        assert "amount_total" in resultado

    def test_adaptar_campos_v17_sin_cambio_account_move(self):
        from models.odoo_versions import adaptar_campos
        campos = ["move_type", "name", "amount_total"]
        resultado = adaptar_campos("account.move", campos, version=17)
        assert resultado == campos  # v17 no cambia estos campos

    def test_adaptar_campos_omite_campo_none(self):
        from models.odoo_versions import adaptar_campos
        # immediate_transfer → None en v14 → debe omitirse
        campos = ["name", "immediate_transfer", "state"]
        resultado = adaptar_campos("stock.picking", campos, version=14)
        assert "immediate_transfer" not in resultado
        assert "name" in resultado
        assert "state" in resultado

    def test_adaptar_campos_version_desconocida_retorna_igual(self):
        from models.odoo_versions import adaptar_campos
        campos = ["move_type", "name"]
        resultado = adaptar_campos("account.move", campos, version=99)
        assert resultado == campos

    def test_adaptar_campos_modelo_sin_overrides(self):
        from models.odoo_versions import adaptar_campos
        campos = ["name", "list_price", "qty_available"]
        resultado = adaptar_campos("product.product", campos, version=14)
        assert resultado == campos

    def test_adaptar_campos_lista_vacia(self):
        from models.odoo_versions import adaptar_campos
        assert adaptar_campos("account.move", [], version=14) == []

    def test_obtener_modelo_canonico_v14_hr_leave(self):
        from models.odoo_versions import obtener_modelo_canonico
        resultado = obtener_modelo_canonico("hr.leave", version=14)
        assert resultado == "hr.holidays"

    def test_obtener_modelo_canonico_v17_sin_cambio(self):
        from models.odoo_versions import obtener_modelo_canonico
        resultado = obtener_modelo_canonico("hr.leave", version=17)
        assert resultado == "hr.leave"

    def test_obtener_modelo_canonico_modelo_sin_override(self):
        from models.odoo_versions import obtener_modelo_canonico
        assert obtener_modelo_canonico("sale.order", version=14) == "sale.order"

    def test_detectar_version_odoo_mock(self):
        from models.odoo_versions import detectar_version_odoo
        mock_odoo = MagicMock()
        mock_odoo.version = "17.0"
        assert detectar_version_odoo(mock_odoo) == 17

    def test_detectar_version_v16(self):
        from models.odoo_versions import detectar_version_odoo
        mock_odoo = MagicMock()
        mock_odoo.version = "16.0"
        assert detectar_version_odoo(mock_odoo) == 16

    def test_detectar_version_odoo_fallback(self):
        from models.odoo_versions import detectar_version_odoo
        mock_odoo = MagicMock()
        mock_odoo.version = "invalid"
        assert detectar_version_odoo(mock_odoo) == 17  # default seguro

    def test_detectar_version_odoo_excepcion(self):
        from models.odoo_versions import detectar_version_odoo
        mock_odoo = MagicMock()
        mock_odoo.version = MagicMock(side_effect=Exception("timeout"))
        assert detectar_version_odoo(mock_odoo) == 17

    def test_erp_adapter_protocol_cumplido_por_mock(self):
        from models.odoo_versions import ERPAdapterProtocol
        mock = MagicMock(spec=["tipo_erp", "conectar", "desconectar", "buscar", "buscar_leer"])
        mock.tipo_erp = "odoo"
        assert isinstance(mock, ERPAdapterProtocol)

    def test_es_erp_soportado(self):
        from models.odoo_versions import es_erp_soportado
        assert es_erp_soportado("odoo") is True
        assert es_erp_soportado("sap") is False
        assert es_erp_soportado("desconocido") is False

    def test_versiones_soportadas_odoo(self):
        from models.odoo_versions import versiones_soportadas_odoo
        versiones = versiones_soportadas_odoo()
        assert 14 in versiones
        assert 17 in versiones
        assert 19 in versiones
        assert 13 not in versiones


# ============================================================
# 6. LOGGING SAAS
# ============================================================

class TestLoggingSaas:
    def test_registrar_consulta_ok(self):
        from services.logging_saas import registrar_consulta
        from models.db_saas import get_session, SesionLog
        empresa_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        registrar_consulta(
            empresa_id=empresa_id,
            accion="chat",
            duracion_ms=120,
            exito=True,
            tipo_consulta="ventas",
            session_id=session_id,
        )
        session = get_session()
        try:
            logs = session.query(SesionLog).filter(SesionLog.session_id == session_id).all()
            assert len(logs) == 1
            assert logs[0].resultado == "ok"
            assert logs[0].tipo_consulta == "ventas"
            assert logs[0].duracion_ms == 120
        finally:
            session.close()

    def test_registrar_consulta_error(self):
        from services.logging_saas import registrar_consulta
        from models.db_saas import get_session, SesionLog
        session_id = str(uuid.uuid4())
        registrar_consulta(
            empresa_id=None,
            accion="chat",
            duracion_ms=50,
            exito=False,
            error_msg="Timeout de conexión",
            session_id=session_id,
        )
        session = get_session()
        try:
            log = session.query(SesionLog).filter(
                SesionLog.session_id == session_id
            ).first()
            assert log is not None
            assert log.resultado == "error"
            assert "Timeout" in (log.error_msg or "")
        finally:
            session.close()

    def test_registrar_consulta_tolera_fallo_bd(self):
        """No debe lanzar excepción aunque la BD falle."""
        import models.db_saas as _mod
        _mod.resetear_db()
        os.environ["DB_URL"] = "sqlite:////ruta/inexistente/no_existe.db"
        try:
            from services.logging_saas import registrar_consulta
            # No debe lanzar
            registrar_consulta("emp1", "chat", 100, True)
        finally:
            os.environ.pop("DB_URL", None)
            _mod.resetear_db()

    def test_obtener_metricas_sin_registros(self):
        from services.logging_saas import obtener_metricas
        m = obtener_metricas(empresa_id="inexistente")
        assert m["total_consultas"] == 0
        assert m["tasa_error"] == 0.0

    def test_obtener_metricas_con_registros(self):
        from services.logging_saas import registrar_consulta, obtener_metricas
        eid = str(uuid.uuid4())
        for i in range(5):
            registrar_consulta(eid, "chat", 100 + i * 10, True, tipo_consulta="ventas")
        registrar_consulta(eid, "chat", 500, False, tipo_consulta="inventario")

        m = obtener_metricas(empresa_id=eid)
        assert m["total_consultas"] == 6
        assert m["consultas_ok"] == 5
        assert m["consultas_error"] == 1
        assert round(m["tasa_error"], 1) == round(1 / 6 * 100, 1)
        assert "ventas" in m["por_tipo"]
        assert m["por_tipo"]["ventas"] == 5

    def test_obtener_metricas_globales(self):
        from services.logging_saas import registrar_consulta, obtener_metricas
        eid1 = str(uuid.uuid4())
        eid2 = str(uuid.uuid4())
        registrar_consulta(eid1, "chat", 100, True)
        registrar_consulta(eid2, "chat", 200, True)
        m = obtener_metricas()
        assert m["total_consultas"] >= 2
        assert m["empresas_activas"] is not None

    def test_rotar_logs_antiguos(self):
        from services.logging_saas import rotar_logs_antiguos
        from models.db_saas import get_session, SesionLog
        session = get_session()
        try:
            # Insertar log antiguo (>30 días)
            log_viejo = SesionLog(
                accion="chat",
                resultado="ok",
                timestamp=datetime.now(timezone.utc) - timedelta(days=45),
            )
            log_nuevo = SesionLog(
                accion="chat",
                resultado="ok",
                timestamp=datetime.now(timezone.utc),
            )
            session.add_all([log_viejo, log_nuevo])
            session.commit()
        finally:
            session.close()

        eliminados = rotar_logs_antiguos(dias=30)
        assert eliminados >= 1

        session2 = get_session()
        try:
            restantes = session2.query(SesionLog).all()
            fechas = [r.timestamp for r in restantes if r.timestamp]
            corte = datetime.now(timezone.utc) - timedelta(days=30)
            for f in fechas:
                f_naive = f.replace(tzinfo=timezone.utc) if f.tzinfo is None else f
                assert f_naive >= corte
        finally:
            session2.close()

    def test_rotar_logs_tolera_fallo(self):
        """No debe lanzar excepción aunque la BD falle."""
        import models.db_saas as _mod
        _mod.resetear_db()
        os.environ["DB_URL"] = "sqlite:////ruta/inexistente/no_existe.db"
        try:
            from services.logging_saas import rotar_logs_antiguos
            resultado = rotar_logs_antiguos()
            assert resultado == 0
        finally:
            os.environ.pop("DB_URL", None)
            _mod.resetear_db()


# ============================================================
# 7. ENDPOINTS /configuracion
# ============================================================

@pytest.fixture()
def api_client():
    """
    TestClient de FastAPI con bot mockeado y dependencias de auth sobreescritas.

    Sprint 1: los endpoints de /configuracion requieren get_solo_admin (dependencies.py)
    y los de /admin/* requieren _solo_admin (admin.py — función local pendiente de refactor).
    Los de /chat requieren get_usuario_autenticado.
    """
    from fastapi.testclient import TestClient
    from app.api.main_api import app
    from app.api.dependencies import get_bot, get_solo_admin, get_usuario_autenticado
    from app.api.routers.admin import _solo_admin as _admin_local

    mock_bot = MagicMock()
    mock_bot.procesar_mensaje.return_value = (
        [{"role": "assistant", "content": "OK"}], "", "✓ ventas"
    )

    _admin_payload = {"sub": "admin-test", "rol": "admin", "empresa_id": None}
    _user_payload  = {"sub": "user-test",  "rol": "agente", "empresa_id": None}

    app.dependency_overrides[get_bot] = lambda: mock_bot
    app.dependency_overrides[get_solo_admin] = lambda: _admin_payload
    app.dependency_overrides[_admin_local] = lambda: _admin_payload
    app.dependency_overrides[get_usuario_autenticado] = lambda: _user_payload

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


EMPRESA_PAYLOAD = {
    "nombre": "Test Corp",
    "odoo_url": "https://test.odoo.com",
    "odoo_db": "test_db",
    "odoo_usuario": "admin",
    "odoo_password": "test_pass_123",
    "version_odoo": 17,
    "tipo_erp": "odoo",
}


class TestConfiguracionEndpoints:
    def test_listar_empresas_vacio(self, api_client):
        r = api_client.get("/configuracion")
        assert r.status_code == 200
        assert r.json() == []

    def test_crear_empresa_201(self, api_client):
        r = api_client.post("/configuracion", json=EMPRESA_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert data["nombre"] == "Test Corp"
        assert data["activa"] is True
        assert "odoo_password" not in data
        assert "odoo_clave_cifrada" not in data
        assert "id" in data

    def test_listar_empresas_con_datos(self, api_client):
        api_client.post("/configuracion", json=EMPRESA_PAYLOAD)
        r = api_client.get("/configuracion")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_obtener_empresa_por_id(self, api_client):
        r_create = api_client.post("/configuracion", json=EMPRESA_PAYLOAD)
        eid = r_create.json()["id"]
        r = api_client.get(f"/configuracion/{eid}")
        assert r.status_code == 200
        assert r.json()["id"] == eid

    def test_obtener_empresa_no_existente_404(self, api_client):
        r = api_client.get("/configuracion/no-existe-id")
        assert r.status_code == 404

    def test_actualizar_empresa(self, api_client):
        r_create = api_client.post("/configuracion", json=EMPRESA_PAYLOAD)
        eid = r_create.json()["id"]
        r = api_client.put(f"/configuracion/{eid}", json={"nombre": "Corp Actualizada"})
        assert r.status_code == 200
        assert r.json()["nombre"] == "Corp Actualizada"

    def test_actualizar_empresa_password_recifra(self, api_client):
        r_create = api_client.post("/configuracion", json=EMPRESA_PAYLOAD)
        eid = r_create.json()["id"]
        r = api_client.put(f"/configuracion/{eid}", json={"odoo_password": "nueva_pass"})
        assert r.status_code == 200
        # Verificar que la nueva contraseña se descifra correctamente en la BD
        from models.db_saas import get_session, Empresa
        session = get_session()
        try:
            e = session.query(Empresa).filter(Empresa.id == eid).first()
            assert e.get_password() == "nueva_pass"
        finally:
            session.close()

    def test_desactivar_empresa_204(self, api_client):
        r_create = api_client.post("/configuracion", json=EMPRESA_PAYLOAD)
        eid = r_create.json()["id"]
        r = api_client.delete(f"/configuracion/{eid}")
        assert r.status_code == 204
        # Verificar que ya no aparece en el listado
        r_list = api_client.get("/configuracion")
        assert all(e["id"] != eid for e in r_list.json())

    def test_desactivar_empresa_no_existente_404(self, api_client):
        r = api_client.delete("/configuracion/no-existe")
        assert r.status_code == 404

    def test_crear_empresa_tipo_erp_invalido_422(self, api_client):
        payload = {**EMPRESA_PAYLOAD, "tipo_erp": "erp_invalido"}
        r = api_client.post("/configuracion", json=payload)
        assert r.status_code == 422

    def test_crear_empresa_version_fuera_de_rango_422(self, api_client):
        payload = {**EMPRESA_PAYLOAD, "version_odoo": 5}
        r = api_client.post("/configuracion", json=payload)
        assert r.status_code == 422

    def test_crear_empresa_sin_campos_requeridos_422(self, api_client):
        r = api_client.post("/configuracion", json={"nombre": "Solo nombre"})
        assert r.status_code == 422


# ============================================================
# 8. ENDPOINTS /admin/metricas
# ============================================================

class TestAdminMetricas:
    def test_metricas_globales_sin_datos(self, api_client):
        r = api_client.get("/admin/metricas")
        assert r.status_code == 200
        data = r.json()
        assert data["total_consultas"] == 0

    def test_metricas_con_dias_parametro(self, api_client):
        r = api_client.get("/admin/metricas?dias=7")
        assert r.status_code == 200

    def test_metricas_con_empresa_id(self, api_client):
        r = api_client.get("/admin/metricas?empresa_id=test-empresa-123")
        assert r.status_code == 200
        assert r.json()["empresa_id"] == "test-empresa-123"

    def test_metricas_dias_invalido(self, api_client):
        r = api_client.get("/admin/metricas?dias=0")
        assert r.status_code == 422

    def test_metricas_por_empresa_endpoint(self, api_client):
        r = api_client.get("/admin/metricas/emp-especifica")
        assert r.status_code == 200
        assert r.json()["empresa_id"] == "emp-especifica"

    def test_metricas_reflejan_datos_registrados(self, api_client):
        from services.logging_saas import registrar_consulta
        eid = str(uuid.uuid4())
        for _ in range(3):
            registrar_consulta(eid, "chat", 200, True, tipo_consulta="ventas")

        r = api_client.get(f"/admin/metricas/{eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total_consultas"] == 3
        assert data["por_tipo"].get("ventas") == 3


# ============================================================
# 9. CHAT con integración SaaS (contexto de sesión)
# ============================================================

class TestChatSesionContexto:
    def test_chat_genera_session_id(self, api_client):
        r = api_client.post("/chat", json={"mensaje": "hola"})
        assert r.status_code == 200
        assert r.json()["session_id"]

    def test_chat_restaura_contexto_de_sesion(self, api_client):
        """Si el historial está vacío pero el session_id tiene contexto guardado, lo usa."""
        from models.db_saas import get_session, SesionContexto
        sid = str(uuid.uuid4())
        # Precargar contexto
        db = get_session()
        try:
            ctx = SesionContexto(
                session_id=sid,
                empresa_id=None,
                creado_en=datetime.now(timezone.utc),
            )
            ctx.set_historial([{"role": "user", "content": "pregunta previa"}])
            db.add(ctx)
            db.commit()
        finally:
            db.close()

        # El chat sin historial debe recuperarlo de BD
        r = api_client.post("/chat", json={"mensaje": "nueva pregunta", "session_id": sid})
        assert r.status_code == 200

    def test_chat_persiste_contexto_actualizado(self, api_client):
        sid = str(uuid.uuid4())
        api_client.post("/chat", json={"mensaje": "Dime ventas", "session_id": sid})

        from models.db_saas import get_session, SesionContexto
        db = get_session()
        try:
            ctx = db.query(SesionContexto).filter(
                SesionContexto.session_id == sid
            ).first()
            assert ctx is not None
            historial = ctx.get_historial()
            assert len(historial) >= 1
        finally:
            db.close()

    def test_chat_registra_en_sesion_log(self, api_client):
        from models.db_saas import get_session, SesionLog
        sid = str(uuid.uuid4())
        api_client.post("/chat", json={
            "mensaje": "Ventas del mes",
            "session_id": sid,
            "empresa_id": "test-emp-001",
        })

        db = get_session()
        try:
            logs = db.query(SesionLog).filter(SesionLog.session_id == sid).all()
            assert len(logs) >= 1
            assert logs[0].accion == "chat"
        finally:
            db.close()


# ============================================================
# 10. DEPENDENCIAS
# ============================================================

class TestDependencies:
    def test_get_db_generador(self):
        from app.api.dependencies import get_db
        gen = get_db()
        session = next(gen)
        assert session is not None
        try:
            next(gen)
        except StopIteration:
            pass

    def test_get_conector_empresa_sin_empresa_en_bd(self):
        """Debe retornar un ConectorOdoo (default) sin lanzar excepción."""
        from app.api.dependencies import get_conector_empresa, _conector_pool
        _conector_pool.clear()
        with patch("models.conector_odoo.ConectorOdoo") as MockConector:
            MockConector.return_value = MagicMock()
            conector = get_conector_empresa("empresa-no-registrada")
            assert conector is not None

    def test_invalidar_pool_empresa(self):
        from app.api.dependencies import _conector_pool, invalidar_pool_empresa
        _conector_pool["test-id"] = MagicMock()
        invalidar_pool_empresa("test-id")
        assert "test-id" not in _conector_pool

    def test_invalidar_pool_inexistente_no_lanza(self):
        from app.api.dependencies import invalidar_pool_empresa
        invalidar_pool_empresa("id-que-no-existe")  # No debe lanzar
