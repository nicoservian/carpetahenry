"""Logs: todo lo que hace el robot queda en logs/AAAA-MM-DD.log y en pantalla.

Formato:  10:01:15 | INFO    | dimac        | Login correcto
"""
import logging
import sys
from datetime import date

from core import rutas

FORMATO = "%(asctime)s | %(levelname)-7s | %(proveedor)-12s | %(message)s"


class _ProveedorPorDefecto(logging.Filter):
    """Si el mensaje no viene de un proveedor, muestra 'AGENTE'."""

    def filter(self, record):
        if not hasattr(record, "proveedor"):
            record.proveedor = "AGENTE"
        return True


def configurar_logs(nivel=logging.INFO):
    # En Windows la consola puede no aceptar acentos o "→": que nunca falle por eso.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    rutas.LOGS.mkdir(parents=True, exist_ok=True)
    archivo = rutas.LOGS / f"{date.today().isoformat()}.log"

    logger = logging.getLogger("robot")
    logger.setLevel(nivel)
    logger.handlers.clear()

    formato = logging.Formatter(FORMATO, datefmt="%H:%M:%S")
    # Si el robot corre dos veces el mismo día, se AGREGA al log (no se pisa).
    a_archivo = logging.FileHandler(archivo, mode="a", encoding="utf-8")
    a_pantalla = logging.StreamHandler(sys.stdout)
    for h in (a_archivo, a_pantalla):
        h.setFormatter(formato)
        h.addFilter(_ProveedorPorDefecto())
        logger.addHandler(h)
    return logger, archivo


def log_de(proveedor_id):
    """Logger que antepone el nombre del proveedor a cada línea."""
    return logging.LoggerAdapter(logging.getLogger("robot"), {"proveedor": proveedor_id[:12]})
