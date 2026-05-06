# ============================================================
# ANDROMEDA — tests.test_sprint2
# Sprint 2 — Modelo de Datos: Áreas, Sub-roles y JWT ampliado
#
# Cobertura:
#   - models/db_saas.py : tabla Area, cols sub_rol/area_id en Usuario
#   - app/api/auth/jwt_utils.py : crear_access_token con sub_rol/area_id
#   - app/api/schemas.py : AreaCrear, AreaRespuesta, UsuarioCrearRequest
#   - app/api/routers/areas.py : CRUD /admin/areas
#   - app/api/routers/auth.py  : login/me devuelven sub_rol/area_id en JWT
#   - app/api/routers/admin.py : CRUD /admin/usuarios respeta sub_rol/area_id
# ============================================================

import os
import uuid
from datetime import datetime, timezone

import pytest


# ── BD en memoria aislada por test ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _db_en_memoria(tmp_path):
    """SQLite temporal — cada test parte con BD limpia."""
    db_path = str(tmp_path / "test_sprint2.db")
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    os.environ.setdefault("SECRET_KEY", "andromeda-test-secret-12345")

    import models.db_saas as _mod
    _mod.resetear_db()
    _mod.inicializar_db()
    yield
    _mod.resetear_db()
    os.environ.pop("DB_URL", None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _crear_empresa(nombre: str = "AreaCorp") -> str:
    from models.db_saas import get_session, Empresa
    s = get_session()
    try:
        e = Empresa(
            id=str(uuid.uuid4()),
            nombre=nombre,
            odoo_url="https://demo.odoo.com",
            odoo_db="demo_db",
            odoo_usuario="admin",
            odoo_clave_cifrada="placeholder",
            version_odoo=17,
            tipo_erp="odoo",
            activa=True,
        )
        s.add(e)
        s.commit()
        return e.id
    finally:
        s.close()


def _crear_area(empresa_id: str, nombre: str = "Tienda Central", codigo: str = "TDA-001") -> str:
    from models.db_saas import get_session, Area
    s = get_session()
    try:
        a = Area(
            id=str(uuid.uuid4()),
            empresa_id=empresa_id,
            nombre=nombre,
            codigo=codigo,
            tipo="tienda",
            activa=True,
            creado_en=datetime.now(timezone.utc),
        )
        s.add(a)
        s.commit()
        return a.id
    finally:
        s.close()


def _crear_usuario(
    empresa_id: str,
    rol: str = "agente",
    sub_rol: str | None = None,
    area_id: str | None = None,
    password: str = "Password123!",
) -> tuple[str, str]:
    from models.db_saas import get_session, Usuario
    s = get_session()
    try:
        u = Usuario(
            id=str(uuid.uuid4()),
            nombre="Sprint2 Tester",
            email=f"sprint2_{uuid.uuid4().hex[:6]}@test.com",
            empresa_id=empresa_id,
            rol=rol,
            sub_rol=sub_rol,
            area_id=area_id,
            activo=True,
            creado_en=datetime.now(timezone.utc),
        )
        u.set_password(password)
        s.add(u)
        s.commit()
        return u.id, u.email
    finally:
        s.close()


@pytest.fixture()
def empresa_id() -> str:
    return _crear_empresa()


@pytest.fixture()
def api_client():
    """TestClient con bot mockeado y sin override de auth (tests reales de login)."""
    from fastapi.testclient import TestClient
    from app.api.main_api import app
    from app.api.dependencies import get_bot
    from unittest.mock import MagicMock

    mock_bot = MagicMock()
    mock_bot.procesar_mensaje.return_value = (
        [{"role": "assistant", "content": "OK"}], "", "✓"
    )
    app.dependency_overrides[get_bot] = lambda: mock_bot
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(empresa_id):
    """TestClient con usuario admin pre-logueado. Devuelve (client, headers)."""
    from fastapi.testclient import TestClient
    from app.api.main_api import app
    from app.api.dependencies import get_bot
    from unittest.mock import MagicMock

    uid, email = _crear_usuario(empresa_id, rol="admin")
    mock_bot = MagicMock()
    mock_bot.procesar_mensaje.return_value = ([{"role": "assistant", "content": "OK"}], "", "✓")
    app.dependency_overrides[get_bot] = lambda: mock_bot

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.post("/auth/login", json={"email": email, "password": "Password123!"})
        token = r.json()["access_token"]
        yield c, {"Authorization": f"Bearer {token}"}
    app.dependency_overrides.clear()


# ============================================================
# 1. Modelo ORM — tabla Area
# ============================================================

class TestAreaModel:

    def test_crear_area_persiste_en_bd(self, empresa_id):
        from models.db_saas import get_session, Area
        aid = _crear_area(empresa_id, nombre="Almacén Norte", codigo="ALM-N")
        s = get_session()
        try:
            a = s.query(Area).filter(Area.id == aid).first()
            assert a is not None
            assert a.nombre == "Almacén Norte"
            assert a.codigo == "ALM-N"
            assert a.empresa_id == empresa_id
            assert a.activa is True
        finally:
            s.close()

    def test_to_dict_incluye_campos_sprint2(self, empresa_id):
        from models.db_saas import get_session, Area
        aid = _crear_area(empresa_id)
        s = get_session()
        try:
            a = s.query(Area).filter(Area.id == aid).first()
            d = a.to_dict()
            assert "id" in d
            assert "empresa_id" in d
            assert "nombre" in d
            assert "codigo" in d
            assert "tipo" in d
            assert "activa" in d
        finally:
            s.close()

    def test_unica_area_por_empresa_codigo(self, empresa_id):
        from models.db_saas import get_session, Area
        from sqlalchemy.exc import IntegrityError
        _crear_area(empresa_id, nombre="A1", codigo="DUP-001")
        # Intentar crear otra con mismo codigo en misma empresa → IntegrityError
        s = get_session()
        try:
            a2 = Area(
                id=str(uuid.uuid4()),
                empresa_id=empresa_id,
                nombre="A2",
                codigo="DUP-001",
                tipo="tienda",
                activa=True,
                creado_en=datetime.now(timezone.utc),
            )
            s.add(a2)
            with pytest.raises(IntegrityError):
                s.commit()
        finally:
            s.rollback()
            s.close()

    def test_area_soft_delete(self, empresa_id):
        from models.db_saas import get_session, Area
        aid = _crear_area(empresa_id)
        s = get_session()
        try:
            a = s.query(Area).filter(Area.id == aid).first()
            a.activa = False
            s.commit()
            s.refresh(a)
            assert a.activa is False
        finally:
            s.close()


# ============================================================
# 2. Modelo ORM — Usuario con sub_rol y area_id
# ============================================================

class TestUsuarioConSubRol:

    def test_usuario_con_sub_rol_persiste(self, empresa_id):
        from models.db_saas import get_session, Usuario
        uid, _ = _crear_usuario(empresa_id, sub_rol="gerente")
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.sub_rol == "gerente"
            assert u.area_id is None
        finally:
            s.close()

    def test_usuario_con_area_persiste(self, empresa_id):
        from models.db_saas import get_session, Usuario
        aid = _crear_area(empresa_id)
        uid, _ = _crear_usuario(empresa_id, area_id=aid)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.area_id == aid
        finally:
            s.close()

    def test_usuario_to_dict_incluye_sub_rol_y_area_id(self, empresa_id):
        from models.db_saas import get_session, Usuario
        aid = _crear_area(empresa_id)
        uid, _ = _crear_usuario(empresa_id, sub_rol="director", area_id=aid)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            d = u.to_dict()
            assert d["sub_rol"] == "director"
            assert d["area_id"] == aid
        finally:
            s.close()

    def test_usuario_sin_sub_rol_es_none(self, empresa_id):
        from models.db_saas import get_session, Usuario
        uid, _ = _crear_usuario(empresa_id)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.sub_rol is None
        finally:
            s.close()

    def test_relacion_usuario_area(self, empresa_id):
        from models.db_saas import get_session, Usuario, Area
        aid = _crear_area(empresa_id, nombre="Caja Central", codigo="CAJA-1")
        uid, _ = _crear_usuario(empresa_id, area_id=aid)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.area is not None
            assert u.area.nombre == "Caja Central"
        finally:
            s.close()


# ============================================================
# 3. JWT ampliado con sub_rol y area_id
# ============================================================

class TestJwtConSubRol:

    def test_access_token_incluye_sub_rol_y_area_id(self):
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        uid = str(uuid.uuid4())
        eid = str(uuid.uuid4())
        aid = str(uuid.uuid4())
        token = crear_access_token(uid, "u@test.com", "agente", eid, sub_rol="gerente", area_id=aid)
        payload = decodificar_access_token(token)
        assert payload is not None
        assert payload["sub_rol"] == "gerente"
        assert payload["area_id"] == aid

    def test_access_token_sin_sub_rol_no_incluye_claim(self):
        """Cuando sub_rol=None NO debe agregarse el claim (JWT limpio)."""
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        token = crear_access_token("uid", "u@x.com", "agente", "eid")
        payload = decodificar_access_token(token)
        assert payload is not None
        # El claim no debe estar presente cuando es None
        assert "sub_rol" not in payload
        assert "area_id" not in payload

    def test_refresh_token_no_incluye_sub_rol(self):
        """El refresh_token nunca debe incluir sub_rol (mínimo de claims)."""
        from app.api.auth.jwt_utils import crear_refresh_token
        from jose import jwt as jose_jwt
        from app.api.auth.jwt_utils import _SECRET_KEY, _ALGORITHM
        token = crear_refresh_token("uid123")
        raw = jose_jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        assert "sub_rol" not in raw
        assert "area_id" not in raw

    def test_access_token_con_solo_sub_rol(self):
        """Puede tener sub_rol sin area_id."""
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        token = crear_access_token("uid", "u@x.com", "agente", "eid", sub_rol="vendedor")
        payload = decodificar_access_token(token)
        assert payload["sub_rol"] == "vendedor"
        assert "area_id" not in payload

    def test_access_token_con_solo_area_id(self):
        """Puede tener area_id sin sub_rol."""
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        aid = str(uuid.uuid4())
        token = crear_access_token("uid", "u@x.com", "agente", "eid", area_id=aid)
        payload = decodificar_access_token(token)
        assert payload["area_id"] == aid
        assert "sub_rol" not in payload


# ============================================================
# 4. Endpoint /auth/login — JWT incluye sub_rol/area_id
# ============================================================

class TestLoginConSubRol:

    def test_login_sin_sub_rol_devuelve_token_valido(self, api_client, empresa_id):
        _, email = _crear_usuario(empresa_id)
        r = api_client.post("/auth/login", json={"email": email, "password": "Password123!"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data

    def test_login_con_sub_rol_encode_en_jwt(self, api_client, empresa_id):
        from app.api.auth.jwt_utils import decodificar_access_token
        aid = _crear_area(empresa_id)
        _, email = _crear_usuario(empresa_id, sub_rol="gerente", area_id=aid)
        r = api_client.post("/auth/login", json={"email": email, "password": "Password123!"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        payload = decodificar_access_token(token)
        assert payload is not None
        assert payload.get("sub_rol") == "gerente"
        assert payload.get("area_id") == aid

    def test_login_usuario_sin_area_no_incluye_area_id_en_jwt(self, api_client, empresa_id):
        from app.api.auth.jwt_utils import decodificar_access_token
        _, email = _crear_usuario(empresa_id, sub_rol="vendedor")  # sin area_id
        r = api_client.post("/auth/login", json={"email": email, "password": "Password123!"})
        token = r.json()["access_token"]
        payload = decodificar_access_token(token)
        assert payload.get("sub_rol") == "vendedor"
        assert "area_id" not in payload


# ============================================================
# 5. Endpoint GET /auth/me — devuelve sub_rol y area_id
# ============================================================

class TestMeConSubRol:

    def test_me_devuelve_sub_rol_y_area_id(self, api_client, empresa_id):
        aid = _crear_area(empresa_id)
        _, email = _crear_usuario(empresa_id, sub_rol="gerente", area_id=aid)
        r_login = api_client.post("/auth/login", json={"email": email, "password": "Password123!"})
        token = r_login.json()["access_token"]

        r = api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["sub_rol"] == "gerente"
        assert data["area_id"] == aid

    def test_me_sin_sub_rol_devuelve_null(self, api_client, empresa_id):
        _, email = _crear_usuario(empresa_id)
        r_login = api_client.post("/auth/login", json={"email": email, "password": "Password123!"})
        token = r_login.json()["access_token"]

        r = api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["sub_rol"] is None
        assert data["area_id"] is None


# ============================================================
# 6. Endpoint POST /auth/usuarios — crear con sub_rol/area_id
# ============================================================

class TestCrearUsuarioConSubRol:

    def test_crear_usuario_con_sub_rol(self, admin_client, empresa_id):
        client, headers = admin_client
        payload = {
            "nombre": "Gerente Test",
            "email": f"gerente_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Password123!",
            "empresa_id": empresa_id,
            "rol": "agente",
            "sub_rol": "gerente",
        }
        r = client.post("/auth/usuarios", json=payload, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["sub_rol"] == "gerente"
        assert data["area_id"] is None

    def test_crear_usuario_con_area(self, admin_client, empresa_id):
        client, headers = admin_client
        aid = _crear_area(empresa_id, nombre="Tienda Sur", codigo="TDA-S")
        payload = {
            "nombre": "Vendedor Sur",
            "email": f"vs_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Password123!",
            "empresa_id": empresa_id,
            "rol": "agente",
            "sub_rol": "vendedor",
            "area_id": aid,
        }
        r = client.post("/auth/usuarios", json=payload, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["sub_rol"] == "vendedor"
        assert data["area_id"] == aid

    def test_crear_usuario_sub_rol_invalido_retorna_422(self, admin_client, empresa_id):
        client, headers = admin_client
        payload = {
            "nombre": "Invalid SubRol",
            "email": f"invalid_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Password123!",
            "empresa_id": empresa_id,
            "rol": "agente",
            "sub_rol": "INVALIDO_ABSOLUTO",
        }
        r = client.post("/auth/usuarios", json=payload, headers=headers)
        assert r.status_code == 422


# ============================================================
# 7. CRUD /admin/areas — Endpoints REST
# ============================================================

class TestAreaEndpoints:

    def test_crear_area_endpoint(self, admin_client, empresa_id):
        client, headers = admin_client
        payload = {
            "nombre": "Almacén CDMX",
            "empresa_id": empresa_id,
            "codigo": "ALM-CDMX",
            "tipo": "almacen",
            "activa": True,
        }
        r = client.post("/admin/areas", json=payload, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["nombre"] == "Almacén CDMX"
        assert data["codigo"] == "ALM-CDMX"
        assert data["tipo"] == "almacen"
        assert data["activa"] is True

    def test_listar_areas_sin_filtro(self, admin_client, empresa_id):
        client, headers = admin_client
        _crear_area(empresa_id, nombre="A1", codigo="C1")
        _crear_area(empresa_id, nombre="A2", codigo="C2")
        r = client.get("/admin/areas", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_listar_areas_filtrado_por_empresa(self, admin_client, empresa_id):
        client, headers = admin_client
        otra_empresa = _crear_empresa("OtraEmpresa")
        _crear_area(empresa_id, nombre="MiArea", codigo="MI-1")
        _crear_area(otra_empresa, nombre="OtraArea", codigo="OT-1")
        r = client.get(f"/admin/areas?empresa_id={empresa_id}", headers=headers)
        assert r.status_code == 200
        ids_empresa = [a["empresa_id"] for a in r.json()]
        assert all(e == empresa_id for e in ids_empresa)

    def test_obtener_area_por_id(self, admin_client, empresa_id):
        client, headers = admin_client
        aid = _crear_area(empresa_id, nombre="Zona Norte", codigo="ZN-1")
        r = client.get(f"/admin/areas/{aid}", headers=headers)
        assert r.status_code == 200
        assert r.json()["nombre"] == "Zona Norte"

    def test_obtener_area_inexistente_404(self, admin_client):
        client, headers = admin_client
        r = client.get(f"/admin/areas/{uuid.uuid4()}", headers=headers)
        assert r.status_code == 404

    def test_desactivar_area_soft_delete(self, admin_client, empresa_id):
        client, headers = admin_client
        aid = _crear_area(empresa_id, nombre="Zona Sur", codigo="ZS-1")
        r = client.delete(f"/admin/areas/{aid}", headers=headers)
        assert r.status_code == 204
        # Verificar en BD que quedó inactiva
        from models.db_saas import get_session, Area
        s = get_session()
        try:
            a = s.query(Area).filter(Area.id == aid).first()
            assert a.activa is False
        finally:
            s.close()

    def test_duplicar_codigo_area_misma_empresa_409(self, admin_client, empresa_id):
        client, headers = admin_client
        payload = {
            "nombre": "Area 1",
            "empresa_id": empresa_id,
            "codigo": "DUP-99",
            "tipo": "tienda",
            "activa": True,
        }
        r1 = client.post("/admin/areas", json=payload, headers=headers)
        assert r1.status_code == 201
        payload["nombre"] = "Area Duplicada"
        r2 = client.post("/admin/areas", json=payload, headers=headers)
        assert r2.status_code == 409

    def test_area_tipo_invalido_retorna_422(self, admin_client, empresa_id):
        client, headers = admin_client
        r = client.post("/admin/areas", json={
            "nombre": "Mala",
            "empresa_id": empresa_id,
            "tipo": "INVALIDO",
            "activa": True,
        }, headers=headers)
        assert r.status_code == 422

    def test_area_empresa_inexistente_404(self, admin_client):
        client, headers = admin_client
        r = client.post("/admin/areas", json={
            "nombre": "HuerfanaArea",
            "empresa_id": str(uuid.uuid4()),
            "tipo": "tienda",
            "activa": True,
        }, headers=headers)
        assert r.status_code == 404

    def test_area_sin_autenticar_retorna_401(self, api_client, empresa_id):
        r = api_client.get("/admin/areas")
        assert r.status_code == 401

    def test_area_rol_no_admin_retorna_403(self, api_client, empresa_id):
        _, email = _crear_usuario(empresa_id, rol="agente")
        r_login = api_client.post("/auth/login", json={"email": email, "password": "Password123!"})
        token = r_login.json()["access_token"]
        r = api_client.get("/admin/areas", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403


# ============================================================
# 8. CRUD /admin/usuarios — sub_rol y area_id en respuestas
# ============================================================

class TestAdminUsuariosSubRol:

    def test_crear_usuario_admin_con_sub_rol(self, admin_client, empresa_id):
        client, headers = admin_client
        aid = _crear_area(empresa_id, nombre="Planta Yucatan", codigo="PLY-1")
        payload = {
            "nombre": "Jefe Yucatan",
            "email": f"jy_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Password123!",
            "empresa_id": empresa_id,
            "rol": "agente",
            "sub_rol": "jefe_area",
            "area_id": aid,
        }
        r = client.post("/admin/usuarios", json=payload, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["sub_rol"] == "jefe_area"
        assert data["area_id"] == aid

    def test_actualizar_usuario_admin_sub_rol(self, admin_client, empresa_id):
        client, headers = admin_client
        uid, email = _crear_usuario(empresa_id, sub_rol=None)
        r = client.put(
            f"/admin/usuarios/{uid}",
            json={"sub_rol": "vendedor"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["sub_rol"] == "vendedor"

    def test_listar_usuarios_incluye_sub_rol(self, admin_client, empresa_id):
        client, headers = admin_client
        _crear_usuario(empresa_id, sub_rol="contador")
        r = client.get("/admin/usuarios", headers=headers)
        assert r.status_code == 200
        # Al menos uno de los usuarios tiene sub_rol
        sub_roles = [u.get("sub_rol") for u in r.json()]
        assert "contador" in sub_roles


# ============================================================
# 9. Compatibilidad — campos opcionales no rompen usuarios legacy
# ============================================================

class TestCompatibilidadLegacy:

    def test_usuario_legacy_sin_sub_rol_funciona(self, empresa_id):
        """Usuarios previos al Sprint 2 (sin sub_rol) siguen funcionando."""
        from models.db_saas import get_session, Usuario
        uid, _ = _crear_usuario(empresa_id)  # sub_rol=None por defecto
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.sub_rol is None
            assert u.area_id is None
            d = u.to_dict()
            assert d["sub_rol"] is None
            assert d["area_id"] is None
        finally:
            s.close()

    def test_schema_usuario_crear_sin_sub_rol_valido(self):
        """UsuarioCrearRequest sin sub_rol es válido."""
        from app.api.schemas import UsuarioCrearRequest
        req = UsuarioCrearRequest(
            nombre="Legacy",
            email="legacy@test.com",
            password="Password123!",
            empresa_id=str(uuid.uuid4()),
            rol="agente",
        )
        assert req.sub_rol is None
        assert req.area_id is None

    def test_jwt_legacy_sin_sub_rol_decodifica_correctamente(self):
        """access_token sin sub_rol/area_id sigue siendo válido."""
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        token = crear_access_token("uid", "u@x.com", "agente", "eid")
        payload = decodificar_access_token(token)
        assert payload is not None
        assert payload["sub"] == "uid"
        assert "sub_rol" not in payload
        assert "area_id" not in payload


# ============================================================
# 10. SUB_ROLES_VALIDOS — constante de modelo
# ============================================================

class TestSubRolesValidos:

    def test_sub_roles_validos_no_vacio(self):
        from models.db_saas import SUB_ROLES_VALIDOS
        assert len(SUB_ROLES_VALIDOS) > 0

    def test_sub_roles_validos_incluye_roles_clave(self):
        from models.db_saas import SUB_ROLES_VALIDOS
        expected = {"director", "gerente", "jefe_area", "vendedor", "almacenero", "contador"}
        assert expected.issubset(SUB_ROLES_VALIDOS)

    def test_schema_valida_contra_sub_roles_validos(self):
        from app.api.schemas import UsuarioCrearRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UsuarioCrearRequest(
                nombre="Test",
                email="t@t.com",
                password="Password123!",
                empresa_id=str(uuid.uuid4()),
                sub_rol="administrador_fantasma",  # inválido
            )
