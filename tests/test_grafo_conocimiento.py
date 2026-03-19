# ============================================================
# ANDROMEDA — Tests de services/memory/grafo_conocimiento
# ============================================================

import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Verificar disponibilidad de networkx
try:
    import networkx as nx
    NETWORKX_DISPONIBLE = True
except ImportError:
    NETWORKX_DISPONIBLE = False

pytestmark = pytest.mark.skipif(
    not NETWORKX_DISPONIBLE, reason="networkx no instalado"
)

from services.memory.grafo_conocimiento import (
    GrafoConocimiento,
    ExtractorEntidades,
    TipoNodo,
    TipoRelacion,
    NETWORKX_DISPONIBLE as GC_DISPONIBLE,
)


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def grafo_tmp(tmp_path):
    """Grafo con archivo de persistencia temporal."""
    archivo = str(tmp_path / "grafo_test.json")
    return GrafoConocimiento(archivo_persistencia=archivo)


@pytest.fixture
def extractor():
    return ExtractorEntidades()


# ═══════════════════════════════════════════════════════════
# TipoNodo y TipoRelacion
# ═══════════════════════════════════════════════════════════

class TestTipos:

    def test_tipos_nodo_existen(self):
        assert TipoNodo.CLIENTE == "cliente"
        assert TipoNodo.PRODUCTO == "producto"
        assert TipoNodo.ACCION == "accion"
        assert TipoNodo.PERIODO == "periodo"
        assert TipoNodo.MONTO == "monto"

    def test_tipos_relacion_existen(self):
        assert TipoRelacion.CONSULTO == "consultó"
        assert TipoRelacion.INVOLUCRA == "involucra"
        assert TipoRelacion.CONTIENE == "contiene"
        assert TipoRelacion.RESULTADO == "resultado"


# ═══════════════════════════════════════════════════════════
# ExtractorEntidades
# ═══════════════════════════════════════════════════════════

class TestExtractorEntidades:

    def test_extraer_montos(self, extractor):
        msg = "Las ventas fueron $10,500.00 y $3,200.50"
        ents = extractor.extraer_de_mensaje(msg)
        tipos = [e[0] for e in ents]
        assert all(t == TipoNodo.MONTO for t in tipos)
        assert len(ents) == 2
        nombres = [e[1] for e in ents]
        assert "$10,500.00" in nombres
        assert "$3,200.50" in nombres

    def test_extraer_periodo_rango(self, extractor):
        msg = "ventas del 2024-01-01 a 2024-06-30"
        ents = extractor.extraer_de_mensaje(msg)
        periodos = [e for e in ents if e[0] == TipoNodo.PERIODO]
        assert len(periodos) == 1
        assert "2024-01-01" in periodos[0][1]
        assert "2024-06-30" in periodos[0][1]

    def test_extraer_sin_entidades(self, extractor):
        ents = extractor.extraer_de_mensaje("hola mundo")
        assert len(ents) == 0

    def test_extraer_de_dataframe_basico(self, extractor):
        import pandas as pd
        df = pd.DataFrame({
            'partner_id': ['Cliente A', 'Cliente B', 'Cliente A', 'Cliente C'],
            'product_id': ['Prod1', 'Prod2', 'Prod1', 'Prod3'],
            'amount_total': [100, 200, 150, 300],
        })
        ents = extractor.extraer_de_dataframe(df, modelo_erp='sale.order')
        tipos = [e[0] for e in ents]
        assert TipoNodo.CLIENTE in tipos
        assert TipoNodo.PRODUCTO in tipos

    def test_extraer_de_dataframe_vacio(self, extractor):
        import pandas as pd
        df = pd.DataFrame()
        assert extractor.extraer_de_dataframe(df) == []
        assert extractor.extraer_de_dataframe(None) == []

    def test_extraer_de_dataframe_tuplas_odoo(self, extractor):
        """Odoo devuelve campos many2one como (id, nombre)."""
        import pandas as pd
        df = pd.DataFrame({
            'partner_id': [(1, 'Juan'), (2, 'María'), (1, 'Juan')],
        })
        ents = extractor.extraer_de_dataframe(df)
        nombres = [e[1] for e in ents if e[0] == TipoNodo.CLIENTE]
        assert 'Juan' in nombres
        assert 'María' in nombres

    def test_extraer_de_parametros_tienda(self, extractor):
        params = {'tienda': 'Sucursal Norte'}
        ents = extractor.extraer_de_parametros(params, 'ventas_pos')
        assert any(e[0] == TipoNodo.TIENDA and e[1] == 'Sucursal Norte' for e in ents)

    def test_extraer_de_parametros_periodo(self, extractor):
        params = {'fecha_inicio': '2024-01-01', 'fecha_fin': '2024-12-31'}
        ents = extractor.extraer_de_parametros(params, 'ventas_totales')
        periodos = [e for e in ents if e[0] == TipoNodo.PERIODO]
        assert len(periodos) == 1

    def test_extraer_de_parametros_vacio(self, extractor):
        assert extractor.extraer_de_parametros({}) == []
        assert extractor.extraer_de_parametros(None) == []


