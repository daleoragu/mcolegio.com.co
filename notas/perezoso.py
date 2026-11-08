"""Librerías pesadas que se cargan solo cuando se usan (no al arrancar la aplicación).

WeasyPrint (PDF), matplotlib y numpy (gráficas) suman unos 100 MB por proceso. Antes se cargaban al arrancar
cada proceso de gunicorn aunque casi nunca se usen, y en un servidor pequeño eso llenaba la memoria y
DigitalOcean reiniciaba la aplicación (estado «Degraded»). Ahora se cargan la primera vez que se piden.
"""
import importlib
import importlib.util

PDF_SUPPORT = importlib.util.find_spec('weasyprint') is not None


class _DeWeasyPrint:
    """Se comporta como weasyprint.HTML / weasyprint.CSS, pero importa la librería al usarla."""

    def __init__(self, nombre):
        self._nombre = nombre

    def __call__(self, *args, **kwargs):
        return getattr(importlib.import_module('weasyprint'), self._nombre)(*args, **kwargs)


class Modulo:
    """Un módulo que se importa la primera vez que se usa uno de sus atributos (np.zeros, plt.subplots…)."""

    def __init__(self, nombre, preparar=None):
        self._nombre, self._preparar, self._mod = nombre, preparar, None

    def __getattr__(self, atributo):
        if self._mod is None:
            if self._preparar:
                self._preparar()
            self._mod = importlib.import_module(self._nombre)
        return getattr(self._mod, atributo)


def _matplotlib_sin_pantalla():
    import matplotlib
    matplotlib.use('Agg')       # backend para servidores (sin pantalla)


HTML = _DeWeasyPrint('HTML') if PDF_SUPPORT else None
CSS = _DeWeasyPrint('CSS') if PDF_SUPPORT else None
matplotlib = Modulo('matplotlib', _matplotlib_sin_pantalla)
plt = Modulo('matplotlib.pyplot', _matplotlib_sin_pantalla)
np = Modulo('numpy')
