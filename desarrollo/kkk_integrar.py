"""kkk_integrar.py - mete bloques traducidos (bloque_AAAA-BBBB.tsv: id TAB spanish) en el CSV del guion
y revisa que los codigos coincidan con el japones.
Uso: python kkk_integrar.py kkk_script_BUENO.csv salida.csv bloque_0200-0399.tsv [mas bloques...] [--final]
Mensajes con '[PENDIENTE] ' (al inicio o tras {v:..}) (escenas sin traducir): se cuentan, se listan en pendientes.txt
y en el CSV se deja el JAPONES ORIGINAL (asi se puede probar el juego). Con --final la herramienta se niega
a escribir el CSV si queda alguno: un juego para publicar no debe llevar mensajes pendientes."""
import sys, csv, re
VOICE = re.compile(r'\{/?v[^}]*\}')
JIN = re.compile(r'(?:\{u0006\}(?:\{[^}]*\}|.))+')        # jindai moji: {u0006} + un caracter (o codigo), en cadena
UCODE = re.compile(r'\{u[0-9a-fA-F]{4}\}')

def check(jp, es):
    errs = []
    if VOICE.findall(jp) != VOICE.findall(es): errs.append('voz distinta')
    if JIN.findall(jp) != JIN.findall(es): errs.append('jindai moji distinto')
    if sorted(UCODE.findall(JIN.sub('', jp))) != sorted(UCODE.findall(JIN.sub('', es))): errs.append('codigos {uXXXX} distintos')
    if not es.endswith('{end}') or es.count('{end}') != jp.count('{end}'): errs.append('{end} mal')
    if '\t' in es or '\n' in es: errs.append('tabulador o salto de linea dentro del texto')
    if '{r:' in es: errs.append('quedo furigana {r:}')
    if len(es) > 900: errs.append('mas de 900 caracteres (%d)' % len(es))
    return errs

PEND = '[PENDIENTE] '

def main(src, dst, *blocks):
    final = '--final' in blocks; blocks = [b for b in blocks if b != '--final']
    pend = []
    rows = list(csv.DictReader(open(src, encoding='utf-8-sig')))
    by = {r['id']: r for r in rows}; n = bad = 0
    for b in blocks:
        for line in open(b, encoding='utf-8-sig'):
            line = line.rstrip('\r\n')
            if not line.strip() or line.startswith('id\t'): continue
            i, es = line.split('\t', 1)
            r = by.get(i.strip())
            if not r: print('id desconocido', i); bad += 1; continue
            if PEND in es:                       # puede ir al inicio o despues de {v:...}
                body = es.replace(PEND, '')
                if body.replace('\u3000', '') != r['japanese'].replace('\u3000', ''): print('msg %s: [PENDIENTE] con texto distinto al japones' % i); bad += 1
                pend.append(int(i)); r['spanish'] = r['japanese']; r['status'] = 'untranslated'; continue
            if 'PENDIENTE' in es: print('msg %s: la palabra PENDIENTE aparece dentro del texto' % i); bad += 1
            e = check(r['japanese'], es)
            if e: print('msg %s: %s' % (i, ', '.join(e))); bad += 1
            r['spanish'] = es
            if r['status'] in ('untranslated', ''): r['status'] = 'draft'
            n += 1
    pend = sorted(set(pend))
    if pend:
        open('pendientes.txt', 'w', encoding='utf-8').write('\n'.join(map(str, pend)) + '\n')
        print('AVISO: %d mensajes [PENDIENTE] (quedan en japones; lista en pendientes.txt)' % len(pend))
        if final: print('--final: NO se escribe el CSV mientras haya pendientes.'); sys.exit(2)
    with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print('integrados %d mensajes, %d con avisos -> %s' % (n, bad, dst))

if __name__ == '__main__': main(*sys.argv[1:])
