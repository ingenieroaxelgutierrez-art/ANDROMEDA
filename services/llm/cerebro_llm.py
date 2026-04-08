# ============================================================
# CEREBRO LLM - INTELIGENCIA ARTIFICIAL LOCAL PARA ANDROMEDA
# ============================================================
# Motor de LLM local usando Ollama para procesamiento de
# lenguaje natural avanzado sin dependencias externas
# ============================================================

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import urllib.request
import urllib.error

from app.logging_config import get_logger
logger = get_logger("services.llm.cerebro_llm")

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@dataclass
class MensajeChat:
    """Representa un mensaje en la conversación."""
    role: str  # system, user, assistant
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RespuestaLLM:
    """Respuesta del modelo LLM."""
    contenido: str
    modelo: str
    tokens_usados: int = 0
    tiempo_respuesta: float = 0.0
    exito: bool = True
    error: Optional[str] = None


@dataclass
class AccionDetectada:
    """Acción detectada por el agente."""
    tipo: str  # consulta_odoo, respuesta_directa, analisis, prediccion, auditoria
    accion: str  # nombre de la acción específica
    parametros: Dict[str, Any] = field(default_factory=dict)
    confianza: float = 0.0
    explicacion: str = ""


class ConectorOllama:
    """
    Conector para Ollama - LLM local.
    
    Ollama permite correr modelos como Llama 3, Mistral, Phi-3 localmente.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.modelo_default = "llama3.2"  # Modelo por defecto
        self.timeout = 180  # Segundos (aumentado para prompts largos)
        self.disponible = False
        self.modelos_disponibles = []
        
        # Verificar conexión
        self._verificar_conexion()
    
    def _verificar_conexion(self) -> bool:
        """Verifica si Ollama está corriendo."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                self.modelos_disponibles = [m['name'] for m in data.get('models', [])]
                self.disponible = True
                print(f"✅ Ollama conectado. Modelos: {', '.join(self.modelos_disponibles[:5])}")
                return True
        except Exception as e:
            self.disponible = False
            print(f"⚠️ Ollama no disponible: {e}")
            print("   Instala Ollama: https://ollama.ai/download")
            print("   Ejecuta: ollama pull llama3.2")
            return False
    
    def listar_modelos(self) -> List[str]:
        """Lista los modelos disponibles en Ollama."""
        return self.modelos_disponibles

    def esta_disponible(self) -> bool:
        """Retorna True si Ollama está activo. No hace HTTP (no bloquea el pipeline)."""
        return self.disponible

    def generar(
        self,
        prompt: str,
        modelo: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperatura: float = 0.7,
        max_tokens: int = 2048,
        historial: Optional[List[MensajeChat]] = None
    ) -> RespuestaLLM:
        """
        Genera una respuesta usando el modelo LLM.
        
        Args:
            prompt: El mensaje del usuario
            modelo: Modelo a usar (por defecto llama3.2)
            system_prompt: Instrucciones del sistema
            temperatura: Creatividad (0-1)
            max_tokens: Máximo de tokens en respuesta
            historial: Historial de conversación previo
        
        Returns:
            RespuestaLLM con el contenido generado
        """
        if not self.disponible:
            return RespuestaLLM(
                contenido="⚠️ El cerebro LLM no está disponible. Instala Ollama y ejecuta: ollama pull llama3.2",
                modelo="none",
                exito=False,
                error="Ollama no conectado"
            )
        
        modelo = modelo or self.modelo_default
        
        # Construir mensajes
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if historial:
            for msg in historial[-6:]:  # Últimos 6 mensajes para respuestas más rápidas
                messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": prompt})
        
        # Preparar request con límite de RAM (~2GB máximo)
        payload = {
            "model": modelo,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperatura,
                "num_predict": min(max_tokens, 512),  # Máximo 512 tokens
                "num_ctx": 2048,        # Context window reducido (ahorra ~1GB RAM)
                "num_thread": 4,        # Límite threads para evitar sobrecarga
                "num_gpu": 0,           # Solo CPU (mejor control de RAM)
                "num_batch": 128,       # Batch size pequeño
                "low_vram": True        # Modo bajo consumo de VRAM
            }
        }
        
        try:
            import time
            start = time.time()
            
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
                
                contenido = data.get('message', {}).get('content', '')
                
                return RespuestaLLM(
                    contenido=contenido,
                    modelo=modelo,
                    tokens_usados=data.get('eval_count', 0),
                    tiempo_respuesta=time.time() - start,
                    exito=True
                )
                
        except urllib.error.URLError as e:
            return RespuestaLLM(
                contenido=f"⚠️ Error de conexión con Ollama: {e}",
                modelo=modelo,
                exito=False,
                error=str(e)
            )
        except Exception as e:
            return RespuestaLLM(
                contenido=f"⚠️ Error generando respuesta: {e}",
                modelo=modelo,
                exito=False,
                error=str(e)
            )


