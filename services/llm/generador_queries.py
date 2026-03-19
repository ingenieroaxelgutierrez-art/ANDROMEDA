# -*- coding: utf-8 -*-
"""
ANDROMEDA - Generador Dinámico de Queries para Odoo
=====================================================
Permite que ANDROMEDA genere sus propios queries de Odoo.
Usa el LLM para interpretar preguntas y generar dominios de búsqueda.

Autor: Axel Gutiérrez
Fecha: 2026
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from app.logging_config import get_logger
logger = get_logger("services.llm.generador_queries")

# Campos sensibles que NUNCA deben ser consultados por el LLM
CAMPOS_PROHIBIDOS = {
    'password', 'password_crypt', 'password_digest',
    'totp_secret', 'totp_token',
    'access_token', 'oauth_access_token', 'oauth_provider_id',
    'signature', 'signature_letter',
    'api_key', 'secret', 'token',
    '__last_update',
}

# Modelos sensibles que NUNCA deben ser consultados por el LLM
MODELOS_PROHIBIDOS = {
    'ir.config_parameter',      # Parámetros de config del sistema (claves secretas)
    'ir.cron',                  # Tareas programadas
    'ir.module.module',         # Módulos instalados (info de seguridad)
    'base.module.update',       # Actualizaciones de módulos
    'ir.mail_server',           # Servidores de correo (credenciales)
    'fetchmail.server',         # Servidores de correo entrante
    'ir.logging',               # Logs del servidor
    'ir.attachment',            # Adjuntos (pueden contener datos sensibles)
    'res.users.log',            # Logs de acceso de usuarios
    'auth_totp.device',         # Dispositivos 2FA
    'auth_totp.wizard',         # Wizard 2FA
}


@dataclass
class QueryOdoo:
    """Representa un query generado para Odoo"""
    modelo: str
    dominio: List
    campos: List[str]
    limite: int = 100
    orden: str = None
    descripcion: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'modelo': self.modelo,
            'dominio': self.dominio,
            'campos': self.campos,
            'limite': self.limite,
            'orden': self.orden,
            'descripcion': self.descripcion
        }


@dataclass
class ResultadoQuery:
    """Resultado de ejecutar un query"""
    query: QueryOdoo
    datos: List[Dict]
    total: int
    tiempo: float
    exito: bool
    error: str = None
    interpretacion: str = ""


class GeneradorQueries:
    """
    Generador inteligente de queries para Odoo.
    Combina conocimiento de la estructura de Odoo con el LLM.
    """
    
    # Conocimiento de modelos principales de Odoo
    MODELOS_ODOO = {
        # Ventas
        'sale.order': {
            'descripcion': 'Órdenes de venta / Cotizaciones',
            'campos_comunes': ['name', 'partner_id', 'date_order', 'amount_total', 'state', 
                              'user_id', 'team_id', 'warehouse_id', 'company_id'],
            'estados': ['draft', 'sent', 'sale', 'done', 'cancel'],
            'relaciones': {'partner_id': 'res.partner', 'user_id': 'res.users'}
        },
        'sale.order.line': {
            'descripcion': 'Líneas de orden de venta',
            'campos_comunes': ['order_id', 'product_id', 'product_uom_qty', 'price_unit', 
                              'price_subtotal', 'discount'],
            'relaciones': {'order_id': 'sale.order', 'product_id': 'product.product'}
        },
        
        # Compras
        'purchase.order': {
            'descripcion': 'Órdenes de compra',
            'campos_comunes': ['name', 'partner_id', 'date_order', 'amount_total', 'state',
                              'user_id', 'company_id'],
            'estados': ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel']
        },
        
        # Inventario
        'stock.quant': {
            'descripcion': 'Cantidades de stock por ubicación',
            'campos_comunes': ['product_id', 'location_id', 'quantity', 'reserved_quantity',
                              'available_quantity', 'value']
        },
        'stock.move': {
            'descripcion': 'Movimientos de inventario',
            'campos_comunes': ['name', 'product_id', 'product_uom_qty', 'location_id',
                              'location_dest_id', 'state', 'date']
        },
        'stock.picking': {
            'descripcion': 'Transferencias de inventario',
            'campos_comunes': ['name', 'partner_id', 'picking_type_id', 'state', 'date_done',
                              'origin', 'move_ids_without_package']
        },
        'product.product': {
            'descripcion': 'Variantes de productos',
            'campos_comunes': ['name', 'default_code', 'barcode', 'qty_available', 
                              'virtual_available', 'list_price', 'standard_price', 'categ_id']
        },
        'product.template': {
            'descripcion': 'Plantillas de productos',
            'campos_comunes': ['name', 'default_code', 'type', 'categ_id', 'list_price',
                              'active', 'sale_ok', 'purchase_ok']
        },
        
        # Contabilidad
        'account.move': {
            'descripcion': 'Asientos contables / Facturas',
            'campos_comunes': ['name', 'partner_id', 'invoice_date', 'amount_total', 
                              'amount_residual', 'state', 'payment_state', 'move_type',
                              'invoice_date_due'],
            'estados': ['draft', 'posted', 'cancel'],
            'payment_states': ['not_paid', 'in_payment', 'paid', 'partial', 'reversed']
        },
        'account.payment': {
            'descripcion': 'Pagos',
            'campos_comunes': ['name', 'partner_id', 'amount', 'date', 'state', 
                              'payment_type', 'journal_id']
        },
        
        # CRM
        'crm.lead': {
            'descripcion': 'Oportunidades / Leads',
            'campos_comunes': ['name', 'partner_id', 'user_id', 'expected_revenue',
                              'probability', 'stage_id', 'date_deadline', 'create_date']
        },
        
        # Contactos
        'res.partner': {
            'descripcion': 'Clientes / Proveedores / Contactos',
            'campos_comunes': ['name', 'email', 'phone', 'mobile', 'street', 'city',
                              'customer_rank', 'supplier_rank', 'credit_limit', 
                              'total_due', 'total_overdue']
        },
        
        # POS
        'pos.order': {
            'descripcion': 'Órdenes de punto de venta',
            'campos_comunes': ['name', 'session_id', 'partner_id', 'amount_total',
                              'date_order', 'state', 'user_id', 'pos_reference']
        },
        'pos.session': {
            'descripcion': 'Sesiones de POS',
            'campos_comunes': ['name', 'config_id', 'user_id', 'start_at', 'stop_at',
                              'state', 'cash_register_balance_end_real']
        },
        'pos.config': {
            'descripcion': 'Configuración de punto de venta (Unidades operativas)',
            'campos_comunes': ['name', 'active', 'company_id', 'picking_type_id',
                              'warehouse_id', 'stock_location_id']
        },
        
        # Recursos Humanos
        'hr.employee': {
            'descripcion': 'Empleados',
            'campos_comunes': ['name', 'job_id', 'department_id', 'work_email',
                              'work_phone', 'parent_id', 'company_id']
        },
        
        # Usuarios
        'res.users': {
            'descripcion': 'Usuarios del sistema',
            'campos_comunes': ['name', 'login', 'email', 'active', 'company_id']
        },
        
        # Diarios
        'account.journal': {
            'descripcion': 'Diarios contables',
            'campos_comunes': ['name', 'code', 'type', 'company_id']
        }
    }
    
    # Plantillas de queries comunes
    PLANTILLAS_QUERIES = {
        'cliente_mas_deuda': QueryOdoo(
            modelo='account.move',
            dominio=[
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ],
            campos=['partner_id', 'amount_residual', 'invoice_date_due', 'name'],
            orden='amount_residual desc',
            limite=20,
            descripcion='Clientes con mayor deuda pendiente'
        ),
        'facturas_vencidas': QueryOdoo(
            modelo='account.move',
            dominio=[
                ('move_type', 'in', ['out_invoice']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', datetime.now().strftime('%Y-%m-%d'))
            ],
            campos=['name', 'partner_id', 'amount_residual', 'invoice_date_due'],
            orden='invoice_date_due asc',
            limite=50,
            descripcion='Facturas vencidas por cobrar'
        ),
        'productos_sin_stock': QueryOdoo(
            modelo='product.product',
            dominio=[
                ('type', '=', 'product'),
                ('qty_available', '<=', 0),
                ('active', '=', True)
            ],
            campos=['name', 'default_code', 'qty_available', 'virtual_available'],
            limite=100,
            descripcion='Productos sin existencias'
        ),
        'ventas_hoy': QueryOdoo(
            modelo='sale.order',
            dominio=[
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', datetime.now().strftime('%Y-%m-%d 00:00:00'))
            ],
            campos=['name', 'partner_id', 'amount_total', 'user_id'],
            orden='date_order desc',
            limite=100,
            descripcion='Ventas del día'
        ),
        'pos_hoy': QueryOdoo(
            modelo='pos.order',
            dominio=[
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('date_order', '>=', datetime.now().strftime('%Y-%m-%d 00:00:00'))
            ],
            campos=['name', 'session_id', 'amount_total', 'partner_id'],
            orden='date_order desc',
            limite=200,
            descripcion='Ventas POS del día'
        ),
        'top_productos_vendidos': QueryOdoo(
            modelo='sale.order.line',
            dominio=[
                ('order_id.state', 'in', ['sale', 'done'])
            ],
            campos=['product_id', 'product_uom_qty', 'price_subtotal'],
            limite=50,
            descripcion='Productos más vendidos'
        )
    }
    
    def __init__(self, conector_odoo=None, agente_llm=None):
        """
        Inicializa el generador de queries.
        
        Args:
            conector_odoo: Instancia del conector de Odoo
            agente_llm: Instancia del agente LLM para generar queries
        """
        self.conector = conector_odoo
        self.agente_llm = agente_llm
        self._cache_estructura = {}
    
    def set_conector(self, conector):
        """Establece el conector de Odoo"""
        self.conector = conector
    
    def set_agente_llm(self, agente):
        """Establece el agente LLM"""
        self.agente_llm = agente
    
    def _filtrar_campos_seguros(self, campos: List[str]) -> List[str]:
        """Elimina campos sensibles que el LLM pueda haber solicitado."""
        seguros = [c for c in campos if c.lower() not in CAMPOS_PROHIBIDOS]
        if len(seguros) < len(campos):
            logger.warning("Campos sensibles filtrados de la query generada por LLM")
        return seguros if seguros else ['name', 'id']
    
    def _obtener_prompt_generacion(self, pregunta: str) -> str:
        """Genera el prompt para que el LLM cree el query"""
        modelos_info = "\n".join([
            f"- {modelo}: {info['descripcion']} | Campos: {', '.join(info['campos_comunes'][:5])}"
            for modelo, info in list(self.MODELOS_ODOO.items())[:15]
        ])
        
        return f"""Eres un experto en Odoo. Genera un query para responder esta pregunta:

