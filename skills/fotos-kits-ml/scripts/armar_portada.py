#!/usr/bin/env python3
"""Arma la portada de un kit: todas las piezas juntas sobre fondo blanco puro.

Cada pieza se escala de forma proporcional (mismo factor en ancho y alto), así
que ninguna puede quedar estirada ni aplastada. Las piezas deben venir sin
fondo (PNG con transparencia, por ejemplo después de remove-background de Canva);
si una pieza no tiene transparencia se usa igual y se avisa.

Uso:
    python armar_portada.py --salida portada.jpg bidon.png filtro_aceite.png filtro_aire.png
"""
import argparse
import math
import sys

from PIL import Image

LADO = 1200
MARGEN = 0.06       # margen blanco alrededor del kit, para no tocar los bordes
SEPARACION = 0.03   # espacio entre piezas


def recortar_a_contenido(img):
    """Saca el espacio transparente alrededor de la pieza."""
    if img.mode != "RGBA":
        return img.convert("RGBA"), False
    caja = img.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
    return (img.crop(caja) if caja else img), True


def distribuir(n):
    """Filas y columnas para n piezas, lo más parejo posible."""
    cols = math.ceil(math.sqrt(n))
    filas = math.ceil(n / cols)
    return filas, cols


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("piezas", nargs="+", help="fotos de cada pieza, en orden (la primera es la principal)")
    ap.add_argument("--salida", default="portada.jpg")
    args = ap.parse_args()

    piezas = []
    for ruta in args.piezas:
        img, con_transparencia = recortar_a_contenido(Image.open(ruta))
        if not con_transparencia:
            print(f"AVISO {ruta}: no tiene el fondo sacado; el fondo va a quedar en la portada.")
        piezas.append((ruta, img))

    filas, cols = distribuir(len(piezas))
    util = LADO * (1 - 2 * MARGEN)
    sep = LADO * SEPARACION
    celda_w = (util - sep * (cols - 1)) / cols
    celda_h = (util - sep * (filas - 1)) / filas

    lienzo = Image.new("RGB", (LADO, LADO), (255, 255, 255))
    alto_total = filas * celda_h + (filas - 1) * sep
    y0 = (LADO - alto_total) / 2
    print("Pieza | tamaño original | tamaño en portada | escala")
    for i, (ruta, img) in enumerate(piezas):
        fila, col = divmod(i, cols)
        en_fila = min(cols, len(piezas) - fila * cols)
        ancho_fila = en_fila * celda_w + (en_fila - 1) * sep
        x0 = (LADO - ancho_fila) / 2
        # Un único factor para ancho y alto: la proporción no cambia.
        escala = min(celda_w / img.width, celda_h / img.height)
        w, h = max(1, round(img.width * escala)), max(1, round(img.height * escala))
        chica = img.resize((w, h), Image.LANCZOS)
        x = round(x0 + col * (celda_w + sep) + (celda_w - w) / 2)
        y = round(y0 + fila * (celda_h + sep) + (celda_h - h) / 2)
        lienzo.paste(chica, (x, y), chica if chica.mode == "RGBA" else None)
        print(f"{ruta} | {img.width}x{img.height} | {w}x{h} | {escala:.2f}")
        if max(w, h) < LADO * 0.15:
            print(f"AVISO {ruta}: quedó muy chica en la portada ({w}x{h}); conviene una foto aparte o otra distribución.")

    lienzo.save(args.salida, "JPEG", quality=92)
    print(f"Portada guardada en {args.salida} ({LADO}x{LADO}).")


if __name__ == "__main__":
    sys.exit(main())
