# -*- coding: utf-8 -*-
"""
ANDROMEDA - Memoria Jerárquica
================================
Estructura de memoria multinivel para conversaciones persistentes:
- Memoria de sesión (corta)
- Memoria contextual (modelo ERP, filtros activos)
- Memoria de preferencias de usuario
- Memoria vectorial semántica
"""

import os
import json
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from .memoria_vectorial import MemoriaVectorial

try:
    from .grafo_conocimiento import GrafoConocimiento, obtener_grafo_conocimiento, NETWORKX_DISPONIBLE
    GRAFO_DISPONIBLE = NETWORKX_DISPONIBLE
except ImportError:
    GRAFO_DISPONIBLE = False
    GrafoConocimiento = None
    obtener_grafo_conocimiento = None

from app.logging_config import get_logger
logger = get_logger("services.memory.memoria_jerarquica")


@dataclass
class RegistroSesion:
    """Interacción breve para memoria de sesión."""
    timestamp: str
    mensaje_usuario: str
    respuesta: str
    intencion: str
    accion: str
    confianza: float


@dataclass
class MemoriaSesion:
    """Memoria corta de la sesión activa."""
    historial: List[RegistroSesion] = field(default_factory=list)
    max_interacciones: int = 25

    def agregar(self, registro: RegistroSesion):
        self.historial.append(registro)
        if len(self.historial) > self.max_interacciones:
            self.historial = self.historial[-self.max_interacciones:]

    def ultimas(self, n: int = 5) -> List[RegistroSesion]:
        return self.historial[-n:]


@dataclass
class MemoriaContextual:
    """Estado operativo contextual del diálogo."""
    modelo_erp_actual: Optional[str] = None
    filtros_activos: Dict[str, Any] = field(default_factory=dict)
    ultima_intencion: Optional[str] = None
    ultima_accion: Optional[str] = None


@dataclass
class MemoriaPreferenciasUsuario:
    """Preferencias persistentes del usuario."""
    usuario_id: str = "default"
    preferencias: Dict[str, Any] = field(default_factory=dict)