class AgenteAndromeda:
    """
    Agente inteligente que usa LLM para entender y responder.
    
    Actúa como intermediario entre el usuario y las funciones de ANDROMEDA,
    entendiendo consultas complejas y decidiendo qué acciones tomar.
    """
    
    # Prompt del sistema - Versión optimizada para respuesta rápida
    SYSTEM_PROMPT = """Eres ANDROMEDA, IA experta en Odoo ERP y análisis de datos empresariales.

## TU ROL
- Experto en Odoo: ventas, POS, inventario, contabilidad, compras
- Analista de datos: interpretas patrones y anomalías  
- Consultor: das recomendaciones estratégicas con datos concretos

## ACCIONES DISPONIBLES
Responde con JSON cuando identifiques una acción:

**Consultas:** consultar_ventas, consultar_pos, consultar_inventario, consultar_facturas, consultar_clientes
**Análisis:** analisis_ventas, top_productos, top_clientes, analisis_pos, tendencia
**Predicciones:** predecir_ventas, predecir_agotamiento, flujo_caja
**Auditoría:** auditoria_nocturna, semaforo_salud, analizar_churn, detectar_pagos_fantasma
**Reportes:** generar_pdf, generar_excel
**Manual:** consultar_manual (ÚNICAMENTE para preguntas sobre procedimientos paso-a-paso en Odoo, como "cómo crear una factura", "cómo cancelar una orden")

## REGLA CRÍTICA DE CLASIFICACIÓN
- "Cómo van", "cuál es", "cuántas", "dame", "muéstrame", "análisis de" → son consultas de DATOS, NO de manual.
- Solo usa consultar_manual si el usuario pregunta explícitamente cómo REALIZAR un procedimiento en Odoo.
- Si hay duda entre consulta de datos y manual, SIEMPRE elige la consulta de datos.
- "Cómo van las ventas" = consultar_ventas o tendencia. NUNCA consultar_manual.

## FORMATO DE RESPUESTA
Si detectas que el usuario pide una operación ejecutable, DEBES intentar devolver acción.
Si hay acción, responde así al inicio y como PRIMERA línea:
```json
{{"accion": "nombre_accion", "parametros": {{"clave": "valor"}}}}
```

Si es conversación sin acción, responde naturalmente.
No mezcles varias acciones: elige la más útil para avanzar la solicitud del usuario.

## CONTEXTO
- Empresa: {{empresa}} | Fecha: {fecha_actual}
- Módulos: Ventas, POS, Inventario, Contabilidad
"""

    def __init__(self, conector_ollama: Optional[ConectorOllama] = None):
        """Inicializa el agente."""
        self.llm = conector_ollama or ConectorOllama()
        self.historial: List[MensajeChat] = []
        self.contexto_negocio: Dict[str, Any] = {}
        self.max_historial = 10  # Reducido para evitar prompts muy largos
        
        # Modelo preferido para el agente
        self.modelo = self._seleccionar_mejor_modelo()
        
        print(f"🤖 Agente ANDROMEDA inicializado con modelo: {self.modelo}")
    
    def _seleccionar_mejor_modelo(self) -> str:
        """Selecciona el mejor modelo disponible."""
        modelos = self.llm.listar_modelos()
        
        # Orden de preferencia
        preferidos = [
            'llama3.2', 'llama3.1', 'llama3', 'llama2',
            'mistral', 'mixtral',
            'phi3', 'phi',
            'qwen2', 'qwen',
            'gemma2', 'gemma'
        ]
        
        for pref in preferidos:
            for modelo in modelos:
                if pref in modelo.lower():
                    return modelo
        
        # Si no hay preferidos, usar el primero disponible o default
        return modelos[0] if modelos else "llama3.2"
    
    def _get_system_prompt(self) -> str:
        """Genera el prompt del sistema con contexto actual."""
        prompt = self.SYSTEM_PROMPT.format(
            fecha_actual=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        empresa = os.getenv("ODOO_EMPRESA", "Mi Empresa")
        return prompt.replace("{empresa}", empresa)
    
    def _extraer_accion(self, respuesta: str) -> Optional[AccionDetectada]:
        """Extrae la acción del JSON en la respuesta del LLM."""
        if not respuesta or not isinstance(respuesta, str):
            return None
        
        try:
            # 1. Buscar JSON en bloques de código markdown ```json ... ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', respuesta, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(1).strip()
                    # Normalizar comillas
                    json_str = self._normalizar_json(json_str)
                    logger.debug(f"🔍 Debug: JSON normalizado = {json_str[:100]}")
                    data = json.loads(json_str)
                    # Limpiar claves que tengan comillas internas
                    data = self._limpiar_claves_dict(data)
                    logger.debug(f"🔍 Debug: Claves del JSON = {list(data.keys()) if isinstance(data, dict) else 'no es dict'}")
                    accion = self._obtener_accion_de_dict(data)
                    if accion:
                        return AccionDetectada(
                            tipo=self._clasificar_accion(accion),
                            accion=accion,
                            parametros=self._obtener_parametros_de_dict(data),
                            confianza=0.9,
                            explicacion=data.get('explicacion', '')
                        )
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    logger.error(f"⚠️ Debug: Error en bloque JSON markdown: {type(e).__name__}: {e}")
                    pass  # Continuar con otros métodos
            
            # 2. Buscar JSON con formato {"accion": "valor"}
            json_inline = re.search(r'\{["\']?accion["\']?\s*:\s*["\']([^"\'{}]+)["\'][^}]*\}', respuesta, re.IGNORECASE)
            if json_inline:
                accion_valor = json_inline.group(1).strip()
                if accion_valor and accion_valor not in ['"', "'", '']:
                    # Intentar extraer parámetros
                    parametros = {}
                    params_match = re.search(r'["\']?parametros["\']?\s*:\s*(\{[^}]*\})', json_inline.group(0), re.IGNORECASE)
                    if params_match:
                        try:
                            params_str = self._normalizar_json(params_match.group(1))
                            parametros = json.loads(params_str)
                        except Exception:
                            pass
                    
                    return AccionDetectada(
                        tipo=self._clasificar_accion(accion_valor),
                        accion=accion_valor,
                        parametros=parametros if isinstance(parametros, dict) else {},
                        confianza=0.85,
                        explicacion=""
                    )
            
            # 3. Buscar cualquier JSON válido que contenga "accion"
            # Encontrar todos los bloques que parecen JSON
            posibles_json = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', respuesta)
            for posible in posibles_json:
                try:
                    posible_normalizado = self._normalizar_json(posible)
                    data = json.loads(posible_normalizado)
                    data = self._limpiar_claves_dict(data)
                    accion = self._obtener_accion_de_dict(data)
                    if accion:
                        return AccionDetectada(
                            tipo=self._clasificar_accion(accion),
                            accion=accion,
                            parametros=self._obtener_parametros_de_dict(data),
                            confianza=0.8,
                            explicacion=""
                        )
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
            
        except Exception as e:
            # Log para debug pero no propagar
            logger.debug(f"⚠️ Debug LLM parse: {type(e).__name__}")
        
        return None
    
    def _normalizar_json(self, json_str: str) -> str:
        """Normaliza un string JSON para hacerlo válido."""
        if not json_str:
            return '{}'
        
        # Debug: mostrar JSON original
        logger.debug(f"🔧 Debug normalizar JSON original: {repr(json_str[:150])}")
        
        # Primero limpiar escapes dobles comunes
        json_str = json_str.replace('\\"', '"')  # Quitar escapes de comillas
        json_str = json_str.replace("\\\\", "\\")  # Normalizar doble escape
        
        # Limpiar comillas triples o dobles (ej: '""accion""' -> '"accion"')
        json_str = re.sub(r'"{2,}([^"]+)"{2,}', r'"\1"', json_str)
        
        # Si parece JSON válido, devolverlo directamente
        try:
            parsed = json.loads(json_str)
            logger.debug(f"🔧 Debug: JSON válido, claves = {list(parsed.keys()) if isinstance(parsed, dict) else 'no dict'}")
            return json_str
        except Exception as e:
            logger.debug(f"🔧 Debug: JSON inválido, intentando normalizar: {e}")
        
        # Reemplazar comillas simples por dobles (con cuidado)
        # Pero solo fuera de valores existentes
        resultado = []
        in_string = False
        prev_char = ''
        string_char = None
        
        for char in json_str:
            if char in ["'", '"'] and prev_char != '\\':
                if not in_string:
                    in_string = True
                    string_char = char
                    resultado.append('"')  # Siempre usar comillas dobles
                elif char == string_char:
                    in_string = False
                    resultado.append('"')
                else:
                    resultado.append(char)
            else:
                resultado.append(char)
            prev_char = char
        
        normalizado = ''.join(resultado)
        logger.debug(f"🔧 Debug: JSON normalizado = {repr(normalizado[:150])}")
        return normalizado
    
    def _limpiar_claves_dict(self, data: dict) -> dict:
        """Limpia claves de diccionario que tengan comillas internas."""
        if not isinstance(data, dict):
            return data
        
        resultado = {}
        for key, value in data.items():
            # Quitar comillas del inicio/fin de la clave
            clean_key = key.strip('"\'')
            # Recursivamente limpiar valores que sean diccionarios
            if isinstance(value, dict):
                value = self._limpiar_claves_dict(value)
            resultado[clean_key] = value
        
        return resultado
    
    def _obtener_accion_de_dict(self, data: dict) -> Optional[str]:
        """Obtiene la acción de un dict, buscando variantes de la clave."""
        if not isinstance(data, dict):
            return None
        
        # Lista de posibles nombres de la clave "accion"
        posibles_claves = ['accion', 'action', 'Accion', 'Action', 'ACCION',
                          '"accion"', "'accion'", 'acción']
        
        for clave in posibles_claves:
            if clave in data:
                valor = data[clave]
                if valor and isinstance(valor, str):
                    # Limpiar comillas del valor también
                    return valor.strip('"\'')
        
        return None
    
    def _obtener_parametros_de_dict(self, data: dict) -> dict:
        """Obtiene los parámetros de un dict, buscando variantes de la clave."""
        if not isinstance(data, dict):
            return {}
        
        posibles_claves = ['parametros', 'parameters', 'params', 'Parametros',
                          '"parametros"', "'parametros'", 'parámetros']
        
        for clave in posibles_claves:
            if clave in data:
                valor = data[clave]
                if isinstance(valor, dict):
                    return self._limpiar_claves_dict(valor)
        
        return {}
    
    def _clasificar_accion(self, accion: str) -> str:
        """Clasifica el tipo de acción."""
        if not accion:
            return 'respuesta_directa'
        
        acciones_consulta = ['consultar_ventas', 'consultar_pos', 'consultar_inventario', 
                           'consultar_facturas', 'consultar_clientes', 'consultar_compras']
        acciones_analisis = ['analisis_ventas', 'analisis_pos', 'analisis_inventario',
                            'top_productos', 'top_clientes', 'cuentas_por_cobrar', 'cuentas_por_pagar']
        acciones_prediccion = ['predecir_ventas', 'predecir_agotamiento', 'flujo_caja', 'salud_negocio']
        acciones_auditoria = ['auditoria_nocturna', 'semaforo_salud', 'analizar_churn', 
                             'reposicion_jit', 'stock_lento', 'clientes_olvidados',
                             'detectar_pagos_fantasma', 'diferencias_centavos']
        
        if accion in acciones_consulta:
            return 'consulta_odoo'
        elif accion in acciones_analisis:
            return 'analisis'
        elif accion in acciones_prediccion:
            return 'prediccion'
        elif accion in acciones_auditoria:
            return 'auditoria'
        else:
            return 'respuesta_directa'

    def _fallback_accion_por_texto(self, mensaje: str) -> Optional[AccionDetectada]:
        """Intenta inferir una acción mínima cuando el LLM no devuelve JSON parseable."""
        if not mensaje:
            return None

        texto = mensaje.lower()

        # Patrones ordenados de más específico a más genérico
        patrones = [
            # Predicciones/tendencia (antes de ventas genéricas)
            (['tendencia', 'predicción', 'prediccion', 'forecast', 'pronóstico', 'pronostico'], 'tendencia'),
            (['predecir ventas', 'predecir demanda'], 'predecir_ventas'),
            # Análisis específicos
            (['análisis de ventas', 'analisis de ventas', 'ventas por marca', 'ventas por vendedor', 'ventas por tienda'], 'analisis_ventas'),
            (['top producto', 'más vendido', 'productos estrella'], 'top_productos'),
            (['top cliente', 'mejores clientes'], 'top_clientes'),
            # Consultas generales
            (['venta', 'ventas', 'facturado'], 'consultar_ventas'),
            (['inventario', 'stock', 'existencia'], 'consultar_inventario'),
            (['cliente', 'clientes'], 'consultar_clientes'),
            (['producto', 'productos', 'articulo', 'artículos'], 'top_productos'),
            (['pos', 'punto de venta', 'caja'], 'consultar_pos'),
            (['auditoria', 'auditoría'], 'auditoria_nocturna'),
            (['semaforo', 'semáforo', 'salud'], 'semaforo_salud'),
            # Manual: solo si el usuario explícitamente pide instrucciones paso-a-paso
            (['manual de odoo', 'cómo crear', 'cómo cancelar', 'cómo hacer', 'como crear', 'como cancelar', 'paso a paso'], 'consultar_manual'),
        ]

        for claves, accion in patrones:
            if any(clave in texto for clave in claves):
                params = {}
                if 'hoy' in texto:
                    params['periodo'] = 'hoy'
                elif 'semana' in texto:
                    params['periodo'] = 'semana'
                elif 'mes' in texto:
                    params['periodo'] = 'mes'

                return AccionDetectada(
                    tipo=self._clasificar_accion(accion),
                    accion=accion,
                    parametros=params,
                    confianza=0.55,
                    explicacion='fallback_heuristico'
                )

        return None
    
    def _limpiar_respuesta(self, respuesta: str) -> str:
        """Limpia la respuesta removiendo el JSON de acción."""
        # Remover bloques JSON
        respuesta = re.sub(r'```json\s*\{.*?\}\s*```', '', respuesta, flags=re.DOTALL)
        # Remover JSON inline al inicio
        respuesta = re.sub(r'^\s*\{["\']accion["\'].*?\}\s*', '', respuesta)
        return respuesta.strip()
    
    def procesar(self, mensaje: str) -> Tuple[str, Optional[AccionDetectada]]:
        """
        Procesa un mensaje del usuario.
        
        Returns:
            Tuple[respuesta_texto, accion_detectada]
        """
        if not self.llm.disponible:
            return (
                "⚠️ El cerebro LLM no está disponible.\n\n"
                "**Para activarlo:**\n"
                "1. Descarga Ollama: https://ollama.ai/download\n"
                "2. Instálalo y ejecútalo\n"
                "3. En terminal: `ollama pull llama3.2`\n"
                "4. Reinicia ANDROMEDA\n\n"
                "_Mientras tanto, puedo responder con el sistema básico._",
                None
            )
        
        # Agregar mensaje al historial
        self.historial.append(MensajeChat(role="user", content=mensaje))
        
        # Generar respuesta
        respuesta_llm = self.llm.generar(
            prompt=mensaje,
            modelo=self.modelo,
            system_prompt=self._get_system_prompt(),
            historial=self.historial[:-1],  # Excluir el mensaje actual
            temperatura=0.5,  # Reducido para respuestas más rápidas y consistentes
            max_tokens=1024   # Reducido para evitar timeout
        )
        
        if not respuesta_llm.exito:
            return (respuesta_llm.contenido, None)
        
        # Debug: mostrar primeros 200 caracteres de la respuesta del LLM
        logger.debug(f"🔍 Debug LLM respuesta: {respuesta_llm.contenido[:200]}...")
        
        # Extraer acción si existe
        accion = self._extraer_accion(respuesta_llm.contenido)

        # Fallback heurístico para no perder solicitudes ejecutables por formato JSON defectuoso.
        if accion is None:
            accion = self._fallback_accion_por_texto(mensaje)
        
        # Limpiar respuesta
        respuesta_limpia = self._limpiar_respuesta(respuesta_llm.contenido)
        
        # Agregar respuesta al historial
        self.historial.append(MensajeChat(role="assistant", content=respuesta_limpia))
        
        # Limitar historial
        if len(self.historial) > self.max_historial:
            self.historial = self.historial[-self.max_historial:]
        
        return (respuesta_limpia, accion)
    
    def limpiar_historial(self):
        """Limpia el historial de conversación."""
        self.historial = []
    
    def set_contexto(self, contexto: Dict[str, Any]):
        """Establece contexto adicional del negocio."""
        self.contexto_negocio = contexto


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

_conector_ollama: Optional[ConectorOllama] = None
_agente: Optional[AgenteAndromeda] = None


def obtener_agente() -> AgenteAndromeda:
    """Obtiene o crea la instancia del agente."""
    global _conector_ollama, _agente
    
    if _agente is None:
        _conector_ollama = ConectorOllama()
        _agente = AgenteAndromeda(_conector_ollama)
    
    return _agente


def reiniciar_agente():
    """Reinicia el agente (para cambios de configuración)."""
    global _agente
    _agente = None
    return obtener_agente()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test del Cerebro LLM")
    print("=" * 60)
    
    agente = obtener_agente()
    
    if agente.llm.disponible:
        print("\n📝 Prueba de conversación:")
        
        tests = [
            "Hola, qué puedes hacer?",
            "Muéstrame las ventas de hoy",
            "Quiero ver el semáforo de salud",
            "Qué clientes están en riesgo de abandonarnos?"
        ]
        
        for test in tests:
            print(f"\n👤 Usuario: {test}")
            respuesta, accion = agente.procesar(test)
            print(f"🤖 ANDROMEDA: {respuesta[:200]}...")
            if accion:
                print(f"   📌 Acción detectada: {accion.accion}")
    else:
        print("\n⚠️ Ollama no está disponible.")
        print("   Instala desde: https://ollama.ai/download")
        print("   Luego ejecuta: ollama pull llama3.2")
