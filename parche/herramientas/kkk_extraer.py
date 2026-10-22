#!/usr/bin/env python3
"""kkk_extraer.py - lee data1.dat / data2.dat / data3.dat SIN descifrarlos completos.

Uso (en C:\\KKK_Project\\tools\\KKK_tools_v3):
  Listar carpetas:   python kkk_extraer.py ..\\..\\work\\game\\data1.dat --listar data/screen
  Buscar nombres:    python kkk_extraer.py ..\\..\\work\\game\\data1.dat --buscar text01
  Extraer carpeta:   python kkk_extraer.py ..\\..\\work\\game\\data1.dat data/screen/config salida_config

Al extraer, copia los nombres EXACTOS del archivo (sin recortar), para poder volver a empacarla.
Solo lee el archivo: no modifica nada.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import malie_cipher as mc

class Dat:
    def __init__(self, path):
        self.f = open(path, 'rb')
        h = self.read(0, 16)
        assert h[:4] == b'LIBP', 'no es un archivo LIBP de MALIE'
        self.cnt, self.fcnt = struct.unpack_from('<II', h, 4)
        self.tbl = 16 + 32 * self.cnt
        head = self.read(0, self.tbl + 4 * self.fcnt)
        self.ents = []
        for i in range(self.cnt):
            o = 16 + 32 * i
            name = head[o:o + 22].split(b'\0')[0].decode('ascii', 'replace')
            fl16, a_, b_ = struct.unpack_from('<HII', head, o + 22)   # nombre 22 bytes + bandera u16
            self.ents.append((name, fl16 << 16, a_, b_))
        self.offs = struct.unpack_from('<%dI' % self.fcnt, head, self.tbl)
        self.base = self._find_base()

    def read(self, pos, size):
        a = pos & ~15; b = (pos + size + 15) & ~15
        self.f.seek(a); raw = self.f.read(b - a)
        raw += b'\0' * ((-len(raw)) % 16)
        dec = mc.crypt(raw, mc.decrypt_block, a)
        return dec[pos - a: pos - a + size]

    def _find_base(self):
        end = self.tbl + 4 * self.fcnt
        # probamos alineaciones posibles con un archivo de texto conocido (.dzi o .svg)
        probe = None
        for i, (n, fl, a, sz) in enumerate(self.ents):
            if fl & 0x10000 and (n.endswith('.dzi') or n.endswith('.svg')) and sz > 4:
                probe = (n, a); break
        for al in (0x1000, 0x400, 0x2000, 0x800, 0x10000):
            base = (end + al - 1) & ~(al - 1)
            if probe is None: return base
            d = self.read(base + self.offs[probe[1]] * 1024, 4)
            if d[:3] == b'DZI' or d[:1] == b'<' or d[:3] == b'\xef\xbb\xbf':
                return base
        raise SystemExit('ERROR: no pude ubicar el inicio de los datos')

    def kids(self, i):
        n, fl, a, b = self.ents[i]
        return [] if fl & 0x10000 else list(range(a, a + b))

    def find(self, path):
        i = 0
        for part in [p for p in path.replace('\\', '/').split('/') if p]:
            for j in self.kids(i):
                if self.ents[j][0].lower() == part.lower(): i = j; break
            else: raise SystemExit('ERROR: no existe "%s" (buscando "%s")' % (path, part))
        return i

    def data(self, i):
        n, fl, a, sz = self.ents[i]
        return self.read(self.base + self.offs[a] * 1024, sz)

    def walk(self, i, prefix=''):
        for j in self.kids(i):
            n, fl = self.ents[j][0], self.ents[j][1]
            p = prefix + '/' + n if prefix else n
            yield j, p, not (fl & 0x10000)
            if not (fl & 0x10000): yield from self.walk(j, p)

def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    d = Dat(a[0])
    if a[1] == '--listar':
        root = a[2] if len(a) > 2 else ''
        i = d.find(root) if root else 0
        for j in d.kids(i):
            n, fl, x, sz = d.ents[j]
            if fl & 0x10000: print('   %-22s %10d bytes' % (n, sz))
            else: print('[C] %-22s %6d elementos' % (n, sz))
    elif a[1] == '--buscar':
        key = a[2].lower(); hits = 0
        for j, p, isdir in d.walk(0):
            if key in p.split('/')[-1].lower():
                print(('[C] ' if isdir else '    ') + p); hits += 1
                if hits >= 200: print('... (hay mas)'); break
        print('encontrados: %d' % hits)
    elif a[1] == '--filtrar':
        # python kkk_extraer.py data1.dat --filtrar data/picture/event "^(r1[04]_)?text\d" salida
        import re
        src, pat, out = a[2], re.compile(a[3], re.I), a[4]
        i = d.find(src); n = 0; tot = 0
        for j, p, isdir in d.walk(i):
            if isdir or not any(pat.search(c) for c in p.split('/')): continue
            dst = os.path.join(out, *p.split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            b = d.data(j); open(dst, 'wb').write(b); n += 1; tot += len(b)
            if n % 50 == 0: print('  ... %d archivos' % n)
        print('OK: %d archivos (%d bytes) extraidos de %s a %s' % (n, tot, src, out))
    else:
        src, out = a[1], a[2]
        i = d.find(src); n = 0; tot = 0
        for j, p, isdir in d.walk(i):
            dst = os.path.join(out, *p.split('/'))
            if isdir: os.makedirs(dst, exist_ok=True); continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            b = d.data(j); open(dst, 'wb').write(b); n += 1; tot += len(b)
            if n % 50 == 0: print('  ... %d archivos' % n)
        print('OK: %d archivos (%d bytes) extraidos de %s a %s' % (n, tot, src, out))

if __name__ == '__main__': main()
