# ============================================================
# ODOO BOT PRO - Agente IA Principal
# ============================================================
# Integra NLP, Conexión Odoo y Generación de Reportes
# Sin APIs externas - 100% local y gratuito
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from dataclasses import dataclass, field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Constantes de sugerencias frecuentes
SUGERENCIA_VER_VENTAS = "Ver ventas"
SUGERENCIA_GENERAR_REPORTE = "Generar reporte"
_MODEL_PRODUCT = 'product.product'
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importar módulos del bot
from services.nlp.motor_nlp import MotorNLP, IntencionDetectada, EntidadExtraida
from models.conector_odoo import ConectorOdoo
from app.config import ConfiguracionOdoo
from views.generador_reportes import GeneradorReportes

from app.logging_config import get_logger
logger = get_logger("core.bot_principal")


@dataclass
class RespuestaBot:
    """Respuesta estructurada del bot."""
    mensaje: str
    tipo: str = "texto"  # texto, tabla, reporte, error, ayuda
    datos: Optional[pd.DataFrame] = None
    archivo: Optional[str] = None
    sugerencias: List[str] = field(default_factory=list)
    confianza: float = 1.0


@dataclass
class ContextoConversacion:
    """Mantiene el contexto de la conversación."""
    ultimo_modelo: Optional[str] = None
    ultima_consulta: Optional[str] = None
    ultimos_datos: Optional[pd.DataFrame] = None
    filtros_activos: Dict = field(default_factory=dict)
    historial: List[Dict] = field(default_factory=list)


