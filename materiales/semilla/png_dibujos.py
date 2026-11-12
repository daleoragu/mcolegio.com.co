"""Herramienta de desarrollo (no corre en el servidor): convierte a PNG los dibujos «d-…» que usan las guías semilla.

    python materiales/semilla/png_dibujos.py          # genera los que falten en materiales/semilla/img/
    python materiales/semilla/png_dibujos.py --todos  # los vuelve a generar todos

Necesita Node con Playwright (Chromium). Los PNG se guardan en el repositorio; el servidor solo los lee.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

NODE = r"""
const {chromium} = require('playwright');
const fs = require('fs');
(async () => {
  const trabajos = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const b = await chromium.launch();
  const p = await b.newPage({deviceScaleFactor: 2});
  for (const [ruta, svg] of trabajos) {
    await p.setContent('<html><body style="margin:0;background:#fff">' + svg + '</body></html>');
    await p.locator('svg').screenshot({path: ruta, omitBackground: false});
  }
  await b.close();
})();
"""


def ids_usados():
    import django
    django.setup()
    from materiales.semilla import armar
    ids = set()
    for (area, grado) in armar.MODULOS:
        for d in armar.documentos(grado, area):
            ids |= {b['img'] for b in d['bloques'] if b['tipo'] == '_imagen' and b['img'].startswith('d-')}
    return sorted(ids)


def main():
    from materiales.semilla import dibujos as D
    carpeta = RAIZ / 'materiales' / 'semilla' / 'img'
    carpeta.mkdir(exist_ok=True)
    todos = '--todos' in sys.argv
    trabajos = [[str(carpeta / f'{i}.png'), D.generar(i)] for i in ids_usados() if todos or not (carpeta / f'{i}.png').exists()]
    if not trabajos:
        print('Nada que generar.')
        return
    with tempfile.TemporaryDirectory() as tmp:
        js, datos = Path(tmp) / 'png.js', Path(tmp) / 'trabajos.json'
        js.write_text(NODE)
        datos.write_text(json.dumps(trabajos))
        subprocess.run(['node', str(js), str(datos)], check=True, cwd=tmp)
    print(f'{len(trabajos)} dibujos en PNG.')


if __name__ == '__main__':
    main()
