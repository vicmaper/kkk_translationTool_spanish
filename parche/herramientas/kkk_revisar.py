#!/usr/bin/env python3
"""kkk_revisar.py - revisa el FORMATO de una traducción hecha a mano antes de integrarla.

Uso:
  python kkk_revisar.py archivo.csv                (revisa, corrige lo seguro y escribe el informe)
  python kkk_revisar.py archivo.csv --solo-revisar (no crea el archivo corregido)
  python kkk_revisar.py archivo.csv --guion ruta\\kkk_script_BUENO.csv

Acepta:
  - CSV con columnas id y spanish (japanese y voz son opcionales; si falta japanese se toma del guion);
  - TSV de bloque: id TAB spanish.
Escribe JUNTO AL ARCHIVO ORIGINAL (misma carpeta):
  <nombre>_CORREGIDO.csv        la traducción con los arreglos seguros (este es el que se integra)
  <nombre>_INFORME.txt          qué se corrigió, qué queda y el detalle fila por fila
  <nombre>_FILAS_CON_ERROR.csv  solo las filas que todavía hay que arreglar a mano
No cambia el archivo original.

ERRORES (rompen el juego o lo muestran mal): voz distinta, jindai distinto, códigos {uXXXX} distintos,
número de {end} distinto o sin {end} final, furigana {r:} sin traducir, saltos de línea o tabuladores
reales, letras japonesas sueltas, más de 900 caracteres, más de 6 renglones de 92, id desconocido o repetido.
AVISOS (estilo de la guía): nombres sin macrón, honoríficos -sama/-san/-dono/-kun/-chan, Matara, Kegai,
Shinshuu, diálogo sin 「」, punto después de 」, ……, espacio japonés al inicio, -[PENDIENTE]-.
"""
import sys, os, re, csv, collections
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace'); sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = re.compile(r'\{/?v[^}]*\}')
JIN = re.compile(r'(?:\{u0006\}(?:\{[^}]*\}|.))+')
UCODE = re.compile(r'\{u[0-9a-fA-F]{4}\}')
JP = re.compile(r'[぀-ヿ一-鿿]')
MAXLEN, WIDTH, LINES = 900, 92, 6
# líneas que se dejan en japonés A PROPÓSITO (citas en kanbun, jindai, la fila de ノ, texto censurado)
# escenas de la guía 1c (Ryūsui, de aspecto infantil): se revisa el formato igual que el resto y además
# se avisa en cada línea para revisar a mano el contenido
EXCLUIDAS = [(16600, 16795), (24739, 24747), (25533, 25692)]
def excluida(i): return i.isdigit() and any(a <= int(i) <= b for a, b in EXCLUIDAS)
COPIA_OK = {173, 174, 175, 2510, 2514, 2517, 3911, 4543, 6372, 6373, 8603, 8604, 8605, 9034, 9039, 12006, 16210}

# arreglos seguros de nombres y términos (mismo criterio que la guía y el glosario)
NOMBRES = [(r'\bRindou\b', 'Rindō'), (r'\bRindo\b', 'Rindō'), (r'\bYakou\b', 'Yakō'), (r'\bYako\b', 'Yakō'),
           (r'\bRyuusui\b', 'Ryūsui'), (r'\bRyusui\b', 'Ryūsui'), (r'\bRyuumei\b', 'Ryūmei'), (r'\bRyumei\b', 'Ryūmei'),
           (r'\bKeishirou\b', 'Keishirō'), (r'\bKeishiro\b', 'Keishirō'), (r'\bSoujirou\b', 'Sōjirō'),
           (r'\bSojirou\b', 'Sōjirō'), (r'\bSojiro\b', 'Sōjirō'), (r'\bKyougetsu\b', 'Kyōgetsu'),
           (r'\bKyogetsu\b', 'Kyōgetsu'), (r'\bKujou\b', 'Kujō'), (r'\bKujo\b', 'Kujō'), (r'\bOotake\b', 'Ōtake'),
           (r'\bOtake\b', 'Ōtake'), (r'\bMatara\b', 'Madara'), (r'\bKegai\b', 'kegai'),
           (r'\bde Shinshuu\b', 'de la Tierra Sagrada'), (r'\bShinshuu\b', 'Tierra Sagrada')]
def clave(run):
    it = re.findall(r'\{r:([^|}]*)\|([^}]*)\}', run)
    if it and all(l.strip() in ('、', '') for b, l in it): return 'énfasis:' + ''.join(b for b, l in it)
    return ' + '.join('%s|%s' % (b, l) for b, l in it)

