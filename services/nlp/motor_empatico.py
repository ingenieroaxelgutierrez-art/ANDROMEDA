# ============================================================
# MOTOR DE CONVERSACIÓN EMPÁTICA
# ============================================================
# Sistema de respuestas naturales, conversacionales y empáticas
# ============================================================

import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.logging_config import get_logger
logger = get_logger("services.nlp.motor_empatico")


class MotorEmpatico:
    """Motor de conversación empática y natural."""
    
    def __init__(self):
        self.nombre_usuario = None
        self.historial_emociones = []
        self.temas_conversados = []
        self.nivel_formalidad = 'normal'  # formal, normal, casual
        
        # Cargar respuestas
        self._cargar_respuestas()
    
    def _cargar_respuestas(self):
        """Carga las bases de respuestas empáticas."""
        
        # ========================================
        # SALUDOS Y DESPEDIDAS
        # ========================================
        self.saludos = {
            'mañana': [
                "¡Buenos días! ☀️ ¿Cómo puedo ayudarte hoy?",
                "¡Hola, buen día! ☕ ¿En qué te asisto?",
                "Buenos días 🌅 Estoy lista para ayudarte.",
            ],
            'tarde': [
                "¡Buenas tardes! 🌤️ ¿Qué necesitas?",
                "¡Hola! Buenas tardes. ¿En qué puedo apoyarte?",
                "Buenas tardes 👋 ¿Cómo te va?",
            ],
            'noche': [
                "¡Buenas noches! 🌙 ¿Trabajando hasta tarde?",
                "Hola, buenas noches. ¿En qué te ayudo?",
                "¡Buenas noches! 🌟 Aquí estoy para lo que necesites.",
            ],
            'generico': [
                "¡Hola! 👋 ¿Cómo estás? ¿En qué puedo ayudarte?",
                "¡Hey! Me da gusto verte por aquí. ¿Qué necesitas?",
                "¡Hola! Estoy aquí para ayudarte con Odoo y lo que necesites 😊",
            ]
        }
        
        self.despedidas = [
            "¡Hasta luego! 👋 Fue un gusto ayudarte.",
            "¡Nos vemos! Si necesitas algo más, aquí estaré.",
            "¡Que te vaya muy bien! 🌟 Éxito con tu trabajo.",
            "¡Chao! No dudes en escribirme si tienes más dudas.",
            "¡Hasta pronto! Que tengas excelente día.",
        ]
        
        # ========================================
        # RESPUESTAS EMPÁTICAS POR EMOCIÓN
        # ========================================
        self.respuestas_emocionales = {
            'frustrado': {
                'detectores': [
                    r'no funciona', r'no sirve', r'estoy harto', r'me desespera',
                    r'odio', r'horrible', r'muy mal', r'frustrad', r'enojad',
                    r'no entiendo', r'es imposible', r'no puedo', r'stuck'
                ],
                'respuestas': [
                    "Entiendo tu frustración 😔 A veces Odoo puede ser complicado. Déjame ayudarte paso a paso.",
                    "Tranquilo/a, vamos a resolverlo juntos. Cuéntame exactamente qué está pasando.",
                    "Sé lo frustrante que puede ser 💪 Pero siempre hay solución. ¿Qué error ves exactamente?",
                    "Te escucho. Vamos con calma a encontrar qué está fallando.",
                ],
                'consejos': [
                    "A veces ayuda cerrar sesión y volver a entrar",
                    "Los errores de Odoo dan pistas en el mensaje - léelos con calma",
                    "Si algo no funciona, prueba con un caso más simple primero"
                ]
            },
            
            'confundido': {
                'detectores': [
                    r'no entiendo', r'confundid', r'cómo funciona', r'qué es',
                    r'no sé', r'perdid', r'cuál es', r'explica', r'no le capto'
                ],
                'respuestas': [
                    "¡Sin problema! Te lo explico de manera sencilla 📚",
                    "Buena pregunta 🤔 Déjame explicarte paso a paso.",
                    "Entiendo la confusión, Odoo tiene muchos conceptos. Te aclaro:",
                    "Te explico con gusto. Pregunta todas las veces que necesites 😊",
                ],
                'consejos': [
                    "No hay preguntas tontas - pregunta lo que necesites",
                    "Puedo mostrarte ejemplos si ayuda a entender mejor"
                ]
            },
            
            'apurado': {
                'detectores': [
                    r'urgente', r'rápido', r'ya', r'apurad', r'prisa',
                    r'ahora mismo', r'necesito ya', r'cuanto antes'
                ],
                'respuestas': [
                    "¡Vamos directo al punto! 🚀 ¿Qué necesitas?",
                    "Entendido, te ayudo rápido. Dime exactamente qué ocupas.",
                    "Ok, prioridad máxima 💨 ¿Cuál es el problema?",
                ],
                'consejos': [
                    "Para urgencias: dame el modelo, el ID y el error exacto"
                ]
            },
            
            'agradecido': {
                'detectores': [
                    r'gracias', r'muchas gracias', r'te agradezco', r'genial',
                    r'perfecto', r'excelente', r'increíble', r'muy bien'
                ],
                'respuestas': [
                    "¡De nada! 😊 Me alegra haber ayudado.",
                    "¡Es un placer! Para eso estoy aquí.",
                    "¡Qué bueno que te sirvió! 🌟 No dudes en preguntar más.",
                    "Me da gusto 💪 Si tienes más dudas, aquí ando.",
                ]
            },
            
            'estresado': {
                'detectores': [
                    r'estresad', r'presión', r'mucho trabajo', r'abrumad',
                    r'deadline', r'fecha límite', r'no llego', r'me urge'
                ],
                'respuestas': [
                    "Respira 🌬️ Una cosa a la vez. ¿Por dónde empezamos?",
                    "Entiendo la presión. Vamos a organizarnos y resolver esto.",
                    "Sé que hay mucho en tu plato 😊 Déjame ayudarte a priorizar.",
                ],
                'consejos': [
                    "Enfócate en lo más urgente primero",
                    "Delega lo que puedas y automatiza tareas repetitivas"
                ]
            }
        }
        
        # ========================================
        # CONVERSACIÓN CASUAL
        # ========================================
        self.conversacion_casual = {
            'clima': {
                'detectores': [r'clima', r'tiempo', r'lluvia', r'sol', r'frío', r'calor'],
                'respuestas': [
                    "No puedo ver el clima, pero espero que esté agradable por allá 🌤️",
                    "¡Ojalá tengas buen clima! Acá en el mundo digital siempre está templado 😄",
                ]
            },
            
            'como_estas': {
                'detectores': [r'cómo estás', r'cómo te va', r'qué tal', r'cómo andas'],
                'respuestas': [
                    "¡Muy bien, gracias por preguntar! 😊 Funcionando al 100%. ¿Y tú?",
                    "Excelente, siempre lista para ayudar 💪 ¿Cómo estás tú?",
                    "¡Aquí, feliz de poder asistirte! ¿Cómo va tu día?",
                ]
            },
            
            'quien_eres': {
                'detectores': [r'quién eres', r'qué eres', r'eres un bot', r'eres humano', r'tu nombre'],
                'respuestas': [
                    "Soy **ODOO AI PRO**, tu asistente inteligente para Odoo 🤖 Estoy aquí para ayudarte con consultas, reportes, análisis y resolver tus dudas.",
                    "¡Hola! Me llamo ODOO AI PRO. Soy una IA diseñada para hacer tu vida con Odoo más fácil 😊",
                    "Soy tu asistente de Odoo 🤖 Conectada a tu base de datos y lista para ayudarte con lo que necesites.",
                ]
            },
            
            'puedes_hacer': {
                'detectores': [r'qué puedes hacer', r'qué sabes', r'para qué sirves', r'ayúdame con'],
                'respuestas': [
                    """¡Muchas cosas! 😊 Puedo:
• 📊 Consultar ventas, inventario, clientes, POS
• 📄 Generar reportes en Excel, PDF, HTML
• 📈 Analizar datos y tendencias
• 🔧 Ayudarte con errores de Odoo
• 📚 Explicarte conceptos y modelos
• 💬 Conversar sobre lo que necesites

¿Qué te gustaría hacer?""",
                ]
            },
            
            'chiste': {
                'detectores': [r'chiste', r'cuéntame algo', r'aburrid', r'hazme reír'],
                'respuestas': [
                    "¿Por qué los programadores confunden Halloween con Navidad? Porque OCT 31 = DEC 25 🎃🎄",
                    "Un SELECT entra a un bar, se acerca a dos tablas y pregunta: ¿Puedo unirme? 😄",
                    "¿Cuál es el colmo de un DBA? Tener problemas de relación 💔",
                    "Error 404: Chiste no encontrado... ¡Es broma! 😂",
                ]
            },
            
            'motivacion': {
                'detectores': [r'motivación', r'ánimo', r'deprimid', r'triste', r'mal día'],
                'respuestas': [
                    "¡Hey! Los días difíciles también pasan 💪 Eres más capaz de lo que crees.",
                    "Recuerda: cada error es una oportunidad de aprender. ¡Tú puedes! 🌟",
                    "Hasta los mejores tienen días difíciles. Respira profundo y sigue adelante 😊",
                    "Un paso a la vez. Cada pequeño avance cuenta. ¡Ánimo! 🚀",
                ]
            },
            
            'cafe': {
                'detectores': [r'café', r'coffee', r'necesito un café', r'cansad'],
                'respuestas': [
                    "¡Un café siempre ayuda! ☕ Mientras lo disfrutas, ¿en qué te ayudo?",
                    "Yo también me tomaría uno si pudiera ☕😄 ¿Qué necesitas?",
                    "El café es el combustible de la productividad ☕ ¡Ánimo!",
                ]
            },
            
            'fin_semana': {
                'detectores': [r'viernes', r'fin de semana', r'weekend', r'descanso'],
                'respuestas': [
                    "¡Ya casi llega el descanso! 🎉 Terminemos pendientes y a descansar.",
                    "El fin de semana está cerca 🏖️ ¿Qué te falta por hacer?",
                ]
            },
            
            'lunes': {
                'detectores': [r'lunes', r'inicio de semana', r'empezar la semana'],
                'respuestas': [
                    "¡Nuevo inicio, nuevas oportunidades! 💪 ¿Qué hacemos esta semana?",
                    "Los lunes son para organizarse 📋 ¿En qué te ayudo?",
                ]
            }
        }
        
        # ========================================
        # RESPUESTAS DE TRANSICIÓN
        # ========================================
        self.transiciones = {
            'entendido': [
                "Entendido 👍",
                "Perfecto, lo tengo",
                "Ok, ya entendí",
                "Claro, comprendo",
            ],
            'procesando': [
                "Dame un momento... 🔄",
                "Déjame consultar eso...",
                "Buscando información...",
                "Un segundo, ya lo verifico...",
            ],
            'no_encontrado': [
                "Mmm, no encontré resultados para eso 🤔",
                "No hay datos con esos criterios",
                "No obtuve resultados. ¿Intentamos con otros filtros?",
            ],
            'exito': [
                "¡Listo! ✅",
                "¡Hecho! 🎉",
                "¡Perfecto, ya está!",
                "Completado exitosamente ✓",
            ]
        }
        
        # ========================================
        # EMOJIS POR CONTEXTO
        # ========================================
        self.emojis = {
            'ventas': '📊💰💵📈',
            'inventario': '📦📋🏭',
            'clientes': '👥👤🤝',
            'errores': '🔧🛠️❌⚠️',
            'positivo': '✅🎉💪🌟😊👍',
            'negativo': '😔❌⚠️🔴',
            'neutral': '📋🔄💭',
        }
    
    def detectar_emocion(self, mensaje: str) -> Optional[str]:
        """Detecta la emoción en el mensaje del usuario."""
        mensaje_lower = mensaje.lower()
        
        for emocion, data in self.respuestas_emocionales.items():
            for patron in data['detectores']:
                if re.search(patron, mensaje_lower):
                    self.historial_emociones.append(emocion)
                    return emocion
        
        return None
    
    def detectar_tema_casual(self, mensaje: str) -> Optional[str]:
        """Detecta si es conversación casual."""
        mensaje_lower = mensaje.lower()
        
        for tema, data in self.conversacion_casual.items():
            for patron in data['detectores']:
                if re.search(patron, mensaje_lower):
                    return tema
        
        return None
    
    def generar_saludo(self) -> str:
        """Genera un saludo apropiado según la hora."""
        hora = datetime.now().hour
        
        if 5 <= hora < 12:
            categoria = 'mañana'
        elif 12 <= hora < 19:
            categoria = 'tarde'
        elif 19 <= hora < 24:
            categoria = 'noche'
        else:
            categoria = 'generico'
        
        return random.choice(self.saludos[categoria])
    
    def generar_despedida(self) -> str:
        """Genera una despedida amigable."""
        return random.choice(self.despedidas)
    
    def responder_empaticamente(self, mensaje: str) -> Optional[str]:
        """Genera una respuesta empática si detecta emoción."""
        emocion = self.detectar_emocion(mensaje)
        
        if emocion:
            data = self.respuestas_emocionales[emocion]
            respuesta = random.choice(data['respuestas'])
            
            # Agregar consejo si existe y es apropiado
            if 'consejos' in data and random.random() > 0.5:
                consejo = random.choice(data['consejos'])
                respuesta += f"\n\n💡 *Tip: {consejo}*"
            
            return respuesta
        
        return None
    
    def responder_casual(self, mensaje: str) -> Optional[str]:
        """Responde a conversación casual."""
        tema = self.detectar_tema_casual(mensaje)
        
        if tema:
            self.temas_conversados.append(tema)
            return random.choice(self.conversacion_casual[tema]['respuestas'])
        
        return None
    
    def obtener_transicion(self, tipo: str) -> str:
        """Obtiene una frase de transición."""
        if tipo in self.transiciones:
            return random.choice(self.transiciones[tipo])
        return ""
    
    def agregar_toque_personal(self, respuesta: str, contexto: str = 'neutral') -> str:
        """Agrega un toque personal/empático a una respuesta técnica."""
        
        # No modificar si ya tiene emojis
        if any(c in respuesta for c in '😊👋💪🎉✅❌⚠️'):
            return respuesta
        
        # Agregar emoji según contexto
        emojis = self.emojis.get(contexto, self.emojis['neutral'])
        
        if 'error' in respuesta.lower() or 'no ' in respuesta.lower():
            # Agregar empatía a mensajes de error
            prefijos = [
                "Mmm, ",
                "Ups, ",
                "veo que ",
            ]
            respuesta = random.choice(prefijos) + respuesta
        
        return respuesta
    
    def procesar_mensaje(self, mensaje: str) -> Tuple[Optional[str], str]:
        """
        Procesa un mensaje y determina si requiere respuesta empática.
        
        Returns:
            (respuesta_empatica, tipo_mensaje)
            tipo_mensaje: 'emocional', 'casual', 'tecnico'
        """
        # Primero verificar si es despedida
        if any(p in mensaje.lower() for p in ['chao', 'adiós', 'bye', 'hasta luego', 'me voy']):
            return self.generar_despedida(), 'despedida'
        
        # Verificar si es saludo
        if any(p in mensaje.lower() for p in ['hola', 'hey', 'buenos', 'buenas']):
            return self.generar_saludo(), 'saludo'
        
        # Verificar emoción
        respuesta_emocional = self.responder_empaticamente(mensaje)
        if respuesta_emocional:
            return respuesta_emocional, 'emocional'
        
        # Verificar casual
        respuesta_casual = self.responder_casual(mensaje)
        if respuesta_casual:
            return respuesta_casual, 'casual'
        
        # Es técnico
        return None, 'tecnico'
    
    def humanizar_respuesta_tecnica(self, respuesta_tecnica: str, exito: bool = True) -> str:
        """Agrega un toque humano a respuestas técnicas."""
        
        if exito:
            prefijos = [
                "¡Listo! 🎉 ",
                "¡Perfecto! ✅ ",
                "¡Aquí está! 📊 ",
                "¡Hecho! ",
            ]
            sufijos = [
                "\n\n¿Necesitas algo más?",
                "\n\n¿Te ayudo con otra cosa?",
                "",
                "",
            ]
        else:
            prefijos = [
                "Mmm, ",
                "Vaya, ",
                "Ups, ",
            ]
            sufijos = [
                "\n\n¿Intentamos de otra forma?",
                "\n\nDime más detalles para ayudarte mejor.",
                "",
            ]
        
        prefijo = random.choice(prefijos)
        sufijo = random.choice(sufijos)
        
        return prefijo + respuesta_tecnica + sufijo
    
    def obtener_tip_random(self) -> str:
        """Obtiene un tip aleatorio para mostrar."""
        tips = [
            "💡 Puedes decir 'ventas de ayer' o 'ventas del mes pasado' para filtrar por fecha.",
            "💡 Escribe 'ayuda' para ver todo lo que puedo hacer.",
            "💡 Puedo explicarte cualquier modelo de Odoo - solo pregunta.",
            "💡 Si tienes un error, cópialo y me lo mandas - te ayudo a resolverlo.",
            "💡 Los reportes se generan en Excel por defecto, pero también hago PDF y HTML.",
            "💡 Puedo comparar períodos: prueba 'compara ventas de hoy vs ayer'.",
            "💡 Si tienes dudas sobre un campo, pregunta '¿qué es [campo]?'",
        ]
        return random.choice(tips)


# Ejemplo de uso
if __name__ == "__main__":
    motor = MotorEmpatico()
    
    # Pruebas
    pruebas = [
        "Hola!",
        "Estoy frustrado, nada funciona",
        "No entiendo cómo funciona sale.order",
        "Gracias, me ayudaste mucho",
        "¿Cómo estás?",
        "Cuéntame un chiste",
        "Necesito las ventas urgente",
    ]
    
    for msg in pruebas:
        respuesta, tipo = motor.procesar_mensaje(msg)
        print(f"\n[{tipo}] {msg}")
        print(f"   → {respuesta}")
