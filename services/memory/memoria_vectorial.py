# -*- coding: utf-8 -*-
"""
ANDROMEDA - Memoria Vectorial Persistente
==========================================
Módulo de memoria a largo plazo usando ChromaDB.
Permite recordar conversaciones, análisis y eventos pasados.

Autor: ANDROMEDA Team
Fecha: 2026
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
# Intentar importar ChromaDB
from app.logging_config import get_logger
logger = get_logger("services.memory.memoria_vectorial")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_DISPONIBLE = True
except ImportError:
    CHROMADB_DISPONIBLE = False
    logger.warning("ChromaDB no disponible - memoria limitada")

# sentence-transformers es opcional (se carga bajo demanda)
EMBEDDINGS_DISPONIBLES = False
SentenceTransformer = None


@dataclass
class Recuerdo:
    """Representa un recuerdo almacenado en la memoria"""
    id: str
    tipo: str  # 'conversacion', 'analisis', 'error', 'alerta', 'reporte'
    contenido: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    relevancia: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tipo': self.tipo,
            'contenido': self.contenido,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'relevancia': self.relevancia
        }


@dataclass
class ResultadoBusqueda:
    """Resultado de una búsqueda en la memoria"""
    recuerdos: List[Recuerdo]
    tiempo_busqueda: float
    total_encontrados: int


class MemoriaVectorial:
    """
    Sistema de memoria persistente con búsqueda semántica.
    Usa ChromaDB para almacenar y buscar recuerdos por similitud.
    """
    
    MAX_DOCUMENTOS_POR_COLECCION = 10000
    
    COLECCIONES = {
        'conversaciones': 'andromeda_conversaciones',
        'analisis': 'andromeda_analisis', 
        'errores': 'andromeda_errores',
        'alertas': 'andromeda_alertas',
        'reportes': 'andromeda_reportes',
        'conocimiento': 'andromeda_conocimiento'
    }
    
    def __init__(self, directorio_db: str = None):
        """
        Inicializa la memoria vectorial.
        
        Args:
            directorio_db: Ruta donde guardar la base de datos
        """
        self.disponible = CHROMADB_DISPONIBLE
        self.directorio = directorio_db or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'memoria'
        )
        
        # Crear directorio si no existe
        os.makedirs(self.directorio, exist_ok=True)
        
        self.cliente = None
        self.colecciones = {}
        self.modelo_embeddings = None
        
        if self.disponible:
            self._inicializar_db()
            self._inicializar_embeddings()
    
    def _inicializar_db(self):
        """Inicializa la conexión a ChromaDB"""
        try:
            self.cliente = chromadb.PersistentClient(
                path=self.directorio,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Embedding function explícita para consistencia vectorial (lazy)
            self._embedding_function = None
            
            # Crear colecciones (embedding function se aplica tras _inicializar_embeddings)
            for nombre, coleccion_id in self.COLECCIONES.items():
                try:
                    self.colecciones[nombre] = self.cliente.get_or_create_collection(
                        name=coleccion_id,
                        metadata={"descripcion": f"Memoria de {nombre}"}
                    )
                except Exception as e:
                    logger.error(f"Error creando colección {nombre}: {e}")
            
            logger.info("Memoria Vectorial ChromaDB inicializada")
            
        except Exception as e:
            logger.error(f"Error inicializando ChromaDB: {e}")
            self.disponible = False
    
    def _inicializar_embeddings(self):
        """Inicializa el modelo de embeddings local (carga lazy)"""
        global EMBEDDINGS_DISPONIBLES, SentenceTransformer
        
        # Intentar cargar sentence_transformers de forma lazy
        if not EMBEDDINGS_DISPONIBLES:
            try:
                from sentence_transformers import SentenceTransformer as ST
                SentenceTransformer = ST
                EMBEDDINGS_DISPONIBLES = True
            except ImportError:
                logger.info("sentence-transformers no disponible - usando embeddings de ChromaDB")
                return
        
        try:
            # Modelo multilingüe ligero y eficiente
            self.modelo_embeddings = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2',
                device='cpu'
            )
            logger.info("Modelo de embeddings cargado")
            # Re-crear colecciones con embedding function explícita para consistencia
            self._aplicar_embedding_function()
        except Exception as e:
            logger.warning(f"No se pudo cargar modelo embeddings: {e}")
            self.modelo_embeddings = None
    
    def _aplicar_embedding_function(self):
        """Recrea colecciones con SentenceTransformerEmbeddingFunction explícita."""
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            ef = SentenceTransformerEmbeddingFunction(
                model_name='paraphrase-multilingual-MiniLM-L12-v2'
            )
            self._embedding_function = ef
            for nombre, coleccion_id in self.COLECCIONES.items():
                try:
                    self.colecciones[nombre] = self.cliente.get_or_create_collection(
                        name=coleccion_id,
                        metadata={"descripcion": f"Memoria de {nombre}"},
                        embedding_function=ef
                    )
                except Exception as e:
                    logger.debug(f"No se pudo re-crear colección {nombre} con EF: {e}")
        except Exception:
            logger.debug("SentenceTransformerEmbeddingFunction no disponible")
    
    def _generar_id(self, contenido: str, tipo: str) -> str:
        """Genera un ID único basado en el contenido"""
        texto = f"{tipo}:{contenido}:{datetime.now().isoformat()}"
        return hashlib.sha256(texto.encode()).hexdigest()[:16]
    
    def _generar_embedding(self, texto: str) -> Optional[List[float]]:
        """Genera embedding para un texto"""
        if self.modelo_embeddings is None:
            return None
        try:
            embedding = self.modelo_embeddings.encode(texto, convert_to_numpy=True)
            result = embedding.tolist()
            # Validar que el resultado es una lista real de números.
            # Se usa float() para aceptar tanto Python float como numpy.float32/float64
            # y rechazar MagicMock/None/strings de contaminación de tests.
            if isinstance(result, list) and len(result) > 0:
                try:
                    float(result[0])   # Lanza TypeError/ValueError si no es numérico
                    return result
                except (TypeError, ValueError):
                    pass
            # Resultado inválido (p.ej. MagicMock de tests) — desactivar modelo
            logger.warning("Embedding retornó tipo inválido, desactivando modelo de embeddings")
            self.modelo_embeddings = None
            return None
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None
    
    # =========================================================================
    # CONTROL DE CRECIMIENTO
    # =========================================================================
    
    def _controlar_crecimiento(self, coleccion) -> None:
        """Auto-limpia una colección si excede el límite de documentos."""
        try:
            total = coleccion.count()
            if total >= self.MAX_DOCUMENTOS_POR_COLECCION:
                logger.warning(f"Colección alcanzó {total} docs (límite {self.MAX_DOCUMENTOS_POR_COLECCION}). Purgando antiguos...")
                self._purgar_coleccion(coleccion, dias=60)
        except Exception as e:
            logger.error(f"Error controlando crecimiento: {e}")

    def _purgar_coleccion(self, coleccion, dias: int = 60) -> int:
        """Purga documentos antiguos de UNA colección específica."""
        eliminados = 0
        try:
            fecha_limite = (datetime.now() - __import__('datetime').timedelta(days=dias)).strftime('%Y-%m-%d')
            resultado = coleccion.get(include=['metadatas'], limit=5000)
            if resultado and resultado['ids']:
                ids_a_eliminar = [
                    resultado['ids'][i]
                    for i, meta in enumerate(resultado['metadatas'])
                    if meta.get('fecha', '9999-99-99') < fecha_limite
                ]
                if ids_a_eliminar:
                    coleccion.delete(ids=ids_a_eliminar)
                    eliminados = len(ids_a_eliminar)
        except Exception as e:
            logger.error(f"Error purgando colección: {e}")
        return eliminados
    
    # =========================================================================
    # GUARDAR RECUERDOS
    # =========================================================================
    
    def guardar_conversacion(
        self,
        mensaje_usuario: str,
        respuesta_andromeda: str,
        intencion: str = None,
        accion_ejecutada: str = None,
        metadata_extra: Dict = None
    ) -> bool:
        """
        Guarda una conversación en la memoria.
        
        Args:
            mensaje_usuario: Lo que escribió el usuario
            respuesta_andromeda: La respuesta de ANDROMEDA
            intencion: Intención detectada
            accion_ejecutada: Acción que se ejecutó
            metadata_extra: Información adicional
        """
        if not self.disponible:
            return False
        
        try:
            contenido = f"Usuario: {mensaje_usuario}\nAndromeda: {respuesta_andromeda}"
            id_recuerdo = self._generar_id(contenido, 'conversacion')
            
            metadata = {
                'tipo': 'conversacion',
                'mensaje_usuario': mensaje_usuario[:500],  # Limitar tamaño
                'intencion': intencion or 'desconocida',
                'accion': accion_ejecutada or 'ninguna',
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'hora': datetime.now().strftime('%H:%M:%S')
            }
            
            if metadata_extra:
                metadata.update({k: str(v)[:200] for k, v in metadata_extra.items()})
            
            # Guardar con o sin embedding propio
            coleccion = self.colecciones.get('conversaciones')
            if coleccion:
                self._controlar_crecimiento(coleccion)
                embedding = self._generar_embedding(contenido)
                if embedding:
                    coleccion.add(
                        ids=[id_recuerdo],
                        embeddings=[embedding],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                else:
                    coleccion.add(
                        ids=[id_recuerdo],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                return True
                
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
        
        return False
    
    def guardar_analisis(
        self,
        tipo_analisis: str,
        resumen: str,
        datos: Dict[str, Any],
        hallazgos: List[str] = None,
        recomendaciones: List[str] = None
    ) -> bool:
        """
        Guarda un análisis realizado.
        
        Args:
            tipo_analisis: Tipo de análisis (auditoría, ventas, inventario, etc.)
            resumen: Resumen del análisis
            datos: Datos del análisis
            hallazgos: Lista de hallazgos importantes
            recomendaciones: Lista de recomendaciones
        """
        if not self.disponible:
            return False
        
        try:
            # Construir contenido rico para búsqueda
            contenido_partes = [
                f"Análisis: {tipo_analisis}",
                f"Resumen: {resumen}"
            ]
            
            if hallazgos:
                contenido_partes.append(f"Hallazgos: {'; '.join(hallazgos[:10])}")
            
            if recomendaciones:
                contenido_partes.append(f"Recomendaciones: {'; '.join(recomendaciones[:10])}")
            
            contenido = "\n".join(contenido_partes)
            id_recuerdo = self._generar_id(contenido, 'analisis')
            
            metadata = {
                'tipo': 'analisis',
                'tipo_analisis': tipo_analisis,
                'resumen': resumen[:500],
                'num_hallazgos': len(hallazgos) if hallazgos else 0,
                'num_recomendaciones': len(recomendaciones) if recomendaciones else 0,
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'datos_json': json.dumps(datos, default=str)[:1000]
            }
            
            coleccion = self.colecciones.get('analisis')
            if coleccion:
                self._controlar_crecimiento(coleccion)
                embedding = self._generar_embedding(contenido)
                if embedding:
                    coleccion.add(
                        ids=[id_recuerdo],
                        embeddings=[embedding],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                else:
                    coleccion.add(
                        ids=[id_recuerdo],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                return True
                
        except Exception as e:
            logger.error(f"Error guardando análisis: {e}")
        
        return False
    
    def guardar_error(
        self,
        tipo_error: str,
        descripcion: str,
        datos_relacionados: Dict = None,
        solucion: str = None,
        resuelto: bool = False
    ) -> str:
        """
        Guarda un error detectado para seguimiento.
        
        Returns:
            ID del error guardado
        """
        if not self.disponible:
            return ""
        
        try:
            contenido = f"Error: {tipo_error}\nDescripción: {descripcion}"
            if solucion:
                contenido += f"\nSolución: {solucion}"
            
            id_recuerdo = self._generar_id(contenido, 'error')
            
            metadata = {
                'tipo': 'error',
                'tipo_error': tipo_error,
                'descripcion': descripcion[:500],
                'resuelto': str(resuelto),
                'solucion': (solucion or '')[:500],
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%Y-%m-%d')
            }
            
            if datos_relacionados:
                metadata['datos'] = json.dumps(datos_relacionados, default=str)[:1000]
            
            coleccion = self.colecciones.get('errores')
            if coleccion:
                self._controlar_crecimiento(coleccion)
                embedding = self._generar_embedding(contenido)
                if embedding:
                    coleccion.add(
                        ids=[id_recuerdo],
                        embeddings=[embedding],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                else:
                    coleccion.add(
                        ids=[id_recuerdo],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                return id_recuerdo
                
        except Exception as e:
            logger.error(f"Error guardando error: {e}")
        
        return ""
    
    def marcar_error_resuelto(self, id_error: str, solucion: str) -> bool:
        """Marca un error como resuelto"""
        if not self.disponible:
            return False
        
        try:
            coleccion = self.colecciones.get('errores')
            if coleccion:
                # Obtener el error actual
                resultado = coleccion.get(ids=[id_error], include=['metadatas', 'documents'])
                if resultado and resultado['ids']:
                    metadata = resultado['metadatas'][0]
                    metadata['resuelto'] = 'True'
                    metadata['solucion'] = solucion[:500]
                    metadata['fecha_resolucion'] = datetime.now().isoformat()
                    
                    coleccion.update(
                        ids=[id_error],
                        metadatas=[metadata]
                    )
                    return True
        except Exception as e:
            logger.error(f"Error marcando como resuelto: {e}")
        
        return False
    
    def guardar_alerta(
        self,
        tipo_alerta: str,
        mensaje: str,
        severidad: str = 'media',  # baja, media, alta, critica
        datos: Dict = None
    ) -> bool:
        """Guarda una alerta para seguimiento"""
        if not self.disponible:
            return False
        
        try:
            contenido = f"Alerta {severidad}: {tipo_alerta} - {mensaje}"
            id_recuerdo = self._generar_id(contenido, 'alerta')
            
            metadata = {
                'tipo': 'alerta',
                'tipo_alerta': tipo_alerta,
                'severidad': severidad,
                'mensaje': mensaje[:500],
                'atendida': 'False',
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%Y-%m-%d')
            }
            
            if datos:
                metadata['datos'] = json.dumps(datos, default=str)[:1000]
            
            coleccion = self.colecciones.get('alertas')
            if coleccion:
                self._controlar_crecimiento(coleccion)
                embedding = self._generar_embedding(contenido)
                if embedding:
                    coleccion.add(
                        ids=[id_recuerdo],
                        embeddings=[embedding],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                else:
                    coleccion.add(
                        ids=[id_recuerdo],
                        documents=[contenido],
                        metadatas=[metadata]
                    )
                return True
                
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")
        
        return False
    
    # =========================================================================
    # BUSCAR RECUERDOS
    # =========================================================================
    
    def buscar(
        self,
        consulta: str,
        coleccion: str = 'conversaciones',
        limite: int = 5,
        filtros: Dict = None
    ) -> ResultadoBusqueda:
        """
        Busca recuerdos similares a la consulta.
        
        Args:
            consulta: Texto a buscar
            coleccion: Colección donde buscar
            limite: Máximo de resultados
            filtros: Filtros adicionales (ej: {'fecha': '2026-02-17'})
        """
        import time
        inicio = time.time()
        recuerdos = []
        
        if not self.disponible:
            return ResultadoBusqueda(recuerdos=[], tiempo_busqueda=0, total_encontrados=0)
        
        try:
            col = self.colecciones.get(coleccion)
            if not col:
                return ResultadoBusqueda(recuerdos=[], tiempo_busqueda=0, total_encontrados=0)
            
            # Preparar filtros ChromaDB
            where_filtro = None
            if filtros:
                condiciones = []
                for k, v in filtros.items():
                    condiciones.append({k: v})
                if len(condiciones) == 1:
                    where_filtro = condiciones[0]
                elif len(condiciones) > 1:
                    where_filtro = {"$and": condiciones}
            
            # Buscar con embedding propio si está disponible
            embedding = self._generar_embedding(consulta)
            
            if embedding:
                resultados = col.query(
                    query_embeddings=[embedding],
                    n_results=limite,
                    where=where_filtro,
                    include=['documents', 'metadatas', 'distances']
                )
            else:
                resultados = col.query(
                    query_texts=[consulta],
                    n_results=limite,
                    where=where_filtro,
                    include=['documents', 'metadatas', 'distances']
                )
            
            # Procesar resultados
            if resultados and resultados['ids'] and resultados['ids'][0]:
                for i, id_rec in enumerate(resultados['ids'][0]):
                    distancia = resultados['distances'][0][i] if resultados['distances'] else 1.0
                    relevancia = max(0, 1 - distancia)  # Convertir distancia a relevancia
                    
                    recuerdo = Recuerdo(
                        id=id_rec,
                        tipo=resultados['metadatas'][0][i].get('tipo', 'desconocido'),
                        contenido=resultados['documents'][0][i],
                        metadata=resultados['metadatas'][0][i],
                        timestamp=resultados['metadatas'][0][i].get('timestamp', ''),
                        relevancia=relevancia
                    )
                    recuerdos.append(recuerdo)
                    
        except Exception as e:
            logger.error(f"Error buscando en memoria: {e}")
        
        tiempo = time.time() - inicio
        return ResultadoBusqueda(
            recuerdos=recuerdos,
            tiempo_busqueda=tiempo,
            total_encontrados=len(recuerdos)
        )
    
    def buscar_errores_similares(self, descripcion: str, solo_no_resueltos: bool = True) -> List[Recuerdo]:
        """Busca errores similares al descrito"""
        filtros = {'resuelto': 'False'} if solo_no_resueltos else None
        resultado = self.buscar(descripcion, 'errores', limite=5, filtros=filtros)
        return resultado.recuerdos
    
    def buscar_conversaciones_recientes(self, tema: str, dias: int = 7) -> List[Recuerdo]:
        """Busca conversaciones recientes sobre un tema"""
        from datetime import timedelta
        fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        
        # Buscar sin filtro de fecha primero y filtrar después
        resultado = self.buscar(tema, 'conversaciones', limite=20)
        
        # Filtrar por fecha
        recuerdos_filtrados = [
            r for r in resultado.recuerdos 
            if r.metadata.get('fecha', '') >= fecha_limite
        ]
        
        return recuerdos_filtrados[:5]
    
    def obtener_contexto_para_llm(self, consulta: str, max_recuerdos: int = 3) -> str:
        """
        Obtiene contexto relevante de la memoria para incluir en el prompt del LLM.
        
        Returns:
            Texto formateado con los recuerdos relevantes
        """
        contexto_partes = []
        
        # Buscar en conversaciones
        conv = self.buscar(consulta, 'conversaciones', limite=2)
        if conv.recuerdos:
            contexto_partes.append("**Conversaciones previas relacionadas:**")
            for r in conv.recuerdos:
                fecha = r.metadata.get('fecha', 'N/A')
                contexto_partes.append(f"  [{fecha}] {r.contenido[:200]}...")
        
        # Buscar en análisis
        analisis = self.buscar(consulta, 'analisis', limite=2)
        if analisis.recuerdos:
            contexto_partes.append("\n**Análisis previos relacionados:**")
            for r in analisis.recuerdos:
                fecha = r.metadata.get('fecha', 'N/A')
                tipo = r.metadata.get('tipo_analisis', 'N/A')
                contexto_partes.append(f"  [{fecha}] {tipo}: {r.metadata.get('resumen', '')[:200]}")
        
        # Buscar errores no resueltos
        errores = self.buscar(consulta, 'errores', limite=2, filtros={'resuelto': 'False'})
        if errores.recuerdos:
            contexto_partes.append("\n**Errores pendientes relacionados:**")
            for r in errores.recuerdos:
                fecha = r.metadata.get('fecha', 'N/A')
                contexto_partes.append(f"  [{fecha}] {r.metadata.get('descripcion', '')[:200]}")
        
        if contexto_partes:
            return "\n".join(contexto_partes)
        
        return ""
    
    # =========================================================================
    # ESTADÍSTICAS Y MANTENIMIENTO
    # =========================================================================
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria"""
        stats = {
            'disponible': self.disponible,
            'colecciones': {}
        }
        
        if self.disponible:
            for nombre, col in self.colecciones.items():
                try:
                    count = col.count()
                    stats['colecciones'][nombre] = count
                except Exception:
                    stats['colecciones'][nombre] = 0
            
            stats['total_recuerdos'] = sum(stats['colecciones'].values())
            stats['directorio'] = self.directorio
            stats['embeddings_disponibles'] = self.modelo_embeddings is not None
        
        return stats
    
    def limpiar_antiguos(self, dias: int = 90) -> int:
        """
        Elimina recuerdos más antiguos que X días.
        
        Returns:
            Número de recuerdos eliminados
        """
        if not self.disponible:
            return 0
        
        from datetime import timedelta
        fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        eliminados = 0
        
        for nombre, col in self.colecciones.items():
            try:
                # Obtener todos los IDs con fecha antigua
                resultado = col.get(include=['metadatas'])
                if resultado and resultado['ids']:
                    ids_a_eliminar = []
                    for i, meta in enumerate(resultado['metadatas']):
                        if meta.get('fecha', '9999-99-99') < fecha_limite:
                            ids_a_eliminar.append(resultado['ids'][i])
                    
                    if ids_a_eliminar:
                        col.delete(ids=ids_a_eliminar)
                        eliminados += len(ids_a_eliminar)
                        
            except Exception as e:
                logger.error(f"Error limpiando {nombre}: {e}")
        
        return eliminados


# Singleton global
_memoria_global: Optional[MemoriaVectorial] = None


def obtener_memoria() -> MemoriaVectorial:
    """Obtiene la instancia global de memoria"""
    global _memoria_global
    if _memoria_global is None:
        _memoria_global = MemoriaVectorial()
    return _memoria_global


# Para importación directa
__all__ = [
    'MemoriaVectorial',
    'Recuerdo',
    'ResultadoBusqueda',
    'obtener_memoria',
    'CHROMADB_DISPONIBLE'
]