PREGUNTA: {pregunta}

MODELOS DISPONIBLES:
{modelos_info}

REGLAS PARA EL DOMINIO:
- Usa tuplas de 3 elementos: (campo, operador, valor)
- Operadores: =, !=, >, <, >=, <=, like, ilike, in, not in, child_of
- Para fechas usa formato: 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS'
- Para relaciones usa el campo_id (ej: partner_id)
- Combina condiciones con & (AND) o | (OR) al inicio

FECHA ACTUAL: {datetime.now().strftime('%Y-%m-%d')}

Responde SOLO con JSON válido:
{{
    "modelo": "nombre.modelo",
    "dominio": [["campo", "operador", "valor"]],
    "campos": ["campo1", "campo2"],
    "limite": 50,
    "orden": "campo desc",
    "descripcion": "Descripción breve"
}}
"""
    
    def generar_query_con_llm(self, pregunta: str) -> Optional[QueryOdoo]:
        """
        Usa el LLM para generar un query basado en una pregunta natural.
        
        Args:
            pregunta: Pregunta en lenguaje natural
            
        Returns:
            QueryOdoo si se pudo generar, None si no
        """
        if not self.agente_llm:
            logger.warning("No hay agente LLM disponible")
            return None
        
        try:
            prompt = self._obtener_prompt_generacion(pregunta)
            respuesta = self.agente_llm.generar_raw(prompt)
            
            if not respuesta:
                return None
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[^{}]*\}', respuesta, re.DOTALL)
            if not json_match:
                return None
            
            datos = json.loads(json_match.group())
            
            # Validar modelo
            modelo_solicitado = datos.get('modelo', 'sale.order')
            if modelo_solicitado in MODELOS_PROHIBIDOS:
                logger.warning(f"Modelo prohibido bloqueado: {modelo_solicitado}")
                return None
            if modelo_solicitado not in self.MODELOS_ODOO:
                logger.warning(f"Modelo desconocido: {modelo_solicitado}")
                # Permitir de todas formas si parece válido
            
            return QueryOdoo(
                modelo=modelo_solicitado,
                dominio=datos.get('dominio', []),
                campos=self._filtrar_campos_seguros(datos.get('campos', ['name', 'id'])),
                limite=min(datos.get('limite', 50), 500),
                orden=datos.get('orden'),
                descripcion=datos.get('descripcion', pregunta)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON del LLM: {e}")
        except Exception as e:
            logger.error(f"Error generando query con LLM: {e}")
        
        return None
    
    def obtener_query_plantilla(self, tipo: str) -> Optional[QueryOdoo]:
        """Obtiene un query de las plantillas predefinidas"""
        return self.PLANTILLAS_QUERIES.get(tipo)
    
    def ejecutar_query(self, query: QueryOdoo) -> ResultadoQuery:
        """
        Ejecuta un query contra Odoo.
        
        Args:
            query: Query a ejecutar
            
        Returns:
            ResultadoQuery con los datos
        """
        import time
        inicio = time.time()
        
        if not self.conector:
            return ResultadoQuery(
                query=query,
                datos=[],
                total=0,
                tiempo=0,
                exito=False,
                error="No hay conexión a Odoo"
            )
        
        try:
            # Ejecutar search_read
            kwargs = {
                'domain': query.dominio,
                'fields': query.campos,
                'limit': query.limite
            }
            
            if query.orden:
                kwargs['order'] = query.orden
            
            datos = self.conector.search_read(query.modelo, **kwargs)
            
            tiempo = time.time() - inicio
            
            return ResultadoQuery(
                query=query,
                datos=datos if datos else [],
                total=len(datos) if datos else 0,
                tiempo=tiempo,
                exito=True
            )
            
        except Exception as e:
            return ResultadoQuery(
                query=query,
                datos=[],
                total=0,
                tiempo=time.time() - inicio,
                exito=False,
                error=str(e)
            )
    
    def procesar_pregunta(self, pregunta: str) -> ResultadoQuery:
        """
        Procesa una pregunta en lenguaje natural y devuelve los resultados.
        
        Args:
            pregunta: Pregunta del usuario
            
        Returns:
            ResultadoQuery con los datos
        """
        # Primero intentar encontrar una plantilla
        pregunta_lower = pregunta.lower()
        
        # Mapeo de palabras clave a plantillas
        if any(p in pregunta_lower for p in ['deuda', 'debe', 'deber', 'adeuda']):
            if 'cliente' in pregunta_lower or 'quien' in pregunta_lower:
                query = self.obtener_query_plantilla('cliente_mas_deuda')
                if query:
                    return self.ejecutar_query(query)
        
        if any(p in pregunta_lower for p in ['vencida', 'vencidas', 'atrasada']):
            query = self.obtener_query_plantilla('facturas_vencidas')
            if query:
                return self.ejecutar_query(query)
        
        if any(p in pregunta_lower for p in ['sin stock', 'agotado', 'sin existencia']):
            query = self.obtener_query_plantilla('productos_sin_stock')
            if query:
                return self.ejecutar_query(query)
        
        if 'venta' in pregunta_lower and 'hoy' in pregunta_lower:
            query = self.obtener_query_plantilla('ventas_hoy')
            if query:
                return self.ejecutar_query(query)
        
        if 'pos' in pregunta_lower and 'hoy' in pregunta_lower:
            query = self.obtener_query_plantilla('pos_hoy')
            if query:
                return self.ejecutar_query(query)
        
        # Si no hay plantilla, usar LLM
        query = self.generar_query_con_llm(pregunta)
        if query:
            return self.ejecutar_query(query)
        
        # Query por defecto
        return ResultadoQuery(
            query=QueryOdoo(
                modelo='sale.order',
                dominio=[],
                campos=['name'],
                descripcion='Query por defecto'
            ),
            datos=[],
            total=0,
            tiempo=0,
            exito=False,
            error="No se pudo generar un query para esta pregunta"
        )
    
    def interpretar_resultados(self, resultado: ResultadoQuery, pregunta: str) -> str:
        """
        Usa el LLM para interpretar los resultados y dar una respuesta natural.
        
        Args:
            resultado: Resultados del query
            pregunta: Pregunta original
            
        Returns:
            Respuesta en lenguaje natural
        """
        if not resultado.exito:
            return f"No pude obtener la información: {resultado.error}"
        
        if not resultado.datos:
            return "No encontré datos que coincidan con tu consulta."
        
        if not self.agente_llm:
            # Si no hay LLM, dar respuesta básica
            return f"Encontré {resultado.total} registros para '{resultado.query.descripcion}'"
        
        # Limitar datos para el prompt
        datos_muestra = resultado.datos[:10]
        
        prompt = f"""Analiza estos datos de Odoo y responde la pregunta del usuario de forma clara y concisa.

