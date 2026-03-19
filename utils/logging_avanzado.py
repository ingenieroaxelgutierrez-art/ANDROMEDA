# ============================================================
# ANDROMEDA - Sistema Avanzado de Logging y Análisis
# Autor: Axel Gutiérrez
# Fecha: 2024-02-27 | Actualizado: 2026-03-02
# ============================================================
# Sistema de logging con:
# - Registro de errores con contexto completo
# - Trazado de eventos NLP y prompts
# - Integración con Ollama para análisis
# - Estadísticas en tiempo real
# ============================================================

import logging
import os
import json
import sqlite3
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import traceback
from enum import Enum


# ============================================================
# ENUMS Y TIPOS
# ============================================================

class TipoEvento(Enum):
    """Tipos de eventos a registrar."""
    ERROR = "ERROR"
    ADVERTENCIA = "WARNING"
    INFO = "INFO"
    NLP = "NLP"
    PROMPT = "PROMPT"
    RESPUESTA = "RESPUESTA"
    ODOO = "ODOO"
    RENDIMIENTO = "RENDIMIENTO"
    OLLAMA = "OLLAMA"
    CONSULTA = "CONSULTA"
    INTERACCION = "INTERACCION"
    DIAGNOSTICO = "DIAGNOSTICO"
    VISUALIZACION = "VISUALIZACION"


class NivelCriticidad(Enum):
    """Niveles de criticidad del error."""
    BAJO = "BAJO"
    BAJA = "BAJA"
    MEDIO = "MEDIO"
    MEDIA = "MEDIA"
    ALTO = "ALTO"
    ALTA = "ALTA"
    CRITICO = "CRITICO"
    CRITICA = "CRITICA"


@dataclass
class EventoLog:
    """Estructura de un evento de log."""
    timestamp: str
    tipo: str
    nivel: str
    modulo: str
    mensaje: str
    contexto: Dict[str, Any]
    traceback: Optional[str] = None
    usuario: Optional[str] = None
    sesion_id: Optional[str] = None


# ============================================================
# LOGGER AVANZADO
# ============================================================

