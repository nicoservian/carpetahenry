#!/usr/bin/env python3
"""Inicia sesión en dimac.com.ar y busca productos (ej. pastillas de freno).

Credenciales por variables de entorno (nunca en el código):
    DIMAC_USUARIO   CUIT sin guiones
    DIMAC_CLAVE     contraseña

Uso:
    python dimac/dimac_buscar.py "pastilla"
    python dimac/dimac_buscar.py "pastilla" "gol trend" --max-paginas 5
    python dimac/dimac_buscar.py "pastilla" --salida salida/pastillas.xlsx

Guarda los resultados en Excel/CSV y el HTML crudo de cada página en
salida/html/ para revisar si el formato del sitio cambia.
"""
import argparse
import csv
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.dimac.com.ar"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def login(sesion, usuario, clave):
    sesion.get(BASE + "/", timeout=30)
    r = sesion.post(
        BASE + "/User/LoginBox",
        data={"Username": usuario, "Password": clave},
        headers={"Referer": BASE + "/"},
        timeout=30,
    )
    r.raise_for_status()
    # Si el login falla, el sitio devuelve otra vez el formulario de ingreso.
    if 'name="Password"' in r.text:
        sys.exit("Login fallido: revisá DIMAC_USUARIO (CUIT sin guiones) y DIMAC_CLAVE.")


def buscar_pagina(sesion, termino, pagina, por_pagina):
    params = {
        "page": pagina,
        "id": 0,
        "recsPerPage": por_pagina,
        "order": "Code",
        "sort": "False",
        "itemtype": "Product",
        "term": termino,
        "getFilterData": "True",
    }
    r = sesion.get(BASE + "/search", params=params, timeout=60)
    if r.status_code == 500 and "CurrentUser" in r.text:
        sys.exit("El sitio no reconoce la sesión (búsqueda requiere login).")
    r.raise_for_status()
    return r.text


def limpiar(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def parsear(html):
    """Extrae productos de la página de resultados.

    Prueba primero con tablas y después con "tarjetas" de producto.
    """
    soup = BeautifulSoup(html, "html.parser")
    filas = []

    for tabla in soup.select("#body table, table"):
        encabezados = [limpiar(th.get_text()) for th in tabla.select("thead th")]
        for tr in tabla.select("tbody tr") or tabla.select("tr")[1:]:
            celdas = [limpiar(td.get_text(" ")) for td in tr.find_all("td")]
            if len(celdas) < 2 or not any(celdas):
                continue
            if encabezados and len(encabezados) == len(celdas):
                filas.append(dict(zip(encabezados, celdas)))
            else:
                filas.append({f"col{i + 1}": c for i, c in enumerate(celdas)})
        if filas:
            return filas

    tarjetas = soup.select(
        "[class*=product-item], [class*=producto], .product, .item-product, [class*=prod-]"
    )
    for t in tarjetas:
        def campo(*selectores):
            for s in selectores:
                el = t.select_one(s)
                if el:
                    return limpiar(el.get_text(" "))
            return ""

        enlace = t.select_one("a[href]")
        img = t.select_one("img[src]")
        filas.append({
            "codigo": campo("[class*=code]", "[class*=codigo]", "[class*=sku]"),
            "descripcion": campo("[class*=name]", "[class*=title]", "[class*=desc]", "h3", "h4"),
            "marca": campo("[class*=brand]", "[class*=marca]"),
            "precio": campo("[class*=price]", "[class*=precio]"),
            "stock": campo("[class*=stock]"),
            "url": BASE + enlace["href"] if enlace and enlace["href"].startswith("/") else (enlace["href"] if enlace else ""),
            "imagen": img["src"] if img else "",
            "texto": limpiar(t.get_text(" ")),
        })
    return filas


def guardar(filas, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    columnas = []
    for f in filas:
        for k in f:
            if k not in columnas:
                columnas.append(k)
    if destino.suffix.lower() == ".xlsx":
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Dimac"
        ws.append(columnas)
        for f in filas:
            ws.append([f.get(c, "") for c in columnas])
        wb.save(destino)
    else:
        with open(destino, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=columnas, delimiter=";")
            w.writeheader()
            w.writerows(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("terminos", nargs="+", help="texto a buscar (se suman con espacios)")
    ap.add_argument("--max-paginas", type=int, default=20)
    ap.add_argument("--por-pagina", type=int, default=50)
    ap.add_argument("--salida", default="salida/dimac_resultados.xlsx")
    args = ap.parse_args()

    usuario = os.environ.get("DIMAC_USUARIO")
    clave = os.environ.get("DIMAC_CLAVE")
    if not usuario or not clave:
        sys.exit("Faltan las variables de entorno DIMAC_USUARIO y DIMAC_CLAVE.")

    termino = " ".join(args.terminos)
    sesion = requests.Session()
    sesion.headers["User-Agent"] = UA
    login(sesion, usuario, clave)
    print("Login OK")

    dir_html = Path("salida/html")
    dir_html.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"\W+", "_", termino).strip("_") or "busqueda"

    todas, vistos = [], set()
    for pagina in range(1, args.max_paginas + 1):
        html = buscar_pagina(sesion, termino, pagina, args.por_pagina)
        (dir_html / f"{slug}_p{pagina}.html").write_text(html, encoding="utf-8")
        filas = parsear(html)
        nuevas = [f for f in filas if repr(sorted(f.items())) not in vistos]
        if not nuevas:
            break
        vistos.update(repr(sorted(f.items())) for f in nuevas)
        todas.extend(nuevas)
        print(f"Página {pagina}: {len(nuevas)} productos")
        if len(filas) < args.por_pagina:
            break

    if not todas:
        print(f"No se encontraron productos para '{termino}'. Revisá el HTML en {dir_html}/.")
        return
    destino = Path(args.salida)
    guardar(todas, destino)
    print(f"{len(todas)} productos guardados en {destino}")


if __name__ == "__main__":
    main()
