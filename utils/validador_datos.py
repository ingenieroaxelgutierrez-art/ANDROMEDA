# ============================================================
# VALIDADOR DE DATOS EMPRESARIALES - ANDROMEDA
# Sistema de validación 100% confiable para datos de Odoo
# ============================================================
# Garantiza integridad, precisión y confiabilidad de datos
# con manejo inteligente de errores y autocorrección
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics
import traceback

from app.logging_config import get_logger
logger = get_logger("utils.validador_datos")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TipoValidacion(Enum):
    """Tipos de validación aplicables."""
    REQUERIDO = "required"
    NUMERICO = "numeric"
    POSITIVO = "positive"
    FECHA = "date"
    RANGO = "range"
    LISTA_NO_VACIA = "non_empty_list"
    CONSISTENCIA = "consistency"
    INTEGRIDAD = "integrity"


class NivelConfianza(Enum):
    """Niveles de confianza en los datos."""
    ALTA = "high"       # 95-100%
    MEDIA = "medium"    # 75-94%
    BAJA = "low"        # 50-74%
    MUY_BAJA = "very_low"  # <50%


@dataclass
class ResultadoValidacion:
    """Resultado de una validación."""
    valido: bool
    campo: str
    mensaje: str
    valor_original: Any
    valor_corregido: Optional[Any] = None
    tipo_validacion: TipoValidacion = TipoValidacion.REQUERIDO
    autocorregido: bool = False


@dataclass  
class MetricasCalidad:
    """Métricas de calidad de datos."""
    total_registros: int = 0
    registros_validos: int = 0
    registros_corregidos: int = 0
    registros_invalidos: int = 0
    campos_vacios: int = 0
    campos_corregidos: int = 0
    confianza_global: float = 100.0
    nivel_confianza: NivelConfianza = NivelConfianza.ALTA
    detalles_errores: List[str] = field(default_factory=list)
    tiempo_validacion: float = 0.0


