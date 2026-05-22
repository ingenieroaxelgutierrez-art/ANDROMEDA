"""
Procesador de Manuales - Base de Conocimiento para ANDROMEDA
=============================================================

Extrae contenido de archivos .docx (texto e imágenes) y crea
un índice de búsqueda para responder preguntas sobre Odoo.

VERSIÓN MEJORADA: Contenido completo con pasos e imágenes inline
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

from app.logging_config import get_logger
logger = get_logger("services.knowledge.procesador_manuales")

# ---------------------------------------------------------------------------
# Diccionario de búsqueda multilingüe
# Mapea términos JA / EN → palabras clave en ES para que buscar() encuentre
# la sección correcta del manual aunque la consulta llegue en otro idioma.
# ---------------------------------------------------------------------------
_KW_JA: Dict[str, str] = {
    # Facturación
    "請求書": "factura facturas facturación",
    "請求": "factura cobro facturación",
    "スタンプ": "timbrar timbrado CFDI",
    "スタンプ済み": "timbrado timbrar CFDI",
    "電子請求": "factura electronica CFDI",
    # Cancelación
    "キャンセル": "cancelar anular cancelación",
    "取り消し": "cancelar anular",
    "無効": "cancelar anular invalidar",
    # Ventas / POS
    "売上": "ventas venta",
    "販売": "ventas venta",
    "販売時点": "punto de venta POS",
    "レジ": "punto de venta caja POS",
    "ポイントオブセール": "punto de venta POS",
    # Inventario
    "在庫": "inventario stock",
    "在庫管理": "inventario gestión",
    "倉庫": "almacén almacenes",
    "入庫": "recepción entrada",
    "出庫": "salida entrega",
    "調整": "ajuste ajustes",
    "転送": "transferir traspaso",
    "カルデックス": "kardex inventario",
    "棚卸し": "inventario cierre",
    # Compras
    "購入": "compra compras",
    "発注": "orden de compra pedido",
    "仕入先": "proveedor proveedores",
    "受入": "recepción",
    # Contabilidad
    "会計": "contabilidad",
    "支払い": "pago pagos",
    "支払": "pago pagos",
    "決済": "pago liquidación",
    "残高": "saldo balance",
    "銀行": "banco",
    "バンク": "banco",
    "振込": "transferencia bancaria",
    "税": "impuesto impuestos",
    "消費税": "impuesto IVA",
    "クレジット": "crédito",
    "デビット": "débito",
    "勘定科目": "cuenta contable",
    "仕訳": "asiento contable",
    "元帳": "mayor contable",
    # Clientes
    "顧客": "cliente clientes",
    "カスタマー": "cliente clientes",
    # Pedidos / Órdenes
    "注文": "pedido orden",
    "オーダー": "pedido orden",
    "配送": "entrega envío",
    "配達": "entrega envío",
    # Usuarios / Configuración
    "ユーザー": "usuario usuarios",
    "設定": "configuración ajuste",
    "従業員": "empleado empleados",
    "レポート": "reporte reportes",
    "印刷": "imprimir impresión",
    "検索": "buscar consultar",
    "登録": "registrar registro",
    "更新": "actualizar",
    "作成": "crear creación",
    "削除": "eliminar borrar",
    "確認": "confirmar confirmación",
    "返品": "devolución",
    "払い戻し": "reembolso devolución",
    "閉じる": "cerrar cierre",
    "クローズ": "cierre cerrar",
    "開く": "abrir apertura",
    "月次": "mensual mes cierre de mes",
    "月末": "cierre de mes fin de mes",
    "締め": "cierre cierre de mes",
    "製品": "producto productos",
    "商品": "producto productos",
    "価格": "precio precios",
    "割引": "descuento",
    "RFCナンバー": "RFC",
    "RFC": "RFC",
    "CFDI": "CFDI timbrado",
    "SAT": "SAT",
    "請求書発行": "emitir factura",
    "明細": "detalle",
    "リポート": "reporte",
    "ダッシュボード": "dashboard",
    "ODOO": "odoo",
}

_KW_EN: Dict[str, str] = {
    # Invoicing / Billing
    "invoice": "factura facturas",
    "invoices": "facturas facturación",
    "billing": "facturación",
    "stamp": "timbrar timbrado",
    "stamped": "timbrado CFDI",
    "cfdi": "CFDI timbrado",
    "electronic invoice": "factura electrónica",
    # Cancellation
    "cancel": "cancelar anular",
    "cancellation": "cancelación",
    "void": "anular cancelar",
    "reverse": "reversar cancelar nota de crédito",
    # Sales / POS
    "sales": "ventas",
    "sale": "venta",
    "point of sale": "punto de venta",
    "pos": "punto de venta POS",
    "cash register": "caja punto de venta",
    # Inventory
    "inventory": "inventario",
    "stock": "stock inventario",
    "warehouse": "almacén almacenes",
    "receipt": "recepción",
    "transfer": "transferir traspaso",
    "adjustment": "ajuste",
    "kardex": "kardex inventario",
    "month end": "cierre de mes",
    "closing": "cierre",
    # Purchases
    "purchase": "compra",
    "purchases": "compras",
    "purchase order": "orden de compra",
    "vendor": "proveedor",
    "supplier": "proveedor proveedores",
    # Accounting
    "accounting": "contabilidad",
    "payment": "pago",
    "payments": "pagos",
    "bank": "banco",
    "balance": "saldo balance",
    "tax": "impuesto",
    "vat": "IVA impuesto",
    "credit": "crédito",
    "debit": "débito",
    "account": "cuenta contable",
    "journal": "asiento diario",
    "ledger": "mayor contable",
    "reconciliation": "conciliación",
    # Customers
    "customer": "cliente",
    "customers": "clientes",
    "client": "cliente",
    # Orders
    "order": "pedido orden",
    "delivery": "entrega envío",
    "shipping": "envío",
    # Users / Config
    "user": "usuario",
    "settings": "configuración",
    "configuration": "configuración",
    "employee": "empleado",
    "report": "reporte",
    "print": "imprimir",
    "search": "buscar",
    "create": "crear",
    "delete": "eliminar",
    "confirm": "confirmar",
    "refund": "devolución reembolso",
    "return": "devolución",
    "close": "cierre cerrar",
    "open": "abrir apertura",
    "product": "producto",
    "products": "productos",
    "price": "precio",
    "discount": "descuento",
    "rfc": "RFC",
    "sat": "SAT",
}


# ---------------------------------------------------------------------------
# Traducción de contenido del manual vía Google Translate (requests, free)
# ---------------------------------------------------------------------------
_SEP_BATCH = "|||S|||"  # separador difícil de traducir


def _traducir_google(texto: str, lang_destino: str) -> str:
    """Llama a la API gratuita de Google Translate y devuelve el texto traducido.

    Usa el cliente 'gtx' (mismo que el navegador web, sin API key).
    Maneja textos largos dividiéndolos en fragmentos de ≤4000 chars.
    """
    import requests as _req  # ya en requirements.txt
    if not texto or not texto.strip():
        return texto

    def _llamar(fragmento: str) -> str:
        resp = _req.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "es", "tl": lang_destino,
                    "dt": "t", "q": fragmento},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(part[0] for part in data[0] if part[0])

    # Dividir en fragmentos de 4000 chars si el texto es largo
    if len(texto) <= 4000:
        return _llamar(texto)
    partes, acum = [], ""
    for linea in texto.split("\n"):
        if len(acum) + len(linea) + 1 > 4000:
            if acum:
                partes.append(_llamar(acum))
            acum = linea
        else:
            acum = (acum + "\n" + linea) if acum else linea
    if acum:
        partes.append(_llamar(acum))
    return "\n".join(partes)


def _traducir_pasos_batch(pasos: List[Dict], lang_destino: str) -> List[Dict]:
    """Traduce una lista de pasos en una sola llamada API (batch)."""
    textos_a_traducir = []
    indices = []
    for i, paso in enumerate(pasos):
        texto = paso.get("texto", "")
        if texto and texto not in ("(Ver imagen)", "(See image)", "（画像参照）"):
            textos_a_traducir.append(texto)
            indices.append(i)

    if not textos_a_traducir:
        return [dict(p) for p in pasos]

    batch = _SEP_BATCH.join(textos_a_traducir)
    try:
        batch_traducido = _traducir_google(batch, lang_destino)
    except Exception:
        return [dict(p) for p in pasos]

    # Re-split — el separador rara vez se altera en traducción
    partes = re.split(r'\|\|\|S\|\|\|', batch_traducido)

    nuevos_pasos = [dict(p) for p in pasos]
    if len(partes) == len(textos_a_traducir):
        for i_p, i_src in enumerate(indices):
            nuevos_pasos[i_src]["texto"] = partes[i_p].strip()
    return nuevos_pasos


def traducir_consulta_i18n(consulta: str, idioma: str) -> str:
    """Traduce términos JA/EN de la consulta a palabras clave ES para buscar().

    No reemplaza la consulta original; construye un string enriquecido
    que concatena la consulta original + los equivalentes en español,
    aumentando la cobertura de coincidencias en el índice.

    Args:
        consulta: Texto tal como lo escribió el usuario (JA, EN, ES, etc.).
        idioma: Código de idioma ("ja", "en", "es").

    Returns:
        String con términos en español para usar como consulta de búsqueda.
    """
    if idioma == "es":
        return consulta

    kw_map = _KW_JA if idioma == "ja" else _KW_EN
    terminos_es: List[str] = []

    # Búsqueda exacta de frases primero (para "point of sale", "purchase order", etc.)
    consulta_lower = consulta.lower()
    for termino, equivalente in sorted(kw_map.items(), key=lambda x: -len(x[0])):
        if termino.lower() in consulta_lower:
            terminos_es.append(equivalente)

    if not terminos_es:
        # Fallback: incluir la consulta original (puede que ya tenga "Odoo", etc.)
        return consulta

    # Combinar equivalentes ES + consulta original (el índice puede tener "Odoo")
    return " ".join(terminos_es) + " " + consulta

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_DISPONIBLE = True
except ImportError:
    DOCX_DISPONIBLE = False
    logger.warning("python-docx no instalado. Ejecutar: pip install python-docx")


@dataclass
class PasoManual:
    """Representa un paso individual con su imagen."""
    numero: int
    texto: str
    imagen: Optional[str] = None  # Ruta absoluta a la imagen


@dataclass
class SeccionManual:
    """Representa una sección del manual."""
    id: str
    titulo: str
    nivel: int  # 1 = Heading 1, 2 = Heading 2
    contenido: str  # Contenido original (español)
    pasos: List[Dict] = field(default_factory=list)  # Lista de pasos con imágenes
    palabras_clave: List[str] = field(default_factory=list)
    imagenes: List[str] = field(default_factory=list)  # Rutas absolutas
    seccion_padre: Optional[str] = None
    # Traducciones pre-generadas (se rellenan con traducir_indice())
    titulo_en: Optional[str] = None
    titulo_ja: Optional[str] = None
    pasos_en: List[Dict] = field(default_factory=list)
    pasos_ja: List[Dict] = field(default_factory=list)


@dataclass
class ResultadoBusqueda:
    """Resultado de una búsqueda en la base de conocimiento."""
    seccion: SeccionManual
    relevancia: float


class ProcesadorManuales:
    """
    Procesa archivos .docx y crea una base de conocimiento indexada.
    """
    
    def __init__(self, directorio_manuales: str = None):
        """
        Inicializa el procesador.
        """
        if directorio_manuales:
            self.directorio = Path(directorio_manuales)
        else:
            # Ruta por defecto - ABSOLUTA
            base = Path(__file__).parent.parent.parent
            self.directorio = base / "data" / "manuales"
        
        self.directorio_imagenes = self.directorio / "imagenes"
        self.archivo_indice = self.directorio / "indice_conocimiento.json"
        
        # Asegurar ruta absoluta
        self.directorio = self.directorio.resolve()
        self.directorio_imagenes = self.directorio_imagenes.resolve()
        
        # Índice de conocimiento
        self.secciones: Dict[str, SeccionManual] = {}
        self.indice_palabras: Dict[str, List[str]] = {}
        
        # Cargar índice existente
        self._cargar_indice()
        
        print(f"Procesador de manuales inicializado")
        print(f"   Directorio: {self.directorio}")
        print(f"   Secciones cargadas: {len(self.secciones)}")
    
    def _cargar_indice(self):
        """Carga el índice de conocimiento si existe."""
        if self.archivo_indice.exists():
            try:
                with open(self.archivo_indice, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                campos_validos = {f.name for f in SeccionManual.__dataclass_fields__.values()}
                for id_seccion, sec_dict in data.get('secciones', {}).items():
                    # Filtrar claves desconocidas (compatibilidad hacia atrás/adelante)
                    sec_filtrado = {k: v for k, v in sec_dict.items() if k in campos_validos}
                    self.secciones[id_seccion] = SeccionManual(**sec_filtrado)

                self.indice_palabras = data.get('indice_palabras', {})

            except Exception as e:
                logger.error(f"Error cargando índice: {e}")
    
    def _guardar_indice(self):
        """Guarda el índice de conocimiento."""
        try:
            data = {
                'fecha_generacion': datetime.now().isoformat(),
                'total_secciones': len(self.secciones),
                'secciones': {k: asdict(v) for k, v in self.secciones.items()},
                'indice_palabras': self.indice_palabras
            }
            
            with open(self.archivo_indice, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Índice guardado: {len(self.secciones)} secciones")
            
        except Exception as e:
            logger.error(f"Error guardando índice: {e}")
    
    def procesar_manual(self, nombre_archivo: str = "MANUAL.docx") -> bool:
        """
        Procesa un archivo .docx y extrae contenido e imágenes.
        """
        if not DOCX_DISPONIBLE:
            print("python-docx no está instalado")
            return False
        
        ruta_archivo = self.directorio / nombre_archivo
        
        if not ruta_archivo.exists():
            print(f"Archivo no encontrado: {ruta_archivo}")
            return False
        
        print(f"Procesando: {nombre_archivo}")
        
        try:
            doc = Document(str(ruta_archivo))
            
            # 1. Extraer imágenes con rutas absolutas
            imagenes_extraidas = self._extraer_imagenes(doc, nombre_archivo)
            print(f"   {len(imagenes_extraidas)} imágenes extraídas")
            
            # 2. Extraer secciones con pasos e imágenes intercaladas
            self._extraer_secciones_con_pasos(doc, imagenes_extraidas)
            print(f"   {len(self.secciones)} secciones procesadas")
            
            # 3. Construir índice de palabras
            self._construir_indice_palabras()
            print(f"   Índice de {len(self.indice_palabras)} palabras clave")
            
            # 4. Guardar índice
            self._guardar_indice()
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando manual: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extraer_imagenes(self, doc: 'Document', nombre_manual: str) -> Dict[str, str]:
        """Extrae todas las imágenes con rutas ABSOLUTAS."""
        imagenes = {}
        
        self.directorio_imagenes.mkdir(parents=True, exist_ok=True)
        
        prefijo = nombre_manual.replace('.docx', '').replace(' ', '_').lower()
        
        contador = 0
        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.reltype:
                try:
                    imagen_part = rel.target_part
                    extension = imagen_part.content_type.split('/')[-1]
                    if extension == 'jpeg':
                        extension = 'jpg'
                    
                    nombre_imagen = f"{prefijo}_img_{contador:03d}.{extension}"
                    ruta_imagen = self.directorio_imagenes / nombre_imagen
                    
                    with open(ruta_imagen, 'wb') as f:
                        f.write(imagen_part.blob)
                    
                    # Guardar ruta ABSOLUTA
                    imagenes[rel_id] = str(ruta_imagen.resolve())
                    contador += 1
                    
                except Exception as e:
                    logger.error(f"   Error extrayendo imagen {rel_id}: {e}")
        
        return imagenes
    
    def _extraer_secciones_con_pasos(self, doc: 'Document', imagenes: Dict[str, str]):
        """Extrae las secciones con pasos e imágenes intercaladas."""
        
        seccion_actual = None
        pasos_actuales = []
        imagenes_seccion = []
        contenido_lineas = []
        contador_seccion = 0
        paso_numero = 0
        ultimo_texto = ""
        
        for para in doc.paragraphs:
            estilo = para.style.name
            texto = para.text.strip()
            
            # Buscar imágenes en este párrafo
            imagenes_parrafo = []
            for run in para.runs:
                blips = run._element.xpath('.//a:blip')
                for blip in blips:
                    embed = blip.get(qn('r:embed'))
                    if embed and embed in imagenes:
                        imagenes_parrafo.append(imagenes[embed])
            
            # Si es un encabezado, guardar sección anterior
            if estilo.startswith('Heading') and texto:
                if seccion_actual:
                    self._guardar_seccion_con_pasos(
                        seccion_actual, 
                        contenido_lineas,
                        pasos_actuales, 
                        imagenes_seccion
                    )
                
                # Nueva sección
                nivel = int(estilo.replace('Heading ', '').replace('Heading', '1'))
                contador_seccion += 1
                
                seccion_actual = {
                    'id': f"sec_{contador_seccion:03d}",
                    'titulo': texto,
                    'nivel': nivel
                }
                pasos_actuales = []
                imagenes_seccion = []
                contenido_lineas = []
                paso_numero = 0
                ultimo_texto = ""
                
            elif seccion_actual:
                # Es contenido de la sección actual
                if texto:
                    contenido_lineas.append(texto)
                    ultimo_texto = texto
                    
                    # Crear un paso para cada línea de texto con contenido significativo
                    if len(texto) > 10:  # Solo textos con contenido relevante
                        paso_numero += 1
                        paso = {
                            'numero': paso_numero,
                            'texto': texto,
                            'imagen': imagenes_parrafo[0] if imagenes_parrafo else None
                        }
                        pasos_actuales.append(paso)
                        
                        # Agregar imágenes restantes como pasos visuales
                        for img_extra in imagenes_parrafo[1:]:
                            paso_numero += 1
                            pasos_actuales.append({
                                'numero': paso_numero,
                                'texto': "(Ver imagen)",
                                'imagen': img_extra
                            })
                
                # Si solo hay imágenes (sin texto nuevo)
                elif imagenes_parrafo:
                    for img in imagenes_parrafo:
                        imagenes_seccion.append(img)
                        # Asociar imagen al último paso si existe
                        if pasos_actuales and not pasos_actuales[-1].get('imagen'):
                            pasos_actuales[-1]['imagen'] = img
                        else:
                            # O crear paso solo con imagen
                            paso_numero += 1
                            pasos_actuales.append({
                                'numero': paso_numero,
                                'texto': f"(Ver imagen de referencia para: {ultimo_texto[:50]}...)" if ultimo_texto else "(Ver imagen)",
                                'imagen': img
                            })
        
        # Guardar última sección
        if seccion_actual:
            self._guardar_seccion_con_pasos(
                seccion_actual, 
                contenido_lineas,
                pasos_actuales, 
                imagenes_seccion
            )
    
    def _guardar_seccion_con_pasos(self, info: Dict, contenido: List[str], 
                                    pasos: List[Dict], imagenes: List[str]):
        """Guarda una sección con sus pasos."""
        
        texto_completo = '\n'.join(contenido)
        
        palabras_clave = self._extraer_palabras_clave(
            info['titulo'] + ' ' + texto_completo
        )
        
        seccion = SeccionManual(
            id=info['id'],
            titulo=info['titulo'],
            nivel=info['nivel'],
            contenido=texto_completo,
            pasos=pasos,
            palabras_clave=palabras_clave,
            imagenes=imagenes
        )
        
        self.secciones[info['id']] = seccion
    
    def _extraer_palabras_clave(self, texto: str) -> List[str]:
        """Extrae palabras clave relevantes del texto."""
        
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del',
            'en', 'con', 'por', 'para', 'al', 'a', 'y', 'o', 'que', 'se', 'es',
            'su', 'sus', 'este', 'esta', 'estos', 'estas', 'como', 'más', 'muy',
            'no', 'si', 'ya', 'le', 'lo', 'me', 'te', 'nos', 'les', 'mi', 'tu',
            'clic', 'click', 'dar', 'daremos', 'vamos', 'hacer', 'donde', 'dónde'
        }
        
        texto_limpio = re.sub(r'[^\w\sáéíóúñü]', ' ', texto.lower())
        palabras = texto_limpio.split()
        
        palabras_filtradas = [
            p for p in palabras 
            if len(p) > 2 and p not in stopwords
        ]
        
        frecuencia = {}
        for p in palabras_filtradas:
            frecuencia[p] = frecuencia.get(p, 0) + 1
        
        ordenadas = sorted(frecuencia.items(), key=lambda x: x[1], reverse=True)
        
        return [p for p, _ in ordenadas[:25]]
    
    def _construir_indice_palabras(self):
        """Construye el índice invertido de palabras."""
        
        self.indice_palabras = {}
        
        for id_seccion, seccion in self.secciones.items():
            # Indexar por título
            for palabra in self._normalizar_texto(seccion.titulo).split():
                if len(palabra) > 2:
                    if palabra not in self.indice_palabras:
                        self.indice_palabras[palabra] = []
                    if id_seccion not in self.indice_palabras[palabra]:
                        self.indice_palabras[palabra].append(id_seccion)
            
            # Indexar por palabras clave
            for palabra in seccion.palabras_clave:
                if palabra not in self.indice_palabras:
                    self.indice_palabras[palabra] = []
                if id_seccion not in self.indice_palabras[palabra]:
                    self.indice_palabras[palabra].append(id_seccion)
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normaliza texto para búsqueda."""
        texto = texto.lower()
        texto = re.sub(r'[^\w\sáéíóúñü]', ' ', texto)
        return texto
    
    def buscar(self, consulta: str, max_resultados: int = 2) -> List[ResultadoBusqueda]:
        """
        Busca en la base de conocimiento con relevancia contextual mejorada.
        """
        if not self.secciones:
            return []
        
        consulta_norm = self._normalizar_texto(consulta)
        palabras_consulta = set(consulta_norm.split())
        
        # Detectar contexto específico
        contexto_dentro = 'dentro' in consulta_norm
        contexto_fuera = 'fuera' in consulta_norm
        contexto_pos = any(p in consulta_norm for p in ['punto de venta', 'pos', 'pdv', 'tpv'])
        contexto_factura = any(p in consulta_norm for p in ['factura', 'facturar', 'facturacion'])
        contexto_inventario = 'inventario' in consulta_norm
        contexto_cierre = any(p in consulta_norm for p in ['cierre', 'mes', 'fin de mes', 'cierre de mes'])
        contexto_kardex = 'kardex' in consulta_norm
        contexto_consulta = any(p in consulta_norm for p in ['consultar', 'consulta', 'ver', 'buscar'])
        
        puntuaciones: Dict[str, float] = {}
        
        for palabra in palabras_consulta:
            if len(palabra) > 2:
                # Búsqueda exacta
                if palabra in self.indice_palabras:
                    for id_seccion in self.indice_palabras[palabra]:
                        puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 3
                
                # Búsqueda parcial
                for palabra_indice, secciones in self.indice_palabras.items():
                    if palabra in palabra_indice or palabra_indice in palabra:
                        for id_seccion in secciones:
                            puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 1
        
        # Bonus por match en título y ajustes de contexto
        for id_seccion, seccion in self.secciones.items():
            titulo_norm = self._normalizar_texto(seccion.titulo)
            contenido_norm = self._normalizar_texto(seccion.contenido[:300]) if seccion.contenido else ""
            
            # ===== CASO ESPECIAL: "inventario de cierre de mes" =====
            if contexto_inventario and contexto_cierre:
                if 'cierre' in titulo_norm and 'mes' in titulo_norm:
                    # Sección exacta de cierre de mes
                    puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 50
                elif 'cierre' in titulo_norm or 'mes' in titulo_norm:
                    puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 15
                # Penalizar secciones de inventario general
                if 'kardex' in titulo_norm or 'consulta' in titulo_norm:
                    puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) - 10
            
            # ===== CASO ESPECIAL: "consultar/ver inventario" o "kardex" =====
            elif contexto_inventario and (contexto_kardex or contexto_consulta):
                if 'kardex' in titulo_norm or 'consulta' in titulo_norm:
                    puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 30
                elif 'cierre' in titulo_norm:
                    # Penalizar cierre de mes si busca kardex
                    puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) - 20
            
            # ===== CASO ESPECIAL: "factura dentro de punto de venta" =====
            if contexto_factura and contexto_pos:
                if contexto_dentro or not contexto_fuera:
                    # Usuario quiere factura DENTRO del POS (o no especificó "fuera")
                    if 'fuera' in titulo_norm:
                        # PENALIZAR fuertemente la sección de facturación fuera de POS
                        puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) - 50
                    elif 'facturacion' in titulo_norm or 'factura' in titulo_norm:
                        # Si el título es solo "FACTURACIÓN" (sin "fuera"), es la correcta
                        if 'fuera' not in titulo_norm:
                            puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 25
                            
                elif contexto_fuera:
                    # Usuario explícitamente quiere FUERA del POS
                    if 'fuera' in titulo_norm:
                        puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 25
                    elif 'facturacion' in titulo_norm and 'fuera' not in titulo_norm:
                        puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) - 20
            
            # Bonus general por palabras en título
            for palabra in palabras_consulta:
                if palabra in titulo_norm and palabra not in ['de', 'en', 'un', 'una', 'el', 'la', 'como', 'cómo']:
                    puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 5
                    
            # Bonus por contexto de punto de venta
            if contexto_pos and ('punto de venta' in titulo_norm or 'pos' in titulo_norm):
                puntuaciones[id_seccion] = puntuaciones.get(id_seccion, 0) + 8
        
        ordenados = sorted(
            puntuaciones.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:max_resultados]
        
        resultados = []
        for id_seccion, puntuacion in ordenados:
            if puntuacion > 0:
                seccion = self.secciones[id_seccion]
                resultados.append(ResultadoBusqueda(
                    seccion=seccion,
                    relevancia=puntuacion
                ))
        
        return resultados
    
    def _imagen_a_url(self, ruta_imagen: str) -> Optional[str]:
        """Devuelve la URL pública de la imagen servida por el endpoint /manuales/imagenes/."""
        try:
            # Usar os.path.basename en lugar de Path().name para manejar correctamente
            # rutas absolutas de Windows (con \\) cuando el código corre en Linux (Docker).
            # Path('C:\\Users\\...\\img.png').name en Linux devuelve la cadena completa.
            nombre = os.path.basename(ruta_imagen.replace('\\', '/'))
            if not nombre:
                return None

            # Verificar que el archivo existe en el directorio real de imágenes
            ruta_real = self.directorio_imagenes / nombre
            if not ruta_real.exists():
                return None

            # Leer host desde variable de entorno para que funcione en local y en Docker
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            return f"{api_base}/manuales/imagenes/{nombre}"
        except Exception as e:
            logger.error(f"Error generando URL de imagen: {e}")
            return None
    
    def traducir_indice(self, idioma: str) -> bool:
        """Pre-traduce títulos y pasos de todas las secciones y guarda el índice.

        Usa Google Translate (API gratuita via requests). La primera llamada
        hace las peticiones de red; las siguientes usan el caché del JSON.

        Args:
            idioma: Código destino ("en" o "ja").

        Returns:
            True si tuvo éxito, False si hubo error de red o idioma inválido.
        """
        lang_map = {"en": "en", "ja": "ja"}
        google_lang = lang_map.get(idioma)
        if not google_lang:
            return False

        campo_titulo = f"titulo_{idioma}"
        campo_pasos = f"pasos_{idioma}"
        hubo_cambios = False

        for seccion in self.secciones.values():
            try:
                # ── Título ──────────────────────────────────────────────
                if not getattr(seccion, campo_titulo, None):
                    traducido = _traducir_google(seccion.titulo, google_lang)
                    setattr(seccion, campo_titulo, traducido)
                    hubo_cambios = True

                # ── Pasos ───────────────────────────────────────────────
                if not getattr(seccion, campo_pasos, None) and seccion.pasos:
                    nuevos = _traducir_pasos_batch(seccion.pasos, google_lang)
                    setattr(seccion, campo_pasos, nuevos)
                    hubo_cambios = True

            except Exception as e:
                logger.warning(f"Error traduciendo sección {seccion.id}: {e}")
                # Dejar campos vacíos para intentarlo la próxima vez

        if hubo_cambios:
            try:
                self._guardar_indice()
            except Exception as e:
                logger.error(f"Error guardando índice tras traducción: {e}")

        return True

    def tiene_traducciones(self, idioma: str) -> bool:
        """True si al menos la primera sección ya tiene el título traducido."""
        primera = next(iter(self.secciones.values()), None)
        if primera is None:
            return False
        return bool(getattr(primera, f"titulo_{idioma}", None))

    def formatear_respuesta(self, resultados: List['ResultadoBusqueda'], idioma: str = "es") -> str:
        """
        Formatea los resultados como Markdown CON PASOS E IMÁGENES.
        Usa URLs del endpoint /manuales/imagenes/ para referenciar imágenes.

        Args:
            resultados: Lista de ResultadoBusqueda.
            idioma: Código de idioma ("es", "en", "ja") para el texto estructural.
        """
        # ── Strings estructurales multilingüe ─────────────────────────────
        _TITULO_SECCION = {
            "en": "## Odoo Manual\n\n",
            "ja": "## Odooマニュアル\n\n",
        }
        _PASO_LABEL = {
            "en": "**Step {n}.**",
            "ja": "**ステップ{n}.**",
        }
        _VER_IMAGEN = {
            "en": "(See image)",
            "ja": "（画像参照）",
        }
        _VER_IMAGEN_REF = {
            "en": "(Reference image for:",
            "ja": "（参照画像：",
        }
        _PIE = {
            "en": "\n---\n *Information extracted from the Odoo Manual*",
            "ja": "\n---\n *Odooマニュアルより抜粋*",
        }
        _NO_ENCONTRADO = {
            "en": (
                "I couldn't find information about that in the Odoo manual.\n\n"
                "Could you rephrase your question or use different keywords?"
            ),
            "ja": (
                "Odooマニュアルにその情報は見つかりませんでした。\n\n"
                "質問を言い換えるか、別のキーワードを使ってみてください。"
            ),
        }

        titulo_md = _TITULO_SECCION.get(idioma, "## Manual de Odoo\n\n")
        paso_fmt = _PASO_LABEL.get(idioma, "**Paso {n}.**")
        ver_img = _VER_IMAGEN.get(idioma, "(Ver imagen)")
        ver_img_ref = _VER_IMAGEN_REF.get(idioma, "(Ver imagen de referencia para:")
        pie_md = _PIE.get(idioma, "\n---\n *Información extraída del Manual de Odoo*")
        no_encontrado = _NO_ENCONTRADO.get(
            idioma,
            "No encontré información sobre eso en el manual.\n\n"
            "¿Podrías reformular tu pregunta o usar otras palabras?"
        )

        if not resultados:
            return no_encontrado

        md = titulo_md

        for resultado in resultados[:1]:  # Solo el resultado más relevante
            seccion = resultado.seccion

            # ── Título: usar traducción si existe ────────────────────────────
            titulo_mostrar = (
                getattr(seccion, f"titulo_{idioma}", None) or seccion.titulo
            )
            md += f"### {titulo_mostrar}\n\n"

            # ── Pasos: usar pasos traducidos si existen ───────────────────────
            pasos_mostrar = (
                getattr(seccion, f"pasos_{idioma}", None) or seccion.pasos
            ) if idioma != "es" else seccion.pasos

            if pasos_mostrar:
                pasos_mostrados = 0
                imagenes_mostradas = 0
                max_imagenes = 30

                for paso in pasos_mostrar:
                    if pasos_mostrados >= 30:
                        md += "\n*... (ver manual completo para más pasos)*\n"
                        break

                    numero = paso.get('numero', '')
                    texto = paso.get('texto', '')
                    # La imagen siempre se toma del paso original (mismo índice)
                    paso_orig = seccion.pasos[pasos_mostrados] if pasos_mostrados < len(seccion.pasos) else paso
                    imagen = paso_orig.get('imagen')

                    if texto and texto not in ("(Ver imagen)", "(See image)", "（画像参照）"):
                        label = paso_fmt.format(n=numero)
                        md += f"{label} {texto}\n\n"
                        pasos_mostrados += 1

                    if imagen and imagenes_mostradas < max_imagenes:
                        url = self._imagen_a_url(imagen)
                        if url:
                            md += f"![{ver_img} {numero}]({url})\n\n"
                            imagenes_mostradas += 1
            else:
                # Contenido sin pasos estructurados
                lineas = seccion.contenido.split('\n')
                for i, linea in enumerate(lineas[:15], 1):
                    if linea.strip():
                        label = paso_fmt.format(n=i)
                        md += f"{label} {linea.strip()}\n\n"

                for i, img in enumerate(seccion.imagenes[:5]):
                    url = self._imagen_a_url(img)
                    if url:
                        md += f"![{ver_img} {i+1}]({url})\n\n"

        md += pie_md

        return md
    
    def obtener_seccion_completa(self, titulo_parcial: str) -> Optional[SeccionManual]:
        """Obtiene una sección completa por título parcial."""
        titulo_lower = titulo_parcial.lower()
        
        for seccion in self.secciones.values():
            if titulo_lower in seccion.titulo.lower():
                return seccion
        
        return None
    
    def listar_temas(self) -> List[str]:
        """Lista todos los temas disponibles en el manual."""
        return [sec.titulo for sec in self.secciones.values() if sec.nivel == 1]


# Instancia global
procesador_manuales = None

def obtener_procesador() -> ProcesadorManuales:
    """Obtiene la instancia global del procesador."""
    global procesador_manuales
    if procesador_manuales is None:
        procesador_manuales = ProcesadorManuales()
    return procesador_manuales


def procesar_manual_odoo():
    """Procesa el manual de Odoo principal."""
    proc = obtener_procesador()
    return proc.procesar_manual("MANUAL.docx")


def buscar_en_manual(consulta: str) -> str:
    """
    Busca en el manual y retorna respuesta formateada.
    """
    proc = obtener_procesador()
    resultados = proc.buscar(consulta)
    return proc.formatear_respuesta(resultados)


# Exportaciones
__all__ = [
    'ProcesadorManuales',
    'SeccionManual',
    'ResultadoBusqueda',
    'PasoManual',
    'obtener_procesador',
    'procesar_manual_odoo',
    'buscar_en_manual'
]
