# ============================================================
# ANDROMEDA — models.odoo_versions
# Mapa de Compatibilidad por Versión de ERP (Fase 4)
#
# Soporta Odoo 14 → 19+.
# Base extensible hacia multi-ERP: SAP, NetSuite, Holded, etc.
#
# Diseño:
#   ODOO_VERSION_MAP  — overrides de campos/modelos por versión
#   ERPAdapterProtocol — protocolo abstracto para multi-ERP
#   detectar_version_odoo() — auto-detección desde instancia odoorpc
#   adaptar_campos()  — aplica overrides sobre lista de campos
#   obtener_modelo_canonico() — resuelve renombres de modelos
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

# ── Mapa de Compatibilidad Odoo ──────────────────────────────────────────────
#
# Estructura:
#   ODOO_VERSION_MAP[version][modelo] = {
#       campo_actual: campo_en_esa_version,   # renombre
#       campo_actual: None,                    # no existe en esa versión → se omite
#       "_modelo_alternativo": "otro.modelo",  # el modelo cambió de nombre
#   }
#
# Los campos no mencionados pasan sin modificación.

ODOO_VERSION_MAP: Dict[int, Dict[str, Dict[str, Optional[str]]]] = {
    14: {
        # account.move: en v14 el campo discriminador se llama 'type', no 'move_type'
        "account.move": {
            "move_type": "type",
        },
        # hr.leave: en v14 el modelo se llamaba hr.holidays
        "hr.leave": {
            "_modelo_alternativo": "hr.holidays",
        },
        # stock.picking: immediate_transfer no existía en v14
        "stock.picking": {
            "immediate_transfer": None,
        },
    },
    15: {
        # v15: move_type ya existe con ese nombre
        "account.move": {
            "move_type": "move_type",
        },
        # hr.leave ya es el modelo correcto desde v15
    },
    16: {
        # Sin cambios relevantes en campos core sobre v15
    },
    17: {
        "account.move": {
            "move_type": "move_type",
        },
        # stock.picking: immediate_transfer deprecado en v17 → None lo omite
        "stock.picking": {
            "immediate_transfer": None,
        },
        # product.template: en v17 'standard_price' pasó a ser compute-only en ciertos contextos
        # (no lo omitimos, solo documentamos)
    },
    18: {
        # Odoo 18 Community/Enterprise: sin breaking changes en campos core confirmados
    },
    19: {
        # Placeholder para versión futura
    },
}

VERSION_MINIMA: int = 14
VERSION_MAXIMA: int = 19


# ── ERPs Soportados ────────────────────────────────────────────────────────────

ERP_SOPORTADOS: Dict[str, Dict[str, Any]] = {
    "odoo": {
        "nombre": "Odoo",
        "versiones": list(range(VERSION_MINIMA, VERSION_MAXIMA + 1)),
        "adaptador": "models.conector_odoo.ConectorOdoo",
        "descripcion": "ERP open-source. Soportado nativo con odoorpc.",
    },
    # Extensiones futuras — cada entrada debe proveer su propio adaptador
    # que implemente ERPAdapterProtocol:
    # "sap": {
    #     "nombre": "SAP Business One",
    #     "versiones": ["9.3", "10.0"],
    #     "adaptador": "models.conector_sap.ConectorSAP",
    # },
    # "netsuite": {
    #     "nombre": "Oracle NetSuite",
    #     "versiones": ["2024.1"],
    #     "adaptador": "models.conector_netsuite.ConectorNetSuite",
    # },
    # "holded": {
    #     "nombre": "Holded",
    #     "versiones": ["v1"],
    #     "adaptador": "models.conector_holded.ConectorHolded",
    # },
}


# ── Protocolo Multi-ERP ───────────────────────────────────────────────────────