class LoggerAvanzado:
    """Logger profesional con BD SQLite y análisis."""
    
    def __init__(self, ruta_logs: str = "logs"):
        # Usar ruta absoluta relativa al directorio del proyecto
        _base_dir = Path(__file__).resolve().parent.parent
        self.ruta_logs = _base_dir / ruta_logs
        self.ruta_logs.mkdir(exist_ok=True)
        
        # Base de datos para análisis
        self.db_path = self.ruta_logs / "eventos.db"
        self._inicializar_db()
        
        # Configurar logging estándar
        self._configurar_handlers()
        
        # Logger
        self.logger = logging.getLogger("ANDROMEDA")
        self.logger.setLevel(logging.DEBUG)
        
    def _inicializar_db(self):
        """Inicializa la base de datos SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de eventos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS eventos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        nivel TEXT NOT NULL,
                        modulo TEXT NOT NULL,
                        mensaje TEXT NOT NULL,
                        contexto TEXT,
                        traceback TEXT,
                        usuario TEXT,
                        sesion_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_eventos_timestamp ON eventos(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos(tipo)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_eventos_nivel ON eventos(nivel)')
                
                # Tabla de prompts para análisis NLP
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prompts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        sesion_id TEXT,
                        prompt_original TEXT NOT NULL,
                        prompt_procesado TEXT,
                        intencion_detectada TEXT,
                        confianza_intencion REAL,
                        respuesta TEXT,
                        tiempo_respuesta_ms INTEGER,
                        usuario TEXT,
                        modelo_usado TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_sesion ON prompts(sesion_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_timestamp ON prompts(timestamp)')
                
                # Tabla de errores con análisis
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS errores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        tipo_error TEXT NOT NULL,
                        criticidad TEXT NOT NULL,
                        modulo TEXT NOT NULL,
                        mensaje TEXT NOT NULL,
                        solucion_sugerida TEXT,
                        frecuencia INTEGER DEFAULT 1,
                        ultimo_visto TEXT,
                        resuelta INTEGER DEFAULT 0,
                        usuario TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_errores_tipo ON errores(tipo_error)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_errores_criticidad ON errores(criticidad)')
                
                # Tabla de rendimiento
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rendimiento (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        modulo TEXT NOT NULL,
                        operacion TEXT NOT NULL,
                        tiempo_ms REAL NOT NULL,
                        exitosa INTEGER,
                        memoria_mb REAL,
                        usuario TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rendimiento_modulo ON rendimiento(modulo)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rendimiento_timestamp ON rendimiento(timestamp)')
                
                conn.commit()
        except Exception as e:
            logging.getLogger(__name__).error(f"Error inicializando DB de eventos: {e}")
            # Reintentar con DB nueva si está corrupta
            try:
                self.db_path.unlink(missing_ok=True)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('SELECT 1')
            except Exception:
                pass
    
    def _configurar_handlers(self):
        """Configura handlers de archivo y consola.
        
        Si logging_config.py ya configuró handlers en root, solo agrega
        el handler de errores.log (que logging_config.py no proporciona).
        """
        logger_root = logging.getLogger()
        
        # Verificar si ya hay handlers por tipo para evitar duplicados
        tiene_file_handler = any(
            isinstance(h, (RotatingFileHandler, logging.FileHandler))
            and getattr(h, 'baseFilename', '').endswith('andromeda.log')
            for h in logger_root.handlers
        )
        tiene_error_handler = any(
            isinstance(h, (RotatingFileHandler, logging.FileHandler))
            and getattr(h, 'baseFilename', '').endswith('errores.log')
            for h in logger_root.handlers
        )
        tiene_console_handler = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in logger_root.handlers
        )
        
        formato_detallado = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Solo agregar handler de archivo si no existe
        if not tiene_file_handler:
            handler_archivo = RotatingFileHandler(
                self.ruta_logs / "andromeda.log",
                maxBytes=10_000_000,
                backupCount=5,
                encoding="utf-8"
            )
            handler_archivo.setFormatter(formato_detallado)
            logger_root.addHandler(handler_archivo)
        
        # Siempre asegurar handler de errores (logging_config.py no lo tiene)
        if not tiene_error_handler:
            handler_errores = RotatingFileHandler(
                self.ruta_logs / "errores.log",
                maxBytes=5_000_000,
                backupCount=3,
                encoding="utf-8"
            )
            handler_errores.setLevel(logging.ERROR)
            handler_errores.setFormatter(formato_detallado)
            logger_root.addHandler(handler_errores)
        
        # Solo agregar consola si no existe
        if not tiene_console_handler:
            handler_consola = logging.StreamHandler()
            handler_consola.setLevel(logging.INFO)
            handler_consola.setFormatter(formato_detallado)
            logger_root.addHandler(handler_consola)
    
    def registrar_evento(self, 
                        tipo: TipoEvento,
                        mensaje: str,
                        modulo: str,
                        contexto: Dict[str, Any] = None,
                        nivel: NivelCriticidad = NivelCriticidad.MEDIA,
                        usuario: str = None,
                        sesion_id: str = None):
        """Registra un evento en BD y logs."""
        try:
            evento = EventoLog(
                timestamp=datetime.now().isoformat(),
                tipo=tipo.value,
                nivel=nivel.value,
                modulo=modulo,
                mensaje=mensaje,
                contexto=contexto or {},
                usuario=usuario,
                sesion_id=sesion_id
            )
            
            # Guardar en BD
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO eventos 
                    (timestamp, tipo, nivel, modulo, mensaje, contexto, usuario, sesion_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    evento.timestamp,
                    evento.tipo,
                    evento.nivel,
                    evento.modulo,
                    evento.mensaje,
                    json.dumps(evento.contexto),
                    evento.usuario,
                    evento.sesion_id
                ))
                conn.commit()
            
            # Log en archivo
            self.logger.info(f"[{tipo.value}] {modulo}: {mensaje}")
            
        except Exception as e:
            self.logger.error(f"Error registrando evento: {e}")
    
    def registrar_error(self,
                       excepcion: Exception,
                       modulo: str,
                       criticidad: NivelCriticidad = NivelCriticidad.MEDIA,
                       contexto: Dict[str, Any] = None,
                       usuario: str = None):
        """Registra un error con análisis y sugerencias."""
        try:
            tipo_error = type(excepcion).__name__
            tb = traceback.format_exc()
            
            # Sugerir solución basada en el error
            solucion = self._sugerir_solucion(tipo_error, str(excepcion))
            
            # Guardar en tabla de errores
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si error similar existe
                cursor.execute('''
                    SELECT id, frecuencia FROM errores 
                    WHERE tipo_error = ? AND modulo = ? AND resuelta = 0
                    LIMIT 1
                ''', (tipo_error, modulo))
                
                fila = cursor.fetchone()
                if fila:
                    # Actualizar frecuencia
                    cursor.execute('''
                        UPDATE errores SET frecuencia = frecuencia + 1, 
                                        ultimo_visto = ? 
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), fila[0]))
                else:
                    # Nuevo error
                    cursor.execute('''
                        INSERT INTO errores 
                        (timestamp, tipo_error, criticidad, modulo, mensaje, 
                         solucion_sugerida, usuario)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        tipo_error,
                        criticidad.value,
                        modulo,
                        str(excepcion),
                        solucion,
                        usuario
                    ))
                
                conn.commit()
            
            # Log del error
            self.logger.error(f"ERROR en {modulo}: {tipo_error} - {excepcion}")
            self.logger.debug(tb)
            
        except Exception as e:
            self.logger.error(f"Error registrando excepción: {e}")
    
    def registrar_prompt(self,
                        prompt_original: str,
                        respuesta: str,
                        sesion_id: str,
                        intencion: str = None,
                        confianza: float = 0.0,
                        tiempo_ms: int = 0,
                        usuario: str = None,
                        modelo: str = "ANDROMEDA"):
        """Registra un prompt y respuesta para análisis NLP."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO prompts 
                    (timestamp, sesion_id, prompt_original, prompt_procesado, 
                     intencion_detectada, confianza_intencion, respuesta, 
                     tiempo_respuesta_ms, usuario, modelo_usado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    sesion_id,
                    prompt_original,
                    prompt_original,  # Se procesa luego si se conecta Ollama
                    intencion,
                    confianza,
                    respuesta,
                    tiempo_ms,
                    usuario,
                    modelo
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error registrando prompt: {e}")
    
    def registrar_rendimiento(self,
                             modulo: str,
                             operacion: str,
                             tiempo_ms: float,
                             exitosa: bool = True,
                             usuario: str = None,
                             memoria_mb: float = None):
        """Registra métricas de rendimiento."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rendimiento 
                    (timestamp, modulo, operacion, tiempo_ms, exitosa, memoria_mb, usuario)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    modulo,
                    operacion,
                    tiempo_ms,
                    1 if exitosa else 0,
                    memoria_mb,
                    usuario
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error registrando rendimiento: {e}")
    
    # ========================================
    # ANÁLISIS Y CONSULTAS
    # ========================================
    
    def obtener_errores_recientes(self, dias: int = 7, limite: int = 20) -> List[Dict]:
        """Obtiene errores recientes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()
                
                cursor.execute('''
                    SELECT * FROM errores 
                    WHERE timestamp > ? AND resuelta = 0
                    ORDER BY frecuencia DESC, timestamp DESC
                    LIMIT ?
                ''', (fecha_limite, limite))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error obteniendo errores: {e}")
            return []
    
    def obtener_prompts_sin_mejorar(self, limite: int = 50) -> List[Dict]:
        """Obtiene prompts con baja confianza para mejorar con Ollama."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM prompts 
                    WHERE confianza_intencion < 0.7 
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limite,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error obteniendo prompts: {e}")
            return []
    
    def estadisticas_dia(self) -> Dict[str, Any]:
        """Estadísticas del día actual."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                hoy = datetime.now().strftime("%Y-%m-%d")
                
                # Contar por tipo de evento
                cursor.execute('''
                    SELECT tipo, COUNT(*) as cantidad FROM eventos 
                    WHERE DATE(timestamp) = ? 
                    GROUP BY tipo
                ''', (hoy,))
                
                eventos = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Errores
                cursor.execute('''
                    SELECT COUNT(*) FROM errores 
                    WHERE DATE(timestamp) = ? AND resuelta = 0
                ''', (hoy,))
                
                errores_nuevos = cursor.fetchone()[0]
                
                # Prompts procesados
                cursor.execute('''
                    SELECT COUNT(*), AVG(confianza_intencion), AVG(tiempo_respuesta_ms)
                    FROM prompts WHERE DATE(timestamp) = ?
                ''', (hoy,))
                
                stats = cursor.fetchone()
                prompts_total = stats[0] if stats[0] else 0
                confianza_promedio = stats[1] if stats[1] else 0.0
                tiempo_promedio = stats[2] if stats[2] else 0.0
                
                return {
                    'eventos': eventos,
                    'errores_nuevos': errores_nuevos,
                    'prompts_procesados': prompts_total,
                    'confianza_promedio': round(confianza_promedio, 2),
                    'tiempo_promedio_ms': round(tiempo_promedio, 1),
                    'fecha': hoy
                }
        except Exception as e:
            self.logger.error(f"Error en estadísticas: {e}")
            return {}
    
    def _sugerir_solucion(self, tipo_error: str, mensaje: str) -> str:
        """Sugiere soluciones basadas en el tipo de error."""
        sugerencias = {
            'ConnectionError': 'Verificar conexión a Odoo. Revisar URL, credenciales y conexión de red.',
            'TimeoutError': 'Aumentar timeout en la conexión. Odoo puede estar lento.',
            'AttributeError': 'Verificar que el modelo/campo existe en Odoo. Ver registro en odoo_config.json',
            'KeyError': 'Verificar la estructura de datos. Posible cambio en API de Odoo.',
            'ValueError': 'Validar datos antes de enviar. Revisar tipos de datos.',
            'PermissionError': 'Usuario sin permisos. Verificar permisos en Odoo.',
        }
        
        return sugerencias.get(tipo_error, 'Revisar logs para más detalles. Contactar soporte.')


# ============================================================
# FUNCIÓN GLOBAL
# ============================================================

_logger_instancia = None

def obtener_logger() -> LoggerAvanzado:
    """Obtiene instancia global del logger."""
    global _logger_instancia
    if _logger_instancia is None:
        _logger_instancia = LoggerAvanzado()
    return _logger_instancia


def configurar_logging():
    """Compatible con versión anterior."""
    return obtener_logger()


__all__ = [
    "configurar_logging",
    "obtener_logger",
    "LoggerAvanzado",
    "TipoEvento",
    "NivelCriticidad",
    "EventoLog"
]