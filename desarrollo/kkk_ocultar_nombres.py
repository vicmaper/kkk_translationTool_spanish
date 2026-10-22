#!/usr/bin/env python3
"""kkk_ocultar_nombres.py (v2) - caja de nombre: «？？？» hasta que la historia revela al personaje.
Uso: python kkk_ocultar_nombres.py base.dat nombres_reglas.tsv kkk_script_BUENO.csv salida.dat
- base.dat: plantilla con los nombres en espanol (kkk_nombres.py), la interfaz y el guion.
- nombres_reglas.tsv: prefijo_voz TAB desde TAB rangos [TAB origen]
    desde  = id desde el que se ve el nombre ('nunca' = siempre «？？？»)
    rangos = 'A-B=???' o 'A-B=Nombre' separados por ';' (A sola = un mensaje). Mandan sobre 'desde'.
    Nombre: si ya existe como etiqueta en espanol se reutiliza; si no, se escribe en un hueco libre.
- El CSV solo se usa para saber que voz tiene cada mensaje. Se muestra la etiqueta que el propio juego
  pone a cada linea (traducida por kkk_nombres.py); esta herramienta solo la cambia por «？？？» o por
  el nombre de 'rangos'. El exec.dat no cambia de tamano."""
import sys, os, re, struct, csv, collections, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import malie_cipher as mc
import kkk_build as kb
from kkk_build import parse, blob
TABLE = 0x2F2A6A
NAMECALL = b'\x2d\x48\x00\x00\x00'; MSGCALL = b'\x2d\x2d\x00\x00\x00'
HIDDEN = '？？？'
# exec.dat ORIGINAL de TU juego (sácalo con kkk_extraer.py de tu data1.dat). NO se sube al repositorio.
ORIG = os.environ.get('KKK_EXEC_ORIGINAL') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exec.dat')

def regions(ex):
    ce = TABLE - 4
    cs = [p for p in range(0x100000, ce - 4) if struct.unpack_from('<I', ex, p)[0] == ce - (p + 4)][0] + 4
    ds = [p for p in range(0, cs - 8) if struct.unpack_from('<I', ex, p)[0] == cs - 4 - (p + 4)][0] + 4
    return ds, cs, ce

def strings(data):
    out = {}; i = 0
    while i < len(data):
        j = i
        while j + 1 < len(data) and data[j:j+2] != b'\0\0': j += 2
        out[i] = data[i:j].decode('utf-16le', 'replace'); i = j + 2
    return out

def msg_id(code, p):
    if code[p - 2] == 0x11: return code[p - 1]
    if code[p - 5] == 0x0d: return struct.unpack_from('<I', code, p - 4)[0]
    return None

def name_ref(code, p, valid):
    """[push nombre] antes de 2D 48: 0C u32 o 0A u16. Se elige la lectura que apunta a un texto real
    (hay casos como '0c 00 0a 14 95' que parecen las dos cosas)."""
    c = []
    if code[p - 3] == 0x0a: c.append((p - 2, 2, struct.unpack_from('<H', code, p - 2)[0]))
    if code[p - 5] == 0x0c: c.append((p - 4, 4, struct.unpack_from('<I', code, p - 4)[0]))
    c = [x for x in c if x[2] in valid]
    if len(c) != 1: raise SystemExit('referencia de nombre rara en %x' % p)
    return c[0]

def parse_rules(path):
    rules = {}
    for r in csv.DictReader(open(path, encoding='utf-8-sig'), delimiter='\t'):
        v = r['desde'].strip(); rg = []
        for part in (r.get('rangos') or '').split(';'):
            part = part.strip()
            if not part: continue
            m = re.fullmatch(r'(\d+)(?:\s*[-–]\s*(\d+))?\s*=\s*(.+)', part)
            if not m: raise SystemExit('rango mal escrito (%s): %r' % (r['prefijo_voz'], part))
            lo = int(m.group(1)); hi = int(m.group(2) or lo); nm = m.group(3).strip()
            rg.append((lo, hi, HIDDEN if nm in ('???', HIDDEN) else nm))
        rules[r['prefijo_voz'].strip()] = (int(v) if v.isdigit() else None, rg)
    return rules

