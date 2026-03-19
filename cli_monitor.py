#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================
# CLI - Herramienta de línea de comandos para Logging
# ============================================================
# Uso: python cli_monitor.py [comando] [opciones]
# Ejemplos:
#   python cli_monitor.py dashboard
#   python cli_monitor.py errores --dias 7 --csv
#   python cli_monitor.py prompts --mejorados
#   python cli_monitor.py rendimiento --modulo conector_odoo
# ============================================================

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Asegurar imports
BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.monitor_sistema import obtener_monitor
from utils.logging_avanzado import obtener_logger
from services.llm.ollama_integrador import obtener_ollama

from app.logging_config import get_logger
logger = get_logger("cli_monitor")


class CLIMANDROMEDA:
    """Interfaz de línea de comandos para ANDROMEDA."""
    
    def __init__(self) -> None:
        self.monitor = obtener_monitor()
        self.logger = obtener_logger()
        self.ollama = obtener_ollama()
    
    def cmd_dashboard(self, args: argparse.Namespace) -> None:
        """Muestra el dashboard del sistema."""
        print("\n🔄 Cargando dashboard...\n")
        self.monitor.mostrar_dashboard()
    
    def cmd_errores(self, args: argparse.Namespace) -> None:
        """Muestra errores recientes."""
        print("\n⚠️  ERRORES RECIENTES\n")
        
        errores = self.monitor.errores_por_modulo(dias=args.dias)
        
        if not errores:
            print("✅ No hay errores abiertos")
            return
        
        total_errores = sum(len(e) for e in errores.values())
        print(f"Total: {total_errores} errores abiertos\n")
        
        for modulo, lista_errores in errores.items():
            print(f"📌 {modulo}")
            for i, error in enumerate(lista_errores[:args.limite], 1):
                print(f"   {i}. {error['tipo']} (x{error['frecuencia']}) [{error['criticidad']}]")
                if args.verbose:
                    print(f"      📝 {error['mensaje'][:70]}...")
                    print(f"      💡 {error['solucion'][:70]}...")
            print()
        
        if args.csv:
            csv_path = self.monitor.exportar_errores_csv(dias=args.dias)
            print(f"📊 Exportado a: {csv_path}\n")
    
    def cmd_prompts(self, args: argparse.Namespace) -> None:
        """Muestra análisis de prompts."""
        print("\n💭 ANÁLISIS DE PROMPTS\n")
        
        if args.mejorados:
            self.monitor.mostrar_prompts_mejorados(limite=args.limite)
        else:
            # Estadísticas generales
            resumen = self.monitor.resumen_general()
            
            print(f"Total procesados: {resumen.get('prompts_totales', 0)}")
            print(f"Confianza promedio: {resumen.get('confianza_promedio', 0):.1%}\n")
            
            # Tendencias
            tendencias = self.monitor.tendencias(dias=args.dias)
            if tendencias['prompts']:
                print("Últimos días:")
                for dia in tendencias['prompts'][-7:]:
                    barra = "█" * int(dia['cantidad'] / 5)
                    print(f"  {dia['fecha']}: {barra} {dia['cantidad']} "
                          f"(confianza: {dia['confianza']:.1%})")
    
    def cmd_rendimiento(self, args: argparse.Namespace) -> None:
        """Muestra análisis de rendimiento."""
        print("\n⚡ ANÁLISIS DE RENDIMIENTO\n")
        
        rendimiento = self.monitor.rendimiento_por_operacion(dias=args.dias)
        
        if not rendimiento:
            print("Sin datos de rendimiento")
            return
        
        if args.modulo:
            if args.modulo not in rendimiento:
                print(f"❌ Módulo '{args.modulo}' no encontrado")
                return
            
            ops = rendimiento[args.modulo]
            print(f"Módulo: {args.modulo}\n")
            
            for op in ops:
                print(f"  📍 {op['operacion']}")
                print(f"     Operaciones: {op['total']}")
                print(f"     Promedio: {op['promedio_ms']:.1f}ms")
                print(f"     Rango: {op['minimo_ms']}-{op['maximo_ms']}ms")
                print(f"     Éxito: {op['tasa_exito']:.0f}%\n")
        else:
            # Mostrar resumen de todos
            for modulo, ops in rendimiento.items():
                print(f"📌 {modulo}")
                for op in ops[:3]:  # Top 3
                    print(f"   {op['operacion']}: {op['promedio_ms']:.1f}ms "
                          f"({op['tasa_exito']:.0f}% éxito)")
                print()
    
    def cmd_tendencias(self, args: argparse.Namespace) -> None:
        """Muestra tendencias en el tiempo."""
        print("\n📈 TENDENCIAS\n")
        
        tendencias = self.monitor.tendencias(dias=args.dias)
        
        print("ERRORES:")
        if tendencias['errores']:
            for dia in tendencias['errores'][-7:]:
                barra = "█" * int(dia['cantidad'])
                print(f"  {dia['fecha']}: {barra} {dia['cantidad']}")
        else:
            print("  Sin datos")
        
        print("\nPROMPTS:")
        if tendencias['prompts']:
            for dia in tendencias['prompts'][-7:]:
                barra = "█" * int(dia['cantidad'] / 5)
                print(f"  {dia['fecha']}: {barra} {dia['cantidad']} "
                      f"(confianza: {dia['confianza']:.1%})")
        else:
            print("  Sin datos")
        
        print()
    
    def cmd_usuarios(self, args: argparse.Namespace) -> None:
        """Muestra usuarios más activos."""
        print("\n👥 USUARIOS MÁS ACTIVOS\n")
        
        usuarios = self.monitor.usuarios_activos(dias=args.dias)
        
        if not usuarios:
            print("Sin datos de usuarios")
            return
        
        for i, u in enumerate(usuarios[:args.limite], 1):
            print(f"{i}. {u['usuario']}")
            print(f"   Interacciones: {u['interacciones']}")
            print(f"   Errores: {u['errores']}")
            print(f"   Prompts: {u['prompts']}")
            print()
    
    def cmd_reporte(self, args: argparse.Namespace) -> None:
        """Genera reporte completo."""
        print("\n📄 Generando reporte...\n")
        
        ruta = self.monitor.generar_reporte(output_path=args.salida)
        
        if ruta:
            print(f"✅ Reporte generado: {ruta}")
            
            if args.abrir:
                import webbrowser
                print("Abriendo archivo...")
                webbrowser.open(ruta)
        else:
            logger.error("❌ Error generando reporte")
    
    def cmd_ollama(self, args: argparse.Namespace) -> None:
        """Comandos de Ollama."""
        if not self.ollama.conectado:
            print("\n❌ Ollama no está conectado")
            print("\nPara conectar Ollama:")
            print("1. Descarga desde https://ollama.ai")
            print("2. Ejecuta: ollama serve")
            print("3. Abre otra terminal y ejecuta: ollama pull mistral")
            return
        
        print(f"\n✅ Ollama conectado en {self.ollama.host}")
        print(f"📦 Modelo: {self.ollama.modelo_activo}\n")
        
        if args.subcommand == "modelos":
            print("Modelos disponibles:")
            modelos = self.ollama.obtener_modelos()
            for m in modelos:
                print(f"  • {m}")
        
        elif args.subcommand == "analizar":
            if not args.prompt:
                print("❌ Usa: ollama analizar --prompt 'tu pregunta'")
                return
            
            print(f"Analizando: {args.prompt}\n")
            resultado = self.ollama.analizar_intencion(args.prompt)
            
            print(f"Intención: {resultado.get('intencion')}")
            print(f"Confianza: {resultado.get('confianza', 0):.1%}")
            print(f"Palabras clave: {resultado.get('palabras_clave', [])}")
            print(f"⏱️  Tiempo: {resultado.get('tiempo_ms', 0)}ms")
        
        elif args.subcommand == "mejorar":
            if not args.prompt:
                print("❌ Usa: ollama mejorar --prompt 'tu pregunta'")
                return
            
            print(f"Mejorando: {args.prompt}\n")
            resultado = self.ollama.mejorar_prompt(args.prompt)
            
            print(f"Original: {resultado['original']}")
            print(f"Mejorado: {resultado['mejorado']}")
            
            if resultado.get('alternativas'):
                print("\nAlternativas:")
                for alt in resultado['alternativas']:
                    print(f"  • {alt}")
        
        elif args.subcommand == "descargar":
            if not args.modelo:
                print("❌ Usa: ollama descargar --modelo mistral")
                return
            
            self.ollama.descargar_modelo(args.modelo)
    
    def cmd_info(self, args: argparse.Namespace) -> None:
        """Información del sistema."""
        print("\n📊 INFORMACIÓN DEL SISTEMA\n")
        
        resumen = self.monitor.resumen_general()
        
        print("Estadísticas Generales:")
        for clave, valor in resumen.items():
            if clave != 'timestamp':
                print(f"  {clave}: {valor}")
        
        print(f"\nGenerado: {resumen.get('timestamp')}")
        print(f"Base de datos: logs/eventos.db")
        print(f"Logs: logs/andromeda.log")
        print(f"Ollama: {'✅ Conectado' if self.ollama.conectado else '❌ Desconectado'}")