def norm(k): return re.sub(r'[っッ\s]', '', k)

DICC = {}
def cargar_diccionario():
    p = os.path.join(HERE, 'diccionario_furigana.tsv')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8-sig'):
            a = line.rstrip('\r\n').split('\t')
            if len(a) >= 2 and a[0] and a[0] != 'clave' and a[1].strip(): DICC[norm(a[0])] = a[1].strip()

# honoríficos con la forma ya usada en el guion (los demás quedan como aviso)
HONOR_MAP = [('Yakō-sama', 'señor Yakō'), ('Ryūsui-sama', 'señorita Ryūsui'), ('ani-sama', 'hermano'), ('Ani-sama', 'Hermano'),
             ('Eboshi-dono', 'señora Eboshi'), ('Ryūmei-dono', 'señora Ryūmei'), ('Ryūmei-sama', 'señora Ryūmei'),
             ('Shiori-san', 'Shiori'), ('Rindō-san', 'Rindō'), ('Sōjirō-kun', 'Sōjirō'), ('Sakuya-sama', 'señora Sakuya')]
HONOR = re.compile(r'\b[\wōūŌŪ]+-(?:sama|san|dono|kun|chan)\b')

def w(ch): return 2 if ord(ch) >= 0x2000 and not (0xFF61 <= ord(ch) <= 0xFF9F) else 1

def vis(tok):
    tok = re.sub(r'\{r:([^}|]*)\|[^}]*\}', r'\1', tok)
    tok = re.sub(r'\{[^}]*\}', '', tok)
    return sum(w(c) for c in tok)

def renglones(t, width=WIDTH):
    """Igual que kkk_build: cuenta los renglones de la página más larga y el largo final con saltos."""
    if t.endswith('{end}'): t = t[:-5]
    glyphs = []
    def keep(m): glyphs.append(m.group(0)); return chr(0xE000 + len(glyphs) - 1)
    t = re.sub(r'\{u0006\}(?:\{[^}]*\}|.)', keep, t, flags=re.S)
    res = ''
    for k, para in enumerate(t.split('{n}')):
        if k: res += '{n}'
        toks = re.findall(r'[-]|\{[^}]*\}|[^\s{-]+(?:\{[^}]*\}[^\s{-]*)*|\s+', para)
        line = ''; col = 0
        for tok in toks:
            if tok == '{u000A}':
                res += line.rstrip() + tok; line = ''; col = 0; continue
            if tok.isspace():
                if col: line += ' '; col += 1
                continue
            L = vis(tok)
            if col and col + L > width: res += line.rstrip() + '{n}'; line = ''; col = 0
            line += tok; col += L
        res += line.rstrip()
    pages = re.split(r'(?:\{u000A\}){2,}', res)
    n = max(p.count('{n}') + p.count('{u000A}') + 1 for p in pages)
    res = re.sub(r'[-]', lambda m: glyphs[ord(m.group(0)) - 0xE000], res)
    return n, len(res) + 5