class OdooBotPro:
    """
    Agente IA profesional para Odoo.
    
    Características:
    - Procesamiento de lenguaje natural (NLP local)
    - Consultas inteligentes a Odoo
    - Generación de reportes (Excel, PDF, HTML)
    - Sin dependencias de APIs externas
    """
    
    VERSION = "1.0.0"
    NOMBRE = "ANDROMEDA"
    
    def __init__(self, config: ConfiguracionOdoo = None, 
                 modo_verbose: bool = False):
        """
        Inicializa el bot.
        
        Args:
            config: Configuración de conexión a Odoo
            modo_verbose: Mostrar información de debug
        """
        self.verbose = modo_verbose
        self.conectado = False
        
        # Inicializar componentes
        print(f"Inicializando {self.NOMBRE} v{self.VERSION}...")
        
        self.nlp = MotorNLP(usar_spacy=True, usar_embeddings=False)
        self.odoo = ConectorOdoo(config)
        self.reportes = GeneradorReportes()
        
        # Contexto de conversación
        self.contexto = ContextoConversacion()
        
        # Mapeo de intenciones a handlers
        self.handlers = {
            'consultar_ventas': self._handle_ventas,
            'consultar_inventario': self._handle_inventario,
            'consultar_clientes': self._handle_clientes,
            'consultar_productos': self._handle_productos,
            'consultar_pos': self._handle_pos,
            'describir_modelo': self._handle_describir,
            'listar_modelos': self._handle_listar_modelos,
            'buscar_campo': self._handle_buscar_campo,
            'generar_reporte': self._handle_reporte,
            'resumen_sistema': self._handle_resumen,
            'comparar': self._handle_comparar,
            'ayuda': self._handle_ayuda,
            'saludo': self._handle_saludo,
            'desconocido': self._handle_desconocido,
        }
        
        # Respuestas predefinidas
        self.respuestas = {
            'saludo': [
                "¡Hola! Soy tu asistente para Odoo. ¿En qué puedo ayudarte?",
                "¡Bienvenido! Estoy listo para consultar datos de Odoo.",
                "¡Hola! Puedo ayudarte con ventas, inventario, clientes y más.",
            ],
            'no_entiendo': [
                "No estoy seguro de entender tu consulta. ¿Podrías reformularla?",
                "Disculpa, no capté eso. ¿Puedes ser más específico?",
            ],
            'sin_datos': [
                "No encontré datos con esos criterios.",
                "La búsqueda no arrojó resultados.",
            ],
            'error_conexion': [
                "No puedo conectar con Odoo. Verifica la configuración.",
            ],
        }
    
    def conectar(self) -> Tuple[bool, str]:
        """Conecta con Odoo."""
        exito, mensaje = self.odoo.conectar()
        self.conectado = exito
        return exito, mensaje
    
    def procesar(self, texto: str) -> RespuestaBot:
        """
        Procesa una entrada del usuario y genera una respuesta.
        
        Args:
            texto: Texto de entrada del usuario
        
        Returns:
            RespuestaBot con la respuesta estructurada
        """
        # Verificar conexión
        if not self.conectado:
            self.conectar()
        
        # Guardar en historial
        self.contexto.historial.append({
            'tipo': 'usuario',
            'texto': texto,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analizar con NLP
        intencion = self.nlp.detectar_intencion(texto)
        
        if self.verbose:
            print(f"[DEBUG] Intención: {intencion.nombre} ({intencion.confianza:.2f})")
            print(f"[DEBUG] Entidades: {[(e.tipo, e.valor) for e in intencion.entidades]}")
            print(f"[DEBUG] Parámetros: {intencion.parametros}")
        
        # Ejecutar handler correspondiente
        handler = self.handlers.get(intencion.nombre, self._handle_desconocido)
        respuesta = handler(texto, intencion)
        
        # Guardar respuesta en historial
        self.contexto.historial.append({
            'tipo': 'bot',
            'texto': respuesta.mensaje,
            'timestamp': datetime.now().isoformat()
        })
        
        return respuesta
    
    # ========================================
    # HANDLERS DE INTENCIONES
    # ========================================
    
    def _handle_ventas(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja consultas de ventas."""
        params = intencion.parametros
        
        # Determinar período
        fecha_inicio = None
        fecha_fin = None
        
        if 'fecha_inicio' in params:
            fecha_val = params['fecha_inicio']
            if fecha_val == 'mes_actual':
                fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            elif fecha_val == 'semana_actual':
                fecha_inicio = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
            elif fecha_val.startswith('desde:'):
                fecha_inicio = fecha_val.replace('desde:', '')
            else:
                fecha_inicio = fecha_val
        else:
            # Por defecto: hoy
            fecha_inicio = datetime.now().strftime('%Y-%m-%d')
        
        fecha_fin = fecha_fin or datetime.now().strftime('%Y-%m-%d')
        
        # Consultar ventas
        df = self.odoo.ventas_periodo(fecha_inicio, fecha_fin)
        
        if df.empty:
            return RespuestaBot(
                mensaje=f"No hay ventas registradas para el período {fecha_inicio}.",
                tipo="texto",
                sugerencias=["Consultar ventas del mes", "Ver tickets POS", "Resumen general"]
            )
        
        # Calcular estadísticas
        total_monto = df['amount_total'].sum()
        num_ordenes = len(df)
        promedio = total_monto / num_ordenes if num_ordenes > 0 else 0
        
        # Guardar contexto
        self.contexto.ultimo_modelo = 'sale.order'
        self.contexto.ultimos_datos = df
        
        mensaje = f"""**VENTAS** ({fecha_inicio})

• **Órdenes:** {num_ordenes:,}
• **Total:** ${total_monto:,.2f}
• **Promedio:** ${promedio:,.2f}

¿Deseas generar un reporte en Excel o ver más detalles?"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df,
            confianza=intencion.confianza,
            sugerencias=["Generar reporte Excel", "Mostrar detalles", "Comparar con ayer"]
        )
    
    def _handle_inventario(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja consultas de inventario/stock."""
        df = self.odoo.stock_disponible()
        
        if df.empty:
            return RespuestaBot(
                mensaje="No se encontró información de stock.",
                tipo="texto"
            )
        
        # Estadísticas
        total_productos = len(df)
        total_unidades = df['quantity'].sum() if 'quantity' in df.columns else 0
        
        self.contexto.ultimo_modelo = 'stock.quant'
        self.contexto.ultimos_datos = df
        
        mensaje = f"""**INVENTARIO**

• **Productos con stock:** {total_productos:,}
• **Unidades totales:** {total_unidades:,.0f}

Puedo mostrarte productos específicos o generar un reporte."""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df,
            sugerencias=["Productos sin stock", "Top 10 con más stock", SUGERENCIA_GENERAR_REPORTE]
        )
    
    def _handle_clientes(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja consultas de clientes."""
        df = self.odoo.clientes_activos(limite=50)
        
        if df.empty:
            return RespuestaBot(
                mensaje="No se encontraron clientes.",
                tipo="texto"
            )
        
        total = len(df)
        
        self.contexto.ultimo_modelo = 'res.partner'
        self.contexto.ultimos_datos = df
        
        mensaje = f"""**CLIENTES ACTIVOS**

• **Total clientes:** {total:,}

Aquí están los clientes más activos. ¿Necesitas más detalles?"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df,
            sugerencias=["Ver todos los clientes", "Buscar cliente específico", SUGERENCIA_GENERAR_REPORTE]
        )
    
    def _handle_productos(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja consultas de productos."""
        df = self.odoo.buscar(
            _MODEL_PRODUCT,
            campos=['name', 'default_code', 'list_price', 'qty_available', 'categ_id'],
            limite=50
        )
        
        if df.empty:
            return RespuestaBot(
                mensaje="No se encontraron productos.",
                tipo="texto"
            )
        
        total = self.odoo.contar(_MODEL_PRODUCT)
        
        self.contexto.ultimo_modelo = _MODEL_PRODUCT
        self.contexto.ultimos_datos = df
        
        mensaje = f"""**PRODUCTOS**

• **Total en catálogo:** {total:,}

Mostrando los primeros 50 productos."""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df,
            sugerencias=["Productos más vendidos", "Buscar por nombre", "Ver stock"]
        )
    
    def _handle_pos(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja consultas de Punto de Venta."""
        params = intencion.parametros
        
        fecha_inicio = datetime.now().strftime('%Y-%m-%d')
        
        if 'fecha_inicio' in params:
            fecha_val = params['fecha_inicio']
            if fecha_val == 'mes_actual':
                fecha_inicio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            else:
                fecha_inicio = fecha_val
        
        df = self.odoo.tickets_pos(fecha_inicio)
        
        if df.empty:
            return RespuestaBot(
                mensaje="No hay tickets de POS para el período consultado.",
                tipo="texto"
            )
        
        total_tickets = len(df)
        total_monto = df['amount_total'].sum() if 'amount_total' in df.columns else 0
        
        self.contexto.ultimo_modelo = 'pos.order'
        self.contexto.ultimos_datos = df
        
        mensaje = f"""**PUNTO DE VENTA** ({fecha_inicio})

• **Tickets:** {total_tickets:,}
• **Total vendido:** ${total_monto:,.2f}
• **Ticket promedio:** ${(total_monto/total_tickets):,.2f}"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df,
            sugerencias=["Ver por tienda", "Tickets del mes", SUGERENCIA_GENERAR_REPORTE]
        )

    def _organizar_campos_por_tipo(self, campos: dict) -> dict:
        """Agrupa los campos de un modelo Odoo por tipo de dato."""
        campos_por_tipo: dict = {}
        for nombre, info in campos.items():
            tipo = info.get('type', 'unknown')
            if tipo not in campos_por_tipo:
                campos_por_tipo[tipo] = []
            campos_por_tipo[tipo].append({
                'campo': nombre,
                'etiqueta': info.get('string', ''),
                'requerido': '✓' if info.get('required') else '',
                'relacion': info.get('relation', '')
            })
        return campos_por_tipo

    def _handle_describir(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Describe un modelo de Odoo."""
        modelo = intencion.parametros.get('modelo', '')
        
        # Intentar inferir modelo del texto
        if not modelo:
            for termino, mod in self.nlp.termino_a_modelo.items():
                if termino in texto.lower():
                    modelo = mod
                    break
        
        # Usar modelo del contexto si no se especificó
        if not modelo and self.contexto.ultimo_modelo:
            modelo = self.contexto.ultimo_modelo
        
        if not modelo:
            return RespuestaBot(
                mensaje="¿Qué modelo quieres que describa? Por ejemplo: sale.order, pos.order, product.product",
                tipo="texto",
                sugerencias=["sale.order", "pos.order", "product.product", "res.partner"]
            )
        
        campos = self.odoo.obtener_campos(modelo)
        
        if not campos:
            return RespuestaBot(
                mensaje=f"No pude obtener los campos del modelo '{modelo}'.",
                tipo="error"
            )
        
        # Organizar campos por tipo
        campos_por_tipo = self._organizar_campos_por_tipo(campos)
        
        # Crear DataFrame para mostrar
        lista_campos = []
        for tipo, campos_list in campos_por_tipo.items():
            for c in campos_list[:10]:  # Limitar por tipo
                lista_campos.append({
                    'Tipo': tipo,
                    'Campo': c['campo'],
                    'Etiqueta': c['etiqueta'],
                    'Requerido': c['requerido']
                })
        
        df = pd.DataFrame(lista_campos)
        
        self.contexto.ultimo_modelo = modelo
        
        mensaje = f"""**MODELO: {modelo}**

• **Total de campos:** {len(campos)}
• **Campos por tipo:** {', '.join([f'{k}: {len(v)}' for k,v in campos_por_tipo.items()])}

Mostrando los campos principales:"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df,
            sugerencias=["Ver todos los campos", "Consultar datos", "Otro modelo"]
        )
    
    def _handle_listar_modelos(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Lista los modelos disponibles."""
        # Mostrar modelos principales primero
        mensaje = """**MODELOS PRINCIPALES DE ODOO**

**Ventas:**
• `sale.order` - Órdenes de venta
• `sale.order.line` - Líneas de venta

**Punto de Venta:**
• `pos.order` - Tickets POS
• `pos.session` - Sesiones de caja

**Productos:**
• `product.product` - Productos
• `product.template` - Plantillas de producto
• `product.category` - Categorías

**Inventario:**
• `stock.quant` - Stock disponible
• `stock.move` - Movimientos de stock
• `stock.picking` - Transferencias

**Contactos:**
• `res.partner` - Clientes/Proveedores

**Contabilidad:**
• `account.move` - Facturas
• `account.move.line` - Líneas contables

Puedes pedirme que describa cualquiera de estos modelos."""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="texto",
            sugerencias=["Describir sale.order", "Describir pos.order", "Buscar modelo"]
        )
    
    def _handle_buscar_campo(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Busca un campo en los modelos."""
        # Extraer término de búsqueda
        palabras = texto.lower().split()
        termino = ''
        for i, p in enumerate(palabras):
            if p in ['campo', 'buscar', 'encontrar'] and i + 1 < len(palabras):
                termino = palabras[i + 1]
                break
        
        if not termino:
            return RespuestaBot(
                mensaje="¿Qué campo quieres buscar? Por ejemplo: 'buscar campo precio'",
                tipo="texto"
            )
        
        # Buscar en modelos principales
        resultados = []
        modelos_buscar = ['sale.order', 'pos.order', 'product.product', 'res.partner', 'stock.quant']
        
        for modelo in modelos_buscar:
            campos = self.odoo.obtener_campos(modelo)
            for nombre, info in campos.items():
                if termino in nombre.lower() or termino in info.get('string', '').lower():
                    resultados.append({
                        'Modelo': modelo,
                        'Campo': nombre,
                        'Etiqueta': info.get('string', ''),
                        'Tipo': info.get('type', '')
                    })
        
        if not resultados:
            return RespuestaBot(
                mensaje=f"No encontré campos relacionados con '{termino}'.",
                tipo="texto"
            )
        
        df = pd.DataFrame(resultados)
        
        mensaje = f"""**Campos encontrados para '{termino}':** {len(resultados)}"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="tabla",
            datos=df
        )
    
    def _handle_reporte(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Genera un reporte."""
        # Determinar formato
        formato = 'excel'
        if 'pdf' in texto.lower():
            formato = 'pdf'
        elif 'html' in texto.lower():
            formato = 'html'
        
        # Usar datos del contexto o consultar nuevos
        if self.contexto.ultimos_datos is not None and not self.contexto.ultimos_datos.empty:
            datos = {self.contexto.ultimo_modelo or 'Datos': self.contexto.ultimos_datos}
            titulo = f"Reporte_{self.contexto.ultimo_modelo or 'General'}"
        else:
            # Generar reporte general
            datos = {
                'Ventas Hoy': self.odoo.ventas_hoy(),
                'Clientes Top': self.odoo.clientes_activos(20),
            }
            titulo = "Reporte_General"
        
        # Generar reporte
        archivo = self.reportes.generar_reporte(datos, titulo, formato)
        
        mensaje = f"""**Reporte generado exitosamente**

• **Formato:** {formato.upper()}
• **Archivo:** {os.path.basename(archivo)}
• **Ubicación:** {archivo}"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="reporte",
            archivo=archivo,
            sugerencias=["Abrir archivo", "Generar otro reporte", "Ver datos"]
        )
    
    def _handle_resumen(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Genera un resumen del sistema."""
        resumen = self.odoo.resumen_general()
        
        contadores = resumen.get('contadores', {})
        ventas_hoy = resumen.get('ventas_hoy', {})
        ventas_mes = resumen.get('ventas_mes', {})
        
        mensaje = f"""**RESUMEN DEL SISTEMA**

**Estadísticas Generales:**
• Contactos: {contadores.get('contactos', 0):,}
• Productos: {contadores.get('productos', 0):,}
• Órdenes de Venta: {contadores.get('ordenes_venta', 0):,}
• Tickets POS: {contadores.get('tickets_pos', 0):,}
• Productos con Stock: {contadores.get('registros_stock', 0):,}

**Ventas de Hoy:**
• Órdenes: {ventas_hoy.get('cantidad', 0):,}
• Total: ${ventas_hoy.get('total', 0):,.2f}

**Ventas del Mes:**
• Órdenes: {ventas_mes.get('cantidad', 0):,}
• Total: ${ventas_mes.get('total', 0):,.2f}

¿Necesitas más detalles de alguna área?"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="texto",
            sugerencias=["Ver ventas detalladas", "Ver inventario", "Generar reporte completo"]
        )
    
    def _handle_comparar(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja comparativas."""
        # Por ahora: comparar con período anterior
        hoy = datetime.now()
        
        # Ventas hoy vs ayer
        ventas_hoy = self.odoo.ventas_periodo(hoy.strftime('%Y-%m-%d'))
        ventas_ayer = self.odoo.ventas_periodo(
            (hoy - timedelta(days=1)).strftime('%Y-%m-%d'),
            (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
        )
        
        total_hoy = ventas_hoy['amount_total'].sum() if not ventas_hoy.empty else 0
        total_ayer = ventas_ayer['amount_total'].sum() if not ventas_ayer.empty else 0
        
        diferencia = total_hoy - total_ayer
        porcentaje = (diferencia / total_ayer * 100) if total_ayer > 0 else 0
        
        if diferencia > 0:
            emoji = "📈"
        elif diferencia < 0:
            emoji = "📉"
        else:
            emoji = "➡️"
        
        mensaje = f"""**COMPARATIVA: HOY vs AYER**

**Hoy:**
• Órdenes: {len(ventas_hoy):,}
• Total: ${total_hoy:,.2f}

**Ayer:**
• Órdenes: {len(ventas_ayer):,}
• Total: ${total_ayer:,.2f}

**Diferencia:** {emoji}
• Monto: ${diferencia:+,.2f}
• Porcentaje: {porcentaje:+.1f}%"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="texto",
            sugerencias=["Comparar mes vs mes anterior", "Ver tendencia semanal", SUGERENCIA_GENERAR_REPORTE]
        )
    
    def _handle_ayuda(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Muestra la ayuda."""
        mensaje = f"""**{self.NOMBRE} v{self.VERSION}**

**¿Qué puedo hacer?**

**Consultas de datos:**
• "¿Cuántas ventas hay hoy?"
• "Mostrar inventario de productos"
• "Lista de clientes activos"
• "Tickets de POS de hoy"

**Explorar estructura:**
• "¿Qué modelos hay?"
• "Campos de sale.order"
• "Buscar campo precio"

**Reportes:**
• "Generar reporte de ventas en Excel"
• "Exportar clientes a PDF"
• "Reporte completo en HTML"

**Análisis:**
• "Resumen del sistema"
• "Comparar ventas hoy vs ayer"
• "Productos más vendidos"

**Tips:**
• Puedo entender preguntas naturales en español
• Los reportes se guardan en la carpeta 'Reportes_Bot'
• Uso NLP local, no necesito internet para entenderte"""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="ayuda",
            sugerencias=["Resumen del sistema", SUGERENCIA_VER_VENTAS, "Listar modelos"]
        )
    
    def _handle_saludo(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja saludos."""
        import random
        mensaje = random.choice(self.respuestas['saludo'])
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="texto",
            sugerencias=["¿Qué puedes hacer?", "Resumen del sistema", SUGERENCIA_VER_VENTAS]
        )
    
    def _handle_desconocido(self, texto: str, intencion: IntencionDetectada) -> RespuestaBot:
        """Maneja intenciones no reconocidas."""
        mensaje = """No estoy seguro de entender tu consulta.

**Prueba con algo como:**
• "¿Cuántas ventas hay hoy?"
• "Mostrar el inventario"
• "¿Qué campos tiene sale.order?"
• "Generar reporte de clientes"

Escribe **'ayuda'** para ver todas las opciones."""
        
        return RespuestaBot(
            mensaje=mensaje,
            tipo="texto",
            confianza=0.0,
            sugerencias=["Ayuda", "Resumen", "Ver ventas"]
        )
    
    # ========================================
    # INTERFAZ DE LÍNEA DE COMANDOS
    # ========================================
    
    def iniciar_chat(self):
        """Inicia una sesión de chat interactivo."""
        print("\n" + "=" * 60)
        print(f"{self.NOMBRE} v{self.VERSION}")
        print("=" * 60)
        print("Escribe tu consulta en español natural.")
        print("Comandos: 'ayuda', 'salir'")
        print("=" * 60)
        
        # Conectar
        exito, msg = self.conectar()
        print(msg)
        
        if not exito:
            print("⚠️ Continuando sin conexión a Odoo...")
        
        while True:
            try:
                entrada = input("\nTú: ").strip()
                
                if not entrada:
                    continue
                
                if entrada.lower() in ['salir', 'exit', 'quit', 'q']:
                    print("👋 ¡Hasta luego!")
                    break
                
                # Procesar
                respuesta = self.procesar(entrada)
                
                # Mostrar respuesta
                print(f"\nBot: {respuesta.mensaje}")
                
                # Mostrar tabla si hay datos
                if respuesta.datos is not None and not respuesta.datos.empty:
                    print("\n" + respuesta.datos.head(10).to_string())
                
                # Mostrar sugerencias
                if respuesta.sugerencias:
                    print("\nSugerencias:", " | ".join(respuesta.sugerencias))
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def main():
    """Función principal."""
    bot = OdooBotPro(modo_verbose=False)
    bot.iniciar_chat()


if __name__ == "__main__":
    main()
