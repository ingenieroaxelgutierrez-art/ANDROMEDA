# ============================================================
# OLLAMA INTEGRADOR - Análisis Local de Prompts con Ollama
# ============================================================
# Permite:
# - Procesar prompts con modelos locales (Ollama)
# - Mejorar detección de intenciones
# - Refinas respuestas
# - Análisis sin depender de APIs externas
# ============================================================

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from app.logging_config import get_logger
logger = get_logger("services.llm.ollama_integrador")


class OllamaIntegrador:
    """Integración con Ollama para análisis de prompts."""
    
    def __init__(self, host: str = "http://localhost:11434"):
        """
        Inicializa el integrador de Ollama.
        
        Args:
            host: URL de Ollama (por default localhost)
        """
        self.host = host
        self.conectado = False
        self.modelo_activo = None
        self.timeout_default = 120
        self.max_reintentos = 3
        self.backoff_base = 1.2
        
        # Modelos disponibles en Ollama
        self.modelos_disponibles = [
            "llama2",           # Modelo general rápido
            "mistral",          # Excelente para instrucciones
            "neural-chat",      # Optimizado para chat
            "openhermes",       # Bueno para análisis
        ]

        # Intenciones válidas del sistema (compatibles con MotorNLPAvanzado)
        self.intenciones_validas = {
            "ventas", "inventario", "clientes", "productos", "pos",
            "reporte", "resumen", "comparar", "describir", "ayuda",
            "saludo", "consultar_manual", "auditoria_nocturna", "semaforo_salud",
            "detectar_pagos_fantasma", "analizar_churn", "reposicion_jit",
            "stock_lento", "clientes_olvidados", "diferencias_centavos",
            "diagnosticar_error", "generar_reporte_auditoria", "consulta_general"
        }
        
        # Verificar conexión
        self._verificar_conexion()
    
    def _verificar_conexion(self) -> bool:
        """Verifica si Ollama está disponible."""
        try:
            respuesta = requests.get(f"{self.host}/api/tags", timeout=5)
            if respuesta.status_code == 200:
                self.conectado = True
                datos = respuesta.json()
                modelos = [m['name'] for m in datos.get('models', [])]
                logger.info(f"Ollama conectado. Modelos: {modelos}")
                
                # Seleccionar primer modelo disponible
                if modelos:
                    self.modelo_activo = modelos[0]
                    logger.info(f"Modelo activo: {self.modelo_activo}")
                return True
            else:
                logger.warning("Ollama no responde correctamente")
                self.conectado = False
                return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"No se puede conectar a Ollama en {self.host}")
            logger.info("Asegúrate de tener Ollama ejecutándose: ollama serve")
            self.conectado = False
            return False
        except Exception as e:
            logger.error(f"Error verificando Ollama: {e}")
            self.conectado = False
            return False
    
    def obtener_modelos(self) -> List[str]:
        """Obtiene lista de modelos disponibles en Ollama."""
        if not self.conectado:
            return []
        
        try:
            respuesta = requests.get(f"{self.host}/api/tags", timeout=5)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return [m['name'] for m in datos.get('models', [])]
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
        
        return []
    
    def establecer_modelo(self, nombre_modelo: str) -> bool:
        """
        Establece el modelo activo.
        
        Args:
            nombre_modelo: Nombre del modelo a usar
        
        Returns:
            True si se estableció correctamente
        """
        if not self.conectado:
            logger.warning("Ollama no está conectado")
            return False
        
        modelos = self.obtener_modelos()
        if nombre_modelo in modelos:
            self.modelo_activo = nombre_modelo
            logger.info(f"Modelo establecido a: {nombre_modelo}")
            return True
        else:
            logger.error(f"Modelo {nombre_modelo} no disponible")
            return False
    
    # ========================================
    # ANÁLISIS DE PROMPTS
    # ========================================
    
    def analizar_intencion(self, prompt: str) -> Dict[str, Any]:
        """
        [SOLO USO DIAGNÓSTICO / CLI] Clasifica la intención del prompt usando el LLM.

        ADVERTENCIA: Este método NO debe usarse en el pipeline principal de mensajes.
        La clasificación de intención pertenece a MotorNLPAvanzado + MotorEmbeddings,
        que calculan confianza real mediante similitud coseno.
        El LLM genera el número de confianza estadísticamente (no lo mide), lo que
        puede contaminar el routing y degradar las respuestas.

        Uso válido: cli_monitor.py para diagnóstico, herramientas de inspección.
        Uso correcto en pipeline: Ollama entra SOLO en generación de respuesta final.

        Args:
            prompt: Texto del usuario

        Returns:
            Dict con intención, confianza y análisis
        """
        if not self.conectado or not self.modelo_activo:
            logger.warning("Ollama no disponible para análisis")
            return {
                'intencion': 'desconocida',
                'confianza': 0.0,
                'analisis': 'Ollama no disponible',
                'mejoras': [],
                'accion_sugerida': None,
                'parametros_sugeridos': {}
            }
        
        try:
            prompt_analisis = f"""Eres un clasificador de intención para ANDROMEDA. Analiza el mensaje del usuario y devuelve SOLO un JSON válido, sin texto adicional ni markdown.

Intenciones posibles (elige UNA): ventas, inventario, clientes, productos, pos, reporte, resumen, comparar, describir, consultar_manual, ayuda, saludo, consulta_general, diagnosticar_error, auditoria_nocturna, semaforo_salud, detectar_pagos_fantasma, analizar_churn, reposicion_jit, stock_lento, clientes_olvidados, diferencias_centavos, generar_reporte_auditoria

Acciones posibles (elige UNA): consulta_general, consultar_ventas, consultar_inventario, consultar_clientes, consultar_productos, consultar_pos, diagnosticar_error, auditoria_nocturna, semaforo_salud, detectar_pagos_fantasma, analizar_churn, reposicion_jit, stock_lento, clientes_olvidados, diferencias_centavos, generar_reporte_auditoria, consultar_manual

Formato de respuesta (rellena SOLO los valores, no copies las opciones):
{{
  "intencion": "<una intencion de la lista>",
  "accion_sugerida": "<una accion de la lista>",
  "parametros_sugeridos": {{"periodo": "<hoy|semana|mes|rango>", "limite": 10}},
  "confianza": 0.85,
  "palabras_clave": ["palabra1", "palabra2"],
  "contexto": "<breve resumen>",
  "mejora_sugerida": ""
}}

Reglas:
- Si no estás seguro, usa "consulta_general" y confianza menor o igual a 0.55.
- Solo devuelve el JSON. Nada más.

Mensaje del usuario: {prompt}"""
            
            inicio = time.time()
            respuesta = self._llamar_ollama(prompt_analisis, temperatura=0.15)
            tiempo_ms = int((time.time() - inicio) * 1000)

            datos = self._parsear_json_respuesta(respuesta)
            if datos:
                intencion = str(datos.get('intencion', 'consulta_general')).strip().lower()
                if intencion not in self.intenciones_validas:
                    intencion = 'consulta_general'

                confianza = datos.get('confianza', 0.0)
                try:
                    confianza = float(confianza)
                except Exception:
                    confianza = 0.0
                confianza = max(0.0, min(1.0, confianza))

                resultado = {
                    'intencion': intencion,
                    'accion_sugerida': datos.get('accion_sugerida'),
                    'parametros_sugeridos': datos.get('parametros_sugeridos') if isinstance(datos.get('parametros_sugeridos'), dict) else {},
                    'confianza': confianza,
                    'palabras_clave': datos.get('palabras_clave') if isinstance(datos.get('palabras_clave'), list) else [],
                    'contexto': str(datos.get('contexto', '')).strip(),
                    'mejora_sugerida': str(datos.get('mejora_sugerida', '')).strip(),
                    'tiempo_ms': tiempo_ms,
                    'analisis': 'ok'
                }
                return resultado

            logger.warning(f"No se pudo parsear JSON de Ollama: {respuesta[:140]}")
            return {
                'intencion': 'consulta_general',
                'accion_sugerida': None,
                'parametros_sugeridos': {},
                'confianza': 0.0,
                'palabras_clave': [],
                'contexto': '',
                'mejora_sugerida': '',
                'analisis': respuesta[:220],
                'tiempo_ms': tiempo_ms
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de Ollama: {e}")
            return {
                'intencion': 'error_parsing',
                'confianza': 0.0,
                'analisis': str(e),
                'accion_sugerida': None,
                'parametros_sugeridos': {}
            }
        except Exception as e:
            logger.error(f"Error en análisis de intención: {e}")
            return {
                'intencion': 'error',
                'confianza': 0.0,
                'analisis': str(e),
                'accion_sugerida': None,
                'parametros_sugeridos': {}
            }
    
    def mejorar_prompt(self, prompt_original: str) -> Dict[str, str]:
        """
        Mejora un prompt para obtener mejores resultados.
        
        Args:
            prompt_original: Prompt original del usuario
        
        Returns:
            Dict con prompts mejorados
        """
        if not self.conectado or not self.modelo_activo:
            return {'original': prompt_original, 'mejorado': prompt_original}
        
        try:
            prompt_mejora = f"""Mejora este prompt para obtener mejores respuestas:

ORIGINAL: {prompt_original}

Dame 3 versiones mejoradas, separadas por "---", que mantengan el significado pero sean más claras:"""
            
            respuesta = self._llamar_ollama(prompt_mejora, temperatura=0.5)
            
            # Dividir respuestas
            versiones = respuesta.split('---')
            
            return {
                'original': prompt_original,
                'mejorado': versiones[0].strip() if versiones else prompt_original,
                'alternativas': [v.strip() for v in versiones[1:] if v.strip()]
            }
        
        except Exception as e:
            logger.error(f"Error mejorando prompt: {e}")
            return {'original': prompt_original, 'mejorado': prompt_original}
    
    def generar_respuesta(self, prompt: str, contexto: str = "", 
                         temperatura: float = 0.7) -> Dict[str, Any]:
        """
        Genera respuesta usando Ollama.
        
        Args:
            prompt: Prompt del usuario
            contexto: Contexto adicional
            temperatura: Control de creatividad (0-1)
        
        Returns:
            Dict con respuesta y metadatos
        """
        if not self.conectado or not self.modelo_activo:
            logger.warning("Ollama no disponible para generar respuesta")
            return {
                'respuesta': 'Sistema no disponible',
                'modelo': None,
                'tiempo_ms': 0,
                'tokens': 0
            }
        
        try:
            prompt_final = f"{contexto}\n\nPregunta: {prompt}"
            
            inicio = time.time()
            respuesta = self._llamar_ollama(prompt_final, temperatura=temperatura)
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            return {
                'respuesta': respuesta.strip(),
                'modelo': self.modelo_activo,
                'tiempo_ms': tiempo_ms,
                'tokens': len(respuesta.split()),
                'temperatura': temperatura
            }
        
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return {
                'respuesta': f'Error: {str(e)}',
                'modelo': self.modelo_activo,
                'tiempo_ms': 0,
                'error': True
            }
    
    # ========================================
    # ANÁLISIS DE LOGS
    # ========================================
    
    def analizar_error(self, tipo_error: str, mensaje: str, traceback: str = "") -> str:
        """
        Analiza un error y sugiere soluciones.
        
        Args:
            tipo_error: Tipo del error
            mensaje: Mensaje del error
            traceback: Traceback completo
        
        Returns:
            Sugerencia de solución
        """
        if not self.conectado or not self.modelo_activo:
            logger.warning("Ollama no disponible para análisis de error")
            return "No disponible"
        
        try:
            prompt_error = f"""Analiza este error de Python y sugiere cómo solucionarlo:

TIPO: {tipo_error}
MENSAJE: {mensaje}
TRACEBACK: {traceback[:500]}

Sé conciso, proporciona la solución más probable."""
            
            respuesta = self._llamar_ollama(prompt_error, temperatura=0.3)
            return respuesta.strip()
        
        except Exception as e:
            logger.error(f"Error analizando error: {e}")
            return "Error en análisis"
    
    # ========================================
    # INTERNO
    # ========================================
    
    def _llamar_ollama(self, prompt: str, temperatura: float = 0.7,
                      timeout: int = 120) -> str:
        """
        Llamada interna a Ollama.
        
        Args:
            prompt: Prompt a procesar
            temperatura: Control de creatividad
            timeout: Timeout en segundos
        
        Returns:
            Respuesta de Ollama
        """
        if not self.conectado or not self.modelo_activo:
            raise RuntimeError("Ollama no conectado")

        timeout = timeout or self.timeout_default
        modelos = [self.modelo_activo] + [m for m in self.obtener_modelos() if m != self.modelo_activo]
        modelos = modelos[:3] if modelos else [self.modelo_activo]
        ultimo_error = None

        for modelo in modelos:
            for intento in range(1, self.max_reintentos + 1):
                try:
                    payload = {
                        "model": modelo,
                        "prompt": prompt,
                        "temperature": temperatura,
                        "stream": False,
                        "options": {
                            "num_ctx": 2048,
                            "num_predict": 512,
                            "num_thread": 4,
                            "num_gpu": 0,
                            "num_batch": 128
                        }
                    }

                    respuesta = requests.post(
                        f"{self.host}/api/generate",
                        json=payload,
                        timeout=timeout
                    )

                    if respuesta.status_code != 200:
                        raise RuntimeError(f"Error Ollama HTTP {respuesta.status_code}")

                    datos = respuesta.json()
                    texto = str(datos.get('response', '')).strip()
                    if not texto:
                        raise RuntimeError("Respuesta vacía de Ollama")

                    if modelo != self.modelo_activo:
                        self.modelo_activo = modelo
                        logger.info(f"Modelo activo cambiado por fallback a: {modelo}")

                    return texto

                except requests.exceptions.Timeout as e:
                    ultimo_error = e
                    logger.warning(f"Timeout en Ollama (modelo={modelo}, intento={intento}/{self.max_reintentos})")
                except Exception as e:
                    ultimo_error = e
                    logger.warning(f"Fallo llamando Ollama (modelo={modelo}, intento={intento}/{self.max_reintentos}): {e}")

                if intento < self.max_reintentos:
                    time.sleep(self.backoff_base * intento)

        raise RuntimeError(f"Ollama sin respuesta tras reintentos: {ultimo_error}")

    def _parsear_json_respuesta(self, respuesta: str) -> Optional[Dict[str, Any]]:
        """Extrae y parsea JSON tolerando ruido en la respuesta."""
        if not respuesta:
            return None

        texto = respuesta.strip()
        candidatos = []

        bloque = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', texto, re.DOTALL | re.IGNORECASE)
        if bloque:
            candidatos.append(bloque.group(1))

        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            candidatos.append(match.group())

        candidatos.append(texto)

        for candidato in candidatos:
            candidato = candidato.strip()
            if not candidato:
                continue
            try:
                return json.loads(candidato)
            except Exception:
                candidato_norm = candidato.replace("'", '"')
                candidato_norm = re.sub(r'\"\"+', '"', candidato_norm)
                try:
                    return json.loads(candidato_norm)
                except Exception:
                    continue

        return None
    
    def descargar_modelo(self, nombre_modelo: str) -> bool:
        """
        Descarga un modelo de Ollama.
        
        Args:
            nombre_modelo: Nombre del modelo a descargar
        
        Returns:
            True si se descarló correctamente
        """
        if not self.conectado:
            logger.warning("Ollama no está conectado")
            return False
        
        try:
            logger.info(f"Descargando modelo {nombre_modelo}...")
            print(f"\n📥 Descargando {nombre_modelo}... esto puede tomar unos minutos")
            
            payload = {"name": nombre_modelo}
            respuesta = requests.post(
                f"{self.host}/api/pull",
                json=payload,
                timeout=600  # 10 minutos timeout
            )
            
            if respuesta.status_code == 200:
                logger.info(f"Modelo {nombre_modelo} descargado exitosamente")
                print(f"✅ {nombre_modelo} descargado")
                return True
            else:
                logger.error(f"Error descargando modelo: {respuesta.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error en descarga: {e}")
            return False


# ============================================================
# FUNCIONES UTILITARIAS
# ============================================================

_ollama_instancia = None

def obtener_ollama() -> OllamaIntegrador:
    """Obtiene instancia global de Ollama."""
    global _ollama_instancia
    if _ollama_instancia is None:
        _ollama_instancia = OllamaIntegrador()
    return _ollama_instancia


__all__ = [
    "OllamaIntegrador",
    "obtener_ollama"
]
