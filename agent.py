#!/usr/bin/env python3
"""AGENTE PRINCIPAL del Robot de Proveedores.

Uso:
    python agent.py                       # todos los proveedores habilitados
    python agent.py --proveedor dimac     # solo uno (para probar)
    python agent.py --forzar              # ignora los días configurados

Ver ARQUITECTURA.md para el diseño completo.
"""
import argparse
import sys
import time
from datetime import datetime

from core import rutas
from core.bloqueo import Bloqueo, YaHayOtroRobotCorriendo
from core.config import ErrorDeConfiguracion, cargar_proveedores, cargar_settings
from core.logs import configurar_logs
from core.proceso import procesar_proveedor
from core.red import hay_internet
from core.resultados import ERROR, OK, ResultadoProveedor


def duracion_texto(segundos):
    m, s = divmod(int(round(segundos)), 60)
    h, m = divmod(m, 60)
    return f"{h} h {m} min {s} s" if h else f"{m} min {s} s"


def resumen(log, resultados, errores_config, inicio, fin):
    ok = [r for r in resultados if r.estado == OK]
    con_error = [r for r in resultados if r.estado != OK]
    log.info("=" * 60)
    log.info("RESUMEN DE LA EJECUCIÓN")
    log.info(f"Inicio:    {inicio:%H:%M:%S}")
    log.info(f"Final:     {fin:%H:%M:%S}")
    log.info(f"Duración:  {duracion_texto((fin - inicio).total_seconds())}")
    log.info(f"PROVEEDORES PROCESADOS: {len(resultados)}")
    log.info(f"CORRECTOS: {len(ok)}")
    log.info(f"CON ERROR: {len(con_error)}")
    for r in con_error:
        log.info(f"  - {r.nombre} [{r.estado}] etapa '{r.etapa}': {r.mensaje}")
    for carpeta, motivo in errores_config:
        log.info(f"  - CONFIG INVÁLIDA en proveedores/{carpeta}: {motivo}")
    log.info("=" * 60)


def main():
    ap = argparse.ArgumentParser(description="Robot de actualización de proveedores")
    ap.add_argument("--proveedor", help="procesar solo este proveedor (nombre de su carpeta)")
    ap.add_argument("--forzar", action="store_true", help="ignorar los días configurados")
    args = ap.parse_args()

    rutas.crear_carpetas()
    log, archivo_log = configurar_logs()
    inicio = datetime.now()
    log.info(f"Inicio del agente ({inicio:%Y-%m-%d %H:%M:%S}) — log: {archivo_log}")

    try:
        with Bloqueo(rutas.ARCHIVO_BLOQUEO):
            settings = cargar_settings()
            general = settings.get("general", {})
            if general.get("modo_simulacion", True):
                log.info("MODO SIMULACIÓN activo: ComercioCity NO se va a modificar")

            if general.get("verificar_internet", True):
                if not hay_internet():
                    log.error("No hay conexión a Internet. Se cancela la ejecución.")
                    return 2
                log.info("Conexión a Internet OK")

            proveedores, errores_config = cargar_proveedores(settings)
            for carpeta, motivo in errores_config:
                log.error(f"Config inválida en proveedores/{carpeta}: {motivo}")

            if args.proveedor:
                proveedores = [p for p in proveedores if p.id == args.proveedor]
                if not proveedores:
                    log.error(f"No existe el proveedor '{args.proveedor}' en la carpeta proveedores/")
                    return 2
            else:
                proveedores = [p for p in proveedores if p.habilitado]
            if not args.forzar:
                for p in [p for p in proveedores if not p.toca_hoy()]:
                    log.info(f"{p.nombre}: hoy no le toca (días: {p.dias})")
                proveedores = [p for p in proveedores if p.toca_hoy()]

            log.info(f"Proveedores a procesar: {len(proveedores)} → {', '.join(p.id for p in proveedores)}")

            # FASE A: cada proveedor aislado. Si uno falla, se sigue con el próximo.
            resultados = []
            for p in proveedores:
                try:
                    resultados.append(procesar_proveedor(p, settings))
                except Exception as e:  # red de seguridad: nunca cortar el recorrido
                    log.exception(f"Error inesperado con {p.id}")
                    resultados.append(ResultadoProveedor(id=p.id, nombre=p.nombre, estado=ERROR,
                                                         etapa="desconocida", mensaje=str(e)))

            # FASE B: ComercioCity (Etapa 3). FASE C: reporte (Etapa 2).
            log.info("Actualización ComercioCity: pendiente de construir (Etapa 3)")

            resumen(log, resultados, errores_config, inicio, datetime.now())
            return 0 if all(r.estado == OK for r in resultados) and not errores_config else 1

    except YaHayOtroRobotCorriendo as e:
        log.error(str(e))
        return 3
    except ErrorDeConfiguracion as e:
        log.error(f"Error de configuración: {e}")
        return 2
    except Exception:
        log.exception("Error grave del agente")
        return 4
    finally:
        log.info(f"Fin del agente ({datetime.now():%H:%M:%S})")


if __name__ == "__main__":
    sys.exit(main())
