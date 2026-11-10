#!/usr/bin/env python3
"""Guarda usuario y contraseña en el Administrador de credenciales de Windows.

Uso:
    python herramientas/guardar_credencial.py DIMAC
    python herramientas/guardar_credencial.py COMERCIOCITY

La contraseña no se ve mientras la escribís (es normal).
Para verla/borrarla: Panel de control → Administrador de credenciales →
Credenciales de Windows → buscar "ROBOT_PROVEEDORES".
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.credenciales import guardar_credencial, obtener_credencial  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python herramientas/guardar_credencial.py NOMBRE   (ej. DIMAC)")
    nombre = sys.argv[1].upper()
    usuario = input(f"Usuario para {nombre}: ").strip()
    clave = getpass.getpass(f"Contraseña para {nombre} (no se ve al escribir): ")
    if not usuario or not clave:
        sys.exit("Usuario y contraseña no pueden quedar vacíos.")
    guardar_credencial(nombre, usuario, clave)
    u, _ = obtener_credencial(nombre)
    print(f"Credencial {nombre} guardada. Usuario leído de vuelta: {u}")


if __name__ == "__main__":
    main()