PREGUNTA: {pregunta}

DATOS ({resultado.total} registros encontrados):
{json.dumps(datos_muestra, default=str, indent=2)[:2000]}

Responde de forma natural, mencionando nombres y cifras relevantes. Si hay muchos datos, resume los principales.
"""
        
        try:
            respuesta = self.agente_llm.generar_raw(prompt)
            return respuesta or f"Encontré {resultado.total} registros."
        except Exception:
            return f"Encontré {resultado.total} registros para '{resultado.query.descripcion}'"
    
    def consulta_completa(self, pregunta: str) -> Tuple[str, List[Dict]]:
        """
        Proceso completo: genera query, ejecuta y responde.
        
        Args:
            pregunta: Pregunta del usuario
            
        Returns:
            Tuple (respuesta_texto, datos_raw)
        """
        resultado = self.procesar_pregunta(pregunta)
        respuesta = self.interpretar_resultados(resultado, pregunta)
        
        return respuesta, resultado.datos


# Singleton
_generador_global: Optional[GeneradorQueries] = None


def obtener_generador_queries() -> GeneradorQueries:
    """Obtiene la instancia global"""
    global _generador_global
    if _generador_global is None:
        _generador_global = GeneradorQueries()
    return _generador_global


__all__ = [
    'GeneradorQueries',
    'QueryOdoo',
    'ResultadoQuery',
    'obtener_generador_queries'
]
