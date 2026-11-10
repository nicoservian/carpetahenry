"""Carpetas del robot. Todo es relativo a donde está agent.py,
así el proyecto funciona en C:\\ROBOT_PROVEEDORES o en cualquier otra carpeta."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CONFIG = BASE / "config"
PROVEEDORES = BASE / "proveedores"
DESCARGAS = BASE / "descargas"
PROCESADOS = BASE / "procesados"
HISTORICO = BASE / "historico"
LOGS = BASE / "logs"
CAPTURAS = LOGS / "capturas"
REPORTES = BASE / "reportes"
BACKUPS = BASE / "backups"
SESIONES = BASE / "sesiones"          # cookies guardadas de cada sitio
ARCHIVO_BLOQUEO = BASE / "robot.lock"

CARPETAS_DE_DATOS = [DESCARGAS, PROCESADOS, HISTORICO, LOGS, CAPTURAS, REPORTES, BACKUPS, SESIONES]


def crear_carpetas():
    for carpeta in CARPETAS_DE_DATOS:
        carpeta.mkdir(parents=True, exist_ok=True)
