"""Verifica que haya Internet antes de empezar."""
import socket
import time

SITIOS = [("www.google.com", 443), ("1.1.1.1", 443)]


def hay_internet(intentos=3, espera=10):
    for intento in range(1, intentos + 1):
        for host, puerto in SITIOS:
            try:
                with socket.create_connection((host, puerto), timeout=5):
                    return True
            except OSError:
                continue
        if intento < intentos:
            time.sleep(espera)
    return False
