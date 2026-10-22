#!/usr/bin/env python3
"""kkk_build.py v2 - UN SOLO COMANDO: CSV -> data3.dat (caja G6 horizontal)
Uso (dentro de C:\\KKK_Project\\tools):
  python kkk_build.py kkk_script_BUENO.csv
Opciones:
  --base  data3_G6_BASE.dat   plantilla G6 (caja horizontal + ajuste 'horizontal'); NO se modifica
  --exec  exec.dat            exec.dat ORIGINAL descifrado (textos japoneses); NO se modifica
  --out   data3_nuevo.dat     archivo de salida
  --width 92                  maximo de medios-anchos por renglon (letra latina = 1, japonesa = 2)
  --lines 6                   renglones que caben en la caja (los que pasen se reportan)
Hace: salto {n} automatico entre palabras, conserva los {n} que tu pongas, agrega {end},
copia el ajuste horizontal de la plantilla, cifra y comprueba el resultado.
"""
import sys, os, re, struct, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import malie_cipher as mc, kkk_exec_tool as kt

BASE = 8192
HPATCH = 0x1510A
HTEXT = "dir='horizontal'".encode('utf-16le')

def arg(n, d): return sys.argv[sys.argv.index(n)+1] if n in sys.argv else d

def parse(path):
    dec = mc.crypt(open(path, 'rb').read(), mc.decrypt_block, 0)
    assert dec[:4] == b'LIBP', 'la plantilla no es un data3.dat valido'
    cnt, fcnt = struct.unpack_from('<II', dec, 4)
    ents = []
    for i in range(cnt):
        o = 16 + 32*i
        fl16, a_, b_ = struct.unpack_from('<HII', dec, o+22)   # nombre de 22 bytes + bandera u16
        ents.append((dec[o:o+22].split(b'\0')[0].decode(), fl16 << 16, a_, b_))
    tbl = 16 + 32*cnt
    offs = struct.unpack_from('<%dI' % fcnt, dec, tbl)
    global BASE
    BASE = (tbl + 4*fcnt + 0xFFF) & ~0xFFF   # inicio de datos = cabecera alineada a 4096 (8192 en las plantillas chicas)
    return dec, ents, tbl, offs, fcnt

def blob(dec, offs, e): o = BASE + offs[e[2]]*1024; return dec[o:o+e[3]]

def w(ch): return 2 if ord(ch) >= 0x2000 and not (0xFF61 <= ord(ch) <= 0xFF9F) else 1  # signos ―…“” y japones = 2 (conservador)

def vis(tok):  # visible width of a piece (tags count 0, ruby counts its base)
    tok = re.sub(r'\{r:([^}|]*)\|[^}]*\}', r'\1', tok)
    tok = re.sub(r'\{[^}]*\}', '', tok)
    return sum(w(c) for c in tok)

def wrap_lines(t, width):
    """Pone {n} entre palabras para que ningun renglon pase de `width`. Devuelve (texto, renglones).
    {u000A} (salto real del japones, usado entre paginas como {end}{u000A}{u000A}) reinicia el renglon y
    no lleva {n}. `renglones` = el maximo de renglones de una pagina (las paginas se separan por {u000A})."""
    end = t.endswith('{end}')
    if end: t = t[:-5]
    # jindai moji: cada {u0006}+caracter es UNA letra (ancho 2); nunca se separa ni se lee como salto
    glyphs = []
    def keep(m): glyphs.append(m.group(0)); return chr(0xE000 + len(glyphs) - 1)
    t = re.sub(r'\{u0006\}(?:\{[^}]*\}|.)', keep, t, flags=re.S)
    res = ''
    for k, para in enumerate(t.split('{n}')):
        if k: res += '{n}'
        toks = re.findall(r'[\ue000-\uf8ff]|\{[^}]*\}|[^\s{\ue000-\uf8ff]+(?:\{[^}]*\}[^\s{\ue000-\uf8ff]*)*|\s+', para)
        line = ''; col = 0
        for tok in toks:
            if tok == '{u000A}':
                res += line.rstrip() + tok; line = ''; col = 0; continue
            if tok.isspace():
                if col: line += ' '; col += 1
                continue
            L = vis(tok)
            if col and col + L > width:
                res += line.rstrip() + '{n}'; line = ''; col = 0
            line += tok; col += L
        res += line.rstrip()
    pages = re.split(r'(?:\{u000A\}){2,}', res)
    res = re.sub(r'[\ue000-\uf8ff]', lambda m: glyphs[ord(m.group(0)) - 0xE000], res)
    n = max(p.count('{n}') + p.count('{u000A}') + 1 for p in pages)
    return res + ('{end}' if end else ''), n

