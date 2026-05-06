# ============================================================
# ANDROMEDA — models.db_saas
# Modelos de Base de Datos SaaS (Fase 4)
#
# Tablas:
#   Empresa         — Organización cliente + credenciales Odoo/ERP cifradas
#   Usuario         — Usuario del sistema (pertenece a Empresa)
#   SesionLog       — Registro de actividad por usuario/empresa/session
#   SesionContexto  — Historial de conversación por session_id (multi-usuario)
#
# Motor por defecto: SQLite (data/andromeda_saas.db)
# Motor en producción: configurar DB_URL=postgresql://... en .env
# ============================================================

import os
import uuid
import json
import base64
import hashlib
import logging
import threading
from typing import Optional, Dict, Any

from cryptography.fernet import Fernet
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("andromeda.db_saas")

Base = declarative_base()

# ── Cifrado de Credenciales ──────────────────────────────────────────────────

def _obtener_clave_cifrado() -> bytes:
    """
    Deriva una clave Fernet válida a partir de SECRET_KEY en .env.

    Se usa SHA-256 sobre el valor de SECRET_KEY para producir siempre
    32 bytes válidos, independientemente de la longitud o formato del
    valor configurado. Esto hace la clave robusta frente a cualquier
    string arbitrario en .env sin requerir una clave pre-generada en
    formato Fernet exacto.

    En producción: SECRET_KEY debe ser una cadena aleatoria larga y privada.
    """
    clave_raw = os.getenv("SECRET_KEY", "andromeda-default-key-change-in-production")
    digest = hashlib.sha256(clave_raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def cifrar_credencial(texto: str) -> str:
    """Cifra texto con Fernet. Retorna string base64 (seguro para almacenar en BD)."""
    f = Fernet(_obtener_clave_cifrado())
    return f.encrypt(texto.encode("utf-8")).decode("utf-8")


def descifrar_credencial(cifrado: str) -> str:
    """Descifra un token Fernet. Retorna texto plano."""
    f = Fernet(_obtener_clave_cifrado())
    return f.decrypt(cifrado.encode("utf-8")).decode("utf-8")


# ── Constantes de sub-roles ───────────────────────────────────────────────────

# Sub-roles disponibles por tipo de rol principal.
# admin    → sin restricción de área (siempre visibilidad global)
# agente   → sub-roles operativos con acceso potencialmente filtrado por área
# usuario  → solo puede ver manuales (sin acceso a datos)

SUB_ROLES_VALIDOS = frozenset({
    # admin — sin restricción de área (visión global)
    "admin",
    # agentes operativos con visión global
    "director",
    "gerente",
    # agentes con filtrado por área/equipo
    "jefe",
    "coordinador",
    # agentes con filtrado por tienda/almacén
    "auxiliar",
    "tienda",
})

# ── Modelos ORM ──────────────────────────────────────────────────────────────

class Area(Base):
    """
    Área funcional dentro de una empresa (e.g. Tienda Cancún, RRHH Central).

    Permite filtrar los datos Odoo que un agente puede consultar.
    Un Usuario con area_id solo verá datos de su área cuando el ejecutor
    lo soporte (Sprint 3). Sin area_id → visibilidad global.
    """
    __tablename__ = "areas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String(36), ForeignKey("empresas.id"), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(100), nullable=True)        # e.g. "TDA-042", "WHouse-CDMX"
    tipo = Column(String(50), nullable=False, default="tienda")  # tienda | almacen | oficina | planta
    activa = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=True)

    empresa = relationship("Empresa", back_populates="areas")
    usuarios = relationship("Usuario", back_populates="area")

    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_area_codigo_por_empresa"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "nombre": self.nombre,
            "codigo": self.codigo,
            "tipo": self.tipo,
            "activa": self.activa,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }


