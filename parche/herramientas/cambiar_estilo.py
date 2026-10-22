#!/usr/bin/env python3
"""cambiar_estilo.py - cambia el estilo del cuadro de texto de un data3.dat YA ARMADO, sin CSV.

Uso:  python cambiar_estilo.py "C:\\ruta\\del\\juego" ESTILO [--alto 150] [--ancho-actual N]
      ESTILO = BARRA (la de siempre) | ABAJO (panel original acostado abajo) | ORIGINAL (panel original de pie)

Qué hace:
 1. Lee el exec.dat original de TU data1.dat (comprueba la edición) y tu data3.dat actual.
 2. Saca el español que ya tiene tu data3, quita los saltos de línea automáticos y vuelve a cortar
    los renglones al ancho del estilo nuevo. Respeta los saltos puestos a mano:
      - si el mensaje coincide con la traducción publicada (datos/traduccion_es.tsv), usa esa versión;
      - si lo editaste, solo quita los saltos que están justo donde caería un corte automático
        y te deja la lista en cambiar_estilo_REVISAR.txt.
 3. Cambia la ventana (data/screen/messageframe) y guarda el data3.dat nuevo.
    El anterior queda como data3_antes_estilo.dat.
No toca data1.dat, data2.dat ni malie_es.exe.
"""
import sys, os, re, csv, hashlib, shutil, tempfile
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace'); sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kkk_exec_tool as kt
from kkk_extraer import Dat
from kkk_build import wrap_lines, vis
from armar import EXEC_MD5, leer_libp, escribir_libp, leer_traduccion
import estilos

def arg(n, d):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d

def sin_saltos(t):
    """Texto sin saltos ni espacios, para comparar (el armador puede cortar entre letras jindai sin espacio)."""
    return re.sub(r'\s+', '', t.replace('{n}', ''))

PEGADO = re.compile(r'(\{u0006\}(\{[^}]*\}|.)|[\u3000-\u30ff\u4e00-\u9fff\uff00-\uffef、。「」『』――…])$')
def unir(izq, der):
    """Une dos trozos al quitar un salto automático: sin espacio si el corte fue entre letras jindai o japonesas."""
    izq = izq.rstrip(); der = der.lstrip()
    if PEGADO.search(izq) or der.startswith('{u0006}') or re.match(r'[\u3000-\u30ff\u4e00-\u9fff\uff00-\uffef、。」』]', der):
        return izq + der
    return izq + ' ' + der

def sin_letras(t):
    """True si el mensaje no tiene letras latinas (solo jindai, japonés o signos): se deja tal cual."""
    return not re.search(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', re.sub(r'\{[^}]*\}', '', re.sub(r'\{u0006\}(\{[^}]*\}|.)', '', t)))