def main():
    if len(sys.argv) < 5: print(__doc__); sys.exit(1)
    basep, tabp, csvp, outp = sys.argv[1:5]
    rules = parse_rules(tabp)
    voice = {}
    for r in csv.DictReader(open(csvp, encoding='utf-8-sig')):
        m = re.search(r'\{v:v_([a-z]+)\d', r['japanese'])
        if m: voice[int(r['id'])] = m.group(1)
    dec, ents, tbl, offs, fcnt = parse(basep)
    i, e = [(i, e) for i, e in enumerate(ents) if e[0] == 'exec.dat'][0]
    ex = bytearray(blob(dec, offs, e)); ds, cs, ce = regions(ex)
    code = bytes(ex[cs:ce]); data = ex[ds:cs - 4]
    orig = open(ORIG, 'rb').read(); ods, ocs, oce = regions(orig)
    assert (ods, ocs) == (ds, cs), 'el exec de la plantilla no corresponde al original'
    odata = orig[ods:ocs - 4]; ocode = orig[ocs:oce]; osmap = strings(odata)
    smap = strings(bytes(data)); valid = set(smap) | set(osmap)
    # huecos libres: textos de depuracion '■...\n' del original que kkk_nombres.py dejo en ceros
    free = []
    for o, s in sorted(osmap.items()):
        if 0 < o < 0x10000 and s.startswith('■') and s.endswith('\n') and '%' not in s:
            pat = b'\x0a' + struct.pack('<H', o)
            if ocode.count(pat) == ocode.count(pat + b'\x04\x22\x01') == 1:
                q = o; end = o + (len(s) + 1) * 2
                while q < end:
                    if (q == o or data[q - 2:q] == b'\0\0') and data[q:q + 2] == b'\0\0':
                        r_ = q
                        while r_ < end and data[r_:r_ + 2] == b'\0\0': r_ += 2
                        if r_ - q >= 8: free.append([q, r_])
                        q = r_
                    else: q += 2
    where = {}
    def put(text):
        if text in where: return where[text]
        for o, s in smap.items():                          # ya existe (etiqueta traducida)
            if s == text and o < 0x10000 and (o == 0 or data[o - 2:o] == b'\0\0'): where[text] = o; return o
        need = (len(text) + 1) * 2
        for f in free:
            if f[1] - f[0] >= need + 2:                    # deja un 00 00 delante para el siguiente
                o = f[0] if f[0] == 0 or data[f[0]-2:f[0]] == b'\0\0' else f[0] + 2
                if f[1] - o < need: continue
                data[o:o + need] = text.encode('utf-16le') + b'\0\0'; f[0] = o + need + 2
                where[text] = o; return o
        raise SystemExit('no hay hueco para %r' % text)
    msgs = sorted(m.start() for m in re.finditer(re.escape(MSGCALL), code))
    cnt = collections.Counter(); shown = collections.Counter(); alias = collections.Counter(); sin = 0
    for m in re.finditer(re.escape(NAMECALL), code):
        p = m.start(); at, n, cur = name_ref(code, p, valid)
        k = bisect.bisect_right(msgs, p)
        mid = msg_id(code, msgs[k]) if k < len(msgs) else None
        if mid is None: sin += 1; continue
        v = voice.get(mid)
        if v not in rules: continue
        desde, rg = rules[v]
        lab = next((nm for lo, hi, nm in rg if lo <= mid <= hi), None)
        if lab is None and (desde is None or mid < desde): lab = HIDDEN
        if lab is None: shown[v] += 1; continue
        o = put(lab)
        if n == 2 and o >= 0x10000: raise SystemExit('hueco fuera de rango')
        struct.pack_into('<H' if n == 2 else '<I', ex, cs + at, o)
        (cnt if lab == HIDDEN else alias)[v] += 1
    ex[ds:cs - 4] = data
    new = bytes(ex); old = blob(dec, offs, e)
    assert len(new) == len(old) and new[TABLE:] == old[TABLE:]
    o = kb.BASE + offs[e[2]] * 1024
    raw = bytearray(dec); raw[o:o + len(new)] = new
    open(outp, 'wb').write(mc.crypt(bytes(raw), mc.encrypt_block, 0))
    print('OK: %s | «？？？» en %d mensajes | otro nombre en %d' % (outp, sum(cnt.values()), sum(alias.values())))
    print('   textos usados: ' + ', '.join('%s@%#x' % kv for kv in where.items()))
    for v in sorted(set(cnt) | set(shown) | set(alias)):
        print('   %-4s ocultos %5d   otro nombre %4d   con su nombre %5d' % (v, cnt[v], alias[v], shown[v]))
    if sin: print('Aviso: %d nombres sin mensaje identificable (se dejaron igual)' % sin)

if __name__ == '__main__': main()
