"""Resultado de procesar un proveedor (lo que después va al reporte)."""
from dataclasses import dataclass, field

OK = "OK"
ADVERTENCIA = "ADVERTENCIA"
ERROR = "ERROR"
BLOQUEADO = "BLOQUEADO"   # la validación frenó la actualización por seguridad
OMITIDO = "OMITIDO"       # no le tocaba hoy


@dataclass
class ResultadoProveedor:
    id: str
    nombre: str
    estado: str = OK
    etapa: str = ""              # última etapa alcanzada / etapa donde falló
    mensaje: str = ""
    archivo: str = ""
    productos: int = 0
    cambios_precio: int = 0
    cambios_stock: int = 0
    nuevos: int = 0
    discontinuados: int = 0
    alertas: list = field(default_factory=list)
    captura: str = ""
    segundos: float = 0.0
