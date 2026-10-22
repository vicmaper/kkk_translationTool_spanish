#!/usr/bin/env python3
"""extraer.py - saca de TU juego un CSV para traducir o corregir: id, voice, japanese, spanish, status.
Uso: python extraer.py "C:\\ruta\\de\\tu\\juego" [salida.csv]
- japanese: el texto original, leído de TU data1.dat (no viene en el paquete).
- spanish: la traducción actual del paquete (datos/traduccion_es.tsv); vacía si no hay.
Edita solo la columna spanish y luego usa INTEGRAR.bat. Este CSV lleva el guion original: es solo para ti,
no lo compartas (comparte solo tu traducción: el revisor te genera un _CORREGIDO).
"""
import sys, os, csv, hashlib, tempfile, shutil
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace'); sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kkk_exec_tool as kt
from kkk_extraer import Dat
from armar import EXEC_MD5, leer_traduccion

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    juego = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(RAIZ, 'mi_traduccion.csv')
    dat = Dat(os.path.join(juego, 'data1.dat')); i = dat.find('data/system/exec.dat')
    n, fl, a, size = dat.ents[i]; orig = dat.read(dat.base + dat.offs[a] * 1024, size)
    if hashlib.md5(orig).hexdigest() != EXEC_MD5: raise SystemExit('ERROR: tu juego es de otra edición.')
    tmp = tempfile.mkdtemp(prefix='kkk_'); f = os.path.join(tmp, 'exec.dat'); open(f, 'wb').write(orig)
    c = os.path.join(tmp, 'guion.csv'); kt.extract(f, c)
    rows = list(csv.DictReader(open(c, encoding='utf-8-sig')))
    shutil.copy(c, os.path.join(HERE, 'kkk_script_BUENO.csv'))          # para el revisor
    es = leer_traduccion(os.path.join(RAIZ, 'datos', 'traduccion_es.tsv'))
    for r in rows:
        t = es.get(r['id'], '')
        r['spanish'] = t; r['status'] = 'draft' if t else 'untranslated'
    with open(out, 'w', encoding='utf-8-sig', newline='') as g:
        w = csv.DictWriter(g, fieldnames=['id', 'voice', 'japanese', 'spanish', 'status']); w.writeheader(); w.writerows(rows)
    shutil.rmtree(tmp, ignore_errors=True)
    print('LISTO: ' + out)
    print('%d mensajes (%d con traducción). Edita la columna spanish (Excel/LibreOffice: guardar como CSV UTF-8).' % (
        len(rows), sum(1 for r in rows if r['spanish'])))

if __name__ == '__main__': main()
