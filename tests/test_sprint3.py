# ============================================================
# ANDROMEDA — tests.test_sprint3
# Sprint 3 — Filtrado de Datos por Área en Ejecutores
#
# Cobertura:
#   - models/conector_odoo.py : _aplicar_filtro_area (método estático)
#   - models/conector_odoo.py : buscar() aplica _ctx_usuario_filtro
#   - models/conector_odoo.py : buscar_leer() aplica _ctx_usuario_filtro
#   - app/api/routers/chat.py : _resolver_area_desde_bd helper
#   - app/api/routers/chat.py : ContextVar se establece antes del bot
#   - Integración: POST /chat con sub_rol → filtro aplicado en buscar()
# ============================================================

import os
import uuid
from typing import List
from unittest.mock import MagicMock, patch

import pytest


# ── BD en memoria aislada por test ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _db_en_memoria(tmp_path):
    """SQLite temporal — cada test parte con BD limpia."""
    db_path = str(tmp_path / "test_sprint3.db")
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    os.environ.setdefault("SECRET_KEY", "andromeda-test-secret-sprint3")

    import models.db_saas as _mod
    _mod.resetear_db()
    _mod.inicializar_db()
    yield
    _mod.resetear_db()
    os.environ.pop("DB_URL", None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _crear_empresa(nombre: str = "FiltradoCorp") -> str:
    from models.db_saas import get_session, Empresa
    s = get_session()
    try:
        e = Empresa(
            id=str(uuid.uuid4()),
            nombre=nombre,
            odoo_url="https://demo.odoo.com",
            odoo_db="demo",
            odoo_usuario="admin",
            odoo_clave_cifrada="placeholder",
        )
        s.add(e)
        s.commit()
        return e.id
    finally:
        s.close()


def _crear_area(empresa_id: str, codigo: str = "TDA-042", tipo: str = "tienda") -> str:
    from models.db_saas import get_session, Area
    s = get_session()
    try:
        a = Area(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            nombre=f"Área {codigo}",
            codigo=codigo,
            tipo=tipo,
            activa=True,
        )
        s.add(a)
        s.commit()
        return a.id
    finally:
        s.close()


# =============================================================================
# 1. Tests de _aplicar_filtro_area (método estático puro)
# =============================================================================

class TestAplicarFiltroArea:
    """Tests unitarios del método estático sin conexión a Odoo."""

    def setup_method(self):
        from models.conector_odoo import ConectorOdoo
        self.fn = ConectorOdoo._aplicar_filtro_area

    # ── Sub-roles globales — sin filtro ──────────────────────────────────────

    def test_admin_global_sin_filtro(self):
        ctx = {"rol": "admin", "sub_rol": "admin_global", "area_codigo": "TDA-042"}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    def test_director_sin_filtro(self):
        ctx = {"rol": "agente", "sub_rol": "director", "area_codigo": "TDA-042"}
        result = self.fn([("state", "=", "sale")], "sale.order", ctx)
        assert len(result) == 1  # solo el filtro original, sin área
        assert ("state", "=", "sale") in result

    def test_gerente_sin_filtro(self):
        ctx = {"rol": "agente", "sub_rol": "gerente", "area_codigo": "NORTE"}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    def test_rol_admin_sin_importar_sub_rol(self):
        """rol=admin siempre pasa sin filtro, aunque tenga area_codigo."""
        ctx = {"rol": "admin", "sub_rol": "vendedor", "area_codigo": "TDA-001"}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    # ── Sub-roles de tienda — filtra por warehouse ────────────────────────────

    def test_vendedor_sale_order_agrega_warehouse(self):
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        result = self.fn([], "sale.order", ctx)
        assert ("warehouse_id.code", "=", "TDA-042") in result

    def test_vendedor_sale_order_preserva_filtros_originales(self):
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        filtro_base = [("state", "in", ["sale", "done"])]
        result = self.fn(filtro_base, "sale.order", ctx)
        assert ("state", "in", ["sale", "done"]) in result
        assert ("warehouse_id.code", "=", "TDA-042") in result
        assert len(result) == 2

    def test_vendedor_sale_order_line_agrega_warehouse(self):
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        result = self.fn([], "sale.order.line", ctx)
        assert ("order_id.warehouse_id.code", "=", "TDA-042") in result

    def test_almacenero_stock_quant_agrega_warehouse(self):
        ctx = {"rol": "usuario", "sub_rol": "almacenero", "area_codigo": "ALM-01"}
        result = self.fn([], "stock.quant", ctx)
        assert ("location_id.warehouse_id.code", "=", "ALM-01") in result

    def test_almacenero_stock_move_agrega_warehouse(self):
        ctx = {"rol": "usuario", "sub_rol": "almacenero", "area_codigo": "ALM-01"}
        result = self.fn([], "stock.move", ctx)
        assert ("warehouse_id.code", "=", "ALM-01") in result

    def test_almacenero_stock_picking_agrega_warehouse(self):
        ctx = {"rol": "usuario", "sub_rol": "almacenero", "area_codigo": "ALM-01"}
        result = self.fn([], "stock.picking", ctx)
        assert ("picking_type_id.warehouse_id.code", "=", "ALM-01") in result

    def test_visor_pos_order_agrega_config(self):
        ctx = {"rol": "usuario", "sub_rol": "visor", "area_codigo": "TDA-003"}
        result = self.fn([], "pos.order", ctx)
        assert ("config_id.name", "=", "TDA-003") in result

    def test_visor_pos_order_line_agrega_config(self):
        ctx = {"rol": "usuario", "sub_rol": "visor", "area_codigo": "TDA-003"}
        result = self.fn([], "pos.order.line", ctx)
        assert ("order_id.config_id.name", "=", "TDA-003") in result

    # ── Sub-roles de área — filtra por equipo/área ────────────────────────────

    def test_jefe_area_sale_order_agrega_team(self):
        ctx = {"rol": "usuario", "sub_rol": "jefe_area", "area_codigo": "NORTE"}
        result = self.fn([], "sale.order", ctx)
        assert ("team_id.name", "ilike", "NORTE") in result

    def test_jefe_area_sale_order_line_agrega_team(self):
        ctx = {"rol": "usuario", "sub_rol": "jefe_area", "area_codigo": "NORTE"}
        result = self.fn([], "sale.order.line", ctx)
        assert ("order_id.team_id.name", "ilike", "NORTE") in result

    def test_contador_account_move_agrega_team(self):
        ctx = {"rol": "usuario", "sub_rol": "contador", "area_codigo": "NORTE"}
        result = self.fn([], "account.move", ctx)
        assert ("team_id.name", "ilike", "NORTE") in result

    def test_rrhh_stock_quant_agrega_ubicacion(self):
        ctx = {"rol": "usuario", "sub_rol": "rrhh", "area_codigo": "BODEGA-NORTE"}
        result = self.fn([], "stock.quant", ctx)
        assert ("location_id.complete_name", "ilike", "BODEGA-NORTE") in result

    # ── Modelos sin filtro configurado ────────────────────────────────────────

    def test_vendedor_purchase_order_sin_filtro(self):
        """Compras: modelo con campo_tienda=None → sin filtro de área."""
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        result = self.fn([("state", "=", "purchase")], "purchase.order", ctx)
        assert result == [("state", "=", "purchase")]  # sin filtro extra

    def test_jefe_area_hr_employee_sin_filtro(self):
        """RRHH modelo empleados: no filtra por área."""
        ctx = {"rol": "usuario", "sub_rol": "jefe_area", "area_codigo": "NORTE"}
        result = self.fn([], "hr.employee", ctx)
        assert result == []

    def test_modelo_no_mapeado_sin_filtro(self):
        """Modelo no en el mapa → sin filtro adicional."""
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        result = self.fn([], "crm.lead", ctx)
        assert result == []

    # ── Sin area_codigo — sin filtro ──────────────────────────────────────────

    def test_sin_area_codigo_no_filtra(self):
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": ""}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    def test_area_codigo_none_no_filtra(self):
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": None}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    def test_sin_sub_rol_no_filtra(self):
        ctx = {"rol": "usuario", "sub_rol": "", "area_codigo": "TDA-042"}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    def test_sub_rol_desconocido_no_filtra(self):
        """Sub-rol fuera del mapa → sin filtro (comportamiento seguro)."""
        ctx = {"rol": "usuario", "sub_rol": "misterioso", "area_codigo": "TDA-042"}
        result = self.fn([], "sale.order", ctx)
        assert result == []

    def test_contexto_vacio_no_filtra(self):
        result = self.fn([], "sale.order", {})
        assert result == []

    # ── Inmutabilidad del filtro original ─────────────────────────────────────

    def test_no_muta_filtro_original(self):
        """_aplicar_filtro_area no modifica la lista de entrada."""
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        filtro_original = [("state", "=", "sale")]
        _ = self.fn(filtro_original, "sale.order", ctx)
        assert filtro_original == [("state", "=", "sale")]


# =============================================================================
# 2. Tests del ContextVar en buscar() y buscar_leer()
# =============================================================================

class TestConectorOdooContextVar:
    """Tests del ContextVar _ctx_usuario_filtro en buscar() y buscar_leer()."""

    def test_buscar_sin_contexto_no_filtra(self):
        """Sin ContextVar activo, buscar() no agrega filtros de área."""
        from models.conector_odoo import ConectorOdoo, _ctx_usuario_filtro

        assert _ctx_usuario_filtro.get() == {}  # default vacío

        conector = ConectorOdoo.__new__(ConectorOdoo)
        conector.conectado = False
        conector.odoo = None
        conector.modelos_principales = {}
        conector._cache_resultados = {}
        conector._cache_ttl = 180
        conector.usuario = "test"
        conector.auditoria_queries = MagicMock()
        conector._cache_resultados = {}

        # buscar sin conexión retorna DataFrame vacío — no lanza excepción
        import pandas as pd
        result = conector.buscar("sale.order", filtro=[("state", "=", "sale")])
        assert isinstance(result, pd.DataFrame)

    def test_ctx_usuario_filtro_default_vacio(self):
        """El ContextVar comienza vacío (dict vacío) por defecto."""
        from models.conector_odoo import _ctx_usuario_filtro
        assert _ctx_usuario_filtro.get() == {}

    def test_ctx_usuario_filtro_set_y_reset(self):
        """ContextVar se puede establecer y restaurar correctamente."""
        from models.conector_odoo import _ctx_usuario_filtro

        ctx_test = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        token = _ctx_usuario_filtro.set(ctx_test)
        try:
            assert _ctx_usuario_filtro.get() == ctx_test
        finally:
            _ctx_usuario_filtro.reset(token)

        # Después del reset vuelve al default
        assert _ctx_usuario_filtro.get() == {}

    def test_ctx_usuario_filtro_aislado_por_thread(self):
        """ContextVar es aislado entre threads (thread-safe)."""
        import threading
        from models.conector_odoo import _ctx_usuario_filtro

        resultados = {}

        def hilo_a():
            token = _ctx_usuario_filtro.set(
                {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-A"}
            )
            import time
            time.sleep(0.05)
            resultados["a"] = _ctx_usuario_filtro.get().get("area_codigo")
            _ctx_usuario_filtro.reset(token)

        def hilo_b():
            token = _ctx_usuario_filtro.set(
                {"rol": "usuario", "sub_rol": "jefe_area", "area_codigo": "NORTE-B"}
            )
            resultados["b"] = _ctx_usuario_filtro.get().get("area_codigo")
            _ctx_usuario_filtro.reset(token)

        t_a = threading.Thread(target=hilo_a)
        t_b = threading.Thread(target=hilo_b)
        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()

        # Cada thread ve su propio valor
        assert resultados["a"] == "TDA-A"
        assert resultados["b"] == "NORTE-B"
        # El hilo principal no fue afectado
        assert _ctx_usuario_filtro.get() == {}

    def test_buscar_aplica_filtro_area_con_contexto(self):
        """buscar() llama _aplicar_filtro_area() cuando el ContextVar está activo."""
        from models.conector_odoo import ConectorOdoo, _ctx_usuario_filtro
        import pandas as pd

        # Configurar un conector mock que capture el filtro que recibe
        conector = ConectorOdoo.__new__(ConectorOdoo)
        conector.conectado = True
        conector.odoo = MagicMock()
        conector.modelos_principales = {}
        conector._cache_resultados = {}
        conector._cache_ttl = 180
        conector.usuario = "test"
        conector.auditoria_queries = MagicMock()

        filtros_usados = []

        def mock_search_read(filtro, campos, **kwargs):
            filtros_usados.append(list(filtro))
            return []

        conector.odoo.env = MagicMock()
        conector.odoo.env.__getitem__ = MagicMock(
            return_value=MagicMock(search_read=mock_search_read)
        )

        with patch.object(ConectorOdoo, "_verificar_conexion", return_value=True):
            with patch.object(ConectorOdoo, "_filtrar_campos_validos", return_value=["name"]):
                ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
                token = _ctx_usuario_filtro.set(ctx)
                try:
                    conector.buscar("sale.order", filtro=[("state", "=", "sale")])
                finally:
                    _ctx_usuario_filtro.reset(token)

        # Debe haber al menos una llamada con el filtro enriquecido
        assert len(filtros_usados) >= 1
        filtro_efectivo = filtros_usados[0]
        assert ("state", "=", "sale") in filtro_efectivo
        assert ("warehouse_id.code", "=", "TDA-042") in filtro_efectivo

    def test_buscar_leer_aplica_filtro_area_con_contexto(self):
        """buscar_leer() también aplica el filtro de área desde ContextVar."""
        from models.conector_odoo import ConectorOdoo, _ctx_usuario_filtro

        conector = ConectorOdoo.__new__(ConectorOdoo)
        conector.conectado = True
        conector.odoo = MagicMock()
        conector.modelos_principales = {}
        conector._cache_resultados = {}
        conector._cache_ttl = 180
        conector.usuario = "test"
        conector.auditoria_queries = MagicMock()

        filtros_usados = []

        def mock_search_read(filtro, campos, **kwargs):
            filtros_usados.append(list(filtro))
            return []

        conector.odoo.env = MagicMock()
        conector.odoo.env.__getitem__ = MagicMock(
            return_value=MagicMock(search_read=mock_search_read)
        )

        with patch.object(ConectorOdoo, "_verificar_conexion", return_value=True):
            with patch.object(ConectorOdoo, "_filtrar_campos_validos", return_value=["name"]):
                ctx = {"rol": "usuario", "sub_rol": "jefe_area", "area_codigo": "NORTE"}
                token = _ctx_usuario_filtro.set(ctx)
                try:
                    conector.buscar_leer("sale.order", filtro=[])
                finally:
                    _ctx_usuario_filtro.reset(token)

        assert len(filtros_usados) >= 1
        assert ("team_id.name", "ilike", "NORTE") in filtros_usados[0]


# =============================================================================
# 3. Tests de _resolver_area_desde_bd
# =============================================================================

class TestResolverAreaDesdeBd:
    """Tests del helper que resuelve (codigo, tipo) desde UUID de área."""

    def test_area_existente_retorna_codigo_y_tipo(self):
        from app.api.routers.chat import _resolver_area_desde_bd

        empresa_id = _crear_empresa()
        area_id = _crear_area(empresa_id, codigo="TDA-100", tipo="tienda")

        codigo, tipo = _resolver_area_desde_bd(area_id)
        assert codigo == "TDA-100"
        assert tipo == "tienda"

    def test_area_inexistente_retorna_none_none(self):
        from app.api.routers.chat import _resolver_area_desde_bd

        codigo, tipo = _resolver_area_desde_bd(str(uuid.uuid4()))
        assert codigo is None
        assert tipo is None

    def test_area_id_vacio_retorna_none_none(self):
        from app.api.routers.chat import _resolver_area_desde_bd

        codigo, tipo = _resolver_area_desde_bd("")
        assert codigo is None
        assert tipo is None

    def test_area_tipo_almacen(self):
        from app.api.routers.chat import _resolver_area_desde_bd

        empresa_id = _crear_empresa()
        area_id = _crear_area(empresa_id, codigo="ALM-05", tipo="almacen")

        codigo, tipo = _resolver_area_desde_bd(area_id)
        assert codigo == "ALM-05"
        assert tipo == "almacen"

    def test_area_tipo_oficina(self):
        from app.api.routers.chat import _resolver_area_desde_bd

        empresa_id = _crear_empresa()
        area_id = _crear_area(empresa_id, codigo="OFI-NORTE", tipo="oficina")

        codigo, tipo = _resolver_area_desde_bd(area_id)
        assert codigo == "OFI-NORTE"
        assert tipo == "oficina"


# =============================================================================
# 4. Tests de integración: endpoint POST /chat con filtrado por área
# =============================================================================

@pytest.fixture
def app_cliente():
    """Cliente HTTP de prueba con dependencias mockeadas."""
    from fastapi.testclient import TestClient
    from app.api.main_api import app
    from app.api.dependencies import get_bot, get_usuario_autenticado
    from app.api.routers.chat import _resolver_area_desde_bd

    _mock_bot = MagicMock()
    _mock_bot.procesar_mensaje.return_value = (
        [{"role": "assistant", "content": "Respuesta de prueba"}],
        "",
        "ventas",
    )

    return app, _mock_bot, get_bot, get_usuario_autenticado


class TestChatIntegracionFiltrado:
    """Tests de integración del endpoint /chat verificando que el filtro se establece."""

    def _make_client(self, sub_rol: str, area_id: str | None = None):
        from fastapi.testclient import TestClient
        from app.api.main_api import app
        from app.api.dependencies import get_bot, get_usuario_autenticado
        from models.conector_odoo import _ctx_usuario_filtro

        mock_bot = MagicMock()
        contexto_capturado = {}

        def bot_captura_contexto(mensaje, historial):
            # Capturar el contexto activo durante la ejecución del bot
            contexto_capturado.update(_ctx_usuario_filtro.get())
            return (
                [{"role": "assistant", "content": "OK"}],
                "",
                "ventas",
            )

        mock_bot.procesar_mensaje.side_effect = bot_captura_contexto

        jwt_payload = {
            "sub": str(uuid.uuid4()),
            "email": "test@empresa.com",
            "rol": "usuario",
            "sub_rol": sub_rol,
            "area_id": area_id,
            "empresa_id": str(uuid.uuid4()),
        }

        app.dependency_overrides[get_bot] = lambda: mock_bot
        app.dependency_overrides[get_usuario_autenticado] = lambda: jwt_payload

        client = TestClient(app)
        return client, contexto_capturado, app

    def test_chat_vendedor_establece_contexto_filtro(self):
        """Vendedor con area_id: el ContextVar tiene sub_rol y area_codigo durante ejecución."""
        empresa_id = _crear_empresa()
        area_id = _crear_area(empresa_id, codigo="TDA-042", tipo="tienda")

        client, ctx_capturado, app = self._make_client("vendedor", area_id)
        try:
            resp = client.post("/chat", json={"mensaje": "¿Cuánto vendí?"})
            assert resp.status_code == 200
            # El contexto fue establecido durante la ejecución del bot
            assert ctx_capturado.get("sub_rol") == "vendedor"
            assert ctx_capturado.get("area_codigo") == "TDA-042"
            assert ctx_capturado.get("area_tipo") == "tienda"
        finally:
            app.dependency_overrides.clear()

    def test_chat_jefe_area_establece_contexto_filtro(self):
        """Jefe de área: el ContextVar refleja sub_rol correcto."""
        empresa_id = _crear_empresa()
        area_id = _crear_area(empresa_id, codigo="NORTE", tipo="oficina")

        client, ctx_capturado, app = self._make_client("jefe_area", area_id)
        try:
            resp = client.post("/chat", json={"mensaje": "Reporte del área"})
            assert resp.status_code == 200
            assert ctx_capturado.get("sub_rol") == "jefe_area"
            assert ctx_capturado.get("area_codigo") == "NORTE"
        finally:
            app.dependency_overrides.clear()

    def test_chat_director_sin_area_id_contexto_sin_area(self):
        """Director sin area_id: el ContextVar no tiene area_codigo."""
        client, ctx_capturado, app = self._make_client("director", area_id=None)
        try:
            resp = client.post("/chat", json={"mensaje": "Reporte global"})
            assert resp.status_code == 200
            # Contexto se establece pero sin area_codigo (director = visión global)
            assert ctx_capturado.get("sub_rol") == "director"
            assert ctx_capturado.get("area_codigo") == ""
        finally:
            app.dependency_overrides.clear()

    def test_chat_sin_sub_rol_contexto_vacio_de_area(self):
        """Usuario sin sub_rol: el ContextVar no debe producir filtro de área."""
        client, ctx_capturado, app = self._make_client(None, area_id=None)
        try:
            resp = client.post("/chat", json={"mensaje": "Hola"})
            assert resp.status_code == 200
            assert ctx_capturado.get("area_codigo", "") == ""
        finally:
            app.dependency_overrides.clear()

    def test_chat_area_id_invalido_contexto_sin_codigo(self):
        """area_id que no existe en BD: _resolver_area retorna None, sin filtro."""
        area_id_falso = str(uuid.uuid4())
        client, ctx_capturado, app = self._make_client("vendedor", area_id_falso)
        try:
            resp = client.post("/chat", json={"mensaje": "¿Cuánto vendí?"})
            assert resp.status_code == 200
            # No pudo resolver el área → area_codigo vacío → sin filtro de área
            assert ctx_capturado.get("area_codigo") == ""
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# 5. Tests de la constante de sub-roles y mapas del módulo
# =============================================================================

class TestConstantesFiltrado:
    """Tests de los conjuntos de sub-roles y el mapa de modelos."""

    def test_sub_roles_sin_filtro_completos(self):
        from models.conector_odoo import _SUB_ROLES_SIN_FILTRO
        assert "admin_global" in _SUB_ROLES_SIN_FILTRO
        assert "director" in _SUB_ROLES_SIN_FILTRO
        assert "gerente" in _SUB_ROLES_SIN_FILTRO

    def test_sub_roles_filtro_tienda_completos(self):
        from models.conector_odoo import _SUB_ROLES_FILTRO_TIENDA
        assert "vendedor" in _SUB_ROLES_FILTRO_TIENDA
        assert "almacenero" in _SUB_ROLES_FILTRO_TIENDA
        assert "visor" in _SUB_ROLES_FILTRO_TIENDA

    def test_sub_roles_filtro_area_completos(self):
        from models.conector_odoo import _SUB_ROLES_FILTRO_AREA
        assert "jefe_area" in _SUB_ROLES_FILTRO_AREA
        assert "contador" in _SUB_ROLES_FILTRO_AREA
        assert "rrhh" in _SUB_ROLES_FILTRO_AREA

    def test_mapa_modelos_clave_venta(self):
        from models.conector_odoo import _FILTROS_ODOO_POR_MODELO
        assert "sale.order" in _FILTROS_ODOO_POR_MODELO
        campo_t, campo_a = _FILTROS_ODOO_POR_MODELO["sale.order"]
        assert campo_t is not None
        assert campo_a is not None

    def test_mapa_modelos_clave_stock(self):
        from models.conector_odoo import _FILTROS_ODOO_POR_MODELO
        assert "stock.quant" in _FILTROS_ODOO_POR_MODELO
        assert "stock.picking" in _FILTROS_ODOO_POR_MODELO

    def test_mapa_modelos_purchase_con_none(self):
        """Compras: ambos campos son None (no se filtra por área)."""
        from models.conector_odoo import _FILTROS_ODOO_POR_MODELO
        campo_t, campo_a = _FILTROS_ODOO_POR_MODELO["purchase.order"]
        assert campo_t is None
        assert campo_a is None

    def test_ctx_usuario_filtro_es_contextvar(self):
        from contextvars import ContextVar
        from models.conector_odoo import _ctx_usuario_filtro
        assert isinstance(_ctx_usuario_filtro, ContextVar)

    def test_ctx_usuario_filtro_default_es_dict_vacio(self):
        from models.conector_odoo import _ctx_usuario_filtro
        assert _ctx_usuario_filtro.get() == {}

    def test_aplicar_filtro_area_es_metodo_estatico(self):
        """_aplicar_filtro_area debe ser staticmethod (no necesita instancia)."""
        from models.conector_odoo import ConectorOdoo
        import inspect
        # Debe ser accesible directamente en la clase sin instanciar
        assert callable(ConectorOdoo._aplicar_filtro_area)
        sig = inspect.signature(ConectorOdoo._aplicar_filtro_area)
        params = list(sig.parameters.keys())
        # No tiene 'self' — es staticmethod
        assert "self" not in params
        assert "filtro" in params
        assert "modelo" in params
        assert "contexto" in params


# =============================================================================
# 6. Tests de compatibilidad con usuarios legacy (sin sub_rol/area_id)
# =============================================================================

class TestCompatibilidadLegacySprint3:
    """Asegura que usuarios sin sub_rol siguen funcionando sin filtros de área."""

    def test_usuario_sin_sub_rol_no_agrega_filtros(self):
        from models.conector_odoo import ConectorOdoo
        ctx = {"rol": "agente", "sub_rol": None, "area_codigo": None}
        result = ConectorOdoo._aplicar_filtro_area(
            [("state", "=", "sale")], "sale.order", ctx
        )
        assert result == [("state", "=", "sale")]

    def test_usuario_sin_area_codigo_no_agrega_filtros(self):
        from models.conector_odoo import ConectorOdoo
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": None}
        result = ConectorOdoo._aplicar_filtro_area([], "sale.order", ctx)
        assert result == []

    def test_filtro_none_se_convierte_a_lista(self):
        """Si filtro=None, el resultado debe ser una lista (nunca None)."""
        from models.conector_odoo import ConectorOdoo
        ctx = {"rol": "usuario", "sub_rol": "vendedor", "area_codigo": "TDA-042"}
        result = ConectorOdoo._aplicar_filtro_area(None, "sale.order", ctx)
        assert isinstance(result, list)
        assert ("warehouse_id.code", "=", "TDA-042") in result

    def test_filtro_vacio_con_contexto_vacio_retorna_lista_vacia(self):
        from models.conector_odoo import ConectorOdoo
        result = ConectorOdoo._aplicar_filtro_area([], "sale.order", {})
        assert result == []