@runtime_checkable
class ERPAdapterProtocol(Protocol):
    """
    Protocolo base para adaptadores de ERP.

    Cualquier ERP que quiera integrarse con ANDROMEDA debe implementar
    estos métodos. No hay herencia forzada: ``isinstance(obj, ERPAdapterProtocol)``
    es suficiente para validar en runtime.

    Extensible hacia SAP, NetSuite, Holded, Dynamics, etc. — cada uno
    provee su propio conector que cumple este contrato sin tocar el núcleo.
    """

    tipo_erp: str  # "odoo" | "sap" | "netsuite" | "holded"

    def conectar(self) -> tuple:
        """
        Establece conexión con el ERP.
        Returns: (exito: bool, mensaje: str)
        """
        ...

    def desconectar(self) -> None:
        """Cierra la conexión de forma limpia."""
        ...

    def buscar(self, modelo: str, filtro: list, campos: list) -> Any:
        """
        Busca registros y retorna un DataFrame.
        ``modelo`` es el nombre técnico del modelo en el ERP.
        """
        ...

    def buscar_leer(self, modelo: str, filtro: list, campos: list) -> list:
        """Busca y retorna lista de dicts (formato raw del ERP)."""
        ...


# ── Funciones de Adaptación de Versión ───────────────────────────────────────

def detectar_version_odoo(odoo_instance: Any) -> int:
    """
    Detecta la versión mayor de Odoo desde una instancia odoorpc conectada.

    odoorpc expone ``instance.version`` como string, p.ej. ``"17.0"`` o ``"16.0"``.
    Esta función extrae la parte entera y la valida dentro del rango conocido.

    Returns:
        Versión entera (e.g. 17). Retorna 17 si no puede detectar (default seguro).
    """
    try:
        version_str: str = str(odoo_instance.version)
        mayor = int(version_str.split(".")[0])
        # Tolerancia +5 años futuro
        if VERSION_MINIMA <= mayor <= VERSION_MAXIMA + 5:
            return mayor
    except Exception:
        pass
    return 17


def adaptar_campos(
    modelo: str,
    campos: List[str],
    version: int,
) -> List[str]:
    """
    Adapta una lista de campos al mapa de compatibilidad de la versión indicada.

    Reglas de transformación:
    - Si campo está en overrides con valor str → sustituir por el nuevo nombre.
    - Si campo está en overrides con valor None → omitir (no existe en esa versión).
    - Si campo NO está en overrides → pasar sin modificación.

    Nunca lanza excepciones. Silencioso ante versiones desconocidas.

    Args:
        modelo:  nombre técnico del modelo (e.g. ``"account.move"``)
        campos:  lista de campos a adaptar
        version: versión entera de Odoo (e.g. 17)

    Returns:
        Lista de campos adaptada.

    Example:
        >>> adaptar_campos("account.move", ["move_type", "name"], version=14)
        ["type", "name"]
    """
    overrides: Dict[str, Optional[str]] = (
        ODOO_VERSION_MAP.get(version, {}).get(modelo, {})
    )
    if not overrides:
        return list(campos)

    resultado: List[str] = []
    for campo in campos:
        if campo in overrides:
            nuevo = overrides[campo]
            if nuevo is not None:
                resultado.append(nuevo)
            # nuevo == None → campo no existe en esta versión, se omite
        else:
            resultado.append(campo)
    return resultado


def obtener_modelo_canonico(modelo: str, version: int) -> str:
    """
    Retorna el nombre técnico del modelo para la versión indicada.

    Útil cuando un modelo fue renombrado entre versiones.
    Ejemplo: ``hr.leave`` → ``hr.holidays`` en Odoo 14.

    Args:
        modelo:  nombre del modelo en la versión actual/más reciente
        version: versión de Odoo del servidor

    Returns:
        Nombre del modelo a usar para esa versión.
    """
    overrides = ODOO_VERSION_MAP.get(version, {}).get(modelo, {})
    alternativo: Optional[str] = overrides.get("_modelo_alternativo")
    return alternativo if alternativo else modelo


def es_erp_soportado(tipo_erp: str) -> bool:
    """Valida que el tipo de ERP indicado tenga soporte en ANDROMEDA."""
    return tipo_erp in ERP_SOPORTADOS


def versiones_soportadas_odoo() -> List[int]:
    """Retorna la lista de versiones de Odoo con soporte definido."""
    return list(range(VERSION_MINIMA, VERSION_MAXIMA + 1))
