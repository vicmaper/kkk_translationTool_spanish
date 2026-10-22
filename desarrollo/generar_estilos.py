#!/usr/bin/env python3
"""generar_estilos.py - crea, a partir de TU data3.dat, una versión por cada estilo de cuadro de texto.

Uso:  python generar_estilos.py "data3 base" "carpeta de salida" [--alto 150] [--juego carpeta_con_data1]
      (usa herramientas\\exec.dat; --juego solo hace falta si ese archivo no está)
Salida: data3_BARRA.dat, data3_ABAJO.dat y data3_ORIGINAL.dat en la carpeta de salida.
Para usar uno: cópialo a la carpeta del juego con el nombre data3.dat.
El texto es el de tu data3 base (tus correcciones se conservan); solo cambian la ventana y dónde se cortan los renglones.
"""
import sys, os, csv, hashlib, tempfile, shutil
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace'); sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kkk_exec_tool as kt
from kkk_extraer import Dat
from kkk_build import wrap_lines
from armar import EXEC_MD5, leer_libp, escribir_libp, leer_traduccion
import estilos, cambiar_estilo as ce

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2: print(__doc__); sys.exit(1)
    base, salida = (os.path.abspath(a) for a in args[:2])
    juego = ce.arg('--juego', '')
    if not os.path.exists(base): raise SystemExit('ERROR: no encontré ' + base)
    alto = int(ce.arg('--alto', estilos.ALTO_ABAJO))
    os.makedirs(salida, exist_ok=True)

    local = os.path.join(HERE, 'exec.dat')            # copia del guion original junto a las herramientas (solo para ti)
    orig = open(local, 'rb').read() if os.path.exists(local) else b''
    if hashlib.md5(orig).hexdigest() != EXEC_MD5:
        if not juego or not os.path.exists(os.path.join(juego, 'data1.dat')):
            raise SystemExit('ERROR: falta herramientas\\exec.dat (el guion original). Vuelve a copiarlo desde tu respaldo.')
        print('== Sacando el guion original de tu data1.dat')
        dat = Dat(os.path.join(juego, 'data1.dat')); i = dat.find('data/system/exec.dat'); n, fl, a, size = dat.ents[i]
        orig = dat.read(dat.base + dat.offs[a] * 1024, size)
        if hashlib.md5(orig).hexdigest() != EXEC_MD5: raise SystemExit('ERROR: tu juego es de otra edición.')
        open(local, 'wb').write(orig); print('   guardado en ' + local)
    else:
        print('== Usando el guion original guardado en herramientas\\exec.dat')
    print('== Leyendo tu data3 base: ' + base + ' (tarda unos minutos)')
    tree = leer_libp(base)
    mf = tree['data']['screen']['messageframe']; actual = tree['data']['system']['exec.dat']
    ancho_actual = int(ce.arg('--ancho-actual', 0)) or estilos.detectar_ancho(mf.get('normal_c.svg', b''))
    if not ancho_actual: raise SystemExit('ERROR: no reconozco el estilo del data3 base. Usa --ancho-actual N.')
    print('   el data3 base tiene %d letras por renglón' % ancho_actual)

    tmp = tempfile.mkdtemp(prefix='kkk_estilos_')
    fo = os.path.join(tmp, 'orig.dat'); open(fo, 'wb').write(orig)
    fa = os.path.join(tmp, 'actual.dat'); open(fa, 'wb').write(actual)
    co = os.path.join(tmp, 'orig.csv'); ca = os.path.join(tmp, 'actual.csv')
    kt.extract(fo, co); kt.extract(fa, ca)
    rows = list(csv.DictReader(open(co, encoding='utf-8-sig')))
    cur = {r['id']: r['japanese'] for r in csv.DictReader(open(ca, encoding='utf-8-sig'))}
    tsv = os.path.join(RAIZ, 'datos', 'traduccion_es.tsv')
    pub = leer_traduccion(tsv) if os.path.exists(tsv) else {}
    texto = {}; fijo = {}; revisar = []
    for r in rows:                                   # texto sin saltos automáticos, una sola vez
        t = cur.get(r['id'], '')
        if not t or t == r['japanese']: continue                    # sin traducir
        if not pub.get(r['id'], '').strip() and (ce.sin_saltos(t) == ce.sin_saltos(r['japanese']) or ce.sin_letras(t)):
            fijo[r['id']] = t; continue                                  # copia del japonés (jindai, citas): se deja tal cual
        p = pub.get(r['id'], '').strip()
        if p and ce.sin_saltos(p) == ce.sin_saltos(t): texto[r['id']] = p
        else:
            texto[r['id']], dudoso = ce.quitar_automaticos(t, ancho_actual)
            if dudoso: revisar.append(r['id'])

    informe = ['Data3 base: %s (%d letras por renglón)' % (base, ancho_actual), '']
    for nombre in ('BARRA', 'ABAJO', 'ORIGINAL'):
        e = estilos.ESTILOS[nombre](alto); largos = []
        print('== %s: %d letras x %d renglones' % (nombre, e['ancho'], e['renglones']))
        for r in rows:
            if r['id'] in fijo:
                r['spanish'] = fijo[r['id']]; r['status'] = 'draft'
            elif r['id'] in texto:
                r['spanish'], nl = wrap_lines(texto[r['id']].strip(), e['ancho']); r['status'] = 'draft'
                if nl > e['renglones']: largos.append('%s (%d renglones)' % (r['id'], nl))
            else:
                r['spanish'] = ''; r['status'] = 'untranslated'
        cw = os.path.join(tmp, 'w.csv')
        with open(cw, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        fn = os.path.join(tmp, 'n.dat'); kt.insert(fo, cw, fn, 0)
        ne = bytearray(open(fn, 'rb').read()); ne[:kt.TABLE] = actual[:kt.TABLE]
        tree['data']['system']['exec.dat'] = bytes(ne)
        for k, v in e['svgs'].items(): mf[k] = v
        out = os.path.join(salida, 'data3_%s.dat' % nombre)
        escribir_libp(tree, out); print('   OK: ' + out)
        informe.append('%s: %d letras x %d renglones. Mensajes que no caben: %s' %
                       (nombre, e['ancho'], e['renglones'], ', '.join(largos) or 'ninguno'))
    if revisar:
        informe += ['', 'Mensajes editados por ti donde un salto de línea podría haber cambiado: ' + ', '.join(revisar)]
    open(os.path.join(salida, 'INFORME_ESTILOS.txt'), 'w', encoding='utf-8').write('\n'.join(informe) + '\n')
    shutil.rmtree(tmp, ignore_errors=True)
    print('\nLISTO. Para usar un estilo: copia data3_ESTILO.dat a la carpeta del juego y ponle de nombre data3.dat.')

if __name__ == '__main__': main()