def corregir(jp, es):
    """Solo arreglos que no cambian el sentido. Devuelve (texto, lista de lo que se corrigió)."""
    hechos = []
    def paso(nuevo, que):
        nonlocal es
        if nuevo != es: hechos.append(que); es = nuevo
    for a, b in NOMBRES:
        m = re.search(a, es)
        if m: paso(re.sub(a, b, es), '%s → %s' % (m.group(0), b))
    for a, b in HONOR_MAP:
        if a in es: paso(es.replace(a, b), '%s → %s' % (a, b))
    def art(m):
        prep, t = m.group(1), m.group(2); a = 'el' if t == 'señor' else 'la'
        if prep.lower() == 'de' and a == 'el': return ('D' if prep[0] == 'D' else 'd') + 'el ' + t
        if prep.lower() == 'a' and a == 'el': return ('A' if prep[0] == 'A' else 'a') + 'l ' + t
        return '%s %s %s' % (prep, a, t)
    paso(re.sub(r'\b(con|Con|para|Para|por|Por|que|y|o|sin|en|de|De|a|A|entre|hacia|según)\s(señor|señora|señorita)\b', art, es), 'artículo antes de señor/señora')
    paso(re.sub(r'(「|^|[.!?¡¿]\s*)(señor|señora|señorita)\b', lambda m: m.group(1) + m.group(2).capitalize(), es), 'mayúscula al inicio')
    if '\n' in es or '\r' in es:                    # saltos reales -> la misma estructura del japonés
        seps = re.findall(r'(?:\{end\})?(?:\{u000A\})+|\{n\}', jp); parts = re.split(r'[\r\n]+', es.strip())
        if len(parts) == len(seps) + 1:
            paso(parts[0] + ''.join(x + y for x, y in zip(seps, parts[1:])), 'saltos de línea reales → códigos del japonés')
    paso(es.replace('\t', ' '), 'tabulador quitado')
    paso(re.sub(r'(^|\{n\}|\{u000A\}|\{v:[^}]*\}|\{end\})\u3000+', r'\1', es).replace('\u3000', ' '), 'espacio japonés quitado')
    paso(re.sub(r'\s*[っッ]+', '', es), 'っ suelta quitada')
    paso(re.sub('…{2,}', '…', es), '«……» → «…»')
    partes = re.split(r'((?:\{u0006\}(?:\{[^}]*\}|.))+)', es)      # no tocar el jindai
    paso(''.join(p if k % 2 else p.replace('！', '!').replace('？', '?') for k, p in enumerate(partes)), '！？ japoneses → ! ?')
    paso(re.sub(r'」\.', '」', es), 'punto después de 」 quitado')
    def furi(m):
        k = clave(m.group(0)); v = DICC.get(norm(k))
        if v: hechos.append('furigana %s → %s (del diccionario: revisar que la frase quede bien)' % (k, v)); return v
        return m.group(0)
    es = re.sub(r'(?:\{r:[^}]*\})+', furi, es)
    jj, ej = JIN.findall(jp), JIN.findall(es)        # marcas jindai sueltas perdidas ({u0006}{u0000}, {u0006}I…)
    if jj != ej:
        miss = [x for x in jj if len(re.findall(r'\{u0006\}', x)) == 1 and x not in ej]
        for x in miss:
            if jp.count(x) != 1: continue
            antes = re.sub(r'\{[^}]*\}', '', jp.split(x)[0]).rstrip('　 っッ')
            despues = jp.split(x)[1]
            nuevo = None
            m = re.search(r'(―+|─+|…+)$', antes)
            runs = re.findall(re.escape(m.group(1)[0]) + '+', es) if m else []
            if m and len(runs) == 1:                     # misma raya o puntos que en japonés
                nuevo = es.replace(runs[0], runs[0] + x, 1)
            elif re.match(r'[」』]?\{/v\}', despues) and '」{/v}' in es:
                nuevo = es.replace('」{/v}', x + '」{/v}', 1)
            elif despues.startswith('{end}') and es.endswith('{end}') and es.count('{end}') == 1:
                nuevo = es[:-5] + x + '{end}'
            if nuevo: paso(nuevo, 'marca jindai %s repuesta' % x)
    paso(es.strip(), 'espacios sobrantes')
    return es, hechos

def revisar(jp, es, i=None):
    err, avi = [], []
    if i in COPIA_OK: return [], []
    if es.replace('\u3000', '').strip() == jp.replace('\u3000', '').strip() and JP.search(re.sub(r'\{[^}]*\}', '', jp)):
        return ['sin traducir (sigue igual al japonés)'], []
    if VOICE.findall(jp) != VOICE.findall(es): err.append('voz distinta al japonés')
    if JIN.findall(jp) != JIN.findall(es): err.append('jindai distinto (copiar las cadenas {u0006}X tal cual)')
    if sorted(UCODE.findall(JIN.sub('', jp))) != sorted(UCODE.findall(JIN.sub('', es))): err.append('códigos {uXXXX} distintos')
    if es.count('{end}') != jp.count('{end}'): err.append('{end}: hay %d y el japonés tiene %d' % (es.count('{end}'), jp.count('{end}')))
    elif not es.endswith('{end}'): err.append('no termina en {end}')
    if '{r:' in es: err.append('quedó furigana {r:…} (traducir el sentido)')
    if '\n' in es or '\r' in es: err.append('salto de línea real (usar {n} o los códigos del japonés)')
    if '\t' in es: err.append('tabulador dentro del texto')
    t = JIN.sub('', re.sub(r'\{[^}]*\}', '', es))
    runs = re.findall(r'[\u3040-\u30fa\u30fc-\u30ff\u4e00-\u9fff]+', t.replace('ノ', ''))
    if runs:
        tj = re.sub(r'\{[^}]*\}', '', jp)
        tjc = JIN.sub('', tj).replace('\u3000', '').strip(); tec = t.replace('\u3000', '').strip()
        ok = tec == tjc or all(x in tj and re.search(r'[\u4e00-\u9fff]', x) for x in runs) or ('■' in t and all(ch in tj for x in runs for ch in x))
        if ok: avi.append('texto japonés copiado del original (cita o censura): ' + ''.join(runs)[:12])
        else: err.append('letras japonesas: ' + ''.join(runs)[:12])
    if len(es) > MAXLEN: err.append('largo %d (máximo %d)' % (len(es), MAXLEN))
    n, largo = renglones(es)
    if n > LINES: err.append('%d renglones en una página (máximo %d)' % (n, LINES))
    if largo > 1000: err.append('con saltos mide %d (con más de ~1016 el juego se cierra)' % largo)
    if '[PENDIENTE]' in es: err.append('todavía dice [PENDIENTE]')
    for a, b in NOMBRES:
        if re.search(a, es): avi.append('nombre o término: %s → %s' % (re.search(a, es).group(0), b))
    for h in sorted(set(HONOR.findall(es))): avi.append('honorífico japonés: ' + h)
    if '「' in jp and '「' not in es: avi.append('diálogo sin 「」')
    if re.search(r'」\.', es): avi.append('punto después de 」')
    if '……' in es: avi.append('puntos dobles «……» (usar «…»)')
    if '　' in es: avi.append('espacio japonés (　)')
    return err, avi

