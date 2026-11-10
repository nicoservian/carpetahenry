"""Carga config/settings.yaml y el config.yaml de cada proveedor."""
import copy
from dataclasses import dataclass, field
from datetime import date

import yaml

from core import rutas

DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]


class ErrorDeConfiguracion(Exception):
    pass


def _leer_yaml(ruta):
    try:
        with open(ruta, encoding="utf-8") as fh:
            datos = yaml.safe_load(fh) or {}
    except yaml.YAMLError as e:
        raise ErrorDeConfiguracion(f"{ruta}: el archivo tiene un error de formato YAML: {e}")
    if not isinstance(datos, dict):
        raise ErrorDeConfiguracion(f"{ruta}: se esperaba una lista de 'clave: valor'")
    return datos


def _combinar(base, encima):
    """Combina diccionarios: lo de 'encima' pisa lo de 'base'."""
    resultado = copy.deepcopy(base)
    for k, v in (encima or {}).items():
        if isinstance(v, dict) and isinstance(resultado.get(k), dict):
            resultado[k] = _combinar(resultado[k], v)
        else:
            resultado[k] = v
    return resultado


def cargar_settings():
    ruta = rutas.CONFIG / "settings.yaml"
    if not ruta.exists():
        raise ErrorDeConfiguracion(f"No existe {ruta}")
    return _leer_yaml(ruta)


@dataclass
class Proveedor:
    id: str                 # nombre de la carpeta
    nombre: str
    habilitado: bool
    prioridad: int
    dias: list
    datos: dict             # el config.yaml completo
    validaciones: dict      # límites ya combinados con los generales
    carpeta: object = field(repr=False, default=None)

    def toca_hoy(self, hoy=None):
        if not self.dias:
            return True
        hoy = hoy or date.today()
        return DIAS[hoy.weekday()] in [d.lower()[:3] for d in self.dias]


def cargar_proveedores(settings):
    """Devuelve (proveedores_ok, errores). Un config roto NO frena a los demás."""
    proveedores, errores = [], []
    for carpeta in sorted(rutas.PROVEEDORES.iterdir()):
        if not carpeta.is_dir() or carpeta.name.startswith(("_", ".")):
            continue
        ruta = carpeta / "config.yaml"
        if not ruta.exists():
            errores.append((carpeta.name, "falta config.yaml"))
            continue
        try:
            datos = _leer_yaml(ruta)
            if "nombre" not in datos:
                raise ErrorDeConfiguracion("falta el campo 'nombre'")
            if not isinstance(datos.get("descarga"), dict) or "metodo" not in datos["descarga"]:
                raise ErrorDeConfiguracion("falta la sección 'descarga' con su 'metodo'")
            proveedores.append(Proveedor(
                id=carpeta.name,
                nombre=str(datos["nombre"]),
                habilitado=bool(datos.get("habilitado", False)),
                prioridad=int(datos.get("prioridad", 50)),
                dias=datos.get("dias") or [],
                datos=datos,
                validaciones=_combinar(settings.get("validaciones", {}), datos.get("validaciones")),
                carpeta=carpeta,
            ))
        except Exception as e:
            errores.append((carpeta.name, str(e)))
    proveedores.sort(key=lambda p: (p.prioridad, p.id))
    return proveedores, errores
