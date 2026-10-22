#!/usr/bin/env python3
"""armar.py - arma la traducción al español de Kajiri Kamui Kagura (神咒神威神楽) a partir de TU copia del juego.

Uso:  python armar.py "C:\\ruta\\de\\tu\\juego"            (la carpeta que tiene data1.dat y malie.exe)
      python armar.py "C:\\ruta\\de\\tu\\juego" --tsv mi_traduccion.tsv   (usa otra traducción, .tsv o .csv)
      python armar.py "C:\\ruta\\de\\tu\\juego" --estilo ABAJO        (cuadro de texto: BARRA, ABAJO u ORIGINAL)

Qué hace (no toca data1.dat ni malie.exe):
 1. Lee de TU data1.dat el guion original (data/system/exec.dat) y comprueba que sea la edición correcta.
 2. Le aplica los ajustes del parche (texto horizontal, cuadro de nombres, «？？？»).
 3. Mete la traducción (datos/traduccion_es.tsv: id TAB spanish) con los saltos de línea automáticos.
 4. Junta eso con la interfaz en español (datos/interfaz_es.dat) y escribe data3.dat en la carpeta del juego
    (si ya había un data3.dat, lo guarda como data3_antes_del_parche.dat).
 5. Crea malie_es.exe (menús de Windows y avisos en español) a partir de TU malie.exe.
 6. Deja en herramientas/ un guion local (kkk_script_BUENO.csv, con el japonés de TU copia) para que
    kkk_revisar.py pueda revisar traducciones. Ese archivo es solo para ti: no lo compartas.
"""
import sys, os, re, csv, json, struct, hashlib, shutil, tempfile
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace'); sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(HERE)
DATOS = os.path.join(RAIZ, 'datos')
sys.path.insert(0, HERE)
import malie_cipher as mc
import kkk_exec_tool as kt
from kkk_extraer import Dat
from kkk_build import wrap_lines
import estilos

EXEC_MD5 = '3543cae9d9d96dae9ff121238e5509fc'      # exec.dat de la edición DVD 2017 (Dies irae & WORLD BOX)
EXE_MD5 = '4b5ab27844120e1f99f9d53dd50c5858'       # malie.exe 1.1 de esa misma edición
TABLE = kt.TABLE
WIDTH, LINES = 92, 6

def leer_traduccion(path):
    """Acepta el .tsv del paquete (id TAB spanish) o un .csv con columnas id y spanish."""
    es = {}
    if path.lower().endswith('.csv'):
        for r in csv.DictReader(open(path, encoding='utf-8-sig', newline='')):
            if r.get('id'): es[r['id'].strip()] = (r.get('spanish') or '')
        return es
    for line in open(path, encoding='utf-8-sig'):
        line = line.rstrip('\r\n')
        if not line.strip() or line.startswith('id\t'): continue
        k, _, v = line.partition('\t'); es[k.strip()] = v
    return es

def md5(b): return hashlib.md5(b).hexdigest()
def paso(t): print('\n== ' + t)

def aplicar(orig, parche):
    out = bytearray(orig)
    for off, hexa in parche['regiones']:
        b = bytes.fromhex(hexa); out[off:off + len(b)] = b
    if parche.get('cola'): out += bytes.fromhex(parche['cola'])
    if 'largo' in parche: del out[parche['largo']:]
    return bytes(out)

def leer_libp(path):
    dec = mc.crypt(open(path, 'rb').read(), mc.decrypt_block, 0)
    assert dec[:4] == b'LIBP', path + ' no es un archivo LIBP'
    cnt, fcnt = struct.unpack_from('<II', dec, 4)
    ents = []
    for i in range(cnt):
        o = 16 + 32 * i
        fl16, a, b = struct.unpack_from('<HII', dec, o + 22)
        ents.append((dec[o:o + 22].split(b'\0')[0].decode('ascii'), fl16 << 16, a, b))
    tbl = 16 + 32 * cnt
    offs = struct.unpack_from('<%dI' % fcnt, dec, tbl)
    base = (tbl + 4 * fcnt + 0xFFF) & ~0xFFF
    def node(i):
        n, fl, a, b = ents[i]
        if fl & 0x10000: o = base + offs[a] * 1024; return dec[o:o + b]
        return {ents[j][0]: node(j) for j in range(a, a + b)}
    return node(0)