def leer(path):
    with open(path, encoding='utf-8-sig', newline='') as f: txt = f.read()
    if path.lower().endswith('.tsv') or ('\t' in txt.splitlines()[0] and ',' not in txt.splitlines()[0]):
        rows = []
        for i, line in enumerate(txt.splitlines(), 1):
            if not line.strip() or line.startswith('id\t'): continue
            a, _, b = line.partition('\t'); rows.append({'id': a.strip(), 'spanish': b, '_linea': i})
        return rows, ['id', 'spanish'], 'tsv'
    rd = csv.DictReader(txt.splitlines(True)); rows = list(rd)
    for k, r in enumerate(rows, 2): r['_linea'] = k
    return rows, rd.fieldnames, 'csv'

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args: print(__doc__); input('Enter para salir...'); sys.exit(1)
    path = os.path.abspath(args[0]); fix = '--solo-revisar' not in sys.argv
    guion = None
    if '--guion' in sys.argv: guion = sys.argv[sys.argv.index('--guion') + 1]
    for g in [guion, os.path.join(HERE, 'kkk_script_BUENO.csv'), os.path.join(HERE, '..', 'KKK_tools_v3', 'kkk_script_BUENO.csv')]:
        if g and os.path.exists(g): guion = g; break
    ref = {}
    if guion:
        for r in csv.DictReader(open(guion, encoding='utf-8-sig')): ref[r['id']] = r['japanese']
    cargar_diccionario()
    rows, cols, kind = leer(path)
    carpeta = os.path.dirname(path); nombre = os.path.splitext(os.path.basename(path))[0]
    ext = '.tsv' if kind == 'tsv' else '.csv'
    f_corr = os.path.join(carpeta, nombre + '_CORREGIDO' + ext)
    f_inf = os.path.join(carpeta, nombre + '_INFORME.txt')
    f_err = os.path.join(carpeta, nombre + '_FILAS_CON_ERROR.csv')
    vistos = collections.Counter(r['id'].strip() for r in rows)
    malos, cuenta, arreglos, cuenta_arr = [], collections.Counter(), [], collections.Counter()
    for r in rows:
        i = r['id'].strip(); es = (r.get('spanish') or '')
        jp = r.get('japanese') or ref.get(i)
        if jp is None: malos.append((i, r['_linea'], ['id desconocido (no está en el guion)'], [])); continue
        if fix and es.strip():
            nuevo, hechos = corregir(jp, es)
            hechos = [h for h in hechos if h != 'espacios sobrantes']
            if hechos:
                arreglos.append((i, hechos, es.strip(), nuevo))
                for h in hechos: cuenta_arr['marca jindai repuesta' if 'jindai' in h else ('furigana traducida con el diccionario (revisar)' if h.startswith('furigana') else h)] += 1
            r['spanish'] = es = nuevo
        es = es.strip()
        if not es and i.isdigit() and int(i) in COPIA_OK: e, a = [], []
        elif not es: e, a = ['línea vacía (sin traducir)'], []
        else: e, a = revisar(jp, es, int(i) if i.isdigit() else None)
        if vistos[i] > 1: e.append('id repetido %d veces' % vistos[i])
        for x in e: cuenta['ERROR: ' + re.split(r' \(|: ', x)[0]] += 1
        for x in a: cuenta['aviso: ' + re.split(r' \(|: ', x)[0]] += 1
        if e or a: malos.append((i, r['_linea'], e, a))
    n_err = sum(1 for m in malos if m[2])
    f_furi = os.path.join(carpeta, nombre + '_FURIGANA_NUEVA.tsv'); nuevas = collections.OrderedDict()
    for r in rows:
        for m in re.finditer(r'(?:\{r:[^}]*\})+', r.get('spanish') or ''):
            nuevas.setdefault(clave(m.group(0)), r['id'].strip())
    if nuevas:
        with open(f_furi, 'w', encoding='utf-8') as f:
            f.write('clave\tespañol\tnota\n' + ''.join('%s\t\tid %s\n' % (k, i) for k, i in nuevas.items()))
    veredicto = ('LISTO PARA INTEGRAR (sin errores)' if n_err == 0 else
                 'NO INTEGRAR TODAVÍA: quedan %d filas con ERROR (ver %s)' % (n_err, os.path.basename(f_err)))
    if fix:
        with open(f_corr, 'w', encoding='utf-8-sig' if kind == 'csv' else 'utf-8', newline='') as f:
            ok_rows = rows
            if kind == 'tsv': f.write('id\tspanish\n' + ''.join('%s\t%s\n' % (r['id'], r['spanish']) for r in ok_rows))
            else:
                wr = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); wr.writeheader(); wr.writerows(ok_rows)
    with open(f_inf, 'w', encoding='utf-8') as f:
        f.write('INFORME DE REVISIÓN\n===================\nArchivo revisado: %s\n' % path)
        if fix: f.write('Archivo corregido: %s\n' % f_corr)
        f.write('Filas: %d\n\nRESULTADO: %s\n\n' % (len(rows), veredicto))
        f.write('1) LO QUE SE CORRIGIÓ SOLO: %d filas\n' % len(arreglos))
        f.write(''.join('   %5d  %s\n' % (v, k) for k, v in cuenta_arr.most_common()) or '   (nada)\n')
        f.write('\n2) LO QUE QUEDA (después de corregir)\n')
        f.write(''.join('   %5d  %s\n' % (v, k) for k, v in cuenta.most_common()) or '   (nada)\n')
        f.write('\n3) FILAS QUE QUEDAN CON ERROR O AVISO\n')
        for i, ln, e, a in malos:
            f.write('id %s (línea %s)\n' % (i, ln))
            for x in e: f.write('   ERROR  ' + x + '\n')
            for x in a: f.write('   aviso  ' + x + '\n')
        f.write('\n4) DETALLE DE CADA CORRECCIÓN AUTOMÁTICA\n')
        for i, h, antes, despues in arreglos:
            f.write('id %s: %s\n   antes:   %s\n   después: %s\n' % (i, '; '.join(h), antes[:200], despues[:200]))
    with open(f_err, 'w', encoding='utf-8-sig', newline='') as f:
        wr = csv.writer(f); wr.writerow(['id', 'errores', 'avisos', 'japanese', 'spanish'])
        by = {r['id'].strip(): r for r in rows}
        for i, ln, e, a in malos:
            if e: wr.writerow([i, ' | '.join(e), ' | '.join(a), ref.get(i, by.get(i, {}).get('japanese', '')), by.get(i, {}).get('spanish', '')])
    print()
    print('=' * 70)
    print(' INFORME FINAL')
    print('=' * 70)
    print(' Filas revisadas: %d' % len(rows))
    if fix:
        print(' Corregido automáticamente: %d filas' % len(arreglos))
        for k, v in cuenta_arr.most_common(): print('     %5d  %s' % (v, k))
    print(' Queda después de corregir:')
    for k, v in cuenta.most_common(): print('     %5d  %s' % (v, k))
    if not cuenta: print('     nada')
    print()
    if fix: print(' ARCHIVO CORREGIDO:  ' + f_corr)
    print(' INFORME:            ' + f_inf)
    if n_err: print(' FILAS CON ERROR:    ' + f_err)
    if nuevas: print(' FURIGANA NUEVA:     ' + f_furi + '  (%d sin traducir: llena la columna español y pégalas en diccionario_furigana.tsv)' % len(nuevas))
    sin_jp = any(not r.get('japanese') for r in rows)
    if not guion and sin_jp: print(' AVISO: no encontré kkk_script_BUENO.csv; solo se revisan filas que traen columna japanese.')
    print()
    print(' >>> ' + veredicto)
    print('=' * 70)
    if os.name == 'nt' and '--sin-abrir' not in sys.argv:
        try: os.system('explorer /select,"%s"' % (f_corr if fix else f_inf))
        except Exception: pass

if __name__ == '__main__': main()
