"""Credenciales de proveedores y de ComercioCity, SIN escribirlas en el código.

Orden de búsqueda para la credencial "DIMAC":
  1. Administrador de credenciales de Windows (librería keyring),
     servicio "ROBOT_PROVEEDORES/DIMAC". Se guarda con:
         python herramientas/guardar_credencial.py DIMAC
  2. Variables de entorno / archivo .env:  DIMAC_USUARIO y DIMAC_CLAVE
"""
import os

from dotenv import load_dotenv

from core import rutas
from core.reintentos import ErrorDefinitivo

SERVICIO = "ROBOT_PROVEEDORES"

load_dotenv(rutas.BASE / ".env")


def _keyring():
    try:
        import keyring
        return keyring
    except ImportError:
        return None


def obtener_credencial(nombre):
    """Devuelve (usuario, clave). Lanza ErrorDefinitivo si no está configurada."""
    nombre = nombre.upper()
    kr = _keyring()
    if kr is not None:
        try:
            usuario = kr.get_password(f"{SERVICIO}/{nombre}", "usuario")
            clave = kr.get_password(f"{SERVICIO}/{nombre}", "clave")
            if usuario and clave:
                return usuario, clave
        except Exception:
            pass  # sin almacén de claves disponible: seguimos con .env

    usuario = os.environ.get(f"{nombre}_USUARIO")
    clave = os.environ.get(f"{nombre}_CLAVE")
    if usuario and clave:
        return usuario, clave

    raise ErrorDefinitivo(
        f"No encontré la credencial '{nombre}'. Guardala con "
        f"'python herramientas/guardar_credencial.py {nombre}' "
        f"o completá {nombre}_USUARIO y {nombre}_CLAVE en el archivo .env"
    )


def guardar_credencial(nombre, usuario, clave):
    kr = _keyring()
    if kr is None:
        raise RuntimeError("Falta la librería keyring: pip install keyring")
    nombre = nombre.upper()
    kr.set_password(f"{SERVICIO}/{nombre}", "usuario", usuario)
    kr.set_password(f"{SERVICIO}/{nombre}", "clave", clave)