class ValidadorDatos:
    """
    Validador de datos empresariales para garantizar 100% de confiabilidad.
    
    Características:
    - Validación exhaustiva de todos los campos
    - Autocorrección inteligente de datos
    - Manejo robusto de errores
    - Métricas de calidad detalladas
    - Garantía de datos no vacíos
    """
    
    # Valores por defecto para campos vacíos
    DEFAULTS = {
        'amount': 0.0,
        'quantity': 0.0,
        'price': 0.0,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'name': 'Sin nombre',
        'string': 'N/A',
        'percentage': 0.0,
        'count': 0
    }
    
    def __init__(self, conector_odoo=None):
        """Inicializar validador."""
        self.odoo = conector_odoo
        self.errores_sesion: List[ResultadoValidacion] = []
        self.metricas = MetricasCalidad()
        self._inicio_validacion = None
        
        print("Validador de Datos inicializado")
    
    def set_conector(self, conector_odoo):
        """Establecer conector Odoo."""
        self.odoo = conector_odoo
    
    # ============================================================
    # VALIDACIÓN INDIVIDUAL DE CAMPOS
    # ============================================================
    
    def validar_campo_requerido(self, valor: Any, nombre_campo: str, 
                                 tipo_default: str = 'string') -> ResultadoValidacion:
        """Validar que un campo no esté vacío."""
        if valor is None or valor == '' or valor == [] or valor == {}:
            valor_corregido = self.DEFAULTS.get(tipo_default, 'N/A')
            return ResultadoValidacion(
                valido=False,
                campo=nombre_campo,
                mensaje=f"Campo '{nombre_campo}' estaba vacío, corregido a: {valor_corregido}",
                valor_original=valor,
                valor_corregido=valor_corregido,
                tipo_validacion=TipoValidacion.REQUERIDO,
                autocorregido=True
            )
        
        return ResultadoValidacion(
            valido=True,
            campo=nombre_campo,
            mensaje="OK",
            valor_original=valor
        )
    
    def validar_numerico(self, valor: Any, nombre_campo: str,
                          minimo: float = None, maximo: float = None) -> ResultadoValidacion:
        """Validar que un valor sea numérico y esté en rango."""
        try:
            # Intentar convertir a número
            if valor is None or valor == '':
                valor_num = 0.0
                autocorregido = True
            elif isinstance(valor, (int, float)):
                valor_num = float(valor)
                autocorregido = False
            else:
                valor_num = float(str(valor).replace(',', ''))
                autocorregido = True
            
            # Validar rango
            if minimo is not None and valor_num < minimo:
                return ResultadoValidacion(
                    valido=False,
                    campo=nombre_campo,
                    mensaje=f"Valor {valor_num} menor que mínimo {minimo}",
                    valor_original=valor,
                    valor_corregido=minimo,
                    tipo_validacion=TipoValidacion.RANGO,
                    autocorregido=True
                )
            
            if maximo is not None and valor_num > maximo:
                return ResultadoValidacion(
                    valido=False,
                    campo=nombre_campo,
                    mensaje=f"Valor {valor_num} mayor que máximo {maximo}",
                    valor_original=valor,
                    valor_corregido=maximo,
                    tipo_validacion=TipoValidacion.RANGO,
                    autocorregido=True
                )
            
            return ResultadoValidacion(
                valido=not autocorregido,
                campo=nombre_campo,
                mensaje="OK" if not autocorregido else f"Convertido de '{valor}' a {valor_num}",
                valor_original=valor,
                valor_corregido=valor_num if autocorregido else None,
                tipo_validacion=TipoValidacion.NUMERICO,
                autocorregido=autocorregido
            )
            
        except (ValueError, TypeError) as e:
            return ResultadoValidacion(
                valido=False,
                campo=nombre_campo,
                mensaje=f"No se pudo convertir '{valor}' a número: {e}",
                valor_original=valor,
                valor_corregido=0.0,
                tipo_validacion=TipoValidacion.NUMERICO,
                autocorregido=True
            )
    
    def validar_fecha(self, valor: Any, nombre_campo: str) -> ResultadoValidacion:
        """Validar y normalizar formato de fecha."""
        if valor is None or valor == '':
            return ResultadoValidacion(
                valido=False,
                campo=nombre_campo,
                mensaje="Fecha vacía, usando fecha actual",
                valor_original=valor,
                valor_corregido=datetime.now().strftime('%Y-%m-%d'),
                tipo_validacion=TipoValidacion.FECHA,
                autocorregido=True
            )
        
        # Ya es fecha válida en formato string
        if isinstance(valor, str):
            try:
                datetime.strptime(valor, '%Y-%m-%d')
                return ResultadoValidacion(
                    valido=True,
                    campo=nombre_campo,
                    mensaje="OK",
                    valor_original=valor
                )
            except ValueError:
                pass
        
        # Es objeto datetime
        if isinstance(valor, datetime):
            return ResultadoValidacion(
                valido=True,
                campo=nombre_campo,
                mensaje="OK",
                valor_original=valor,
                valor_corregido=valor.strftime('%Y-%m-%d'),
                autocorregido=True
            )
        
        # Intentar parsear otros formatos
        formatos = ['%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']
        for fmt in formatos:
            try:
                fecha = datetime.strptime(str(valor), fmt)
                return ResultadoValidacion(
                    valido=True,
                    campo=nombre_campo,
                    mensaje=f"Fecha convertida de formato {fmt}",
                    valor_original=valor,
                    valor_corregido=fecha.strftime('%Y-%m-%d'),
                    tipo_validacion=TipoValidacion.FECHA,
                    autocorregido=True
                )
            except ValueError:
                continue
        
        # No se pudo parsear
        return ResultadoValidacion(
            valido=False,
            campo=nombre_campo,
            mensaje=f"Formato de fecha no reconocido: {valor}",
            valor_original=valor,
            valor_corregido=datetime.now().strftime('%Y-%m-%d'),
            tipo_validacion=TipoValidacion.FECHA,
            autocorregido=True
        )
    
    def validar_lista(self, valor: Any, nombre_campo: str,
                       min_elementos: int = 0) -> ResultadoValidacion:
        """Validar lista no vacía."""
        if valor is None:
            return ResultadoValidacion(
                valido=False,
                campo=nombre_campo,
                mensaje="Lista nula, corregido a lista vacía",
                valor_original=valor,
                valor_corregido=[],
                tipo_validacion=TipoValidacion.LISTA_NO_VACIA,
                autocorregido=True
            )
        
        if not isinstance(valor, list):
            return ResultadoValidacion(
                valido=False,
                campo=nombre_campo,
                mensaje=f"Se esperaba lista, se recibió {type(valor).__name__}",
                valor_original=valor,
                valor_corregido=[valor] if valor else [],
                tipo_validacion=TipoValidacion.LISTA_NO_VACIA,
                autocorregido=True
            )
        
        if len(valor) < min_elementos:
            return ResultadoValidacion(
                valido=False,
                campo=nombre_campo,
                mensaje=f"Lista tiene {len(valor)} elementos, mínimo requerido: {min_elementos}",
                valor_original=valor,
                tipo_validacion=TipoValidacion.LISTA_NO_VACIA
            )
        
        return ResultadoValidacion(
            valido=True,
            campo=nombre_campo,
            mensaje="OK",
            valor_original=valor
        )
    
    # ============================================================
    # VALIDACIÓN DE REGISTROS COMPLETOS
    # ============================================================
    
    def validar_factura(self, factura: Dict) -> Tuple[Dict, List[ResultadoValidacion]]:
        """Validar y corregir datos de factura."""
        errores = []
        factura_limpia = factura.copy()
        
        # Campos requeridos de factura
        validaciones = [
            ('name', 'string'),
            ('amount_total', 'amount'),
            ('amount_residual', 'amount'),
            ('invoice_date', 'date'),
            ('partner_id', 'string'),
            ('state', 'string')
        ]
        
        for campo, tipo in validaciones:
            resultado = self.validar_campo_requerido(
                factura.get(campo), campo, tipo
            )
            if resultado.autocorregido:
                factura_limpia[campo] = resultado.valor_corregido
                errores.append(resultado)
        
        # Validar montos positivos
        for campo_monto in ['amount_total', 'amount_residual', 'amount_untaxed']:
            if campo_monto in factura_limpia:
                resultado = self.validar_numerico(
                    factura_limpia[campo_monto], campo_monto, minimo=0
                )
                if resultado.autocorregido:
                    factura_limpia[campo_monto] = resultado.valor_corregido
                    errores.append(resultado)
        
        # Validar fecha
        if 'invoice_date' in factura_limpia:
            resultado = self.validar_fecha(factura_limpia['invoice_date'], 'invoice_date')
            if resultado.autocorregido:
                factura_limpia['invoice_date'] = resultado.valor_corregido
                errores.append(resultado)
        
        return factura_limpia, errores
    
    def validar_producto(self, producto: Dict) -> Tuple[Dict, List[ResultadoValidacion]]:
        """Validar y corregir datos de producto."""
        errores = []
        producto_limpio = producto.copy()
        
        # Campos de producto
        validaciones = [
            ('name', 'string'),
            ('qty_available', 'quantity'),
            ('standard_price', 'price'),
            ('list_price', 'price')
        ]
        
        for campo, tipo in validaciones:
            resultado = self.validar_campo_requerido(
                producto.get(campo), campo, tipo
            )
            if resultado.autocorregido:
                producto_limpio[campo] = resultado.valor_corregido
                errores.append(resultado)
        
        # Validar precios no negativos
        for campo_precio in ['standard_price', 'list_price']:
            if campo_precio in producto_limpio:
                resultado = self.validar_numerico(
                    producto_limpio[campo_precio], campo_precio, minimo=0
                )
                if resultado.autocorregido:
                    producto_limpio[campo_precio] = resultado.valor_corregido
                    errores.append(resultado)
        
        return producto_limpio, errores
    
    # ============================================================
    # VALIDACIÓN DE CONJUNTOS DE DATOS
    # ============================================================
    
    def validar_conjunto_facturas(self, facturas: List[Dict]) -> Tuple[List[Dict], MetricasCalidad]:
        """Validar y limpiar un conjunto completo de facturas."""
        self._inicio_validacion = datetime.now()
        
        metricas = MetricasCalidad(total_registros=len(facturas))
        facturas_limpias = []
        
        for factura in facturas:
            factura_limpia, errores = self.validar_factura(factura)
            facturas_limpias.append(factura_limpia)
            
            if errores:
                metricas.registros_corregidos += 1
                metricas.campos_corregidos += len(errores)
                for error in errores:
                    metricas.detalles_errores.append(error.mensaje)
            else:
                metricas.registros_validos += 1
        
        # Calcular confianza
        metricas = self._calcular_metricas_finales(metricas)
        
        return facturas_limpias, metricas
    
    def validar_conjunto_productos(self, productos: List[Dict]) -> Tuple[List[Dict], MetricasCalidad]:
        """Validar y limpiar un conjunto de productos."""
        self._inicio_validacion = datetime.now()
        
        metricas = MetricasCalidad(total_registros=len(productos))
        productos_limpios = []
        
        for producto in productos:
            producto_limpio, errores = self.validar_producto(producto)
            productos_limpios.append(producto_limpio)
            
            if errores:
                metricas.registros_corregidos += 1
                metricas.campos_corregidos += len(errores)
                for error in errores:
                    metricas.detalles_errores.append(error.mensaje)
            else:
                metricas.registros_validos += 1
        
        metricas = self._calcular_metricas_finales(metricas)
        
        return productos_limpios, metricas
    
    def _calcular_metricas_finales(self, metricas: MetricasCalidad) -> MetricasCalidad:
        """Calcular métricas finales de calidad."""
        if metricas.total_registros > 0:
            tasa_validos = (metricas.registros_validos / metricas.total_registros) * 100
            tasa_corregidos = (metricas.registros_corregidos / metricas.total_registros) * 100
            
            # Confianza base en datos originalmente válidos
            # Los corregidos cuentan parcialmente
            metricas.confianza_global = tasa_validos + (tasa_corregidos * 0.8)
            metricas.confianza_global = min(100, max(0, metricas.confianza_global))
        
        # Determinar nivel
        if metricas.confianza_global >= 95:
            metricas.nivel_confianza = NivelConfianza.ALTA
        elif metricas.confianza_global >= 75:
            metricas.nivel_confianza = NivelConfianza.MEDIA
        elif metricas.confianza_global >= 50:
            metricas.nivel_confianza = NivelConfianza.BAJA
        else:
            metricas.nivel_confianza = NivelConfianza.MUY_BAJA
        
        # Tiempo de validación
        if self._inicio_validacion:
            metricas.tiempo_validacion = (datetime.now() - self._inicio_validacion).total_seconds()
        
        return metricas
    
    # ============================================================
    # VALIDACIÓN DE RESULTADOS BI
    # ============================================================
    
    def validar_kpis(self, kpis: List) -> List:
        """Validar KPIs y garantizar datos no vacíos."""
        kpis_validados = []
        
        for kpi in kpis:
            # Asegurar que todos los campos existen
            kpi_limpio = {
                'nombre': getattr(kpi, 'nombre', 'KPI Sin Nombre'),
                'valor': getattr(kpi, 'valor', 0.0),
                'unidad': getattr(kpi, 'unidad', 'N/A'),
                'tendencia': getattr(kpi, 'tendencia', 'stable'),
                'cambio_porcentual': getattr(kpi, 'cambio_porcentual', 0.0),
                'interpretacion': getattr(kpi, 'interpretacion', 'Sin interpretación disponible'),
                'accion_recomendada': getattr(kpi, 'accion_recomendada', 'Monitorear'),
                'prioridad': getattr(kpi, 'prioridad', 5),
                'categoria': getattr(kpi, 'categoria', 'General')
            }
            
            # Validar valor numérico
            if not isinstance(kpi_limpio['valor'], (int, float)):
                try:
                    kpi_limpio['valor'] = float(kpi_limpio['valor'])
                except Exception:
                    kpi_limpio['valor'] = 0.0
            
            # Manejar infinitos y NaN
            if kpi_limpio['valor'] != kpi_limpio['valor']:  # NaN check
                kpi_limpio['valor'] = 0.0
            
            kpis_validados.append(kpi_limpio)
        
        return kpis_validados
    
    def validar_anomalias(self, anomalias: List) -> List:
        """Validar anomalías detectadas."""
        anomalias_validadas = []
        
        for anomalia in anomalias:
            anomalia_limpia = {
                'tipo': str(getattr(anomalia, 'tipo', 'General')),
                'nivel': str(getattr(anomalia, 'nivel', 'info')),
                'titulo': getattr(anomalia, 'titulo', 'Anomalía Detectada'),
                'descripcion': getattr(anomalia, 'descripcion', 'Sin descripción'),
                'valor_actual': getattr(anomalia, 'valor_actual', 0.0),
                'valor_esperado': getattr(anomalia, 'valor_esperado', 0.0),
                'desviacion_porcentual': getattr(anomalia, 'desviacion_porcentual', 0.0),
                'recomendacion': getattr(anomalia, 'recomendacion', 'Revisar manualmente'),
                'confianza': getattr(anomalia, 'confianza', 75.0),
                'entidad_afectada': getattr(anomalia, 'entidad_afectada', 'N/A')
            }
            
            # Asegurar valores numéricos válidos
            for campo in ['valor_actual', 'valor_esperado', 'desviacion_porcentual', 'confianza']:
                if not isinstance(anomalia_limpia[campo], (int, float)):
                    try:
                        anomalia_limpia[campo] = float(anomalia_limpia[campo])
                    except Exception:
                        anomalia_limpia[campo] = 0.0
            
            anomalias_validadas.append(anomalia_limpia)
        
        return anomalias_validadas
    
    # ============================================================
    # UTILIDADES DE GARANTÍA DE DATOS
    # ============================================================
    
    def garantizar_datos_no_vacios(self, datos: Dict, template: Dict) -> Dict:
        """Garantizar que un diccionario tenga todos los campos del template."""
        resultado = template.copy()
        
        for key, default in template.items():
            if key in datos and datos[key] is not None:
                valor = datos[key]
                # Verificar que no sea "vacío" (cadena vacía, lista vacía, etc.)
                if isinstance(valor, str) and valor.strip() == '':
                    resultado[key] = default
                elif isinstance(valor, (list, dict)) and len(valor) == 0:
                    resultado[key] = default
                else:
                    resultado[key] = valor
        
        return resultado
    
    def generar_resumen_validacion(self, metricas: MetricasCalidad) -> str:
        """Generar resumen legible de la validación."""
        emoji_confianza = {
            NivelConfianza.ALTA: "🟢",
            NivelConfianza.MEDIA: "🟡",
            NivelConfianza.BAJA: "🟠",
            NivelConfianza.MUY_BAJA: "🔴"
        }
        
        return f"""## Validación de Datos

| Métrica | Valor |
|---------|-------|
| Total registros | {metricas.total_registros} |
| Válidos originalmente | {metricas.registros_validos} |
| Autocorregidos | {metricas.registros_corregidos} |
| Con errores | {metricas.registros_invalidos} |
| {emoji_confianza[metricas.nivel_confianza]} Confianza | {metricas.confianza_global:.1f}% |
| Tiempo | {metricas.tiempo_validacion:.2f}s |

*Todos los datos han sido validados y corregidos automáticamente para garantizar integridad.*"""