class Empresa(Base):
    """
    Organización cliente. Cada empresa tiene su propia instancia ERP
    (Odoo u otro) con credenciales almacenadas cifradas.
    """
    __tablename__ = "empresas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(255), nullable=False)

    # Conexión ERP
    odoo_url = Column(String(512), nullable=False)
    odoo_db = Column(String(255), nullable=False)
    odoo_usuario = Column(String(255), nullable=False)
    odoo_clave_cifrada = Column(Text, nullable=False)   # Nunca en texto plano
    version_odoo = Column(Integer, nullable=False, default=17)
    tipo_erp = Column(String(50), nullable=False, default="odoo")  # odoo | sap | netsuite | holded

    activa = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=True)
    actualizado_en = Column(DateTime, nullable=True)

    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    sesiones_log = relationship("SesionLog", back_populates="empresa", cascade="all, delete-orphan")
    areas = relationship("Area", back_populates="empresa", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Cifra y persiste la contraseña del ERP."""
        self.odoo_clave_cifrada = cifrar_credencial(password)

    def get_password(self) -> str:
        """Descifra y retorna la contraseña del ERP en texto plano."""
        return descifrar_credencial(self.odoo_clave_cifrada)

    def to_dict(self, include_credentials: bool = False) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "nombre": self.nombre,
            "odoo_url": self.odoo_url,
            "odoo_db": self.odoo_db,
            "odoo_usuario": self.odoo_usuario,
            "version_odoo": self.version_odoo,
            "tipo_erp": self.tipo_erp,
            "activa": self.activa,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
            "actualizado_en": self.actualizado_en.isoformat() if self.actualizado_en else None,
        }
        if include_credentials:
            d["odoo_password"] = self.get_password()
        return d


class Usuario(Base):
    """
    Usuario del sistema ANDROMEDA.
    Pertenece a exactamente una Empresa.
    Roles: admin → agente → usuario (en orden de privilegio descendente).
    Sub-roles (Sprint 2): refinan el perfil dentro de cada rol principal.
    area_id (Sprint 2): filtra datos a un área específica (Sprint 3 aplica el filtro).
    """
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    empresa_id = Column(String(36), ForeignKey("empresas.id"), nullable=False)
    rol = Column(
        SAEnum("admin", "agente", "usuario", name="rol_usuario"),
        nullable=False,
        default="agente",
    )
    # Sprint 2 — sub-rol y área
    sub_rol = Column(String(50), nullable=True)         # e.g. "director", "gerente", "vendedor"
    area_id = Column(String(36), ForeignKey("areas.id"), nullable=True, index=True)

    activo = Column(Boolean, nullable=False, default=True)
    password_hash = Column(String(255), nullable=True)  # pbkdf2_sha256; nullable para migraciones
    creado_en = Column(DateTime, nullable=True)

    empresa = relationship("Empresa", back_populates="usuarios")
    area = relationship("Area", back_populates="usuarios")
    sesiones_log = relationship("SesionLog", back_populates="usuario", cascade="all, delete-orphan")

    def set_password(self, password_plain: str) -> None:
        """Hashea y almacena la contraseña.

        Usa pbkdf2_sha256 (OWASP; mismo esquema por defecto de Django).
        Puro Python — sin dependencia de librería C bcrypt.
        """
        from passlib.context import CryptContext
        _pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self.password_hash = _pwd_ctx.hash(password_plain)

    def check_password(self, password_plain: str) -> bool:
        """Verifica una contraseña en texto plano contra el hash almacenado."""
        if not self.password_hash:
            return False
        from passlib.context import CryptContext
        _pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        return _pwd_ctx.verify(password_plain, self.password_hash)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "empresa_id": self.empresa_id,
            "rol": self.rol,
            "sub_rol": self.sub_rol,
            "area_id": self.area_id,
            "activo": self.activo,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }


class SesionLog(Base):
    """
    Registro de actividad por empresa/usuario.
    Fuente de verdad para las métricas SaaS.
    Rotación automática: registros > ROTACION_DIAS días se purgan.
    """
    __tablename__ = "sesiones_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(String(36), ForeignKey("empresas.id"), nullable=True, index=True)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True)
    session_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=True, index=True)
    accion = Column(String(255), nullable=False)
    tipo_consulta = Column(String(100), nullable=True)
    resultado = Column(String(50), nullable=False, default="ok")  # ok | error | rate_limit
    duracion_ms = Column(Integer, nullable=True)
    error_msg = Column(Text, nullable=True)

    empresa = relationship("Empresa", back_populates="sesiones_log")
    usuario = relationship("Usuario", back_populates="sesiones_log")


class SesionContexto(Base):
    """
    Historial de conversación almacenado server-side por session_id.

    Permite que los clientes omitan el historial en requests sucesivos:
    el servidor lo recupera automáticamente. Esencial para el soporte
    multi-usuario real donde cada dispositivo/usuario mantiene su contexto
    de forma independiente en la BD.
    """
    __tablename__ = "sesiones_contexto"

    session_id = Column(String(36), primary_key=True)
    empresa_id = Column(String(36), nullable=True, index=True)
    historial_json = Column(Text, nullable=False, default="[]")
    mensajes_total = Column(Integer, nullable=False, default=0)
    ultima_actividad = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=True)

    def get_historial(self) -> list:
        try:
            return json.loads(self.historial_json)
        except Exception:
            return []

    def set_historial(self, historial: list) -> None:
        self.historial_json = json.dumps(historial, ensure_ascii=False)
        self.mensajes_total = len(historial)


# ── Motor y Fábrica de Sesiones ───────────────────────────────────────────────

_engine = None
_SessionFactory = None
_init_lock = threading.Lock()


def _obtener_db_url() -> str:
    """
    Resuelve la URL de base de datos.
    Prioridad: DB_URL en .env → SQLite local en data/.
    Usa forward slashes en el path para compatibilidad cross-platform con SQLAlchemy.
    """
    url = os.getenv("DB_URL", "")
    if not url:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
        )
        os.makedirs(data_dir, exist_ok=True)
        db_file = os.path.join(data_dir, "andromeda_saas.db").replace("\\", "/")
        url = f"sqlite:///{db_file}"
    return url


def inicializar_db() -> None:
    """
    Crea las tablas si no existen y prepara la fábrica de sesiones.
    Thread-safe. Idempotente: llamar múltiples veces es seguro.
    Debe invocarse al arrancar la aplicación (evento startup de FastAPI).

    Robusto ante fallos transitorios (DB bloqueada durante reload de uvicorn):
    el engine global solo se asigna DESPUÉS de que create_all() tenga éxito.
    Si falla, _engine queda None y el siguiente llamador lo reintentará.
    """
    global _engine, _SessionFactory
    if _engine is None:
        with _init_lock:
            if _engine is None:
                db_url = _obtener_db_url()
                is_sqlite = "sqlite" in db_url
                connect_args = {"check_same_thread": False} if is_sqlite else {}
                # Crear engine local primero; solo promover a global si todo va bien
                _eng_tmp = create_engine(
                    db_url,
                    connect_args=connect_args,
                    pool_pre_ping=True,
                    echo=False,
                )
                _sf_tmp = sessionmaker(
                    bind=_eng_tmp, autoflush=False, autocommit=False
                )
                Base.metadata.create_all(_eng_tmp)
                if is_sqlite:
                    # WAL mode: mejor concurrencia con múltiples procesos/workers
                    from sqlalchemy import text as _text
                    with _eng_tmp.connect() as _conn:
                        _conn.execute(_text("PRAGMA journal_mode=WAL"))
                        _conn.execute(_text("PRAGMA synchronous=NORMAL"))
                        # ── Migraciones incrementales (Sprint 2) ──────────────
                        # ALTER TABLE no falla si la columna ya existe: primero
                        # inspeccionamos las columnas presentes y solo añadimos
                        # las que falten.  SQLite no soporta IF NOT EXISTS en
                        # ALTER TABLE, así que lo hacemos manualmente.
                        _cols_result = _conn.execute(_text("PRAGMA table_info(usuarios)"))
                        _col_names = {row[1] for row in _cols_result.fetchall()}
                        if "sub_rol" not in _col_names:
                            _conn.execute(_text(
                                "ALTER TABLE usuarios ADD COLUMN sub_rol VARCHAR(50)"
                            ))
                            logger.info("Migración aplicada: usuarios.sub_rol añadida")
                        if "area_id" not in _col_names:
                            _conn.execute(_text(
                                "ALTER TABLE usuarios ADD COLUMN area_id VARCHAR(36)"
                            ))
                            logger.info("Migración aplicada: usuarios.area_id añadida")
                        _conn.commit()
                # Promocionar a globales solo tras éxito completo
                _engine = _eng_tmp
                _SessionFactory = _sf_tmp
                logger.info("BD SaaS inicializada: %s", db_url.split("///")[-1])


def resetear_db() -> None:
    """
    Resetea el motor global. SOLO para tests: permite reutilizar un
    engine distinto entre suites sin interferencias.
    """
    global _engine, _SessionFactory
    _engine = None
    _SessionFactory = None


def get_session() -> Session:
    """
    Retorna una nueva sesión de BD administrada.

    Uso:
        session = get_session()
        try:
            ...
        finally:
            session.close()

    En endpoints FastAPI usar ``Depends(deps.get_db)`` que maneja
    el ciclo de vida de la sesión automáticamente.
    """
    if _SessionFactory is None:
        inicializar_db()
    return _SessionFactory()