def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith('--'): print(__doc__); sys.exit(1)
    csvp = sys.argv[1]
    basep = arg('--base', 'data3_G6_BASE.dat'); exp = arg('--exec', 'exec.dat' if os.path.exists('exec.dat') else r'..\work\exec.dat')
    out = arg('--out', 'data3_nuevo.dat'); width = int(arg('--width', '92')); maxl = int(arg('--lines', '6'))
    dec, ents, tbl, offs, fcnt = parse(basep)
    ex = [e for e in ents if e[0] == 'exec.dat'][0]
    bexec = blob(dec, offs, ex)
    assert bexec[HPATCH:HPATCH+len(HTEXT)] == HTEXT, 'la plantilla no trae el ajuste horizontal'
    # 1) CSV con saltos automaticos
    rows = list(csv.DictReader(open(csvp, newline='', encoding='utf-8-sig')))
    largos = []
    for r in rows:
        # cualquier fila con texto en spanish cuenta como traducida, salvo status 'untranslated'
        if r['spanish'].strip() and r['status'].strip().lower() != 'untranslated': r['status'] = 'draft'
        if r['spanish'].strip() and r['status'].strip().lower() in ('draft', 'reviewed', 'approved'):
            r['spanish'], n = wrap_lines(r['spanish'].strip(), width)
            if n > maxl: largos.append((r['id'], n))
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp(prefix='kkk_build_')           # archivos temporales propios de esta corrida
    tmpcsv = os.path.join(tmpdir, '_tmp_wrapped.csv')
    with open(tmpcsv, 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys()); wr.writeheader(); wr.writerows(rows)
    # 2) insertar en exec original y copiar el codigo (ajuste horizontal) de la plantilla
    kt.insert(exp, tmpcsv, os.path.join(tmpdir, '_tmp_exec.dat'), 0)
    ne = bytearray(open(os.path.join(tmpdir, '_tmp_exec.dat'), 'rb').read())
    ne[:kt.TABLE] = bexec[:kt.TABLE]; ne = bytes(ne)
    # 3) reempaquetar con las demas piezas de la plantilla (caja G6)
    hdr = bytearray(dec[:BASE]); body = bytearray(); newoffs = [0]*fcnt
    files = [(i, e) for i, e in enumerate(ents) if e[1] & 0x10000]
    for i, e in sorted(files, key=lambda t: t[1][2]):
        b = ne if e[0] == 'exec.dat' else blob(dec, offs, e)
        newoffs[e[2]] = len(body)//1024
        struct.pack_into('<I', hdr, 16 + 32*i + 28, len(b))
        body += b; body += b'\0' * ((-len(body)) % 4096)
    struct.pack_into('<%dI' % fcnt, hdr, tbl, *newoffs)
    raw = bytes(hdr) + bytes(body); raw += b'\0' * ((-len(raw)) % 4096)
    open(out, 'wb').write(mc.crypt(raw, mc.encrypt_block, 0))
    # 4) comprobacion
    d2, e2, t2, o2, _ = parse(out)
    x2 = [e for e in e2 if e[0] == 'exec.dat'][0]
    open(os.path.join(tmpdir, '_tmp_check.dat'), 'wb').write(blob(d2, o2, x2))
    _, msgs, _ = kt.load(os.path.join(tmpdir, '_tmp_check.dat'))
    assert blob(d2, o2, x2)[HPATCH:HPATCH+len(HTEXT)] == HTEXT
    shutil.rmtree(tmpdir, ignore_errors=True)
    print('OK: %s creado | %d mensajes | horizontal: si' % (out, len(msgs)))
    if largos:
        print('AVISO: %d mensajes pasan de %d renglones (revisalos):' % (len(largos), maxl))
        for i, n in largos: print('   id %s -> %d renglones' % (i, n))
    else: print('Ningun mensaje pasa de %d renglones.' % maxl)

if __name__ == '__main__': main()
