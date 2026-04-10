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
    contenido: str  # Contenido original
    pasos: List[Dict] = field(default_factory=list)  # Lista de pasos con imágenes
    palabras_clave: List[str] = field(default_factory=list)
    imagenes: List[str] = field(default_factory=list)  # Rutas absolutas
    seccion_padre: Optional[str] = None


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
                
                for id_seccion, sec_dict in data.get('secciones', {}).items():
                    self.secciones[id_seccion] = SeccionManual(**sec_dict)
                
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
            if not os.path.exists(ruta_imagen):
                return None
            nombre = Path(ruta_imagen).name
            return f"http://127.0.0.1:8000/manuales/imagenes/{nombre}"
        except Exception as e:
            logger.error(f"Error generando URL de imagen: {e}")
            return None
    
    def formatear_respuesta(self, resultados: List[ResultadoBusqueda]) -> str:
        """
        Formatea los resultados como Markdown CON PASOS E IMÁGENES.
        Usa URLs del endpoint /manuales/imagenes/ para referenciar imágenes.
        """
        if not resultados:
            return "No encontré información sobre eso en el manual.\n\n¿Podrías reformular tu pregunta o usar otras palabras?"
        
        md = "## Manual de Odoo\n\n"
        
        for resultado in resultados[:1]:  # Solo el resultado más relevante
            seccion = resultado.seccion
            
            md += f"### {seccion.titulo}\n\n"
            
            # Mostrar pasos con imágenes
            if seccion.pasos:
                pasos_mostrados = 0
                imagenes_mostradas = 0
                max_imagenes = 8  # Limitar imágenes para no saturar
                
                for paso in seccion.pasos:
                    if pasos_mostrados >= 15:  # Máximo 15 pasos
                        md += "\n*... (ver manual completo para más pasos)*\n"
                        break
                    
                    numero = paso.get('numero', '')
                    texto = paso.get('texto', '')
                    imagen = paso.get('imagen')
                    
                    # Solo mostrar si tiene texto significativo
                    if texto and texto != "(Ver imagen)":
                        md += f"**Paso {numero}.** {texto}\n\n"
                        pasos_mostrados += 1
                    
                    # Mostrar imagen como URL (con límite)
                    if imagen and imagenes_mostradas < max_imagenes:
                        url = self._imagen_a_url(imagen)
                        if url:
                            md += f"![Paso {numero}]({url})\n\n"
                            imagenes_mostradas += 1
            else:
                # Si no hay pasos estructurados, mostrar contenido como lista
                lineas = seccion.contenido.split('\n')
                for i, linea in enumerate(lineas[:15], 1):
                    if linea.strip():
                        md += f"**{i}.** {linea.strip()}\n\n"
                
                # Agregar algunas imágenes
                for i, img in enumerate(seccion.imagenes[:5]):
                    url = self._imagen_a_url(img)
                    if url:
                        md += f"![Referencia {i+1}]({url})\n\n"
        
        md += "\n---\n *Información extraída del Manual de Odoo*"
        
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
