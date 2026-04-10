# ============================================================
# MONITOR DE SISTEMA - Dashboard de Logs y Análisis
# ============================================================
# Permite:
# - Ver errores recientes y patrones
# - Consultar prompts con baja confianza
# - Estadísticas en tiempo real
# - Exportar análisis
# ============================================================

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from tabulate import tabulate
import csv

from app.logging_config import get_logger
logger = get_logger("utils.monitor_sistema")


class MonitorSistema:
    """Monitor para analizar logs y eventos del sistema."""
    
    def __init__(self, db_path: str = "logs/eventos.db"):
        """
        Inicializa el monitor.
        
        Args:
            db_path: Ruta de la base de datos
        """
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            logger.warning(f"Base de datos no encontrada: {db_path}")
    
    def resumen_general(self) -> Dict[str, Any]:
        """Resumen general del sistema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de eventos
                cursor.execute("SELECT COUNT(*) FROM eventos")
                total_eventos = cursor.fetchone()[0]
                
                # Errores sin resolver
                cursor.execute("SELECT COUNT(*) FROM errores WHERE resuelta = 0")
                errores_abiertos = cursor.fetchone()[0]
                
                # Prompts procesados
                cursor.execute("SELECT COUNT(*) FROM prompts")
                prompts_total = cursor.fetchone()[0]
                
                # Confianza promedio
                cursor.execute("SELECT AVG(confianza_intencion) FROM prompts")
                confianza_promedio = cursor.fetchone()[0] or 0.0
                
                # Operaciones en rendimiento
                cursor.execute("SELECT COUNT(*) FROM rendimiento")
                operaciones_rastreadas = cursor.fetchone()[0]
                
                return {
                    'total_eventos': total_eventos,
                    'errores_abiertos': errores_abiertos,
                    'prompts_totales': prompts_total,
                    'confianza_promedio': round(confianza_promedio, 2),
                    'operaciones_rastreadas': operaciones_rastreadas,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error en resumen general: {e}")
            return {}
    
    def errores_por_modulo(self, dias: int = 7) -> Dict[str, List[Dict]]:
        """Errores agrupados por módulo."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()
                
                cursor.execute('''
                    SELECT modulo, tipo_error, frecuencia, mensaje, solucion_sugerida,
                           timestamp, criticidad
                    FROM errores
                    WHERE timestamp > ? AND resuelta = 0
                    ORDER BY modulo, frecuencia DESC
                ''', (fecha_limite,))
                
                errores = {}
                for row in cursor.fetchall():
                    modulo = row['modulo']
                    if modulo not in errores:
                        errores[modulo] = []
                    
                    errores[modulo].append({
                        'tipo': row['tipo_error'],
                        'frecuencia': row['frecuencia'],
                        'criticidad': row['criticidad'],
                        'mensaje': row['mensaje'],
                        'solucion': row['solucion_sugerida'],
                        'fecha': row['timestamp']
                    })
                
                return errores
        except Exception as e:
            logger.error(f"Error en errores por módulo: {e}")
            return {}
    
    def prompts_criticos(self, limite: int = 20) -> List[Dict]:
        """Prompts con baja confianza que necesitan mejora."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, sesion_id, prompt_original, intencion_detectada,
                           confianza_intencion, tiempo_respuesta_ms, usuario
                    FROM prompts
                    WHERE confianza_intencion < 0.7
                    ORDER BY confianza_intencion ASC
                    LIMIT ?
                ''', (limite,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo prompts críticos: {e}")
            return []
    
    def rendimiento_por_operacion(self, dias: int = 7) -> Dict[str, Dict]:
        """Análisis de rendimiento por operación."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()
                
                cursor.execute('''
                    SELECT modulo, operacion, 
                           COUNT(*) as total,
                           AVG(tiempo_ms) as promedio,
                           MIN(tiempo_ms) as minimo,
                           MAX(tiempo_ms) as maximo,
                           SUM(CASE WHEN exitosa = 1 THEN 1 ELSE 0 END) as exitosas
                    FROM rendimiento
                    WHERE timestamp > ?
                    GROUP BY modulo, operacion
                    ORDER BY promedio DESC
                ''', (fecha_limite,))
                
                resultados = {}
                for row in cursor.fetchall():
                    modulo = row[0]
                    if modulo not in resultados:
                        resultados[modulo] = []
                    
                    tasa_exito = (row[6] / row[2] * 100) if row[2] > 0 else 0
                    
                    resultados[modulo].append({
                        'operacion': row[1],
                        'total': row[2],
                        'promedio_ms': round(row[3], 1),
                        'minimo_ms': row[4],
                        'maximo_ms': row[5],
                        'tasa_exito': round(tasa_exito, 1)
                    })
                
                return resultados
        except Exception as e:
            logger.error(f"Error en rendimiento: {e}")
            return {}
    
    def tendencias(self, dias: int = 30) -> Dict[str, List]:
        """Tendencias de errores y rendimiento."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()
                
                # Errores por día
                cursor.execute('''
                    SELECT DATE(timestamp) as fecha, COUNT(*) as cantidad
                    FROM errores
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY fecha
                ''', (fecha_limite,))
                
                errores_diarios = [
                    {'fecha': row[0], 'cantidad': row[1]}
                    for row in cursor.fetchall()
                ]
                
                # Prompts por día
                cursor.execute('''
                    SELECT DATE(timestamp) as fecha, COUNT(*) as cantidad, 
                           AVG(confianza_intencion) as confianza_promedio
                    FROM prompts
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY fecha
                ''', (fecha_limite,))
                
                prompts_diarios = [
                    {
                        'fecha': row[0],
                        'cantidad': row[1],
                        'confianza': round(row[2], 2) if row[2] else 0
                    }
                    for row in cursor.fetchall()
                ]
                
                return {
                    'errores': errores_diarios,
                    'prompts': prompts_diarios
                }
        except Exception as e:
            logger.error(f"Error en tendencias: {e}")
            return {'errores': [], 'prompts': []}
    
    def usuarios_activos(self, dias: int = 7) -> List[Dict]:
        """Usuarios más activos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()
                
                cursor.execute('''
                    SELECT usuario, 
                           COUNT(*) as interacciones,
                           SUM(CASE WHEN tipo = 'ERROR' THEN 1 ELSE 0 END) as errores,
                           (SELECT COUNT(*) FROM prompts WHERE eventos.usuario = usuario 
                            AND timestamp > ?) as prompts
                    FROM eventos
                    WHERE timestamp > ? AND usuario IS NOT NULL
                    GROUP BY usuario
                    ORDER BY interacciones DESC
                    LIMIT 20
                ''', (fecha_limite, fecha_limite))
                
                return [
                    {
                        'usuario': row[0],
                        'interacciones': row[1],
                        'errores': row[2],
                        'prompts': row[3] or 0
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error en usuarios activos: {e}")
            return []
    
    # ========================================
    # EXPORTACIÓN Y REPORTES
    # ========================================
    
    def exportar_errores_csv(self, dias: int = 7, output_path: str = "logs/errores_export.csv"):
        """Exporta errores a CSV."""
        try:
            errores = self.errores_por_modulo(dias)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Módulo', 'Tipo Error', 'Frecuencia', 'Criticidad', 'Mensaje', 'Solución'])
                
                for modulo, lista_errores in errores.items():
                    for error in lista_errores:
                        writer.writerow([
                            modulo,
                            error['tipo'],
                            error['frecuencia'],
                            error['criticidad'],
                            error['mensaje'][:100],
                            error['solucion'][:100]
                        ])
            
            logger.info(f"Errores exportados a {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")
            return None
    
    def generar_reporte(self, output_path: str = "logs/reporte_sistema.txt") -> Optional[str]:
        """Genera reporte completo del sistema."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("REPORTE DEL SISTEMA ANDROMEDA\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n\n")
                
                # Resumen
                f.write("RESUMEN GENERAL\n")
                f.write("-" * 70 + "\n")
                resumen = self.resumen_general()
                for clave, valor in resumen.items():
                    f.write(f"{clave}: {valor}\n")
                f.write("\n")
                
                # Errores por módulo
                f.write("ERRORES POR MÓDULO (últimos 7 días)\n")
                f.write("-" * 70 + "\n")
                errores = self.errores_por_modulo(7)
                for modulo, lista_errores in errores.items():
                    f.write(f"\n{modulo}:\n")
                    for error in lista_errores[:5]:  # Top 5
                        f.write(f"  • {error['tipo']} (x{error['frecuencia']}) [{error['criticidad']}]\n")
                        f.write(f"    Solución: {error['solucion'][:80]}\n")
                f.write("\n")
                
                # Prompts críticos
                f.write("PROMPTS CON BAJA CONFIANZA\n")
                f.write("-" * 70 + "\n")
                prompts = self.prompts_criticos(10)
                for p in prompts:
                    f.write(f"  • Confianza: {p['confianza_intencion']:.1%}\n")
                    f.write(f"    Prompt: {p['prompt_original'][:60]}...\n")
                f.write("\n")
                
                # Rendimiento
                f.write("RENDIMIENTO\n")
                f.write("-" * 70 + "\n")
                rendimiento = self.rendimiento_por_operacion(7)
                for modulo, ops in rendimiento.items():
                    f.write(f"\n{modulo}:\n")
                    for op in ops[:3]:
                        f.write(f"  • {op['operacion']}: {op['promedio_ms']:.1f}ms " + 
                               f"({op['tasa_exito']:.0f}% éxito)\n")
            
            logger.info(f"Reporte generado: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return None
    
    # ========================================
    # VISUALIZACIÓN EN CONSOLA
    # ========================================
    
    def mostrar_dashboard(self):
        """Muestra un dashboard en la consola."""
        print("\n" + "=" * 80)
        print("DASHBOARD SISTEMA ANDROMEDA".center(80))
        print("=" * 80)
        
        # Resumen
        print("\n📊 RESUMEN GENERAL")
        print("-" * 80)
        resumen = self.resumen_general()
        resumen_tabla = [
            ["Total de Eventos", f"{resumen.get('total_eventos', 0):,}"],
            ["Errores Abiertos", f"{resumen.get('errores_abiertos', 0)}"],
            ["Prompts Procesados", f"{resumen.get('prompts_totales', 0):,}"],
            ["Confianza Promedio", f"{resumen.get('confianza_promedio', 0):.1%}"],
        ]
        print(tabulate(resumen_tabla, headers=["Métrica", "Valor"], tablefmt="grid"))
        
        # Errores por módulo
        print("\n⚠️  ERRORES POR MÓDULO")
        print("-" * 80)
        errores = self.errores_por_modulo(7)
        if errores:
            for modulo, lista_errores in list(errores.items())[:5]:
                print(f"\n{modulo}:")
                tabla = [
                    [e['tipo'], e['frecuencia'], e['criticidad']]
                    for e in lista_errores[:3]
                ]
                print(tabulate(tabla, 
                             headers=["Tipo", "Frecuencia", "Criticidad"],
                             tablefmt="simple"))
        else:
            print("✅ Sin errores abiertos")
        
        # Prompts críticos
        print("\n💭 PROMPTS CON BAJA CONFIANZA")
        print("-" * 80)
        prompts = self.prompts_criticos(5)
        if prompts:
            tabla = [
                [p['intencion_detectada'], f"{p['confianza_intencion']:.1%}"]
                for p in prompts
            ]
            print(tabulate(tabla, 
                         headers=["Intención", "Confianza"],
                         tablefmt="simple"))
        else:
            print("✅ Todos los prompts con confianza adecuada")
        
        # Usuarios activos
        print("\n👥 USUARIOS MÁS ACTIVOS")
        print("-" * 80)
        usuarios = self.usuarios_activos(7)
        if usuarios:
            tabla = [
                [u['usuario'], u['interacciones'], u['errores'], u['prompts']]
                for u in usuarios[:5]
            ]
            print(tabulate(tabla,
                         headers=["Usuario", "Interacciones", "Errores", "Prompts"],
                         tablefmt="simple"))
        
        print("\n" + "=" * 80 + "\n")
    
    def mostrar_prompts_mejorados(self, limite: int = 10):
        """Muestra prompts que necesitan mejora."""
        prompts = self.prompts_criticos(limite)
        
        if not prompts:
            print("✅ No hay prompts que necesiten mejora")
            return
        
        print("\n" + "🔧 PROMPTS QUE NECESITAN MEJORA".center(80))
        print("=" * 80)
        
        for i, p in enumerate(prompts, 1):
            print(f"\n{i}. Confianza: {p['confianza_intencion']:.1%}")
            print(f"   Intención detectada: {p['intencion_detectada']}")
            print(f"   Prompt: {p['prompt_original'][:70]}")
            if len(p['prompt_original']) > 70:
                print(f"           {p['prompt_original'][70:140]}")
            print(f"   Tiempo: {p['tiempo_respuesta_ms']}ms | Sesión: {p['sesion_id']}")


# ============================================================
# FUNCIONES UTILITARIAS
# ============================================================

_monitor_instancia = None

def obtener_monitor() -> MonitorSistema:
    """Obtiene instancia global del monitor."""
    global _monitor_instancia
    if _monitor_instancia is None:
        _monitor_instancia = MonitorSistema()
    return _monitor_instancia


__all__ = [
    "MonitorSistema",
    "obtener_monitor"
]
