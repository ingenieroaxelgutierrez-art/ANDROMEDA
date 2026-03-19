# -*- coding: utf-8 -*-
"""
ANDROMEDA - Grafo de Conocimiento Empresarial
===============================================
Grafo en memoria con NetworkX que conecta entidades del negocio
(clientes, productos, acciones, análisis) y permite razonamiento
relacional multi-hop para consultas complejas y cadenas de agentes.

Arquitectura:
  - Nodos: entidades del negocio (cliente, producto, accion, periodo, etc.)
  - Aristas: relaciones con peso temporal y tipo (compro, analizo, incluye, etc.)
  - Persistencia: JSON en data/memoria/grafo_conocimiento.json
  - Integración: se llama desde MemoriaJerarquica.registrar_interaccion()
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

try:
    import networkx as nx
    NETWORKX_DISPONIBLE = True
except ImportError:
    NETWORKX_DISPONIBLE = False
    nx = None

from app.logging_config import get_logger

logger = get_logger("services.memory.grafo_conocimiento")


# ============================================================
# Tipos de nodos y relaciones
# ============================================================

class TipoNodo:
    CLIENTE = "cliente"
    PRODUCTO = "producto"
    PROVEEDOR = "proveedor"
    EMPLEADO = "empleado"
    FACTURA = "factura"
    ORDEN = "orden"
    ACCION = "accion"
    INTENCION = "intencion"
    PERIODO = "periodo"
    MONTO = "monto"
    CATEGORIA = "categoria"
    TIENDA = "tienda"
    ALMACEN = "almacen"
    ANALISIS = "analisis"


class TipoRelacion:
    CONSULTO = "consultó"          # usuario → accion
    INVOLUCRA = "involucra"        # accion → entidad
    PERIODO_DE = "período_de"      # accion → periodo
    COMPRA = "compra"              # cliente → producto
    PROVEE = "provee"              # proveedor → producto
    VENDE = "vende"                # empleado/tienda → producto
    RELACIONADO = "relacionado"    # entidad → entidad (genérico)
    CONTIENE = "contiene"          # analisis → entidad
    RESULTADO = "resultado"        # accion → monto


# ============================================================
# Extractor de entidades desde texto y datos
# ============================================================

class ExtractorEntidades:
    """Extrae entidades de mensajes, respuestas y DataFrames."""

    # Patrones regex para extracción
    _PATRON_MONTO = re.compile(r'\$\s?([\d,]+\.?\d*)')
    _PATRON_PORCENTAJE = re.compile(r'(\d+\.?\d*)\s*%')
    _PATRON_FECHA_RANGO = re.compile(r'(\d{4}-\d{2}-\d{2})\s*(?:a|→|al?|-)\s*(\d{4}-\d{2}-\d{2})')

    # Columnas de Odoo que contienen nombres de entidad
    _COLS_ENTIDAD = {
        'partner_id': TipoNodo.CLIENTE,
        'partner_name': TipoNodo.CLIENTE,
        'customer_id': TipoNodo.CLIENTE,
        'cliente': TipoNodo.CLIENTE,
        'product_id': TipoNodo.PRODUCTO,
        'product_name': TipoNodo.PRODUCTO,
        'producto': TipoNodo.PRODUCTO,
        'display_name': None,  # genérico, depende del modelo
        'name': None,
        'supplier_id': TipoNodo.PROVEEDOR,
        'proveedor': TipoNodo.PROVEEDOR,
        'employee_id': TipoNodo.EMPLEADO,
        'empleado': TipoNodo.EMPLEADO,
        'vendedor': TipoNodo.EMPLEADO,
        'user_id': TipoNodo.EMPLEADO,
        'warehouse_id': TipoNodo.ALMACEN,
        'almacen': TipoNodo.ALMACEN,
        'location_id': TipoNodo.ALMACEN,
        'categ_id': TipoNodo.CATEGORIA,
        'categoria': TipoNodo.CATEGORIA,
        'pos_session_id': TipoNodo.TIENDA,
        'sesion': TipoNodo.TIENDA,
    }

    # Modelo Odoo → tipo de nodo predeterminado para 'name'/'display_name'
    _MODELO_A_TIPO = {
        'sale.order': TipoNodo.ORDEN,
        'account.move': TipoNodo.FACTURA,
        'product.product': TipoNodo.PRODUCTO,
        'product.template': TipoNodo.PRODUCTO,
        'res.partner': TipoNodo.CLIENTE,
        'purchase.order': TipoNodo.ORDEN,
        'pos.order': TipoNodo.ORDEN,
        'hr.employee': TipoNodo.EMPLEADO,
        'stock.warehouse': TipoNodo.ALMACEN,
    }

    def extraer_de_mensaje(self, mensaje: str) -> List[Tuple[str, str, Dict]]:
        """Extrae entidades de un mensaje de texto.
        Returns: lista de (tipo_nodo, nombre_nodo, metadata)
        """
        entidades = []

        # Montos
        for match in self._PATRON_MONTO.finditer(mensaje):
            valor = match.group(1).replace(',', '')
            try:
                monto = float(valor)
                if monto > 0:
                    entidades.append((TipoNodo.MONTO, f"${monto:,.2f}", {'valor': monto}))
            except ValueError:
                pass

        # Periodos
        for match in self._PATRON_FECHA_RANGO.finditer(mensaje):
            periodo = f"{match.group(1)}_{match.group(2)}"
            entidades.append((TipoNodo.PERIODO, periodo, {
                'fecha_inicio': match.group(1),
                'fecha_fin': match.group(2)
            }))

        return entidades

    def extraer_de_dataframe(self, df, modelo_erp: str = '', top_n: int = 10) -> List[Tuple[str, str, Dict]]:
        """Extrae entidades de un DataFrame de resultados Odoo.
        Solo extrae los top_n registros relevantes para no sobrecargar el grafo.
        """
        if df is None or not hasattr(df, 'columns') or df.empty:
            return []

        entidades = []
        tipo_default = self._MODELO_A_TIPO.get(modelo_erp)

        for col in df.columns:
            col_lower = str(col).lower()
            tipo = self._COLS_ENTIDAD.get(col_lower)

            # Si es name/display_name, usar tipo del modelo
            if tipo is None and col_lower in ('name', 'display_name'):
                tipo = tipo_default
            if tipo is None:
                continue

            # Extraer valores únicos (top N por frecuencia)
            try:
                valores = df[col].dropna()
                # Resolver tuplas de Odoo (id, name)
                valores = valores.apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else x
                )
                # Top N más frecuentes
                top = valores.value_counts().head(top_n)
                for nombre, count in top.items():
                    nombre_str = str(nombre).strip()
                    if nombre_str and nombre_str not in ('False', 'None', '', 'nan'):
                        entidades.append((tipo, nombre_str, {'frecuencia': int(count), 'columna': col}))
            except Exception:
                continue

        return entidades

    def extraer_de_parametros(self, parametros: Dict, accion: str = '') -> List[Tuple[str, str, Dict]]:
        """Extrae entidades de los parámetros de una consulta."""
        entidades = []
        if not parametros:
            return entidades

        if parametros.get('tienda'):
            entidades.append((TipoNodo.TIENDA, str(parametros['tienda']), {}))

        if parametros.get('fecha_inicio') and parametros.get('fecha_fin'):
            periodo = f"{parametros['fecha_inicio']}_{parametros['fecha_fin']}"
            entidades.append((TipoNodo.PERIODO, periodo, {
                'fecha_inicio': parametros['fecha_inicio'],
                'fecha_fin': parametros['fecha_fin']
            }))

        return entidades


# ============================================================
# Grafo de Conocimiento
# ============================================================

class GrafoConocimiento:
    """Grafo de conocimiento empresarial con NetworkX.
    
    Conecta entidades del negocio extraídas de consultas y resultados,
    permitiendo razonamiento relacional para cadenas multi-agente.
    """

    MAX_NODOS = 500         # Límite para evitar crecimiento descontrolado
    MAX_ARISTAS = 2000
    DECAY_DIAS = 90         # Aristas más viejas que esto se podan

    def __init__(self, archivo_persistencia: Optional[str] = None):
        if not NETWORKX_DISPONIBLE:
            self.grafo = None
            self.disponible = False
            logger.warning("NetworkX no disponible — grafo desactivado")
            return

        self.grafo = nx.DiGraph()
        self.disponible = True
        self.extractor = ExtractorEntidades()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.archivo = archivo_persistencia or os.path.join(
            base_dir, 'data', 'memoria', 'grafo_conocimiento.json'
        )

        self._cargar()
        self._contador_interacciones = 0

    # ============================================================
    # Persistencia
    # ============================================================

    def _cargar(self):
        """Carga el grafo desde JSON."""
        if not os.path.exists(self.archivo):
            return
        try:
            with open(self.archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for nodo in data.get('nodos', []):
                self.grafo.add_node(
                    nodo['id'],
                    tipo=nodo.get('tipo', ''),
                    nombre=nodo.get('nombre', ''),
                    creado=nodo.get('creado', ''),
                    **nodo.get('meta', {})
                )

            for arista in data.get('aristas', []):
                self.grafo.add_edge(
                    arista['origen'],
                    arista['destino'],
                    tipo=arista.get('tipo', ''),
                    peso=arista.get('peso', 1.0),
                    timestamp=arista.get('timestamp', ''),
                    **arista.get('meta', {})
                )

            logger.info(f"Grafo cargado: {self.grafo.number_of_nodes()} nodos, {self.grafo.number_of_edges()} aristas")
        except Exception as e:
            logger.error(f"Error cargando grafo: {e}")
            self.grafo = nx.DiGraph()

    def guardar(self):
        """Persiste el grafo a JSON."""
        if not self.disponible:
            return
        try:
            nodos = []
            for nid, attrs in self.grafo.nodes(data=True):
                meta = {k: v for k, v in attrs.items() if k not in ('tipo', 'nombre', 'creado')}
                nodos.append({
                    'id': nid,
                    'tipo': attrs.get('tipo', ''),
                    'nombre': attrs.get('nombre', ''),
                    'creado': attrs.get('creado', ''),
                    'meta': meta
                })

            aristas = []
            for u, v, attrs in self.grafo.edges(data=True):
                meta = {k: v_attr for k, v_attr in attrs.items() if k not in ('tipo', 'peso', 'timestamp')}
                aristas.append({
                    'origen': u,
                    'destino': v,
                    'tipo': attrs.get('tipo', ''),
                    'peso': attrs.get('peso', 1.0),
                    'timestamp': attrs.get('timestamp', ''),
                    'meta': meta
                })

            os.makedirs(os.path.dirname(self.archivo), exist_ok=True)
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump({'nodos': nodos, 'aristas': aristas}, f, ensure_ascii=False, indent=1)

        except Exception as e:
            logger.error(f"Error guardando grafo: {e}")

    # ============================================================
    # Gestión de nodos y aristas
    # ============================================================

    def _nodo_id(self, tipo: str, nombre: str) -> str:
        """Genera un ID determinista para un nodo."""
        clave = f"{tipo}:{nombre.lower().strip()}"
        return hashlib.md5(clave.encode()).hexdigest()[:12]

    def agregar_nodo(self, tipo: str, nombre: str, **metadata) -> str:
        """Agrega o actualiza un nodo. Retorna su ID."""
        if not self.disponible:
            return ""
        nid = self._nodo_id(tipo, nombre)
        ahora = datetime.now().isoformat()

        if self.grafo.has_node(nid):
            # Actualizar peso (acceso reciente)
            self.grafo.nodes[nid]['ultimo_acceso'] = ahora
            accesos = self.grafo.nodes[nid].get('accesos', 0)
            self.grafo.nodes[nid]['accesos'] = accesos + 1
        else:
            self.grafo.add_node(
                nid,
                tipo=tipo,
                nombre=nombre,
                creado=ahora,
                ultimo_acceso=ahora,
                accesos=1,
                **metadata
            )

        return nid

    def agregar_relacion(self, origen_id: str, destino_id: str, tipo_relacion: str, **metadata):
        """Agrega o refuerza una relación entre nodos."""
        if not self.disponible or not origen_id or not destino_id:
            return
        ahora = datetime.now().isoformat()

        if self.grafo.has_edge(origen_id, destino_id):
            # Reforzar: incrementar peso
            datos = self.grafo[origen_id][destino_id]
            datos['peso'] = datos.get('peso', 1.0) + 0.5
            datos['timestamp'] = ahora
        else:
            self.grafo.add_edge(
                origen_id,
                destino_id,
                tipo=tipo_relacion,
                peso=1.0,
                timestamp=ahora,
                **metadata
            )

    # ============================================================
    # Registro de interacciones
    # ============================================================

    def registrar_interaccion(
        self,
        mensaje: str,
        respuesta: str,
        accion: str,
        intencion: str,
        parametros: Optional[Dict] = None,
        df=None,
        modelo_erp: str = '',
        confianza: float = 0.0
    ):
        """Extrae entidades y construye relaciones a partir de una interacción completa.
        
        Se llama desde MemoriaJerarquica.registrar_interaccion() después de guardar
        en sesión/contexto/vectorial.
        """
        if not self.disponible:
            return

        ahora = datetime.now().isoformat()

        # 1. Nodo central: la acción ejecutada
        nodo_accion = self.agregar_nodo(
            TipoNodo.ACCION, accion,
            intencion=intencion,
            confianza=round(confianza, 3),
            mensaje_resumen=mensaje[:150]
        )

        # 2. Nodo de intención (si difiere de acción)
        if intencion and intencion != accion:
            nodo_intencion = self.agregar_nodo(TipoNodo.INTENCION, intencion)
            self.agregar_relacion(nodo_intencion, nodo_accion, TipoRelacion.CONSULTO)

        # 3. Entidades del mensaje
        ents_msg = self.extractor.extraer_de_mensaje(mensaje)
        for tipo, nombre, meta in ents_msg:
            nid = self.agregar_nodo(tipo, nombre, **meta)
            self.agregar_relacion(nodo_accion, nid, TipoRelacion.INVOLUCRA)

        # 4. Entidades de parámetros
        ents_params = self.extractor.extraer_de_parametros(parametros or {}, accion)
        for tipo, nombre, meta in ents_params:
            nid = self.agregar_nodo(tipo, nombre, **meta)
            rel = TipoRelacion.PERIODO_DE if tipo == TipoNodo.PERIODO else TipoRelacion.INVOLUCRA
            self.agregar_relacion(nodo_accion, nid, rel)

        # 5. Entidades del DataFrame (datos reales de Odoo)
        ents_df = self.extractor.extraer_de_dataframe(df, modelo_erp, top_n=8)
        for tipo, nombre, meta in ents_df:
            nid = self.agregar_nodo(tipo, nombre, **meta)
            self.agregar_relacion(nodo_accion, nid, TipoRelacion.CONTIENE)

        # 6. Entidades de la respuesta (montos mencionados)
        ents_resp = self.extractor.extraer_de_mensaje(respuesta[:500])
        for tipo, nombre, meta in ents_resp:
            if tipo == TipoNodo.MONTO:
                nid = self.agregar_nodo(tipo, nombre, **meta)
                self.agregar_relacion(nodo_accion, nid, TipoRelacion.RESULTADO)

        # 7. Conectar entidades entre sí por co-ocurrencia en la misma acción
        nodos_entidades = [self._nodo_id(t, n) for t, n, _ in ents_df if t != TipoNodo.MONTO]
        for i, nid_a in enumerate(nodos_entidades):
            for nid_b in nodos_entidades[i+1:]:
                if nid_a != nid_b:
                    self.agregar_relacion(nid_a, nid_b, TipoRelacion.RELACIONADO)

        # 8. Podar si supera límites
        self._podar_si_necesario()

        # 9. Persistir cada 5 interacciones
        self._contador_interacciones += 1
        if self._contador_interacciones % 5 == 0:
            self.guardar()

    # ============================================================
    # Consultas al grafo
    # ============================================================

    def obtener_contexto_relacional(self, accion: str, entidades: List[str] = None, max_hops: int = 2, limite: int = 10) -> str:
        """Obtiene contexto relacional relevante para una acción/consulta.
        
        Recorre el grafo N hops desde los nodos de interés y genera
        un resumen de texto para inyectar en prompts del LLM.
        
        Args:
            accion: nombre de la acción actual
            entidades: nombres de entidades mencionadas por el usuario
            max_hops: profundidad de búsqueda (1=directo, 2=transitivo)
            limite: máximo de relaciones a incluir
            
        Returns:
            Texto con relaciones relevantes del grafo
        """
        if not self.disponible or self.grafo.number_of_nodes() == 0:
            return ""

        nodos_semilla = set()

        # Semilla: nodo de la acción actual
        nid_accion = self._nodo_id(TipoNodo.ACCION, accion)
        if self.grafo.has_node(nid_accion):
            nodos_semilla.add(nid_accion)

        # Semilla: entidades mencionadas (buscar por nombre parcial)
        if entidades:
            for ent in entidades:
                for nid, attrs in self.grafo.nodes(data=True):
                    nombre = attrs.get('nombre', '').lower()
                    if ent.lower() in nombre or nombre in ent.lower():
                        nodos_semilla.add(nid)

        if not nodos_semilla:
            return ""

        # BFS limitado desde semillas
        relaciones_encontradas = []
        visitados = set()

        for semilla in nodos_semilla:
            cola = [(semilla, 0)]
            while cola and len(relaciones_encontradas) < limite:
                nodo_actual, hop = cola.pop(0)
                if nodo_actual in visitados or hop > max_hops:
                    continue
                visitados.add(nodo_actual)

                # Explorar aristas salientes
                for _, vecino, data in self.grafo.out_edges(nodo_actual, data=True):
                    attrs_origen = self.grafo.nodes.get(nodo_actual, {})
                    attrs_destino = self.grafo.nodes.get(vecino, {})
                    if attrs_origen.get('tipo') and attrs_destino.get('tipo'):
                        relaciones_encontradas.append({
                            'origen': attrs_origen.get('nombre', ''),
                            'tipo_origen': attrs_origen.get('tipo', ''),
                            'relacion': data.get('tipo', ''),
                            'destino': attrs_destino.get('nombre', ''),
                            'tipo_destino': attrs_destino.get('tipo', ''),
                            'peso': data.get('peso', 1.0),
                        })
                    if hop < max_hops:
                        cola.append((vecino, hop + 1))

                # Explorar aristas entrantes
                for predecesor, _, data in self.grafo.in_edges(nodo_actual, data=True):
                    attrs_pred = self.grafo.nodes.get(predecesor, {})
                    attrs_actual = self.grafo.nodes.get(nodo_actual, {})
                    if attrs_pred.get('tipo') and attrs_actual.get('tipo'):
                        relaciones_encontradas.append({
                            'origen': attrs_pred.get('nombre', ''),
                            'tipo_origen': attrs_pred.get('tipo', ''),
                            'relacion': data.get('tipo', ''),
                            'destino': attrs_actual.get('nombre', ''),
                            'tipo_destino': attrs_actual.get('tipo', ''),
                            'peso': data.get('peso', 1.0),
                        })
                    if hop < max_hops:
                        cola.append((predecesor, hop + 1))

        if not relaciones_encontradas:
            return ""

        # Ordenar por peso (más relevantes primero) y deduplicar
        seen = set()
        unicas = []
        for rel in sorted(relaciones_encontradas, key=lambda x: x['peso'], reverse=True):
            key = (rel['origen'], rel['relacion'], rel['destino'])
            if key not in seen:
                seen.add(key)
                unicas.append(rel)

        # Generar texto
        lineas = ["**Relaciones conocidas del grafo:**"]
        for rel in unicas[:limite]:
            lineas.append(
                f"- {rel['tipo_origen'].title()} \"{rel['origen']}\" "
                f"→ [{rel['relacion']}] → "
                f"{rel['tipo_destino'].title()} \"{rel['destino']}\" "
                f"(peso: {rel['peso']:.1f})"
            )

        return "\n".join(lineas)

    def entidades_frecuentes(self, tipo: str = None, limite: int = 10) -> List[Dict]:
        """Retorna las entidades más consultadas/mencionadas."""
        if not self.disponible:
            return []

        nodos = []
        for nid, attrs in self.grafo.nodes(data=True):
            if tipo and attrs.get('tipo') != tipo:
                continue
            nodos.append({
                'id': nid,
                'tipo': attrs.get('tipo', ''),
                'nombre': attrs.get('nombre', ''),
                'accesos': attrs.get('accesos', 0),
                'conexiones': self.grafo.degree(nid),
            })

        return sorted(nodos, key=lambda x: (x['accesos'], x['conexiones']), reverse=True)[:limite]

    def relaciones_de(self, nombre_entidad: str) -> List[Dict]:
        """Obtiene todas las relaciones de una entidad específica."""
        if not self.disponible:
            return []

        # Buscar nodo por nombre
        nodo_id = None
        for nid, attrs in self.grafo.nodes(data=True):
            if attrs.get('nombre', '').lower() == nombre_entidad.lower():
                nodo_id = nid
                break

        if not nodo_id:
            return []

        relaciones = []

        # Salientes
        for _, vecino, data in self.grafo.out_edges(nodo_id, data=True):
            attrs = self.grafo.nodes.get(vecino, {})
            relaciones.append({
                'direccion': 'saliente',
                'relacion': data.get('tipo', ''),
                'entidad': attrs.get('nombre', ''),
                'tipo_entidad': attrs.get('tipo', ''),
                'peso': data.get('peso', 1.0),
            })

        # Entrantes
        for predecesor, _, data in self.grafo.in_edges(nodo_id, data=True):
            attrs = self.grafo.nodes.get(predecesor, {})
            relaciones.append({
                'direccion': 'entrante',
                'relacion': data.get('tipo', ''),
                'entidad': attrs.get('nombre', ''),
                'tipo_entidad': attrs.get('tipo', ''),
                'peso': data.get('peso', 1.0),
            })

        return sorted(relaciones, key=lambda x: x['peso'], reverse=True)

    def camino_entre(self, entidad_a: str, entidad_b: str) -> Optional[List[Dict]]:
        """Encuentra el camino más corto entre dos entidades.
        Útil para consultas multi-hop como "relación entre cliente X y producto Y".
        """
        if not self.disponible:
            return None

        nodo_a = nodo_b = None
        for nid, attrs in self.grafo.nodes(data=True):
            nombre = attrs.get('nombre', '').lower()
            if entidad_a.lower() in nombre:
                nodo_a = nid
            if entidad_b.lower() in nombre:
                nodo_b = nid

        if not nodo_a or not nodo_b:
            return None

        try:
            # Buscar en grafo no dirigido para encontrar cualquier camino
            camino = nx.shortest_path(self.grafo.to_undirected(), nodo_a, nodo_b)
            resultado = []
            for i, nid in enumerate(camino):
                attrs = self.grafo.nodes.get(nid, {})
                paso = {
                    'paso': i,
                    'tipo': attrs.get('tipo', ''),
                    'nombre': attrs.get('nombre', ''),
                }
                if i < len(camino) - 1:
                    siguiente = camino[i + 1]
                    edge = self.grafo.get_edge_data(nid, siguiente) or self.grafo.get_edge_data(siguiente, nid) or {}
                    paso['relacion'] = edge.get('tipo', 'conectado')
                resultado.append(paso)
            return resultado
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    # ============================================================
    # Estadísticas y mantenimiento
    # ============================================================

    def estadisticas(self) -> Dict[str, Any]:
        """Retorna estadísticas del grafo."""
        if not self.disponible:
            return {'disponible': False}

        tipos_nodos = defaultdict(int)
        for _, attrs in self.grafo.nodes(data=True):
            tipos_nodos[attrs.get('tipo', 'desconocido')] += 1

        tipos_relaciones = defaultdict(int)
        for _, _, attrs in self.grafo.edges(data=True):
            tipos_relaciones[attrs.get('tipo', 'desconocida')] += 1

        return {
            'disponible': True,
            'total_nodos': self.grafo.number_of_nodes(),
            'total_aristas': self.grafo.number_of_edges(),
            'nodos_por_tipo': dict(tipos_nodos),
            'relaciones_por_tipo': dict(tipos_relaciones),
            'densidad': round(nx.density(self.grafo), 4) if self.grafo.number_of_nodes() > 0 else 0,
        }

    def _podar_si_necesario(self):
        """Elimina nodos y aristas antiguos o con poco peso si se superan los límites."""
        if not self.disponible:
            return

        # Podar aristas viejas
        if self.grafo.number_of_edges() > self.MAX_ARISTAS:
            umbral = (datetime.now() - timedelta(days=self.DECAY_DIAS)).isoformat()
            aristas_eliminar = []
            for u, v, data in self.grafo.edges(data=True):
                ts = data.get('timestamp', '')
                if ts and ts < umbral and data.get('peso', 1.0) < 2.0:
                    aristas_eliminar.append((u, v))

            for u, v in aristas_eliminar[:200]:
                self.grafo.remove_edge(u, v)

        # Limpiar nodos huérfanos si el grafo tiene tamaño significativo
        if self.grafo.number_of_nodes() > 10:
            nodos_eliminar = [
                nid for nid, attrs in self.grafo.nodes(data=True)
                if self.grafo.degree(nid) == 0 and attrs.get('accesos', 0) < 2
            ]
            for nid in nodos_eliminar[:200]:
                self.grafo.remove_node(nid)

            if nodos_eliminar:
                logger.debug(f"Grafo: eliminados {min(len(nodos_eliminar), 200)} nodos huérfanos")


# ============================================================
# Singleton
# ============================================================

_grafo_global: Optional[GrafoConocimiento] = None


def obtener_grafo_conocimiento() -> GrafoConocimiento:
    """Retorna la instancia global del grafo de conocimiento."""
    global _grafo_global
    if _grafo_global is None:
        _grafo_global = GrafoConocimiento()
    return _grafo_global