# ═══════════════════════════════════════════════════════════
# GrafoConocimiento — Nodos y aristas
# ═══════════════════════════════════════════════════════════

class TestGrafoNodos:

    def test_agregar_nodo_simple(self, grafo_tmp):
        nid = grafo_tmp.agregar_nodo(TipoNodo.CLIENTE, "Juan Pérez")
        assert nid
        assert grafo_tmp.grafo.has_node(nid)
        assert grafo_tmp.grafo.nodes[nid]['nombre'] == "Juan Pérez"
        assert grafo_tmp.grafo.nodes[nid]['tipo'] == TipoNodo.CLIENTE

    def test_agregar_nodo_duplicado_incrementa_accesos(self, grafo_tmp):
        nid1 = grafo_tmp.agregar_nodo(TipoNodo.PRODUCTO, "Widget X")
        nid2 = grafo_tmp.agregar_nodo(TipoNodo.PRODUCTO, "Widget X")
        assert nid1 == nid2
        assert grafo_tmp.grafo.nodes[nid1]['accesos'] == 2

    def test_nodo_id_determinista(self, grafo_tmp):
        """El mismo tipo+nombre siempre genera el mismo ID."""
        id1 = grafo_tmp._nodo_id(TipoNodo.CLIENTE, "Test")
        id2 = grafo_tmp._nodo_id(TipoNodo.CLIENTE, "Test")
        id3 = grafo_tmp._nodo_id(TipoNodo.PRODUCTO, "Test")
        assert id1 == id2
        assert id1 != id3  # distinto tipo → distinto ID

    def test_nodo_id_case_insensitive(self, grafo_tmp):
        id1 = grafo_tmp._nodo_id(TipoNodo.CLIENTE, "JUAN")
        id2 = grafo_tmp._nodo_id(TipoNodo.CLIENTE, "juan")
        assert id1 == id2

    def test_agregar_relacion(self, grafo_tmp):
        n1 = grafo_tmp.agregar_nodo(TipoNodo.ACCION, "ventas_totales")
        n2 = grafo_tmp.agregar_nodo(TipoNodo.CLIENTE, "Empresa ABC")
        grafo_tmp.agregar_relacion(n1, n2, TipoRelacion.INVOLUCRA)
        assert grafo_tmp.grafo.has_edge(n1, n2)
        edge_data = grafo_tmp.grafo[n1][n2]
        assert edge_data['tipo'] == TipoRelacion.INVOLUCRA
        assert edge_data['peso'] == 1.0

    def test_relacion_duplicada_refuerza_peso(self, grafo_tmp):
        n1 = grafo_tmp.agregar_nodo(TipoNodo.ACCION, "inventario")
        n2 = grafo_tmp.agregar_nodo(TipoNodo.ALMACEN, "Bodega 1")
        grafo_tmp.agregar_relacion(n1, n2, TipoRelacion.INVOLUCRA)
        assert grafo_tmp.grafo[n1][n2]['peso'] == 1.0
        grafo_tmp.agregar_relacion(n1, n2, TipoRelacion.INVOLUCRA)
        assert grafo_tmp.grafo[n1][n2]['peso'] == 1.5
        grafo_tmp.agregar_relacion(n1, n2, TipoRelacion.INVOLUCRA)
        assert grafo_tmp.grafo[n1][n2]['peso'] == 2.0

    def test_relacion_ids_vacios_no_falla(self, grafo_tmp):
        """No debe agregar relación con IDs vacíos."""
        grafo_tmp.agregar_relacion("", "abc", TipoRelacion.INVOLUCRA)
        grafo_tmp.agregar_relacion("abc", "", TipoRelacion.INVOLUCRA)
        assert grafo_tmp.grafo.number_of_edges() == 0


