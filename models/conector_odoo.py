# ============================================================
# CONECTOR ODOO PRO - Conexión y Consultas Inteligentes
# ============================================================

import odoorpc
import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

from dotenv import load_dotenv

from app.logging_config import get_logger
logger = get_logger("models.conector_odoo")

load_dotenv()

# Silenciar logging de odoorpc que expone credenciales en DEBUG
logging.getLogger('odoorpc.rpc.jsonrpclib').setLevel(logging.WARNING)
logging.getLogger('odoorpc').setLevel(logging.WARNING)

from services.security.auditoria_queries import AuditoriaQueries
from utils.seguridad import firmar_prompt
from utils.validador_queries import validar_query, QueryNoPermitida

@dataclass
class ConfiguracionOdoo:
    """Configuración de conexión a Odoo."""
    url: str
    db: str
    usuario: str
    password: str
    
    @classmethod
    def desde_json(cls, ruta: str) -> 'ConfiguracionOdoo':
        """Carga configuración desde archivo JSON."""
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(
            url=data.get('url', ''),
            db=data.get('db', ''),
            usuario=data.get('usuario', ''),
            password=data.get('password', '')
        )
    
    @classmethod
    def default(cls) -> 'ConfiguracionOdoo':
        """Carga configuración desde variables de entorno."""
        return cls(
            url=os.getenv('ODOO_URL', ''),
            db=os.getenv('ODOO_DB', ''),
            usuario=os.getenv('ODOO_USER', ''),
            password=os.getenv('ODOO_PASSWORD', '')
        )