def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="ANDROMEDA - Sistema de Logging y Monitoreo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s dashboard                    Mostrar dashboard
  %(prog)s errores --dias 7 --csv      Ver errores y exportar
  %(prog)s prompts --mejorados         Prompts con baja confianza
  %(prog)s rendimiento --modulo conector_odoo
  %(prog)s tendencias --dias 30
  %(prog)s usuarios 
  %(prog)s reporte
  %(prog)s ollama modelos
  %(prog)s ollama analizar --prompt "¿ventas de hoy?"
  %(prog)s ollama mejorar --prompt "dame datos"
  %(prog)s info

Ver: https://github.com/axelgutierrez/andromeda/wiki/logging
        """
    )
    
    subparsers = parser.add_subparsers(dest='comando', help='Comando a ejecutar')
    
    # Dashboard
    subparsers.add_parser('dashboard', help='Mostrar dashboard del sistema')
    
    # Errores
    p_errores = subparsers.add_parser('errores', help='Ver errores')
    p_errores.add_argument('--dias', type=int, default=7, help='Últimos N días')
    p_errores.add_argument('--limite', type=int, default=5, help='Límite de errores por módulo')
    p_errores.add_argument('--csv', action='store_true', help='Exportar a CSV')
    p_errores.add_argument('--verbose', action='store_true', help='Información detallada')
    
    # Prompts
    p_prompts = subparsers.add_parser('prompts', help='Ver análisis de prompts')
    p_prompts.add_argument('--mejorados', action='store_true', 
                          help='Mostrar prompts con baja confianza')
    p_prompts.add_argument('--dias', type=int, default=7, help='Últimos N días')
    p_prompts.add_argument('--limite', type=int, default=10, help='Límite de prompts')
    
    # Rendimiento
    p_rend = subparsers.add_parser('rendimiento', help='Análisis de rendimiento')
    p_rend.add_argument('--modulo', help='Filtrar por módulo')
    p_rend.add_argument('--dias', type=int, default=7, help='Últimos N días')
    
    # Tendencias
    p_tend = subparsers.add_parser('tendencias', help='Ver tendencias')
    p_tend.add_argument('--dias', type=int, default=30, help='Últimos N días')
    
    # Usuarios
    p_usuarios = subparsers.add_parser('usuarios', help='Usuarios más activos')
    p_usuarios.add_argument('--dias', type=int, default=7, help='Últimos N días')
    p_usuarios.add_argument('--limite', type=int, default=10, help='Límite de usuarios')
    
    # Reporte
    p_report = subparsers.add_parser('reporte', help='Generar reporte')
    p_report.add_argument('--salida', default='logs/reporte_sistema.txt', 
                         help='Ruta del archivo de salida')
    p_report.add_argument('--abrir', action='store_true', help='Abrir archivo al terminar')
    
    # Ollama
    p_ollama = subparsers.add_parser('ollama', help='Comandos de Ollama')
    p_ollama_sub = p_ollama.add_subparsers(dest='subcommand', 
                                          help='Subcomando Ollama')
    
    p_ollama_sub.add_parser('modelos', help='Listar modelos disponibles')
    
    p_analizar = p_ollama_sub.add_parser('analizar', help='Analizar prompt')
    p_analizar.add_argument('--prompt', help='Prompt a analizar')
    
    p_mejorar = p_ollama_sub.add_parser('mejorar', help='Mejorar prompt')
    p_mejorar.add_argument('--prompt', help='Prompt a mejorar')
    
    p_descargar = p_ollama_sub.add_parser('descargar', help='Descargar modelo')
    p_descargar.add_argument('--modelo', help='Nombre del modelo')
    
    # Info
    subparsers.add_parser('info', help='Información del sistema')
    
    # Parsear argumentos
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    # Ejecutar comando
    cli = CLIMANDROMEDA()
    
    try:
        if args.comando == 'dashboard':
            cli.cmd_dashboard(args)
        elif args.comando == 'errores':
            cli.cmd_errores(args)
        elif args.comando == 'prompts':
            cli.cmd_prompts(args)
        elif args.comando == 'rendimiento':
            cli.cmd_rendimiento(args)
        elif args.comando == 'tendencias':
            cli.cmd_tendencias(args)
        elif args.comando == 'usuarios':
            cli.cmd_usuarios(args)
        elif args.comando == 'reporte':
            cli.cmd_reporte(args)
        elif args.comando == 'ollama':
            cli.cmd_ollama(args)
        elif args.comando == 'info':
            cli.cmd_info(args)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
