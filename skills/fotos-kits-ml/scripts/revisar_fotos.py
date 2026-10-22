#!/usr/bin/env python3
"""Revisa fotos de publicaciones de ML y avisa lo que no cumple.

Controla lo que se puede medir: formato, peso, tamaño, que sea cuadrada y, en
la portada, fondo blanco puro y cuánto ocupa el producto. No lee textos: los
textos, logos y datos de contacto se revisan mirando la imagen.

Uso:
    python revisar_fotos.py --portada portada.jpg info1.jpg info2.jpg
    python revisar_fotos.py --deformacion 3024x4032:600x800 1200x1200:900x700
"""
import argparse
import os
import sys

from PIL import Image

MAX_MB = 10
MIN_LADO = 500
LADO_RECOMENDADO = 1200
TOLERANCIA_DEFORMACION = 0.02   # 2%: menos que eso no se nota a la vista
BLANCO = 250                    # un píxel cuenta como blanco desde 250 en R, G y B


def revisar_foto(ruta, es_portada):
    """Devuelve (no_cumple, mejorar): listas de textos."""
    no_cumple, mejorar = [], []
    ext = os.path.splitext(ruta)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        no_cumple.append(f"formato {ext or 'desconocido'}: tiene que ser JPG o PNG")
    mb = os.path.getsize(ruta) / 1024 / 1024
    if mb > MAX_MB:
        no_cumple.append(f"pesa {mb:.1f} MB: el máximo es {MAX_MB} MB")

    img = Image.open(ruta).convert("RGB")
    w, h = img.size
    if min(w, h) < MIN_LADO:
        no_cumple.append(f"mide {w}x{h}: el mínimo es {MIN_LADO} px por lado")
    elif min(w, h) < LADO_RECOMENDADO:
        mejorar.append(f"mide {w}x{h}: conviene {LADO_RECOMENDADO}x{LADO_RECOMENDADO} para que ML deje hacer zoom")
    if abs(w - h) / max(w, h) > 0.02:
        mejorar.append(f"no es cuadrada ({w}x{h}): ML la muestra con franjas a los costados")

    if es_portada:
        no_cumple += revisar_fondo(img)
        no_cumple_ocupa, mejorar_ocupa = revisar_ocupacion(img)
        no_cumple += no_cumple_ocupa
        mejorar += mejorar_ocupa
    return no_cumple, mejorar


def es_blanco(px):
    return all(c >= BLANCO for c in px)


def revisar_fondo(img):
    """El borde de la portada tiene que ser blanco puro."""
    w, h = img.size
    px = img.load()
    borde = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
    borde += [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    no_blancos = sum(1 for p in borde if not es_blanco(px[p]))
    if no_blancos / len(borde) > 0.01:
        return [f"el fondo no es blanco puro ({no_blancos / len(borde):.0%} del borde tiene color) "
                "o el producto toca el borde"]
    return []


def revisar_ocupacion(img):
    """Cuánto del ancho o alto ocupa el producto (lo que no es blanco)."""
    gris = img.convert("L").point(lambda v: 0 if v >= BLANCO else 255)
    caja = gris.getbbox()
    if not caja:
        return ["la portada está toda en blanco: no se ve el producto"], []
    w, h = img.size
    ocupa = max((caja[2] - caja[0]) / w, (caja[3] - caja[1]) / h)
    if ocupa < 0.6:
        return [], [f"el producto ocupa solo {ocupa:.0%}: conviene agrandarlo (ideal entre 60% y 95%)"]
    if ocupa > 0.97:
        return [], [f"el producto ocupa {ocupa:.0%}: dejar un poco de margen blanco alrededor"]
    return [], []


def revisar_deformacion(par):
    """par = 'ANCHOxALTO:ANCHOxALTO' (original : en el diseño)."""
    original, colocada = par.split(":")
    ow, oh = (float(v) for v in original.lower().split("x"))
    cw, ch = (float(v) for v in colocada.lower().split("x"))
    diferencia = (cw / ch) / (ow / oh) - 1
    if abs(diferencia) <= TOLERANCIA_DEFORMACION:
        return None
    sentido = "estirada a lo ancho (o aplastada de alto)" if diferencia > 0 else "estirada a lo alto (o aplastada de ancho)"
    return f"{par}: {sentido} un {abs(diferencia):.0%}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fotos", nargs="*", help="fotos secundarias")
    ap.add_argument("--portada", help="foto de portada (se revisa fondo blanco y tamaño del producto)")
    ap.add_argument("--deformacion", nargs="+", default=[], metavar="ORIG:DISEÑO",
                    help="tamaño original y tamaño en el diseño de cada foto, ej. 3024x4032:600x800")
    args = ap.parse_args()

    problemas = 0
    fotos = ([(args.portada, True)] if args.portada else []) + [(f, False) for f in args.fotos]
    for ruta, es_portada in fotos:
        no_cumple, mejorar = revisar_foto(ruta, es_portada)
        nombre = f"{ruta} (portada)" if es_portada else ruta
        if not no_cumple and not mejorar:
            print(f"OK {nombre}")
        for t in no_cumple:
            print(f"NO CUMPLE ML {nombre}: {t}")
        for t in mejorar:
            print(f"MEJORAR {nombre}: {t}")
        problemas += len(no_cumple)

    for par in args.deformacion:
        aviso = revisar_deformacion(par)
        if aviso:
            print(f"DEFORMADA {aviso}")
            problemas += 1
        else:
            print(f"OK sin deformar {par}")

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
