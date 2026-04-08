# ANDROMEDA - Validador de Queries Odoo (Sandbox)
# Autor: KAIROS-SYNERGY
# Descripción: Validador previo a la ejecución de queries Odoo. Whitelist de modelos, límite de registros, bloqueo de campos sensibles y solo-lectura.

MODELOS_PERMITIDOS = {
    # Ejemplo: solo modelos de negocio principales
    'sale.order', 'sale.order.line', 'pos.order', 'pos.order.line',
    'product.product', 'product.template', 'stock.quant',
    'res.partner', 'account.move', 'purchase.order', 'hr.employee'
}

CAMPOS_SENSIBLES = {
    'password', 'password_crypt', 'totp_secret', 'access_token', 'api_key',
    'clave', 'banco', 'iban', 'cc', 'credit_card', 'cvv', 'token', 'secret',
    'user_token', 'session_token', 'auth_token', 'pin', 'clave_bancaria'
}

MAX_REGISTROS = 200

class QueryNoPermitida(Exception):
    pass

def validar_query(modelo: str, campos: list, limite: int, modo: str = 'read'):
    """
    Valida si una query es permitida según reglas de seguridad.
    Args:
        modelo: Nombre técnico del modelo Odoo
        campos: Lista de campos solicitados
        limite: Límite de registros
        modo: 'read' (solo-lectura)
    Raises:
        QueryNoPermitida si la query no cumple las reglas
    """
    if modelo not in MODELOS_PERMITIDOS:
        raise QueryNoPermitida(f"Modelo '{modelo}' no permitido")
    if any(c.lower() in CAMPOS_SENSIBLES for c in campos):
        raise QueryNoPermitida("Campo sensible solicitado")
    if limite > MAX_REGISTROS:
        raise QueryNoPermitida(f"Límite de registros excedido: {limite} > {MAX_REGISTROS}")
    if modo != 'read':
        raise QueryNoPermitida("Solo se permiten queries de solo-lectura")
    return True

# Ejemplo de uso (eliminar en producción)
if __name__ == "__main__":
    try:
        validar_query('sale.order', ['name', 'amount_total'], 100)
        print("Query permitida")
        validar_query('ir.config_parameter', ['key', 'value'], 10)
    except QueryNoPermitida as e:
        print(f"Bloqueada: {e}")
