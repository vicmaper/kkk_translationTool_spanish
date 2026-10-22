#!/usr/bin/env python3
"""kkk_exec_tool.py - extract/insert text of MALIE exec.dat (Kajiri Kamui Kagura, 2017 build).
  python kkk_exec_tool.py extract exec.dat script.csv
  python kkk_exec_tool.py insert  exec.dat script.csv exec_new.dat [--wrap 0] [--status draft]
CSV columns: id, voice, japanese, spanish, status
(id of an inserted message = any non-number, e.g. new1)
Tags: {n}=line break(07 04)  {v:ID}..{/v}=voice(07 08 ID 00 .. 07 09)  {r:base|ruby}=ruby(07 01)  {uXXXX}=other control unit
"""
import sys, struct, csv, re
TABLE = 0x2F2A6A   # message table offset (verified on this build)
COUNT = 27864

def load(path):
    d = open(path, 'rb').read()
    count = None
    for n in range(COUNT - 50, COUNT + 2000):   # detect message count (supports inserted messages)
        po = TABLE + 8*n
        if po + 4 <= len(d) and po + 4 + struct.unpack_from('<I', d, po)[0] == len(d):
            count = n; break
    assert count, 'layout mismatch: cannot detect message table'
    ents = [struct.unpack_from('<II', d, TABLE + 8*k) for k in range(count)]
    psize_off = TABLE + 8*count
    base = psize_off + 4
    psize, = struct.unpack_from('<I', d, psize_off)
    msgs = [d[base+o:base+o+l].decode('utf-16le') for o, l in ents]
    return d, msgs, base

def to_tags(s):
    out = []; i = 0
    while i < len(s):
        c = s[i]
        if c == '\x07' and i+1 < len(s):
            k = s[i+1]
            if k == '\x04': out.append('{n}'); i += 2; continue
            if k == '\x06': out.append('{end}'); i += 2; continue
            if k == '\x09': out.append('{/v}'); i += 2; continue
            if k == '\x08':
                j = s.index('\0', i); out.append('{v:%s}' % s[i+2:j]); i = j+1; continue
            if k == '\x01':
                j = s.index('\0', i); b, r = s[i+2:j].split('\n', 1)
                out.append('{r:%s|%s}' % (b, r)); i = j+1; continue
        if ord(c) < 0x20 or 0x600 <= ord(c) < 0x700:
            out.append('{u%04X}' % ord(c))
        elif c in '{}': out.append('{u%04X}' % ord(c))
        else: out.append(c)
        i += 1
    return ''.join(out)

TAG = re.compile(r'\{(?:n|end|/v|v:[^}]*|r:[^}|]*\|[^}]*|u[0-9A-Fa-f]{4})\}')
def from_tags(t):
    def rep(m):
        g = m.group(0)[1:-1]
        if g == 'n': return '\x07\x04'
        if g == 'end': return '\x07\x06'
        if g == '/v': return '\x07\x09'
        if g.startswith('v:'): return '\x07\x08' + g[2:] + '\0'
        if g.startswith('r:'):
            b, r = g[2:].split('|', 1); return '\x07\x01' + b + '\n' + r + '\0'
        return chr(int(g[1:], 16))
    return TAG.sub(rep, t)

def wrap(t, width):
    """Column padding: the game hard-wraps at `width` chars/column (62 measured) and splits words.
    Pad with spaces so a word that does not fit starts the next column. {n}/{end} reset the column."""
    if not width: return t
    parts = re.split(r'(\{[^}]*\})', t)
    out = []; col = 0
    for p in parts:
        if TAG.fullmatch(p):
            out.append(p)
            if p in ('{n}', '{end}'): col = 0
            continue
        for tok in re.findall(r'\S+|\s+', p):
            if tok.isspace():
                if col and col < width: out.append(' '); col += 1
                if col >= width: col = 0
                continue
            L = len(tok)
            if col and col + L > width:
                out.append(' ' * (width - col)); col = 0
            out.append(tok); col += L
            while col >= width: col -= width
    return ''.join(out)

def extract(src, dst):
    d, msgs, _ = load(src)
    with open(dst, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['id', 'voice', 'japanese', 'spanish', 'status'])
        for k, m in enumerate(msgs):
            v = ' '.join(re.findall(r'\x07\x08([^\0]*)\0', m))
            w.writerow([k, v, to_tags(m), '', 'untranslated'])

def insert(src, csvp, dst, width=0, accept=('draft', 'reviewed', 'approved')):
    """Rows keep their ORIGINAL numeric id. A row whose id is not a number (e.g. new1) is a NEW message
    inserted at that position (everything after it shifts by one). Final order = CSV row order."""
    d, msgs, base = load(src)
    new = []; used = 0; added = 0; seen = set()
    with open(csvp, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rid = r['id'].strip(); es = r['spanish']
            ok = r['status'].strip().lower() in accept and es.strip()
            if rid.isdigit():
                k = int(rid); seen.add(k); cur = msgs[k]
                if ok:
                    es = wrap(es, width)
                    if not es.endswith('{end}') and cur.endswith('\x07\x06'): es += '{end}'
                    cur = from_tags(es); used += 1
                new.append(cur)
            else:
                if not es.strip(): continue
                es = wrap(es, width)
                if not es.endswith('{end}'): es += '{end}'
                new.append(from_tags(es)); added += 1
    assert seen == set(range(len(msgs))), 'CSV is missing original ids (every original id must appear once)'
    pool = bytearray(); table = bytearray()
    for m in new:
        b = m.encode('utf-16le'); table += struct.pack('<II', len(pool), len(b)); pool += b + b'\0\0'
    out = d[:TABLE] + table + struct.pack('<I', len(pool)) + pool
    open(dst, 'wb').write(out)
    print('translated:', used, '| new messages inserted:', added, '| total messages:', len(new), '| exec size', len(out))

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'extract': extract(a[1], a[2])
    elif a[0] == 'insert':
        wd = int(a[a.index('--wrap')+1]) if '--wrap' in a else 0
        insert(a[1], a[2], a[3], wd)
    else: print(__doc__)