class MemoriaJerarquica:
    """Gestor unificado de memoria jerárquica."""

    def __init__(self, memoria_vectorial: Optional[MemoriaVectorial] = None, archivo_preferencias: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_memoria_dir = os.path.join(base_dir, 'data', 'memoria')
        os.makedirs(data_memoria_dir, exist_ok=True)

        self.memoria_sesion = MemoriaSesion()
        self.memoria_contextual = MemoriaContextual()
        self.memoria_preferencias = MemoriaPreferenciasUsuario()

        self.memoria_vectorial = memoria_vectorial
        self.archivo_preferencias = archivo_preferencias or os.path.join(data_memoria_dir, 'preferencias_usuario.json')

        # Grafo de conocimiento empresarial
        self.grafo = None
        if GRAFO_DISPONIBLE:
            try:
                self.grafo = obtener_grafo_conocimiento()
                logger.info(f"Grafo de conocimiento activo: {self.grafo.estadisticas().get('total_nodos', 0)} nodos")
            except Exception as e:
                logger.warning(f"No se pudo inicializar grafo: {e}")

        self._cargar_preferencias()

    # ============================================================
    # Preferencias de usuario (persistentes)
    # ============================================================

    def _cargar_preferencias(self):
        if not os.path.exists(self.archivo_preferencias):
            return

        try:
            with open(self.archivo_preferencias, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.memoria_preferencias.preferencias = data.get('preferencias', {})
                self.memoria_preferencias.usuario_id = data.get('usuario_id', 'default')
        except Exception:
            self.memoria_preferencias.preferencias = {}

    def _guardar_preferencias(self):
        payload = {
            'usuario_id': self.memoria_preferencias.usuario_id,
            'preferencias': self.memoria_preferencias.preferencias,
            'actualizado': datetime.now().isoformat()
        }
        with open(self.archivo_preferencias, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _extraer_preferencias_desde_mensaje(self, mensaje: str):
        mensaje_lower = mensaje.lower().strip()

        # Preferencias de formato
        if re.search(r'\b(prefiero|preferencia|siempre)\b', mensaje_lower):
            if 'pdf' in mensaje_lower:
                self.memoria_preferencias.preferencias['formato_reporte'] = 'pdf'
            elif 'excel' in mensaje_lower:
                self.memoria_preferencias.preferencias['formato_reporte'] = 'excel'

            if 'resumen' in mensaje_lower:
                self.memoria_preferencias.preferencias['detalle_respuesta'] = 'resumen'
            elif 'detallado' in mensaje_lower or 'detalle' in mensaje_lower:
                self.memoria_preferencias.preferencias['detalle_respuesta'] = 'detallado'

            self._guardar_preferencias()

    # ============================================================
    # Contexto operativo
    # ============================================================

    def actualizar_contexto(self, accion: str, intencion: str, parametros: Dict[str, Any], modelo_erp: Optional[str] = None):
        self.memoria_contextual.ultima_accion = accion
        self.memoria_contextual.ultima_intencion = intencion

        if modelo_erp:
            self.memoria_contextual.modelo_erp_actual = modelo_erp

        filtros = {}
        for clave in ['fecha_inicio', 'fecha_fin', 'tienda', 'estado', 'limite', 'periodo']:
            if clave in (parametros or {}):
                filtros[clave] = parametros[clave]

        if filtros:
            self.memoria_contextual.filtros_activos.update(filtros)

    def aplicar_contexto_a_consulta(self, consulta: Any):
        """Inyecta contexto operativo si faltan parámetros en la consulta."""
        if not hasattr(consulta, 'parametros') or consulta.parametros is None:
            consulta.parametros = {}

        if not hasattr(consulta, 'temporalidad') or consulta.temporalidad is None:
            consulta.temporalidad = {}

        filtros = self.memoria_contextual.filtros_activos

        if 'fecha_inicio' not in consulta.temporalidad and filtros.get('fecha_inicio'):
            consulta.temporalidad['fecha_inicio'] = filtros['fecha_inicio']
        if 'fecha_fin' not in consulta.temporalidad and filtros.get('fecha_fin'):
            consulta.temporalidad['fecha_fin'] = filtros['fecha_fin']

        if 'tienda' not in consulta.parametros and filtros.get('tienda'):
            consulta.parametros['tienda'] = filtros['tienda']
        if 'limite' not in consulta.parametros and filtros.get('limite'):
            consulta.parametros['limite'] = filtros['limite']

        return consulta

    # ============================================================
    # Registro integral de interacción
    # ============================================================

    def registrar_interaccion(
        self,
        mensaje_usuario: str,
        respuesta: str,
        intencion: str,
        accion: str,
        confianza: float,
        parametros: Optional[Dict[str, Any]] = None,
        modelo_erp: Optional[str] = None,
        metadata_extra: Optional[Dict[str, Any]] = None
    ):
        timestamp = datetime.now().isoformat()

        # 1) Sesión corta
        self.memoria_sesion.agregar(
            RegistroSesion(
                timestamp=timestamp,
                mensaje_usuario=mensaje_usuario[:500],
                respuesta=respuesta[:700],
                intencion=intencion,
                accion=accion,
                confianza=float(confianza or 0.0)
            )
        )

        # 2) Contextual
        self.actualizar_contexto(
            accion=accion,
            intencion=intencion,
            parametros=parametros or {},
            modelo_erp=modelo_erp
        )

        # 3) Preferencias
        self._extraer_preferencias_desde_mensaje(mensaje_usuario)

        # 4) Semántica vectorial
        if self.memoria_vectorial:
            metadata = {
                'confianza': round(float(confianza or 0.0), 4),
                'modelo_erp': modelo_erp or self.memoria_contextual.modelo_erp_actual,
                'filtros_activos': json.dumps(self.memoria_contextual.filtros_activos, ensure_ascii=False)[:400]
            }
            if metadata_extra:
                # Excluir claves internas y sanitizar valores para ChromaDB
                for k, v in metadata_extra.items():
                    if k.startswith('_'):
                        continue
                    if isinstance(v, (str, int, float, bool)):
                        metadata[k] = v
                    elif v is not None:
                        metadata[k] = str(v)[:500]

            self.memoria_vectorial.guardar_conversacion(
                mensaje_usuario=mensaje_usuario,
                respuesta_andromeda=respuesta,
                intencion=intencion,
                accion_ejecutada=accion,
                metadata_extra=metadata
            )

        # 5) Grafo de conocimiento
        if self.grafo and self.grafo.disponible:
            try:
                df = metadata_extra.get('_df') if metadata_extra else None
                self.grafo.registrar_interaccion(
                    mensaje=mensaje_usuario,
                    respuesta=respuesta,
                    accion=accion,
                    intencion=intencion,
                    parametros=parametros,
                    df=df,
                    modelo_erp=modelo_erp or '',
                    confianza=float(confianza or 0.0)
                )
            except Exception as e:
                logger.debug(f"Error registrando en grafo: {e}")

    def obtener_contexto_grafo(self, accion: str, entidades: List[str] = None) -> str:
        """Obtiene contexto relacional del grafo para inyectar en LLM/agentes."""
        if not self.grafo or not self.grafo.disponible:
            return ""
        try:
            return self.grafo.obtener_contexto_relacional(accion, entidades, max_hops=2, limite=8)
        except Exception:
            return ""

    def buscar_semantico(self, consulta: str, limite: int = 3) -> List[str]:
        """Busca recuerdos semánticos relevantes."""
        if not self.memoria_vectorial:
            return []
        resultado = self.memoria_vectorial.buscar(consulta, coleccion='conversaciones', limite=limite)
        return [r.contenido[:220] for r in resultado.recuerdos]

    def snapshot(self) -> Dict[str, Any]:
        """Estado actual resumido de la memoria jerárquica."""
        return {
            'sesion': {
                'interacciones': len(self.memoria_sesion.historial),
                'ultimas': [
                    {
                        'timestamp': x.timestamp,
                        'intencion': x.intencion,
                        'accion': x.accion,
                        'confianza': x.confianza
                    }
                    for x in self.memoria_sesion.ultimas(3)
                ]
            },
            'contextual': {
                'modelo_erp_actual': self.memoria_contextual.modelo_erp_actual,
                'filtros_activos': self.memoria_contextual.filtros_activos,
                'ultima_intencion': self.memoria_contextual.ultima_intencion,
                'ultima_accion': self.memoria_contextual.ultima_accion
            },
            'preferencias': self.memoria_preferencias.preferencias,
            'semantica': {
                'vectorial_disponible': self.memoria_vectorial is not None
            },
            'grafo': self.grafo.estadisticas() if self.grafo else {'disponible': False}
        }

    # ============================================================
    # Limpieza sincronizada de todos los subsistemas
    # ============================================================

    def limpiar_todo(self, dias_antiguedad: int = 90) -> Dict[str, Any]:
        """
        Limpieza coordinada: sesión + vectorial + grafo.
        Propaga la operación a los 3 subsistemas de memoria.
        """
        resultado = {'sesion': False, 'vectorial': 0, 'grafo': False}

        # 1) Sesión
        try:
            self.memoria_sesion.historial.clear()
            self.memoria_contextual.modelo_erp_actual = None
            self.memoria_contextual.filtros_activos = {}
            self.memoria_contextual.ultima_intencion = None
            self.memoria_contextual.ultima_accion = None
            resultado['sesion'] = True
        except Exception as e:
            logger.error(f"Error limpiando sesión: {e}")

        # 2) Vectorial
        if self.memoria_vectorial:
            try:
                eliminados = self.memoria_vectorial.limpiar_antiguos(dias=dias_antiguedad)
                resultado['vectorial'] = eliminados
            except Exception as e:
                logger.error(f"Error limpiando vectorial: {e}")

        # 3) Grafo
        if self.grafo and self.grafo.disponible:
            try:
                self.grafo._podar_si_necesario()
                self.grafo.guardar()
                resultado['grafo'] = True
            except Exception as e:
                logger.error(f"Error limpiando grafo: {e}")

        logger.info(f"Limpieza sincronizada: {resultado}")
        return resultado


_memoria_jerarquica_global: Optional[MemoriaJerarquica] = None


def obtener_memoria_jerarquica(memoria_vectorial: Optional[MemoriaVectorial] = None) -> MemoriaJerarquica:
    global _memoria_jerarquica_global
    if _memoria_jerarquica_global is None:
        _memoria_jerarquica_global = MemoriaJerarquica(memoria_vectorial=memoria_vectorial)
    elif memoria_vectorial is not None and _memoria_jerarquica_global.memoria_vectorial is None:
        _memoria_jerarquica_global.memoria_vectorial = memoria_vectorial
    return _memoria_jerarquica_global
