"""Impide que corran dos robots al mismo tiempo.

Se bloquea un archivo con el mecanismo del sistema operativo. Si el robot se
cuelga o se corta la luz, Windows libera el bloqueo solo: nunca queda un
"candado huérfano" que haya que borrar a mano.
"""
import os
from datetime import datetime


class YaHayOtroRobotCorriendo(Exception):
    pass


class Bloqueo:
    def __init__(self, ruta):
        self.ruta = ruta
        self._archivo = None

    def __enter__(self):
        self._archivo = open(self.ruta, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                self._archivo.seek(0)
                msvcrt.locking(self._archivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._archivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._archivo.close()
            raise YaHayOtroRobotCorriendo(
                f"Ya hay un robot ejecutándose (bloqueo: {self.ruta}). Se cancela esta ejecución."
            )
        # Dejamos anotado quién tiene el bloqueo, para diagnóstico.
        self._archivo.seek(0)
        self._archivo.truncate()
        self._archivo.write(f"PID {os.getpid()} desde {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        self._archivo.flush()
        return self

    def __exit__(self, *exc):
        try:
            if os.name == "nt":
                import msvcrt
                self._archivo.seek(0)
                msvcrt.locking(self._archivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._archivo.fileno(), fcntl.LOCK_UN)
        finally:
            self._archivo.close()
        return False
