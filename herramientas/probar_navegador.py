#!/usr/bin/env python3
"""Prueba que Python + Playwright puedan abrir Chrome.

Uso:
    python herramientas/probar_navegador.py

Debería abrirse una ventana de Chrome, entrar a una página de prueba,
guardar logs/capturas/prueba_navegador.png y cerrarse sola.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import expect, sync_playwright  # noqa: E402

from core import rutas  # noqa: E402
from core.config import cargar_settings  # noqa: E402


def main():
    nav = cargar_settings().get("navegador", {})
    canal = nav.get("canal", "chrome")
    rutas.crear_carpetas()
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(channel=None if canal == "chromium" else canal,
                                          headless=bool(nav.get("headless", False)), slow_mo=500)
        except Exception as e:
            print(f"No pude abrir '{canal}': {e}\nProbando con el Chromium de Playwright...")
            navegador = p.chromium.launch(headless=bool(nav.get("headless", False)), slow_mo=500)
        pagina = navegador.new_page()
        pagina.goto("https://example.com")
        # Espera inteligente: no un sleep, sino "esperá hasta que aparezca este título".
        expect(pagina.get_by_role("heading", name="Example Domain")).to_be_visible()
        destino = rutas.CAPTURAS / "prueba_navegador.png"
        pagina.screenshot(path=str(destino))
        navegador.close()
    print(f"OK: el navegador funciona. Captura guardada en {destino}")


if __name__ == "__main__":
    main()