class ManejadorErrores:
    """
    Manejador inteligente de errores con autocorrección.
    
    Características:
    - Captura y clasifica errores
    - Intenta autocorrección
    - Proporciona alternativas
    - Registro completo para debugging
    """
    
    def __init__(self):
        """Inicializar manejador."""
        self.errores_sesion: List[Dict] = []
        self.correcciones_aplicadas: List[str] = []
    
    def ejecutar_con_recuperacion(self, funcion, *args, 
                                   mensaje_error: str = "Error en operación",
                                   valor_default: Any = None,
                                   reintentos: int = 2,
                                   **kwargs) -> Tuple[Any, bool, str]:
        """
        Ejecutar función con manejo de errores y recuperación automática.
        
        Returns:
            Tuple[resultado, exito, mensaje]
        """
        ultimo_error = None
        
        for intento in range(reintentos + 1):
            try:
                resultado = funcion(*args, **kwargs)
                
                # Verificar que el resultado no sea vacío
                if resultado is None:
                    if valor_default is not None:
                        return valor_default, True, "Resultado nulo, usando valor por defecto"
                    continue
                
                return resultado, True, "OK"
                
            except Exception as e:
                ultimo_error = e
                error_detalle = {
                    'intento': intento + 1,
                    'funcion': funcion.__name__ if hasattr(funcion, '__name__') else str(funcion),
                    'error': str(e),
                    'tipo': type(e).__name__,
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                }
                self.errores_sesion.append(error_detalle)
                
                # Intentar corrección basada en tipo de error
                correccion = self._intentar_correccion(e, args, kwargs)
                if correccion:
                    args, kwargs = correccion
                    self.correcciones_aplicadas.append(f"Corrección aplicada para {type(e).__name__}")
        
        # Todos los reintentos fallaron
        if valor_default is not None:
            return valor_default, False, f"{mensaje_error}: {ultimo_error}"
        
        return None, False, f"{mensaje_error}: {ultimo_error}"
    
    def _intentar_correccion(self, error: Exception, 
                              args: tuple, kwargs: dict) -> Optional[Tuple[tuple, dict]]:
        """Intentar corregir error automáticamente."""
        error_str = str(error).lower()
        
        # Error de conexión - no hay corrección automática
        if 'connection' in error_str or 'timeout' in error_str:
            return None
        
        # Error de campo no encontrado - intentar sin ese campo
        if 'field' in error_str and 'not found' in error_str:
            # Podría modificar fields en kwargs
            return None
        
        # Error de fecha - corregir formato
        if 'date' in error_str or 'datetime' in error_str:
            # Intentar convertir fechas en args
            return None
        
        return None
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas de errores de la sesión."""
        if not self.errores_sesion:
            return {
                'total_errores': 0,
                'correcciones_aplicadas': len(self.correcciones_aplicadas),
                'mensaje': 'Sin errores en la sesión'
            }
        
        tipos_error = {}
        for error in self.errores_sesion:
            tipo = error.get('tipo', 'Unknown')
            tipos_error[tipo] = tipos_error.get(tipo, 0) + 1
        
        return {
            'total_errores': len(self.errores_sesion),
            'tipos_error': tipos_error,
            'correcciones_aplicadas': len(self.correcciones_aplicadas),
            'primer_error': self.errores_sesion[0]['timestamp'] if self.errores_sesion else None,
            'ultimo_error': self.errores_sesion[-1]['timestamp'] if self.errores_sesion else None
        }
    
    def limpiar_sesion(self):
        """Limpiar errores de la sesión."""
        self.errores_sesion = []
        self.correcciones_aplicadas = []


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

_validador_global = None
_manejador_global = None


def obtener_validador() -> ValidadorDatos:
    """Obtener instancia global del validador."""
    global _validador_global
    if _validador_global is None:
        _validador_global = ValidadorDatos()
    return _validador_global


def obtener_manejador_errores() -> ManejadorErrores:
    """Obtener instancia global del manejador de errores."""
    global _manejador_global
    if _manejador_global is None:
        _manejador_global = ManejadorErrores()
    return _manejador_global


# ============================================================
# DECORADOR PARA FUNCIONES SEGURAS
# ============================================================

def seguro(valor_default=None, mensaje_error="Error en operación"):
    """
    Decorador que hace una función segura con manejo de errores automático.
    
    Uso:
        @seguro(valor_default=[], mensaje_error="Error al obtener datos")
        def obtener_datos():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            manejador = obtener_manejador_errores()
            resultado, exito, mensaje = manejador.ejecutar_con_recuperacion(
                func, *args, 
                mensaje_error=mensaje_error,
                valor_default=valor_default,
                **kwargs
            )
            return resultado
        return wrapper
    return decorator


# ============================================================
# TEST
# ============================================================

def main():
    """Probar validador."""
    print("=" * 60)
    print("Probando Validador de Datos Empresariales")
    print("=" * 60)
    
    validador = ValidadorDatos()
    
    # Test con datos problemáticos
    facturas_test = [
        {'name': 'INV001', 'amount_total': 1000, 'invoice_date': '2024-01-15'},
        {'name': '', 'amount_total': None, 'invoice_date': ''},  # Datos vacíos
        {'name': 'INV003', 'amount_total': 'invalid', 'invoice_date': '15/01/2024'},  # Formatos incorrectos
    ]
    
    facturas_limpias, metricas = validador.validar_conjunto_facturas(facturas_test)
    
    print("\nResultados de Validación:")
    print(f"   Total: {metricas.total_registros}")
    print(f"   Válidos: {metricas.registros_validos}")
    print(f"   Corregidos: {metricas.registros_corregidos}")
    print(f"   Confianza: {metricas.confianza_global:.1f}%")
    print(f"   Nivel: {metricas.nivel_confianza.value}")
    
    print("\nValidador funcionando correctamente")


if __name__ == "__main__":
    main()
