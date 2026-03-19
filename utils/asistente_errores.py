# ============================================================
# ASISTENTE DE ERRORES ODOO
# ============================================================
# Base de conocimiento para solucionar errores comunes
# ============================================================

from typing import Dict, List, Optional, Tuple
import re

from app.logging_config import get_logger
logger = get_logger("utils.asistente_errores")


class AsistenteErroresOdoo:
    """Sistema experto para diagnosticar y solucionar errores de Odoo."""
    
    def __init__(self):
        self.errores_conocidos = self._cargar_errores()
        self.soluciones_aplicadas = []
    
    def _cargar_errores(self) -> Dict:
        """Base de conocimiento de errores comunes de Odoo."""
        return {
            # ========================================
            # ERRORES DE ACCESO Y PERMISOS
            # ========================================
            'access_denied': {
                'patrones': [
                    r'access denied',
                    r'acceso denegado',
                    r'permission denied',
                    r'no tiene permisos',
                    r'AccessError',
                    r'not allowed'
                ],
                'titulo': 'Error de Acceso/Permisos',
                'descripcion': 'El usuario no tiene permisos suficientes para realizar esta acción.',
                'causas': [
                    'El usuario no pertenece al grupo correcto',
                    'Las reglas de registro (record rules) bloquean el acceso',
                    'El modelo no tiene permisos de lectura/escritura configurados',
                    'El registro pertenece a otra compañía'
                ],
                'solucion': '''### Cómo solucionar errores de acceso:

1. **Verificar grupos del usuario:**
   - Ir a Ajustes → Usuarios → [Usuario]
   - Revisar los grupos asignados
   - Agregar al grupo necesario (ej: Ventas/Usuario o Ventas/Administrador)

2. **Revisar reglas de registro:**
   - Activar modo desarrollador
   - Ir a Ajustes → Técnico → Seguridad → Reglas de Registro
   - Buscar reglas del modelo afectado
   - Verificar que no haya filtros muy restrictivos

3. **Verificar permisos del modelo:**
   - Ir a Ajustes → Técnico → Seguridad → Derechos de Acceso
   - Buscar el modelo (ej: sale.order)
   - Verificar permisos de lectura/escritura/creación/eliminación

4. **Multi-compañía:**
   - Verificar que el usuario tenga acceso a la compañía correcta
   - El registro debe pertenecer a una compañía del usuario

**Código para verificar permisos:**
```python
# En consola de Odoo
user = env['res.users'].browse(uid)
print(user.groups_id.mapped('name'))
```''',
                'nivel': 'medio'
            },
            
            'constraint_error': {
                'patrones': [
                    r'constraint',
                    r'restricción',
                    r'UNIQUE constraint',
                    r'duplicate key',
                    r'ya existe',
                    r'ValidationError'
                ],
                'titulo': 'Error de Restricción/Validación',
                'descripcion': 'Los datos violan una restricción de integridad o validación.',
                'causas': [
                    'Valor duplicado en un campo único',
                    'Campo requerido vacío',
                    'Valor fuera del rango permitido',
                    'Violación de restricción SQL'
                ],
                'solucion': '''### Cómo solucionar errores de restricción:

1. **Valor duplicado:**
   - El campo tiene restricción UNIQUE
   - Buscar el registro existente con ese valor
   - Cambiar el valor o editar el registro existente

2. **Campo requerido:**
   - Identificar qué campo falta
   - El error usualmente indica el campo (ej: "El campo X es obligatorio")
   - Completar el valor antes de guardar

3. **Validación de datos:**
   - Verificar formato (emails, teléfonos, RFC)
   - Revisar rangos (fechas, cantidades, precios)
   - Asegurar relaciones válidas (partner_id existe, etc.)

**Ejemplo de error común:**
```
IntegrityError: UNIQUE constraint failed: res_partner.vat
```
Significa que ya hay otro contacto con ese mismo RFC/VAT.''',
                'nivel': 'bajo'
            },
            
            'missing_field': {
                'patrones': [
                    r'field .+ does not exist',
                    r'campo .+ no existe',
                    r'AttributeError',
                    r'KeyError',
                    r'no attribute',
                    r'undefined field'
                ],
                'titulo': 'Campo No Encontrado',
                'descripcion': 'Se intenta acceder a un campo que no existe en el modelo.',
                'causas': [
                    'El campo fue eliminado o renombrado',
                    'Un módulo no está instalado',
                    'Error de tipeo en el nombre del campo',
                    'El campo es de un módulo desinstalado'
                ],
                'solucion': '''### Cómo solucionar campos no encontrados:

1. **Verificar nombre del campo:**
   - Comparar con la definición del modelo
   - Buscar typos (ej: `partner_id` vs `parner_id`)
   
2. **Verificar módulo instalado:**
   - Algunos campos vienen de módulos específicos
   - Ir a Apps → Buscar el módulo → Instalar

3. **Ver campos disponibles:**
   ```python
   # En shell de Odoo
   env['sale.order'].fields_get().keys()
   ```

4. **Actualizar lista de apps:**
   - Activar modo desarrollador
   - Ir a Apps → Actualizar lista de apps
   - Buscar e instalar módulos faltantes

**Campos comunes por módulo:**
- `sale`: sale.order, sale.order.line
- `stock`: stock.quant, stock.move
- `account`: account.move, account.move.line''',
                'nivel': 'medio'
            },
            
            'connection_error': {
                'patrones': [
                    r'connection refused',
                    r'conexión rechazada',
                    r'timeout',
                    r'no se pudo conectar',
                    r'ConnectionError',
                    r'socket error',
                    r'ECONNREFUSED'
                ],
                'titulo': 'Error de Conexión',
                'descripcion': 'No se puede establecer conexión con el servidor Odoo.',
                'causas': [
                    'El servidor está apagado',
                    'URL o puerto incorrectos',
                    'Firewall bloqueando conexión',
                    'Problemas de red',
                    'SSL/HTTPS mal configurado'
                ],
                'solucion': '''### Cómo solucionar errores de conexión:

1. **Verificar que el servidor esté arriba:**
   - Acceder a la URL desde el navegador
   - Verificar el estado del servicio Odoo

2. **Verificar URL y puerto:**
   ```python
   # Configuración típica
   url = "https://miempresa.odoo.com"  # Odoo.sh / Cloud
   url = "http://localhost:8069"        # Local
   ```

3. **Para Odoo.sh:**
   - Verificar que la instancia esté activa
   - Revisar logs en el panel de Odoo.sh

4. **Para servidor propio:**
   ```bash
   # Linux
   sudo systemctl status odoo
   sudo systemctl restart odoo
   
   # Ver logs
   tail -f /var/log/odoo/odoo.log
   ```

5. **Firewall:**
   - Abrir puerto 8069 (HTTP) o 8072 (longpolling)
   - Verificar reglas de seguridad en la nube''',
                'nivel': 'alto'
            },
            
            'login_error': {
                'patrones': [
                    r'login failed',
                    r'invalid credentials',
                    r'usuario.+contraseña',
                    r'authentication',
                    r'wrong password',
                    r'user not found'
                ],
                'titulo': 'Error de Autenticación',
                'descripcion': 'Las credenciales de acceso son incorrectas.',
                'causas': [
                    'Usuario o contraseña incorrectos',
                    'Base de datos incorrecta',
                    'Usuario desactivado',
                    'API key inválida'
                ],
                'solucion': '''### Cómo solucionar errores de login:

1. **Verificar credenciales:**
   - Usuario: email completo (ej: admin@empresa.com)
   - Contraseña: case-sensitive
   - Base de datos: nombre exacto

2. **Probar en navegador primero:**
   - Ir a la URL de Odoo
   - Intentar login manual
   - Si falla, resetear contraseña

3. **Para API:**
   - Usar API key en lugar de contraseña
   - Generar en: Usuario → Preferencias → API Keys
   
4. **Usuario desactivado:**
   - Un admin debe activar el usuario
   - Ajustes → Usuarios → [Usuario] → Activo

**Config para odoorpc:**
```python
import odoorpc
odoo = odoorpc.ODOO('miempresa.odoo.com', protocol='jsonrpc+ssl', port=443)
odoo.login('nombre_base_datos', 'usuario@email.com', 'api_key_o_password')
```''',
                'nivel': 'bajo'
            },
            
            # ========================================
            # ERRORES DE DATOS
            # ========================================
            
            'record_not_found': {
                'patrones': [
                    r'record does not exist',
                    r'registro no existe',
                    r'MissingError',
                    r'no records found',
                    r'ID .+ does not exist'
                ],
                'titulo': 'Registro No Encontrado',
                'descripcion': 'El ID del registro buscado no existe en la base de datos.',
                'causas': [
                    'El registro fue eliminado',
                    'ID incorrecto',
                    'Registro en otra compañía',
                    'Filtro de seguridad bloqueando acceso'
                ],
                'solucion': '''### Cómo solucionar registro no encontrado:

1. **Verificar que el ID sea correcto:**
   ```python
   # Buscar el registro
   env['modelo'].search([('id', '=', ID)])
   ```

2. **Buscar en archivo (eliminados):**
   - Activar modo desarrollador
   - Buscar con filtro: "Archivado" está definido
   
3. **Multi-compañía:**
   - El registro puede estar en otra compañía
   - Cambiar de compañía o usar sudo()

4. **Verificar en base de datos:**
   ```sql
   SELECT id, active FROM tabla WHERE id = X;
   ```''',
                'nivel': 'bajo'
            },
            
            'type_error': {
                'patrones': [
                    r'TypeError',
                    r'tipo de dato',
                    r'expected .+ got',
                    r'cannot convert',
                    r'invalid literal'
                ],
                'titulo': 'Error de Tipo de Dato',
                'descripcion': 'El tipo de dato proporcionado no es el esperado.',
                'causas': [
                    'Enviar string donde se espera número',
                    'Formato de fecha incorrecto',
                    'None donde se espera valor',
                    'Lista donde se espera ID único'
                ],
                'solucion': '''### Cómo solucionar errores de tipo:

**Tipos comunes en Odoo:**
| Campo | Tipo Python | Ejemplo |
|-------|-------------|---------|
| Integer | int | 42 |
| Float | float | 19.99 |
| Char/Text | str | "Hola" |
| Boolean | bool | True/False |
| Date | str | "2024-01-15" |
| Datetime | str | "2024-01-15 10:30:00" |
| Many2one | int | 5 (ID del registro) |
| Many2many | list | [(6, 0, [1,2,3])] |
| One2many | list | [(0, 0, {dict})] |

**Ejemplos de corrección:**
```python
# Incorrecto
partner_id = "5"  # String

# Correcto
partner_id = 5  # Integer

# Fecha
date_order = "2024-01-15"  # String ISO

# Many2many - agregar IDs
tag_ids = [(6, 0, [1, 2, 3])]
```''',
                'nivel': 'medio'
            },
            
            # ========================================
            # ERRORES DE INVENTARIO
            # ========================================
            
            'stock_error': {
                'patrones': [
                    r'not enough stock',
                    r'stock insuficiente',
                    r'negative stock',
                    r'stock negativo',
                    r'no disponible',
                    r'reserv'
                ],
                'titulo': 'Error de Stock/Inventario',
                'descripcion': 'Problema relacionado con disponibilidad de inventario.',
                'causas': [
                    'No hay suficiente stock disponible',
                    'Stock reservado para otra orden',
                    'Ubicación de stock incorrecta',
                    'Producto no permite stock negativo'
                ],
                'solucion': '''### Cómo solucionar errores de stock:

1. **Verificar disponibilidad:**
   - Inventario → Informes → Stock disponible
   - Filtrar por producto y ubicación

2. **Liberar reservas:**
   - Ir a la orden que reservó el stock
   - Cancelar o completar la transferencia

3. **Ajuste de inventario:**
   - Inventario → Operaciones → Ajuste de inventario
   - Crear nuevo ajuste para el producto

4. **Permitir stock negativo (temporal):**
   - Inventario → Config → Ubicaciones
   - Activar "Permitir cantidades negativas"
   
5. **Forzar disponibilidad:**
   ```python
   # En código
   picking.action_assign()  # Reservar
   picking.action_force_assign()  # Forzar
   ```''',
                'nivel': 'medio'
            },
            
            # ========================================
            # ERRORES DE FACTURACIÓN
            # ========================================
            
            'invoice_error': {
                'patrones': [
                    r'factura',
                    r'invoice',
                    r'account.move',
                    r'CFDI',
                    r'timbr',
                    r'SAT'
                ],
                'titulo': 'Error de Facturación',
                'descripcion': 'Problema al crear o validar facturas.',
                'causas': [
                    'Datos fiscales incompletos',
                    'Secuencia no configurada',
                    'Cuenta contable faltante',
                    'Error de timbrado CFDI'
                ],
                'solucion': '''### Cómo solucionar errores de facturación:

1. **Datos fiscales del cliente:**
   - RFC válido y completo
   - Régimen fiscal correcto
   - Uso de CFDI seleccionado
   - Código postal fiscal

2. **Configuración de empresa:**
   - RFC de la empresa
   - Certificado y llave privada (CSD)
   - PAC configurado correctamente

3. **Secuencias:**
   - Contabilidad → Config → Diarios
   - Verificar secuencia de facturas

4. **Cuentas contables:**
   - Productos deben tener cuenta de ingresos
   - Impuestos bien configurados

5. **Errores CFDI comunes:**
   | Código | Significado |
   |--------|-------------|
   | 301 | RFC no válido |
   | 302 | Certificado revocado |
   | 303 | Sello inválido |
   | 401 | Fecha inválida |''',
                'nivel': 'alto'
            },
            
            # ========================================
            # ERRORES DE RENDIMIENTO
            # ========================================
            
            'performance_error': {
                'patrones': [
                    r'timeout',
                    r'muy lento',
                    r'se traba',
                    r'memoria',
                    r'memory',
                    r'tarda mucho'
                ],
                'titulo': 'Problema de Rendimiento',
                'descripcion': 'El sistema está lento o no responde.',
                'causas': [
                    'Consultas muy pesadas',
                    'Demasiados registros',
                    'Campos calculados costosos',
                    'Memoria insuficiente'
                ],
                'solucion': '''### Cómo mejorar el rendimiento:

1. **Limitar registros:**
   ```python
   # Usar limit
   records = env['model'].search([], limit=100)
   
   # Paginación
   records = env['model'].search([], offset=0, limit=50)
   ```

2. **Optimizar búsquedas:**
   ```python
   # Usar read() en lugar de browse para campos específicos
   data = env['model'].search_read(
       domain=[],
       fields=['name', 'amount'],
       limit=100
   )
   ```

3. **Cachear datos frecuentes:**
   - Usar vistas materializadas
   - Implementar caché en memoria

4. **Revisar campos computados:**
   - Campos store=True se calculan una vez
   - Campos sin store se calculan cada vez

5. **Índices de base de datos:**
   ```sql
   CREATE INDEX idx_orden_fecha ON sale_order(date_order);
   ```''',
                'nivel': 'alto'
            },
            
            # ========================================
            # ERRORES GENERALES
            # ========================================
            
            'syntax_error': {
                'patrones': [
                    r'SyntaxError',
                    r'IndentationError',
                    r'NameError',
                    r'syntax',
                    r'invalid syntax'
                ],
                'titulo': 'Error de Sintaxis',
                'descripcion': 'Error en el código Python o dominio.',
                'causas': [
                    'Error de tipeo',
                    'Paréntesis/corchetes no balanceados',
                    'Indentación incorrecta',
                    'Variable no definida'
                ],
                'solucion': '''### Cómo solucionar errores de sintaxis:

1. **Revisar el mensaje de error:**
   - Indica la línea exacta
   - Muestra el carácter problemático

2. **Errores comunes en dominios:**
   ```python
   # Incorrecto
   [('state' = 'draft')]  # Usar = en lugar de ,
   
   # Correcto
   [('state', '=', 'draft')]
   ```

3. **Verificar comillas y paréntesis:**
   ```python
   # Balancear
   [(  )]  # Corchetes y paréntesis
   '  '    # Comillas simples
   "  "    # Comillas dobles
   ```

4. **Para dominios complejos:**
   ```python
   domain = [
       '&',
       ('state', '=', 'sale'),
       ('date_order', '>=', '2024-01-01')
   ]
   ```''',
                'nivel': 'bajo'
            }
        }
    
    def diagnosticar(self, error_texto: str) -> Dict:
        """Diagnostica un error y ofrece soluciones."""
        error_lower = error_texto.lower()
        
        for key, error_info in self.errores_conocidos.items():
            for patron in error_info['patrones']:
                if re.search(patron, error_lower, re.IGNORECASE):
                    return {
                        'encontrado': True,
                        'tipo': key,
                        'info': error_info
                    }
        
        # Error no reconocido
        return {
            'encontrado': False,
            'tipo': 'desconocido',
            'info': {
                'titulo': 'Error No Identificado',
                'descripcion': 'No pude identificar este error específicamente.',
                'solucion': self._solucion_generica()
            }
        }
    
    def _solucion_generica(self) -> str:
        """Solución genérica para errores no identificados."""
        return '''### Pasos Generales de Diagnóstico

1. **Leer el mensaje completo:**
   - El error usualmente indica la causa
   - Buscar líneas con "Error", "Exception", "Failed"

2. **Buscar en logs:**
   - Odoo.sh: Panel → Logs
   - Local: `/var/log/odoo/odoo.log`

3. **Reproducir el error:**
   - ¿Qué acción causa el error?
   - ¿Ocurre siempre o intermitente?

4. **Modo desarrollador:**
   - Activar para ver detalles técnicos
   - URL + ?debug=1

5. **Buscar en comunidad:**
   - [Foro Odoo](https://www.odoo.com/forum)
   - [Stack Overflow tag:odoo](https://stackoverflow.com/questions/tagged/odoo)
   - GitHub issues del módulo

6. **Si persiste:**
   - Comparte el traceback completo
   - Indica versión de Odoo
   - Describe los pasos para reproducir

¿Puedes compartir más detalles del error?'''
    
    def formatear_diagnostico(self, diagnostico: Dict) -> str:
        """Formatea el diagnóstico como Markdown."""
        info = diagnostico['info']
        
        md = f"## {info['titulo']}\n\n"
        md += f"**Descripción:** {info['descripcion']}\n\n"
        
        if 'causas' in info:
            md += "### Posibles Causas:\n"
            for causa in info['causas']:
                md += f"• {causa}\n"
            md += "\n"
        
        md += info['solucion']
        
        if 'nivel' in info:
            niveles = {'bajo': 'Fácil', 'medio': 'Medio', 'alto': 'Complejo'}
            md += f"\n\n**Dificultad de solución:** {niveles.get(info['nivel'], 'N/A')}"
        
        return md
    
    def obtener_consejos_rapidos(self) -> List[str]:
        """Retorna consejos rápidos para evitar errores."""
        return [
            "Siempre haz respaldo antes de cambios masivos",
            "Actualiza módulos después de cambios en el código",
            "Usa modo desarrollador para ver IDs y nombres técnicos",
            "Revisa permisos si un usuario no ve datos",
            "Las fechas en Odoo son strings: '2024-01-15'",
            "Los Many2one se envían como IDs (int), no como nombres",
            "Valida datos antes de write() o create()",
            "Usa search_count() antes de search() para datos grandes",
            "Los campos compute sin store se calculan en cada acceso",
            "Prefiere search_read() sobre browse() + read()"
        ]


# Ejemplo de uso
if __name__ == "__main__":
    asistente = AsistenteErroresOdoo()
    
    # Probar diagnóstico
    error = "AccessError: No tiene permisos para acceder a este registro"
    resultado = asistente.diagnosticar(error)
    print(asistente.formatear_diagnostico(resultado))
