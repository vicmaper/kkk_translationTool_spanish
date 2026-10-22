#!/usr/bin/env python3
"""kkk_agregar_carpeta.py - mete una carpeta suelta dentro de una plantilla data3.dat
Uso (en C:\\KKK_Project\\tools):
  python kkk_agregar_carpeta.py base_NOMBRES.dat title_es\title data/screen/title base_TITULO.dat
  (plantilla)  (carpeta local)  (ruta dentro del juego)  (salida)
La carpeta COMPLETA reemplaza a la del juego (svg + .dzi + tex/), por eso hay que meterla entera.
Despues: python kkk_build.py kkk_script_BUENO.csv --base base_TITULO.dat
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import malie_cipher as mc
from kkk_build import parse, blob

def read_tree(path):
    dec, ents, tbl, offs, fcnt = parse(path)
    def node(i):
        n, fl, a, b = ents[i]
        if fl & 0x10000: return blob(dec, offs, ents[i])
        return {ents[j][0]: node(j) for j in range(a, a + b)}
    return node(0), dec[:16]

def local_tree(folder):
    t = {}
    for n in os.listdir(folder):
        p = os.path.join(folder, n)
        t[n] = local_tree(p) if os.path.isdir(p) else open(p, 'rb').read()
    return t

def write(tree, out):
    ents = [['', tree]]; q = [0]; files = []
    while q:                                   # recorrido por niveles, hijos ordenados por nombre
        i = q.pop(0); kids = ents[i][1]
        if isinstance(kids, dict):
            first = len(ents)
            for n in sorted(kids): ents.append([n, kids[n]])
            ents[i] += [first, len(kids)]
            q += range(first, first + len(kids))
    hdr = bytearray(); body = bytearray(); offs = []
    for e in ents:
        name = e[0].encode('ascii'); assert len(name) <= 22, 'nombre muy largo (max 22): ' + e[0]
        if isinstance(e[1], dict): fl, a, b = 0, e[2], e[3]
        else:
            fl, a, b = 0x10000, len(files), len(e[1]); files.append(e[1])
        hdr += name.ljust(22, b'\0') + struct.pack('<HII', fl >> 16, a, b)
    for f in files:
        offs.append(len(body) // 1024); body += f; body += b'\0' * ((-len(body)) % 4096)
    head = b'LIBP' + struct.pack('<III', len(ents), len(files), 0) + hdr + struct.pack('<%dI' % len(offs), *offs)
    base = (len(head) + 0xFFF) & ~0xFFF
    raw = head + b'\0' * (base - len(head)) + body; raw += b'\0' * ((-len(raw)) % 4096)
    open(out, 'wb').write(mc.crypt(raw, mc.encrypt_block, 0))
    return len(ents), len(files)

def main():
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__); sys.exit(1)
    base, folder, inner, out = a
    tree, _ = read_tree(base)
    node = tree
    parts = inner.strip('/').split('/')
    for p in parts[:-1]: node = node.setdefault(p, {})
    node[parts[-1]] = local_tree(folder)
    ne, nf = write(tree, out)
    # comprobacion: releer y comparar
    back, _ = read_tree(out)
    assert back == tree, 'la relectura no coincide'
    print('OK: %s | %d entradas | %d archivos | %s agregado y verificado' % (out, ne, nf, inner))

if __name__ == '__main__': main()