def escribir_libp(tree, out):
    ents = [['', tree]]; q = [0]; files = []
    while q:
        i = q.pop(0); kids = ents[i][1]
        if isinstance(kids, dict):
            first = len(ents)
            for n in sorted(kids): ents.append([n, kids[n]])
            ents[i] += [first, len(kids)]; q += range(first, first + len(kids))
    hdr = bytearray(); body = bytearray(); offs = []
    for e in ents:
        name = e[0].encode('ascii'); assert len(name) <= 22
        if isinstance(e[1], dict): fl, a, b = 0, e[2], e[3]
        else: fl, a, b = 0x10000, len(files), len(e[1]); files.append(e[1])
        hdr += name.ljust(22, b'\0') + struct.pack('<HII', fl >> 16, a, b)
    for f in files:
        offs.append(len(body) // 1024); body += f; body += b'\0' * ((-len(body)) % 4096)
    head = b'LIBP' + struct.pack('<III', len(ents), len(files), 0) + hdr + struct.pack('<%dI' % len(offs), *offs)
    base = (len(head) + 0xFFF) & ~0xFFF
    raw = head + b'\0' * (base - len(head)) + body; raw += b'\0' * ((-len(raw)) % 4096)
    open(out, 'wb').write(mc.crypt(raw, mc.encrypt_block, 0))

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args: print(__doc__); sys.exit(1)
    juego = os.path.abspath(args[0])
    tsv = sys.argv[sys.argv.index('--tsv') + 1] if '--tsv' in sys.argv else (sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv else os.path.join(DATOS, 'traduccion_es.tsv'))
    nombre = (sys.argv[sys.argv.index('--estilo') + 1] if '--estilo' in sys.argv else 'BARRA').upper()
    if nombre not in estilos.ESTILOS: raise SystemExit('ERROR: estilo desconocido: %s (usa BARRA, ABAJO u ORIGINAL)' % nombre)
    alto = int(sys.argv[sys.argv.index('--alto') + 1]) if '--alto' in sys.argv else estilos.ALTO_ABAJO
    estilo = estilos.ESTILOS[nombre](alto); WIDTH, LINES = estilo['ancho'], estilo['renglones']
    print('Cuadro de texto: %s (%d letras x %d renglones)' % (nombre, WIDTH, LINES))
    d1 = os.path.join(juego, 'data1.dat')
    if not os.path.exists(d1): raise SystemExit('ERROR: no encontré data1.dat en ' + juego)

    paso('1/6 Leyendo el guion original de tu data1.dat')
    dat = Dat(d1); i = dat.find('data/system/exec.dat')
    if i is None: raise SystemExit('ERROR: tu data1.dat no tiene data/system/exec.dat')
    n, fl, a, size = dat.ents[i]
    orig = dat.read(dat.base + dat.offs[a] * 1024, size)
    if md5(orig) != EXEC_MD5:
        raise SystemExit('ERROR: tu juego es de otra edición (el guion no coincide). Este parche es para el DVD de '
                         'Kajiri Kamui Kagura incluido en «Dies irae & WORLD BOX» (2017), versión 1.1.')
    print('   edición correcta')

    paso('2/6 Aplicando los ajustes del parche al guion')
    parche = json.load(open(os.path.join(DATOS, 'exec_parche.json'), encoding='utf-8'))
    base = aplicar(orig[:TABLE], parche)
    assert len(base) == TABLE and md5(base) == parche['md5_resultado'], 'el parche del guion no se aplicó bien'

    paso('3/6 Metiendo la traducción: ' + os.path.basename(tsv))
    tmp = tempfile.mkdtemp(prefix='kkk_')
    f_orig = os.path.join(tmp, 'exec_orig.dat'); open(f_orig, 'wb').write(orig)
    f_csv = os.path.join(tmp, 'guion.csv'); kt.extract(f_orig, f_csv)
    guion = list(csv.DictReader(open(f_csv, encoding='utf-8-sig')))
    shutil.copy(f_csv, os.path.join(HERE, 'kkk_script_BUENO.csv'))     # para kkk_revisar (solo uso local)
    es = leer_traduccion(tsv)
    largos = []
    for r in guion:
        t = es.get(r['id'], '').strip()
        if t:
            t, nl = wrap_lines(t, WIDTH)
            if nl > LINES: largos.append(r['id'])
            r['spanish'] = t; r['status'] = 'draft'
    with open(f_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(guion[0].keys())); w.writeheader(); w.writerows(guion)
    f_new = os.path.join(tmp, 'exec_es.dat'); kt.insert(f_orig, f_csv, f_new, 0)
    ne = bytearray(open(f_new, 'rb').read()); ne[:TABLE] = base; ne = bytes(ne)
    print('   %d mensajes traducidos' % sum(1 for r in guion if r['status'] == 'draft'))
    if largos: print('   AVISO: %d mensajes pasan de %d renglones: %s' % (len(largos), LINES, ', '.join(largos[:20])))

    paso('4/6 Armando data3.dat (interfaz en español + guion)')
    tree = leer_libp(os.path.join(DATOS, 'interfaz_es.dat'))
    tree.setdefault('data', {}).setdefault('system', {})['exec.dat'] = ne
    mf = tree['data'].setdefault('screen', {}).setdefault('messageframe', {})
    for k, v in estilo['svgs'].items(): mf[k] = v
    d3 = os.path.join(juego, 'data3.dat')
    if os.path.exists(d3) and not os.path.exists(os.path.join(juego, 'data3_antes_del_parche.dat')):
        shutil.copy(d3, os.path.join(juego, 'data3_antes_del_parche.dat'))
        print('   tu data3.dat anterior quedó como data3_antes_del_parche.dat')
    escribir_libp(tree, d3)
    back = leer_libp(d3)['data']['system']['exec.dat']
    assert back == ne, 'la comprobación de data3.dat falló'
    print('   OK: ' + d3)

    paso('5/6 Creando malie_es.exe')
    exe = os.path.join(juego, 'malie.exe')
    if not os.path.exists(exe): print('   AVISO: no encontré malie.exe; me salto este paso')
    else:
        b = open(exe, 'rb').read()
        if md5(b) != EXE_MD5: print('   AVISO: tu malie.exe es de otra versión; me salto este paso (usa malie.exe)')
        else:
            p = json.load(open(os.path.join(DATOS, 'exe_parche.json'), encoding='utf-8'))
            nb = aplicar(b, p); assert md5(nb) == p['md5_resultado']
            open(os.path.join(juego, 'malie_es.exe'), 'wb').write(nb); print('   OK: malie_es.exe')

    paso('6/6 Limpieza')
    shutil.rmtree(tmp, ignore_errors=True)
    print('\nLISTO. Abre el juego con malie_es.exe (o malie.exe, con los menús de Windows en japonés).')
    print('Para quitar el parche: borra data3.dat (o vuelve a poner data3_antes_del_parche.dat).')

if __name__ == '__main__': main()
