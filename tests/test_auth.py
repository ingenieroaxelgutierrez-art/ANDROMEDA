# ============================================================
# ANDROMEDA — tests.test_auth
# Tests Fase 5 — JWT Authentication
#
# Cobertura:
#   - app/api/auth/jwt_utils.py : crear/decodificar tokens, expiración, tipo
#   - models/db_saas.py         : Usuario.set_password, check_password
#   - app/api/routers/auth.py   : login, refresh, me, logout, crear_usuario
#   - CORS                      : cabeceras preflight
# ============================================================

import os
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest


# ── BD en memoria aislada por test ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _db_en_memoria(tmp_path):
    """SQLite temporal — cada test parte con BD limpia."""
    db_path = str(tmp_path / "test_auth.db")
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    os.environ.setdefault("SECRET_KEY", "andromeda-test-secret-12345")

    import models.db_saas as _mod
    _mod.resetear_db()
    _mod.inicializar_db()
    yield
    _mod.resetear_db()
    os.environ.pop("DB_URL", None)


# ── Helpers de creación de entidades ─────────────────────────────────────────

def _nueva_empresa() -> str:
    """Persiste Empresa en la BD de test y devuelve su id."""
    from models.db_saas import get_session, Empresa
    s = get_session()
    try:
        e = Empresa(
            id=str(uuid.uuid4()),
            nombre="Auth Corp",
            odoo_url="https://auth.odoo.com",
            odoo_db="auth_db",
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


def _nuevo_usuario(
    empresa_id: str,
    rol: str = "operador",
    password: str = "Password123!",
    activo: bool = True,
) -> tuple[str, str]:
    """Persiste Usuario con contraseña en la BD de test y retorna (id, email)."""
    from models.db_saas import get_session, Usuario
    s = get_session()
    try:
        u = Usuario(
            id=str(uuid.uuid4()),
            nombre="Auth Tester",
            email=f"auth_{uuid.uuid4().hex[:6]}@test.com",
            empresa_id=empresa_id,
            rol=rol,
            activo=activo,
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
    return _nueva_empresa()


@pytest.fixture()
def operador(empresa_id: str) -> tuple[str, str]:
    """Retorna (usuario_id, email) de un usuario con rol operador."""
    return _nuevo_usuario(empresa_id, rol="operador")


@pytest.fixture()
def admin(empresa_id: str) -> tuple[str, str]:
    """Retorna (usuario_id, email) de un usuario con rol admin."""
    return _nuevo_usuario(empresa_id, rol="admin")


@pytest.fixture()
def api_client():
    """TestClient del app FastAPI con bot mockeado."""
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


# ── Util: obtener tokens vía login ────────────────────────────────────────────

def _login(client, email: str, password: str = "Password123!") -> dict:
    """Hace POST /auth/login y retorna el JSON de respuesta."""
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r


# ============================================================
# 1. JWT Utils — Tests unitarios
# ============================================================

class TestJwtUtils:

    def test_access_token_decodifica_correctamente(self):
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        eid = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        token = crear_access_token(uid, "u@test.com", "admin", eid)
        payload = decodificar_access_token(token)
        assert payload is not None
        assert payload["sub"] == uid
        assert payload["email"] == "u@test.com"
        assert payload["rol"] == "admin"
        assert payload["empresa_id"] == eid
        assert payload["tipo"] == "access"

    def test_refresh_token_decodifica_correctamente(self):
        from app.api.auth.jwt_utils import crear_refresh_token, decodificar_refresh_token
        uid = str(uuid.uuid4())
        token = crear_refresh_token(uid)
        result = decodificar_refresh_token(token)
        assert result == uid

    def test_access_token_rechazado_como_refresh(self):
        from app.api.auth.jwt_utils import crear_access_token, decodificar_refresh_token
        token = crear_access_token("x", "x@x.com", "operador", "e1")
        assert decodificar_refresh_token(token) is None

    def test_refresh_token_rechazado_como_access(self):
        from app.api.auth.jwt_utils import crear_refresh_token, decodificar_access_token
        token = crear_refresh_token("uid123")
        assert decodificar_access_token(token) is None

    def test_token_invalido_retorna_none_access(self):
        from app.api.auth.jwt_utils import decodificar_access_token
        assert decodificar_access_token("not.a.real.token") is None

    def test_token_invalido_retorna_none_refresh(self):
        from app.api.auth.jwt_utils import decodificar_refresh_token
        assert decodificar_refresh_token("garbage") is None

    def test_access_token_expirado_retorna_none(self):
        from app.api.auth.jwt_utils import decodificar_access_token
        import app.api.auth.jwt_utils as ju
        # Parchear temporalmente duración a 0 minutos (token ya expirado)
        with patch.object(ju, "ACCESS_TOKEN_EXPIRE_MINUTES", -1):
            token = ju.crear_access_token("uid", "e@e.com", "viewer", "eid")
        assert decodificar_access_token(token) is None

    def test_refresh_token_expirado_retorna_none(self):
        from app.api.auth.jwt_utils import decodificar_refresh_token
        import app.api.auth.jwt_utils as ju
        with patch.object(ju, "REFRESH_TOKEN_EXPIRE_DAYS", -1):
            token = ju.crear_refresh_token("uid")
        assert decodificar_refresh_token(token) is None

    def test_token_firmado_con_clave_incorrecta_retorna_none(self):
        from jose import jwt as jose_jwt
        from app.api.auth.jwt_utils import decodificar_access_token, _ALGORITHM
        import datetime as dt
        payload = {
            "sub": "uid",
            "tipo": "access",
            "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15),
        }
        alien_token = jose_jwt.encode(payload, "wrong_secret", algorithm=_ALGORITHM)
        assert decodificar_access_token(alien_token) is None

    def test_access_token_contiene_exp(self):
        from app.api.auth.jwt_utils import crear_access_token, decodificar_access_token
        token = crear_access_token("u", "u@x.com", "admin", "e")
        payload = decodificar_access_token(token)
        assert "exp" in payload

    def test_refresh_token_solo_tiene_sub_tipo_exp(self):
        from app.api.auth.jwt_utils import crear_refresh_token
        from jose import jwt as jose_jwt
        from app.api.auth.jwt_utils import _SECRET_KEY, _ALGORITHM
        token = crear_refresh_token("uid123")
        raw = jose_jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        assert set(raw.keys()) == {"sub", "tipo", "exp"}


# ============================================================
# 2. Modelo Usuario — contraseña
# ============================================================

class TestPasswordModel:

    def test_set_password_guarda_hash_no_texto_plano(self, empresa_id):
        from models.db_saas import get_session, Usuario
        uid, email = _nuevo_usuario(empresa_id)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.password_hash is not None
            assert "Password123!" not in u.password_hash
        finally:
            s.close()

    def test_check_password_correcto_devuelve_true(self, empresa_id):
        from models.db_saas import get_session, Usuario
        uid, _ = _nuevo_usuario(empresa_id, password="MiPass99$")
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.check_password("MiPass99$") is True
        finally:
            s.close()

    def test_check_password_incorrecto_devuelve_false(self, empresa_id):
        from models.db_saas import get_session, Usuario
        uid, _ = _nuevo_usuario(empresa_id)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            assert u.check_password("ContraseñaWrong") is False
        finally:
            s.close()

    def test_check_password_sin_hash_devuelve_false(self, empresa_id):
        from models.db_saas import get_session, Usuario
        s = get_session()
        try:
            u = Usuario(
                id=str(uuid.uuid4()),
                nombre="NoPass",
                email=f"nopass_{uuid.uuid4().hex[:4]}@test.com",
                empresa_id=empresa_id,
                rol="viewer",
            )
            # No llamar set_password → password_hash = None
            s.add(u)
            s.commit()
            assert u.check_password("cualquier_cosa") is False
        finally:
            s.close()

    def test_hash_pbkdf2_formato(self, empresa_id):
        from models.db_saas import get_session, Usuario
        uid, _ = _nuevo_usuario(empresa_id)
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            # Hashes pbkdf2_sha256 empiezan con $pbkdf2-sha256$
            assert u.password_hash.startswith("$pbkdf2-sha256$")
        finally:
            s.close()


# ============================================================
# 3. POST /auth/login
# ============================================================

class TestLogin:

    def test_login_exitoso_200(self, api_client, empresa_id, operador):
        uid, email = operador
        r = _login(api_client, email)
        assert r.status_code == 200

    def test_login_retorna_tokens(self, api_client, empresa_id, operador):
        uid, email = operador
        r = _login(api_client, email)
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_access_token_es_jwt_valido(self, api_client, empresa_id, operador):
        uid, email = operador
        r = _login(api_client, email)
        token = r.json()["access_token"]
        from app.api.auth.jwt_utils import decodificar_access_token
        payload = decodificar_access_token(token)
        assert payload is not None
        assert payload["email"] == email
        assert payload["rol"] == "operador"

    def test_login_password_incorrecta_401(self, api_client, empresa_id, operador):
        uid, email = operador
        r = api_client.post("/auth/login", json={"email": email, "password": "wrong!"})
        assert r.status_code == 401

    def test_login_email_desconocido_401(self, api_client):
        r = api_client.post(
            "/auth/login",
            json={"email": "noexiste@unknown.com", "password": "Password123!"},
        )
        assert r.status_code == 401

    def test_login_error_generico_no_revela_si_existe(self, api_client, empresa_id, operador):
        """El mensaje de error debe ser idéntico para email desconocido y password incorrecta."""
        uid, email = operador
        r_bad_pass = api_client.post("/auth/login", json={"email": email, "password": "XXXX"})
        r_bad_email = api_client.post(
            "/auth/login", json={"email": "noexiste@x.com", "password": "Password123!"}
        )
        assert r_bad_pass.json()["detail"] == r_bad_email.json()["detail"]

    def test_login_usuario_inactivo_401(self, api_client, empresa_id):
        uid, email = _nuevo_usuario(empresa_id, activo=False)
        r = _login(api_client, email)
        assert r.status_code == 401

    def test_login_cuerpo_invalido_422(self, api_client):
        r = api_client.post("/auth/login", json={"email": "solo_email_sin_pass"})
        assert r.status_code == 422

    def test_login_sin_cuerpo_422(self, api_client):
        r = api_client.post("/auth/login")
        assert r.status_code == 422


# ============================================================
# 4. POST /auth/refresh
# ============================================================

class TestRefresh:

    def test_refresh_exitoso_200(self, api_client, empresa_id, operador):
        uid, email = operador
        tokens = _login(api_client, email).json()
        r = api_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert r.status_code == 200

    def test_refresh_emite_nuevo_access_token(self, api_client, empresa_id, operador):
        uid, email = operador
        tokens = _login(api_client, email).json()
        r = api_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        data = r.json()
        assert "access_token" in data
        # El nuevo token debe ser un JWT de acceso válido
        from app.api.auth.jwt_utils import decodificar_access_token
        payload = decodificar_access_token(data["access_token"])
        assert payload is not None
        assert payload["sub"] == uid
        assert payload["tipo"] == "access"

    def test_refresh_token_invalido_401(self, api_client):
        r = api_client.post("/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert r.status_code == 401

    def test_refresh_con_access_token_401(self, api_client, empresa_id, operador):
        """Un access_token no debe servir como refresh_token."""
        uid, email = operador
        tokens = _login(api_client, email).json()
        r = api_client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
        assert r.status_code == 401

    def test_refresh_usuario_inactivo_401(self, api_client, empresa_id):
        uid, email = _nuevo_usuario(empresa_id)
        tokens = _login(api_client, email).json()
        # Desactivar usuario después del login
        from models.db_saas import get_session, Usuario
        s = get_session()
        try:
            u = s.query(Usuario).filter(Usuario.id == uid).first()
            u.activo = False
            s.commit()
        finally:
            s.close()
        r = api_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert r.status_code == 401

    def test_refresh_sin_cuerpo_422(self, api_client):
        r = api_client.post("/auth/refresh")
        assert r.status_code == 422


# ============================================================
# 5. POST /auth/logout
# ============================================================

class TestLogout:

    def test_logout_204(self, api_client):
        r = api_client.post("/auth/logout")
        assert r.status_code == 204

    def test_logout_sin_token_204(self, api_client):
        """Logout es stateless — 204 aunque no se envíe token."""
        r = api_client.post("/auth/logout")
        assert r.status_code == 204

    def test_logout_no_retorna_cuerpo(self, api_client):
        r = api_client.post("/auth/logout")
        assert r.content == b""


# ============================================================
# 6. GET /auth/me
# ============================================================

class TestMe:

    def test_me_200(self, api_client, empresa_id, operador):
        uid, email = operador
        tokens = _login(api_client, email).json()
        r = api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.status_code == 200

    def test_me_retorna_perfil_correcto(self, api_client, empresa_id, operador):
        uid, email = operador
        tokens = _login(api_client, email).json()
        r = api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        data = r.json()
        assert data["email"] == email
        assert data["rol"] == "operador"
        assert data["empresa_id"] == empresa_id
        assert data["activo"] is True

    def test_me_sin_token_401(self, api_client):
        r = api_client.get("/auth/me")
        assert r.status_code == 401

    def test_me_token_invalido_401(self, api_client):
        r = api_client.get("/auth/me", headers={"Authorization": "Bearer garbage_token"})
        assert r.status_code == 401

    def test_me_con_refresh_token_401(self, api_client, empresa_id, operador):
        uid, email = operador
        tokens = _login(api_client, email).json()
        # El refresh token no debe servir para autenticarse en /me
        r = api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert r.status_code == 401

    def test_me_no_expone_password_hash(self, api_client, empresa_id, operador):
        uid, email = operador
        tokens = _login(api_client, email).json()
        r = api_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        data = r.json()
        assert "password_hash" not in data
        assert "password" not in data


# ============================================================
# 7. POST /auth/usuarios — crear usuario
# ============================================================

class TestCrearUsuario:

    def _token_admin(self, client, empresa_id: str) -> str:
        uid, email = _nuevo_usuario(empresa_id, rol="admin")
        return _login(client, email).json()["access_token"]

    def _token_operador(self, client, empresa_id: str) -> str:
        uid, email = _nuevo_usuario(empresa_id, rol="operador")
        return _login(client, email).json()["access_token"]

    def test_crear_usuario_admin_201(self, api_client, empresa_id):
        token = self._token_admin(api_client, empresa_id)
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "Nuevo Operador",
                "email": f"nuevo_{uuid.uuid4().hex[:6]}@corp.com",
                "password": "Seguro12345!",
                "empresa_id": empresa_id,
                "rol": "operador",
            },
        )
        assert r.status_code == 201

    def test_crear_usuario_retorna_perfil(self, api_client, empresa_id):
        token = self._token_admin(api_client, empresa_id)
        email = f"nuevo_{uuid.uuid4().hex[:6]}@corp.com"
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "El Nuevo",
                "email": email,
                "password": "Seguro12345!",
                "empresa_id": empresa_id,
                "rol": "viewer",
            },
        )
        data = r.json()
        assert data["email"] == email
        assert data["rol"] == "viewer"
        assert "password_hash" not in data

    def test_crear_usuario_operador_403(self, api_client, empresa_id):
        """Un operador no puede crear usuarios."""
        token = self._token_operador(api_client, empresa_id)
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "Alguien",
                "email": f"x_{uuid.uuid4().hex[:6]}@x.com",
                "password": "Seguro12345!",
                "empresa_id": empresa_id,
                "rol": "viewer",
            },
        )
        assert r.status_code == 403

    def test_crear_usuario_sin_token_401(self, api_client, empresa_id):
        r = api_client.post(
            "/auth/usuarios",
            json={
                "nombre": "Ghost",
                "email": "ghost@x.com",
                "password": "Seguro12345!",
                "empresa_id": empresa_id,
                "rol": "viewer",
            },
        )
        assert r.status_code == 401

    def test_crear_usuario_email_duplicado_409(self, api_client, empresa_id):
        token = self._token_admin(api_client, empresa_id)
        payload = {
            "nombre": "Dup",
            "email": f"dup_{uuid.uuid4().hex[:6]}@dup.com",
            "password": "Seguro12345!",
            "empresa_id": empresa_id,
            "rol": "operador",
        }
        api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        # Segunda vez con mismo email
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert r.status_code == 409

    def test_crear_usuario_empresa_inexistente_404(self, api_client, empresa_id):
        token = self._token_admin(api_client, empresa_id)
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "Huerfano",
                "email": f"huerfano_{uuid.uuid4().hex[:6]}@x.com",
                "password": "Seguro12345!",
                "empresa_id": str(uuid.uuid4()),  # ID que no existe
                "rol": "operador",
            },
        )
        assert r.status_code == 404

    def test_crear_usuario_rol_invalido_422(self, api_client, empresa_id):
        token = self._token_admin(api_client, empresa_id)
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "Bad",
                "email": "bad@x.com",
                "password": "Seguro12345!",
                "empresa_id": empresa_id,
                "rol": "superadmin",  # rol inválido
            },
        )
        assert r.status_code == 422

    def test_crear_usuario_password_corta_422(self, api_client, empresa_id):
        token = self._token_admin(api_client, empresa_id)
        r = api_client.post(
            "/auth/usuarios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nombre": "Short",
                "email": "short@x.com",
                "password": "1234567",  # menos de 8 caracteres
                "empresa_id": empresa_id,
                "rol": "viewer",
            },
        )
        assert r.status_code == 422


# ============================================================
# 8. CORS — preflight
# ============================================================

class TestCors:

    def test_cors_preflight_origen_frontend(self, api_client):
        r = api_client.options(
            "/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        # Starlette retorna 200 en OPTIONS con CORS configurado
        assert r.status_code in (200, 204)
        assert "access-control-allow-origin" in r.headers

    def test_cors_cabecera_en_respuesta_login(self, api_client, empresa_id, operador):
        uid, email = operador
        r = api_client.post(
            "/auth/login",
            json={"email": email, "password": "Password123!"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert "access-control-allow-origin" in r.headers
