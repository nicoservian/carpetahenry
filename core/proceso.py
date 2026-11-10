"""Procesa UN proveedor, etapa por etapa.

DESCARGA → LECTURA → NORMALIZACIÓN → VALIDACIÓN → COMPARACIÓN → PREPARACIÓN

Etapa 1 del proyecto: solo existe la descarga "simulada" para probar el
circuito completo. Las demás etapas se completan en las próximas entregas.
"""
import time

from core.logs import log_de
from core.reintentos import ErrorDefinitivo, ErrorTemporal, ejecutar_con_reintentos
from core.resultados import ERROR, OK, ResultadoProveedor


def _descarga_simulada(proveedor, log):
    modo = proveedor.datos["descarga"].get("simular", "ok")
    if modo == "error_temporal":
        raise ErrorTemporal("timeout simulado al abrir el sitio del proveedor")
    if modo == "error_definitivo":
        raise ErrorDefinitivo("contraseña incorrecta (simulado)")
    log.info("Descarga simulada correcta")
    return None


def descargar(proveedor, settings, log):
    metodo = proveedor.datos["descarga"]["metodo"]
    if metodo == "simulada":
        return _descarga_simulada(proveedor, log)
    # "receta" y "modulo" llegan en la Etapa 2.
    raise ErrorDefinitivo(f"El método de descarga '{metodo}' todavía no está implementado (Etapa 2).")


def procesar_proveedor(proveedor, settings):
    log = log_de(proveedor.id)
    res = ResultadoProveedor(id=proveedor.id, nombre=proveedor.nombre)
    inicio = time.monotonic()
    reint = settings.get("reintentos", {})
    log.info(f"===== Inicio proveedor: {proveedor.nombre} =====")
    try:
        res.etapa = "descarga"
        ejecutar_con_reintentos(
            lambda: descargar(proveedor, settings, log),
            intentos=int(reint.get("intentos", 3)),
            espera_segundos=int(reint.get("espera_segundos", 30)),
            log=log,
            descripcion="Descarga",
        )
        for etapa in ("lectura", "normalizacion", "validacion", "comparacion", "preparacion"):
            res.etapa = etapa
            log.info(f"Etapa {etapa}: pendiente de construir")
        res.estado = OK
        res.etapa = "fin"
        log.info("Proveedor OK")
    except Exception as e:
        res.estado = ERROR
        res.mensaje = f"{type(e).__name__}: {e}"
        log.error(f"ERROR en etapa '{res.etapa}': {res.mensaje}")
    finally:
        res.segundos = time.monotonic() - inicio
    return res