def quitar_automaticos(t, ancho):
    """Quita los {n} que puso el armador: los que están donde la palabra siguiente ya no cabía."""
    partes = t.split('{n}')
    if len(partes) == 1: return t, False
    res = partes[0]; dudoso = False
    linea = res.split('{u000A}')[-1]
    for p in partes[1:]:
        primera = re.match(r'\s*(\S+)', p)
        L = vis(linea.rstrip()); W = vis(primera.group(1)) if primera else 0
        if primera and L + 1 + W > ancho and L <= ancho:
            res = unir(res, p)                              # automático: se quita
            linea = unir(linea, p).split('{u000A}')[-1]
        else:
            res += '{n}' + p; linea = p.split('{u000A}')[-1]
            if primera and L > ancho * 0.85: dudoso = True     # parece automático pero no encaja del todo
    return res, dudoso

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2 or args[1].upper() not in estilos.ESTILOS: print(__doc__); sys.exit(1)
    juego = os.path.abspath(args[0]); nombre = args[1].upper()
    alto = int(arg('--alto', estilos.ALTO_ABAJO))
    nuevo = estilos.ESTILOS[nombre](alto)
    d1 = os.path.join(juego, 'data1.dat'); d3 = os.path.join(juego, 'data3.dat')
    for f in (d1, d3):
        if not os.path.exists(f): raise SystemExit('ERROR: no encontré ' + f)

    print('== 1/4 Leyendo tu data1.dat y tu data3.dat (tarda unos minutos)')
    dat = Dat(d1); i = dat.find('data/system/exec.dat'); n, fl, a, size = dat.ents[i]
    orig = dat.read(dat.base + dat.offs[a] * 1024, size)
    if hashlib.md5(orig).hexdigest() != EXEC_MD5:
        raise SystemExit('ERROR: tu juego es de otra edición (no es el DVD 2017 de la caja Dies irae & WORLD BOX).')
    tree = leer_libp(d3)
    try:
        mf = tree['data']['screen']['messageframe']; actual = tree['data']['system']['exec.dat']
    except KeyError:
        raise SystemExit('ERROR: ese data3.dat no trae el parche en español (falta messageframe o exec.dat).')
    ancho_actual = int(arg('--ancho-actual', 0)) or estilos.detectar_ancho(mf.get('normal_c.svg', b''))
    if not ancho_actual:
        raise SystemExit('ERROR: no reconozco el estilo actual. Usa --ancho-actual N (92 = barra de siempre).')
    print('   estilo actual: %d letras por renglón -> %s: %d letras, %d renglones' %
          (ancho_actual, nombre, nuevo['ancho'], nuevo['renglones']))

    print('== 2/4 Sacando el español y re-cortando los renglones')
    tmp = tempfile.mkdtemp(prefix='kkk_estilo_')
    fo = os.path.join(tmp, 'orig.dat'); open(fo, 'wb').write(orig)
    fa = os.path.join(tmp, 'actual.dat'); open(fa, 'wb').write(actual)
    co = os.path.join(tmp, 'orig.csv'); ca = os.path.join(tmp, 'actual.csv')
    kt.extract(fo, co); kt.extract(fa, ca)
    rows = list(csv.DictReader(open(co, encoding='utf-8-sig')))
    cur = {r['id']: r['japanese'] for r in csv.DictReader(open(ca, encoding='utf-8-sig'))}
    tsv = os.path.join(RAIZ, 'datos', 'traduccion_es.tsv')
    pub = leer_traduccion(tsv) if os.path.exists(tsv) else {}
    revisar = []; largos = []; de_pub = 0
    for r in rows:
        t = cur.get(r['id'], '')
        if not t or t == r['japanese']:                     # sin traducir: se queda igual
            r['status'] = 'untranslated'; continue
        if not pub.get(r['id'], '').strip() and (sin_saltos(t) == sin_saltos(r['japanese']) or sin_letras(t)):
            r['spanish'] = t; r['status'] = 'draft'; continue   # copia del japonés (jindai, citas): se deja tal cual
        p = pub.get(r['id'], '').strip()
        if p and sin_saltos(p) == sin_saltos(t):
            base = p; de_pub += 1
        else:
            base, dudoso = quitar_automaticos(t, ancho_actual)
            if dudoso: revisar.append(r['id'])
        r['spanish'], nl = wrap_lines(base.strip(), nuevo['ancho']); r['status'] = 'draft'
        if nl > nuevo['renglones']: largos.append((r['id'], nl))
    cw = os.path.join(tmp, 'nuevo.csv')
    with open(cw, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    fn = os.path.join(tmp, 'nuevo.dat'); kt.insert(fo, cw, fn, 0)
    ne = bytearray(open(fn, 'rb').read()); ne[:kt.TABLE] = actual[:kt.TABLE]   # conserva nombres, «？？？», horizontal
    print('   %d mensajes iguales a la traducción publicada; %d editados por ti' %
          (de_pub, sum(1 for r in rows if r['status'] == 'draft') - de_pub))

    print('== 3/4 Cambiando la ventana')
    tree['data']['system']['exec.dat'] = bytes(ne)
    for k, v in nuevo['svgs'].items(): mf[k] = v

    print('== 4/4 Guardando')
    resp = os.path.join(juego, 'data3_antes_estilo.dat')
    shutil.copy(d3, resp); print('   respaldo: ' + resp)
    escribir_libp(tree, d3)
    shutil.rmtree(tmp, ignore_errors=True)
    rep = os.path.join(juego, 'cambiar_estilo_REVISAR.txt')
    with open(rep, 'w', encoding='utf-8') as f:
        f.write('Estilo nuevo: %s (%d letras x %d renglones)\n\n' % (nombre, nuevo['ancho'], nuevo['renglones']))
        f.write('Mensajes que pasan de %d renglones (se verán cortados o con barra):\n' % nuevo['renglones'])
        for i, n in largos: f.write('  %s -> %d renglones\n' % (i, n))
        f.write('\nMensajes editados por ti donde no estoy seguro de qué salto era tuyo (revísalos en el juego):\n')
        for i in revisar: f.write('  %s\n' % i)
    print('\nLISTO. Estilo %s aplicado. Abre el juego con malie_es.exe.' % nombre)
    if largos: print('AVISO: %d mensajes pasan de %d renglones (ver %s).' % (len(largos), nuevo['renglones'], rep))
    if revisar: print('AVISO: %d mensajes editados para revisar (ver %s).' % (len(revisar), rep))
    print('Para deshacer: borra data3.dat y cambia el nombre de data3_antes_estilo.dat a data3.dat.')

if __name__ == '__main__': main()