class ConectorOdoo:
    """
    Conector profesional para Odoo con cache y optimizaciones.
    """
    
    def __init__(self, config: ConfiguracionOdoo = None, usuario: str = "system"):
        """Inicializa el conector."""
        self.config = config or self._cargar_config()
        self.odoo: Optional[odoorpc.ODOO] = None
        self.conectado = False
        
        # Cache de metadatos
        self._cache_modelos: Dict[str, Dict] = {}
        self._cache_campos: Dict[str, Dict] = {}
        
        # Modelos de uso frecuente
        self.modelos_principales = {
            'ventas': {
                'modelo': 'sale.order',
                'campos_default': ['name', 'partner_id', 'date_order', 'amount_total', 'state'],
                'campo_fecha': 'date_order',
                'campo_monto': 'amount_total',
            },
            'ventas_lineas': {
                'modelo': 'sale.order.line',
                'campos_default': ['order_id', 'product_id', 'product_uom_qty', 'price_unit', 'price_subtotal'],
            },
            'pos': {
                'modelo': 'pos.order',
                'campos_default': ['name', 'partner_id', 'date_order', 'amount_total', 'state', 'session_id'],
                'campo_fecha': 'date_order',
                'campo_monto': 'amount_total',
            },
            'pos_lineas': {
                'modelo': 'pos.order.line',
                'campos_default': ['order_id', 'product_id', 'qty', 'price_unit', 'price_subtotal'],
            },
            'productos': {
                'modelo': 'product.product',
                'campos_default': ['name', 'default_code', 'list_price', 'qty_available', 'categ_id'],
            },
            'plantillas': {
                'modelo': 'product.template',
                'campos_default': ['name', 'default_code', 'list_price', 'type', 'categ_id'],
            },
            'stock': {
                'modelo': 'stock.quant',
                'campos_default': ['product_id', 'location_id', 'quantity', 'reserved_quantity'],
            },
            'clientes': {
                'modelo': 'res.partner',
                'campos_default': ['name', 'email', 'phone', 'city', 'customer_rank'],
            },
            'facturas': {
                'modelo': 'account.move',
                'campos_default': ['name', 'partner_id', 'invoice_date', 'amount_total', 'state', 'move_type'],
                'campo_fecha': 'invoice_date',
                'campo_monto': 'amount_total',
            },
            'compras': {
                'modelo': 'purchase.order',
                'campos_default': ['name', 'partner_id', 'date_order', 'amount_total', 'state'],
                'campo_fecha': 'date_order',
            },
            'empleados': {
                'modelo': 'hr.employee',
                'campos_default': ['name', 'job_id', 'department_id', 'work_email'],
            },
        }
        # Usuario para auditoría y trazabilidad
        self.usuario = usuario
        # Inicializar auditoría de queries (fallback seguro si falla)
        try:
            self.auditoria_queries = AuditoriaQueries()
        except Exception as e:
            logger.error(f"Error inicializando AuditoriaQueries: {e}")
            class _NoOpAuditoria:
                def registrar_query(self, *args, **kwargs):
                    return None
            self.auditoria_queries = _NoOpAuditoria()
    
    def _cargar_config(self) -> ConfiguracionOdoo:
        """Carga la configuración desde archivo o usa default."""
        rutas_posibles = [
            os.path.join(os.path.dirname(__file__), '..', 'ANALISISTICKETS', 'odoo_config.json'),
            os.path.join(os.path.dirname(__file__), 'config.json'),
            'odoo_config.json',
        ]
        
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                try:
                    return ConfiguracionOdoo.desde_json(ruta)
                except Exception:
                    continue
        
        return ConfiguracionOdoo.default()
    
    def conectar(self) -> Tuple[bool, str]:
        """
        Establece conexión con Odoo.
        
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            # Parsear URL
            url = self.config.url
            host = url.replace('https://', '').replace('http://', '').split(':')[0]
            port = 443 if 'https' in url else 80
            protocol = 'jsonrpc+ssl' if 'https' in url else 'jsonrpc'
            
            self.odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
            self.odoo.login(
                self.config.db,
                self.config.usuario,
                self.config.password
            )
            
            self.conectado = True
            return True, f"Conectado a {host} como {self.config.usuario}"
            
        except Exception as e:
            self.conectado = False
            return False, f"Error de conexión: {str(e)}"
    
    def desconectar(self):
        """Cierra la conexión."""
        self.odoo = None
        self.conectado = False
    
    def _verificar_conexion(self) -> bool:
        """Verifica que hay conexión activa."""
        if not self.conectado or not self.odoo:
            print("No hay conexión activa. Conectando...")
            exito, msg = self.conectar()
            print(msg)
            return exito
        return True
    
    # ========================================
    # MÉTODOS DE CONSULTA
    # ========================================
    
    def contar(self, modelo: str, filtro: List = None) -> int:
        """Cuenta registros de un modelo."""
        if not self._verificar_conexion():
            return 0
        
        try:
            return self.odoo.env[modelo].search_count(filtro or [])
        except Exception as e:
            logger.error(f"Error contando {modelo}: {e}")
            return 0
    
    def buscar(self, modelo: str, filtro: List = None, 
               campos: List[str] = None, limite: int = 100,
               orden: str = None, hash_prompt: str = None, prompt: str = None) -> pd.DataFrame:
        """
        Busca registros en un modelo.
        
        Args:
            modelo: Nombre técnico del modelo
            filtro: Dominio de búsqueda Odoo
            campos: Campos a obtener
            limite: Máximo de registros
            orden: Campo de ordenamiento
            hash_prompt: Hash de prompt (opcional)
            prompt: Prompt de búsqueda (opcional)
        
        Returns:
            DataFrame con los resultados
        """
        if not self._verificar_conexion():
            return pd.DataFrame()
        
        try:
            inicio = datetime.utcnow()
            Model = self.odoo.env[modelo]
            
            # Obtener campos por defecto si no se especifican
            if campos is None:
                info = self.modelos_principales.get(modelo)
                if info:
                    campos = info.get('campos_default', ['name'])
                else:
                    campos = ['name', 'id']
            
            # Verificar que los campos existen
            campos_validos = self._filtrar_campos_validos(modelo, campos)
            
            # Buscar IDs
            kwargs = {'limit': limite}
            if orden:
                kwargs['order'] = orden
            
            ids = Model.search(filtro or [], **kwargs)
            
            if not ids:
                return pd.DataFrame()
            
            # Leer datos
            datos = Model.read(ids, campos_validos)
            df = pd.DataFrame(datos)
            duracion = int((datetime.utcnow() - inicio).total_seconds() * 1000)
            self.auditoria_queries.registrar_query(
                usuario=self.usuario,
                modelo_odoo=modelo,
                filtros=filtro or [],
                campos=campos_validos,
                registros_retornados=len(df),
                duracion_ms=duracion,
                hash_prompt=hash_prompt,
                nivel="INFO"
            )
            return df
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return pd.DataFrame()
    
    def buscar_leer(self, modelo: str, filtro: List = None, 
                    campos: List[str] = None, limite: int = 100,
                    orden: str = None, hash_prompt: str = None, prompt: str = None) -> List[Dict]:
        """
        Busca registros y retorna lista de diccionarios (sin DataFrame).
        
        Args:
            modelo: Nombre técnico del modelo
            filtro: Dominio de búsqueda Odoo
            campos: Campos a obtener
            limite: Máximo de registros
            orden: Campo de ordenamiento
            hash_prompt: Hash de prompt (opcional)
            prompt: Prompt de búsqueda (opcional)
        
        Returns:
            Lista de diccionarios con los resultados
        """
        if not self._verificar_conexion():
            return []
        
        try:
            inicio = datetime.utcnow()
            Model = self.odoo.env[modelo]
            
            # Obtener campos por defecto si no se especifican
            if campos is None:
                info = self.modelos_principales.get(modelo)
                if info:
                    campos = info.get('campos_default', ['name'])
                else:
                    campos = ['name', 'id']
            
            # Verificar que los campos existen
            campos_validos = self._filtrar_campos_validos(modelo, campos)
            
            # Buscar IDs
            kwargs = {'limit': limite}
            if orden:
                kwargs['order'] = orden
            
            ids = Model.search(filtro or [], **kwargs)
            
            if not ids:
                return []
            
            # Leer datos en lotes para evitar "Expected singleton" en campos computados
            BATCH_SIZE = 200
            datos = []
            for i in range(0, len(ids), BATCH_SIZE):
                lote_ids = ids[i:i + BATCH_SIZE]
                try:
                    datos.extend(Model.read(lote_ids, campos_validos))
                except Exception as e_lote:
                    if 'Expected singleton' in str(e_lote):
                        # Fallback: leer uno por uno para registros problemáticos
                        for rid in lote_ids:
                            try:
                                datos.extend(Model.read([rid], campos_validos))
                            except Exception:
                                pass  # Omitir registros con error de campo computado
                    else:
                        raise
            
            # Convertir frozendict/tuplas inmutables de Odoo a tipos serializables
            datos_limpios = []
            for registro in datos:
                reg_limpio = {}
                for k, v in registro.items():
                    if hasattr(v, 'items'):  # frozendict u otro mapping
                        reg_limpio[k] = dict(v)
                    elif isinstance(v, (list, tuple)):
                        reg_limpio[k] = [dict(item) if hasattr(item, 'items') else item for item in v]
                    else:
                        reg_limpio[k] = v
                datos_limpios.append(reg_limpio)
            
            if hash_prompt is None and prompt:
                hash_prompt = firmar_prompt(prompt)
            duracion = int((datetime.utcnow() - inicio).total_seconds() * 1000)
            self.auditoria_queries.registrar_query(
                usuario=self.usuario,
                modelo_odoo=modelo,
                filtros=filtro or [],
                campos=campos_validos,
                registros_retornados=len(datos_limpios),
                duracion_ms=duracion,
                hash_prompt=hash_prompt,
                nivel="INFO"
            )
            return datos_limpios
            
        except Exception as e:
            logger.error(f"Error en buscar_leer: {e}")
            return []
    
    def _filtrar_campos_validos(self, modelo: str, campos: List[str]) -> List[str]:
        """Filtra campos que existen en el modelo."""
        if modelo not in self._cache_campos:
            try:
                self._cache_campos[modelo] = self.odoo.env[modelo].fields_get()
            except Exception:
                return campos
        
        campos_existentes = self._cache_campos[modelo]
        return [c for c in campos if c in campos_existentes]

    def search_read(self, modelo: str, dominio: list = None,
                    campos: list = None, limite: int = 0,
                    orden: str = None, limit: int = None, hash_prompt: str = None, prompt: str = None) -> list:
        """Ejecuta search_read en un modelo Odoo.
        
        Wrapper sobre odoorpc search_read para encapsular
        el acceso directo a self.odoo.env (ARQ-003).
        
        Acepta tanto 'limite' (español) como 'limit' (inglés).
        
        Returns:
            Lista de diccionarios con los registros encontrados.
        """
        if not self._verificar_conexion():
            return []
        try:
            Model = self.odoo.env[modelo]
            kwargs = {}
            if campos:
                kwargs['fields'] = campos
            real_limite = limit if limit is not None else limite
            if real_limite:
                kwargs['limit'] = real_limite
            if orden:
                kwargs['order'] = orden
            inicio = datetime.utcnow()
            resultados = Model.search_read(dominio or [], **kwargs)
            duracion = int((datetime.utcnow() - inicio).total_seconds() * 1000)
            self.auditoria_queries.registrar_query(
                usuario=self.usuario,
                modelo_odoo=modelo,
                filtros=dominio or [],
                campos=campos or [],
                registros_retornados=len(resultados),
                duracion_ms=duracion,
                hash_prompt=hash_prompt,
                nivel="INFO"
            )
            return resultados
        except Exception as e:
            logger.error(f"Error en search_read({modelo}): {e}")
            return []
    
    def obtener_campos(self, modelo: str) -> Dict:
        """Obtiene los campos de un modelo con descripciones."""
        if not self._verificar_conexion():
            return {}
        
        if modelo in self._cache_campos:
            return self._cache_campos[modelo]
        
        try:
            campos = self.odoo.env[modelo].fields_get()
            self._cache_campos[modelo] = campos
            return campos
        except Exception as e:
            logger.error(f"Error obteniendo campos de {modelo}: {e}")
            return {}
    
    def listar_modelos(self, filtro: str = None, limite: int = 50) -> List[Dict]:
        """Lista los modelos disponibles."""
        if not self._verificar_conexion():
            return []
        
        try:
            IrModel = self.odoo.env['ir.model']
            domain = []
            
            if filtro:
                domain = ['|', 
                    ('model', 'ilike', filtro),
                    ('name', 'ilike', filtro)
                ]
            
            ids = IrModel.search(domain, limit=limite)
            return IrModel.read(ids, ['model', 'name', 'info'])
            
        except Exception as e:
            logger.error(f"Error listando modelos: {e}")
            return []
    
    # ========================================
    # CONSULTAS ESPECÍFICAS DE NEGOCIO
    # ========================================
    
    def ventas_periodo(self, fecha_inicio: str = None, fecha_fin: str = None,
                       tienda: str = None) -> pd.DataFrame:
        """
        Obtiene ventas de un período específico.
        
        Args:
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
            tienda: Filtro por tienda (opcional)
        """
        filtro = []
        
        if fecha_inicio:
            filtro.append(('date_order', '>=', f'{fecha_inicio} 00:00:00'))
        if fecha_fin:
            filtro.append(('date_order', '<=', f'{fecha_fin} 23:59:59'))
        
        campos = ['name', 'partner_id', 'date_order', 'amount_total', 
                  'amount_untaxed', 'state', 'user_id']
        
        df = self.buscar('sale.order', filtro, campos, limite=5000, 
                        orden='date_order desc')
        
        return df
    
    def ventas_hoy(self) -> pd.DataFrame:
        """Ventas del día actual."""
        hoy = datetime.now().strftime('%Y-%m-%d')
        return self.ventas_periodo(hoy, hoy)
    
    def ventas_mes_actual(self) -> pd.DataFrame:
        """Ventas del mes actual."""
        hoy = datetime.now()
        inicio_mes = hoy.replace(day=1).strftime('%Y-%m-%d')
        fin_mes = hoy.strftime('%Y-%m-%d')
        return self.ventas_periodo(inicio_mes, fin_mes)
    
    def tickets_pos(self, fecha_inicio: str = None, fecha_fin: str = None,
                    sucursal: str = None) -> pd.DataFrame:
        """Obtiene tickets de punto de venta."""
        filtro = []
        
        if fecha_inicio:
            filtro.append(('date_order', '>=', f'{fecha_inicio} 00:00:00'))
        if fecha_fin:
            filtro.append(('date_order', '<=', f'{fecha_fin} 23:59:59'))
        
        campos = ['name', 'partner_id', 'date_order', 'amount_total', 
                  'state', 'session_id', 'pos_reference']
        
        return self.buscar('pos.order', filtro, campos, limite=5000,
                          orden='date_order desc')
    
    def stock_disponible(self, producto: str = None, 
                         ubicacion: str = None) -> pd.DataFrame:
        """Obtiene stock disponible."""
        filtro = [('quantity', '>', 0)]
        
        if producto:
            filtro.append(('product_id', 'ilike', producto))
        
        campos = ['product_id', 'location_id', 'quantity', 'reserved_quantity']
        
        return self.buscar('stock.quant', filtro, campos, limite=1000)
    
    def clientes_activos(self, limite: int = 100) -> pd.DataFrame:
        """Lista clientes con compras."""
        filtro = [('customer_rank', '>', 0)]
        campos = ['name', 'email', 'phone', 'city', 'country_id', 
                  'customer_rank', 'create_date']
        
        return self.buscar('res.partner', filtro, campos, limite, 
                          orden='customer_rank desc')
    
    def productos_mas_vendidos(self, fecha_inicio: str = None, 
                               limite: int = 20) -> pd.DataFrame:
        """
        Obtiene los productos más vendidos.
        Nota: Requiere agregar lógica de agrupación.
        """
        filtro = []
        if fecha_inicio:
            filtro.append(('order_id.date_order', '>=', fecha_inicio))
        
        # Obtener líneas de venta
        campos = ['product_id', 'product_uom_qty', 'price_subtotal']
        
        df = self.buscar('sale.order.line', filtro, campos, limite=5000)
        
        if df.empty:
            return df
        
        # Procesar product_id que viene como [id, name]
        if 'product_id' in df.columns:
            df['producto_nombre'] = df['product_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else str(x)
            )
            
            # Agrupar por producto
            resumen = df.groupby('producto_nombre').agg({
                'product_uom_qty': 'sum',
                'price_subtotal': 'sum'
            }).reset_index()
            
            resumen.columns = ['producto', 'cantidad_vendida', 'total_vendido']
            resumen = resumen.sort_values('cantidad_vendida', ascending=False)
            
            return resumen.head(limite)
        
        return df
    
    # ========================================
    # ESTADÍSTICAS Y RESUMEN
    # ========================================
    
    def resumen_general(self) -> Dict:
        """Genera un resumen completo del sistema."""
        if not self._verificar_conexion():
            return {}
        
        resumen = {
            'fecha_consulta': datetime.now().isoformat(),
            'conexion': {
                'servidor': self.config.url,
                'base_datos': self.config.db,
                'usuario': self.config.usuario
            },
            'contadores': {},
            'ventas_hoy': {},
            'ventas_mes': {}
        }
        
        # Contar registros principales
        modelos_contar = [
            ('res.partner', 'contactos', []),
            ('product.product', 'productos', []),
            ('sale.order', 'ordenes_venta', []),
            ('purchase.order', 'ordenes_compra', []),
            ('pos.order', 'tickets_pos', []),
            ('stock.quant', 'registros_stock', [('quantity', '>', 0)]),
        ]
        
        for modelo, clave, filtro in modelos_contar:
            try:
                resumen['contadores'][clave] = self.contar(modelo, filtro)
            except Exception:
                resumen['contadores'][clave] = 0
        
        # Ventas de hoy
        try:
            hoy = datetime.now().strftime('%Y-%m-%d')
            ventas_hoy = self.ventas_periodo(hoy, hoy)
            resumen['ventas_hoy'] = {
                'cantidad': len(ventas_hoy),
                'total': ventas_hoy['amount_total'].sum() if not ventas_hoy.empty else 0
            }
        except Exception:
            resumen['ventas_hoy'] = {'cantidad': 0, 'total': 0}
        
        # Ventas del mes
        try:
            hoy = datetime.now()
            inicio_mes = hoy.replace(day=1).strftime('%Y-%m-%d')
            ventas_mes = self.ventas_periodo(inicio_mes)
            resumen['ventas_mes'] = {
                'cantidad': len(ventas_mes),
                'total': ventas_mes['amount_total'].sum() if not ventas_mes.empty else 0
            }
        except Exception:
            resumen['ventas_mes'] = {'cantidad': 0, 'total': 0}
        
        return resumen


# ============================================================
# PRUEBAS
# ============================================================

if __name__ == "__main__":
    print("Probando Conector Odoo...")
    print("=" * 60)
    
    conector = ConectorOdoo()
    exito, msg = conector.conectar()
    print(msg)
    
    if exito:
        print("\nGenerando resumen...")
        resumen = conector.resumen_general()
        
        print(f"\nESTADÍSTICAS:")
        for clave, valor in resumen['contadores'].items():
            print(f"   • {clave}: {valor:,}")
        
        print(f"\nVENTAS HOY: {resumen['ventas_hoy']['cantidad']} ordenes, ${resumen['ventas_hoy']['total']:,.2f}")
        print(f"VENTAS MES: {resumen['ventas_mes']['cantidad']} ordenes, ${resumen['ventas_mes']['total']:,.2f}")