# ═══════════════════════════════════════════════════════════
# GrafoConocimiento — Registro de interacciones
# ═══════════════════════════════════════════════════════════

class TestRegistrarInteraccion:

    def test_registrar_crea_nodo_accion(self, grafo_tmp):
        grafo_tmp.registrar_interaccion(
            mensaje="ver ventas totales",
            respuesta="Total: $50,000",
            accion="ventas_totales",
            intencion="consultar_ventas",
            parametros={},
        )
        # Debe tener al menos el nodo de acción
        tipos = [attrs.get('tipo') for _, attrs in grafo_tmp.grafo.nodes(data=True)]
        assert TipoNodo.ACCION in tipos

    def test_registrar_crea_nodo_intencion(self, grafo_tmp):
        grafo_tmp.registrar_interaccion(
            mensaje="ver ventas",
            respuesta="ok",
            accion="ventas_totales",
            intencion="consultar_ventas",  # difiere de accion
        )
        tipos = [attrs.get('tipo') for _, attrs in grafo_tmp.grafo.nodes(data=True)]
        assert TipoNodo.INTENCION in tipos

    def test_registrar_no_crea_intencion_duplicada(self, grafo_tmp):
        """Si intención == acción, no crea nodo de intención separado."""
        grafo_tmp.registrar_interaccion(
            mensaje="ver ventas",
            respuesta="ok",
            accion="ventas_totales",
            intencion="ventas_totales",
        )
        tipos = [attrs.get('tipo') for _, attrs in grafo_tmp.grafo.nodes(data=True)]
        assert TipoNodo.INTENCION not in tipos

    def test_registrar_extrae_montos_de_respuesta(self, grafo_tmp):
        grafo_tmp.registrar_interaccion(
            mensaje="total de ventas",
            respuesta="Las ventas totales son $125,000.00",
            accion="ventas_totales",
            intencion="consultar_ventas",
        )
        montos = [
            attrs['nombre']
            for _, attrs in grafo_tmp.grafo.nodes(data=True)
            if attrs.get('tipo') == TipoNodo.MONTO
        ]
        assert len(montos) >= 1
        assert "$125,000.00" in montos

    def test_registrar_con_dataframe(self, grafo_tmp):
        import pandas as pd
        df = pd.DataFrame({
            'partner_id': ['Cliente A', 'Cliente B'],
            'amount_total': [1000, 2000],
        })
        grafo_tmp.registrar_interaccion(
            mensaje="listar clientes",
            respuesta="ok",
            accion="ventas_por_cliente",
            intencion="consultar_ventas",
            df=df,
            modelo_erp='sale.order'
        )
        clientes = [
            attrs['nombre']
            for _, attrs in grafo_tmp.grafo.nodes(data=True)
            if attrs.get('tipo') == TipoNodo.CLIENTE
        ]
        assert 'Cliente A' in clientes
        assert 'Cliente B' in clientes

    def test_registrar_con_parametros_periodo(self, grafo_tmp):
        grafo_tmp.registrar_interaccion(
            mensaje="ventas enero",
            respuesta="$10,000",
            accion="ventas_totales",
            intencion="consultar_ventas",
            parametros={'fecha_inicio': '2024-01-01', 'fecha_fin': '2024-01-31'},
        )
        periodos = [
            attrs['nombre']
            for _, attrs in grafo_tmp.grafo.nodes(data=True)
            if attrs.get('tipo') == TipoNodo.PERIODO
        ]
        assert any('2024-01-01' in p for p in periodos)

    def test_registrar_multiples_crea_co_ocurrencias(self, grafo_tmp):
        """Entidades del mismo DataFrame se conectan entre sí."""
        import pandas as pd
        df = pd.DataFrame({
            'partner_id': ['A', 'B', 'A'],
            'product_id': ['X', 'Y', 'X'],
        })
        grafo_tmp.registrar_interaccion(
            mensaje="test",
            respuesta="ok",
            accion="test",
            intencion="test",
            df=df,
        )
        # Debe haber al menos una relación RELACIONADO entre entidades del DF
        relaciones = [
            attrs.get('tipo')
            for _, _, attrs in grafo_tmp.grafo.edges(data=True)
        ]
        assert TipoRelacion.RELACIONADO in relaciones


