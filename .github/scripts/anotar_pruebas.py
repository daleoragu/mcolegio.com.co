"""Lee la salida de `manage.py test` y publica cada prueba que falló como aviso de GitHub
(con el final de su traceback), para verlo sin abrir los registros."""
import re
import sys

texto = open(sys.argv[1], encoding='utf-8', errors='replace').read()
bloques = re.split(r'\n=+\n', texto)
n = 0
for b in bloques:
    m = re.match(r'(FAIL|ERROR): (\S+) \(([^)]+)\)', b.strip())
    if not m:
        continue
    cuerpo = b.split('\n-' * 1)[0]
    lineas = [x for x in b.strip().splitlines() if x.strip() and not set(x.strip()) <= {'-'}]
    final = lineas[-8:]
    msg = f'{m.group(1)} {m.group(3)}.{m.group(2)}: ' + ' | '.join(x.strip() for x in final)
    print('::error::' + msg[:1800].replace('%', '%25'))
    n += 1
    if n >= 30:
        break
resumen = [x for x in texto.splitlines() if x.startswith(('Ran ', 'FAILED', 'OK'))]
print('::notice::' + ' · '.join(resumen[-3:]))
