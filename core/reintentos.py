"""Reintentos con espera creciente.

Hay dos tipos de error:
  ErrorTemporal   → vale la pena reintentar (timeout, sitio caído, descarga
                    incompleta, sesión expirada, error de conexión).
  ErrorDefinitivo → NO se reintenta (contraseña incorrecta, columnas
                    faltantes, archivo corrupto). Reintentar una contraseña
                    incorrecta puede bloquear la cuenta en el proveedor.
Cualquier otro error inesperado se trata como temporal.
"""
import time


class ErrorTemporal(Exception):
    pass


class ErrorDefinitivo(Exception):
    pass


def ejecutar_con_reintentos(funcion, intentos, espera_segundos, log, descripcion="tarea"):
    espera = espera_segundos
    for intento in range(1, intentos + 1):
        try:
            if intento > 1:
                log.info(f"{descripcion}: intento {intento} de {intentos}")
            return funcion()
        except ErrorDefinitivo:
            raise
        except Exception as e:
            if intento == intentos:
                log.error(f"{descripcion}: falló el intento {intento} de {intentos} ({e}). Sin más reintentos.")
                raise
            log.warning(f"{descripcion}: falló el intento {intento} de {intentos} ({e}). "
                        f"Reintento en {espera} s.")
            time.sleep(espera)
            espera *= 2