# ═══════════════════════════════════════════════════════════
# GrafoConocimiento — Consultas
# ═══════════════════════════════════════════════════════════

class TestConsultas:

    def _poblar_grafo(self, grafo):
        """Puebla un grafo con datos de ejemplo para consultas."""
        grafo.registrar_interaccion(
            mensaje="ver ventas de enero",
            respuesta="Total: $50,000.00",
            accion="ventas_totales",
            intencion="consultar_ventas",
            parametros={'fecha_inicio': '2024-01-01', 'fecha_fin': '2024-01-31'},
        )
        import pandas as pd
        df = pd.DataFrame({
            'partner_id': ['Empresa ABC', 'Empresa XYZ'],
            'product_id': ['Laptop Pro', 'Monitor 27'],
            'amount_total': [15000, 8000],
        })
        grafo.registrar_interaccion(
            mensaje="ventas por cliente",
            respuesta="Empresa ABC compró $15,000",
            accion="ventas_por_cliente",
            intencion="consultar_ventas",
            df=df,
            modelo_erp='sale.order',
        )

    def test_contexto_relacional_accion_conocida(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        ctx = grafo_tmp.obtener_contexto_relacional("ventas_por_cliente")
        assert ctx
        assert "Relaciones conocidas" in ctx

    def test_contexto_relacional_accion_desconocida(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        ctx = grafo_tmp.obtener_contexto_relacional("accion_inexistente_xyz")
        assert ctx == ""  # No hay semillas → vacío

    def test_contexto_relacional_con_entidades(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        ctx = grafo_tmp.obtener_contexto_relacional(
            "ventas_totales",
            entidades=["Empresa ABC"]
        )
        assert ctx
        assert "Empresa ABC" in ctx

    def test_contexto_relacional_grafo_vacio(self, grafo_tmp):
        ctx = grafo_tmp.obtener_contexto_relacional("ventas_totales")
        assert ctx == ""

    def test_entidades_frecuentes(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        frecuentes = grafo_tmp.entidades_frecuentes()
        assert len(frecuentes) > 0
        assert all('nombre' in e and 'accesos' in e for e in frecuentes)

    def test_entidades_frecuentes_por_tipo(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        clientes = grafo_tmp.entidades_frecuentes(tipo=TipoNodo.CLIENTE)
        assert all(e['tipo'] == TipoNodo.CLIENTE for e in clientes)

    def test_relaciones_de_entidad(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        rels = grafo_tmp.relaciones_de("Empresa ABC")
        assert len(rels) > 0

    def test_relaciones_de_entidad_inexistente(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        rels = grafo_tmp.relaciones_de("Entidad Que No Existe")
        assert rels == []

    def test_camino_entre_entidades(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        camino = grafo_tmp.camino_entre("Empresa ABC", "Laptop Pro")
        # Puede que haya camino directo o transitivo
        if camino:
            assert len(camino) >= 2
            nombres = [p['nombre'] for p in camino]
            assert 'Empresa ABC' in nombres
            assert 'Laptop Pro' in nombres

    def test_camino_entre_inexistentes(self, grafo_tmp):
        self._poblar_grafo(grafo_tmp)
        assert grafo_tmp.camino_entre("NoExiste1", "NoExiste2") is None


# ═══════════════════════════════════════════════════════════
# GrafoConocimiento — Persistencia
# ═══════════════════════════════════════════════════════════

class TestPersistencia:

    def test_guardar_y_cargar(self, tmp_path):
        archivo = str(tmp_path / "grafo_persist.json")

        # Crear y poblar
        g1 = GrafoConocimiento(archivo_persistencia=archivo)
        g1.agregar_nodo(TipoNodo.CLIENTE, "Test Client")
        g1.agregar_nodo(TipoNodo.PRODUCTO, "Test Product")
        n1 = g1._nodo_id(TipoNodo.CLIENTE, "Test Client")
        n2 = g1._nodo_id(TipoNodo.PRODUCTO, "Test Product")
        g1.agregar_relacion(n1, n2, TipoRelacion.COMPRA)
        g1.guardar()

        assert os.path.exists(archivo)

        # Cargar en nueva instancia
        g2 = GrafoConocimiento(archivo_persistencia=archivo)
        assert g2.grafo.number_of_nodes() == 2
        assert g2.grafo.number_of_edges() == 1
        assert g2.grafo.has_node(n1)
        assert g2.grafo.has_node(n2)
        assert g2.grafo.nodes[n1]['nombre'] == "Test Client"

    def test_cargar_archivo_inexistente(self, tmp_path):
        archivo = str(tmp_path / "no_existe.json")
        g = GrafoConocimiento(archivo_persistencia=archivo)
        assert g.disponible
        assert g.grafo.number_of_nodes() == 0

    def test_guardar_json_valido(self, tmp_path):
        archivo = str(tmp_path / "grafo_json.json")
        g = GrafoConocimiento(archivo_persistencia=archivo)
        g.agregar_nodo(TipoNodo.ACCION, "test_action")
        g.guardar()

        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'nodos' in data
        assert 'aristas' in data
        assert len(data['nodos']) == 1
        assert data['nodos'][0]['tipo'] == TipoNodo.ACCION


# ═══════════════════════════════════════════════════════════
# GrafoConocimiento — Estadísticas y poda
# ═══════════════════════════════════════════════════════════

class TestEstadisticas:

    def test_estadisticas_basicas(self, grafo_tmp):
        n1 = grafo_tmp.agregar_nodo(TipoNodo.CLIENTE, "A")
        n2 = grafo_tmp.agregar_nodo(TipoNodo.PRODUCTO, "B")
        grafo_tmp.agregar_relacion(n1, n2, TipoRelacion.COMPRA)

        stats = grafo_tmp.estadisticas()
        assert stats['disponible'] is True
        assert stats['total_nodos'] == 2
        assert stats['total_aristas'] == 1
        assert TipoNodo.CLIENTE in stats['nodos_por_tipo']
        assert TipoNodo.PRODUCTO in stats['nodos_por_tipo']

    def test_estadisticas_grafo_vacio(self, grafo_tmp):
        stats = grafo_tmp.estadisticas()
        assert stats['total_nodos'] == 0
        assert stats['total_aristas'] == 0
        assert stats['densidad'] == 0

    def test_poda_no_rompe_con_pocos_nodos(self, grafo_tmp):
        grafo_tmp.agregar_nodo(TipoNodo.ACCION, "test")
        grafo_tmp._podar_si_necesario()
        assert grafo_tmp.grafo.number_of_nodes() == 1


# ═══════════════════════════════════════════════════════════
# GrafoConocimiento — Modo degradado (sin networkx)
# ═══════════════════════════════════════════════════════════

class TestModoSinNetworkx:

    def test_grafo_no_disponible(self, tmp_path):
        """Simula que networkx no está instalado."""
        archivo = str(tmp_path / "grafo_sin_nx.json")
        g = GrafoConocimiento(archivo_persistencia=archivo)
        # Forzar modo degradado
        g.disponible = False
        g.grafo = None

        assert g.agregar_nodo(TipoNodo.CLIENTE, "test") == ""
        g.agregar_relacion("a", "b", TipoRelacion.COMPRA)  # no falla
        assert g.obtener_contexto_relacional("test") == ""
        assert g.entidades_frecuentes() == []
        assert g.relaciones_de("test") == []
        assert g.camino_entre("a", "b") is None
        assert g.estadisticas() == {'disponible': False}
        g.guardar()  # No falla
