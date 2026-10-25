#!/usr/bin/env python3
"""kkk_gui.py - Kajiri Kamui Kagura en español: instalador y editor con ventana.

Se abre con ABRIR_GUI.bat (o con KKK_Traduccion.exe si lo creaste con CREAR_EXE.bat).
Hace lo mismo que los .bat: instalar el parche, cambiar el cuadro de texto, extraer / editar /
revisar / integrar la traducción. Nunca modifica data1.dat, data2.dat ni malie.exe.
"""
import sys, os, io, re, csv, json, hashlib, threading, queue, contextlib, traceback, webbrowser, shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---------- carpetas (funciona igual como .py o como .exe) ----------
if getattr(sys, 'frozen', False):
    BASE = os.path.dirname(sys.executable)                 # el .exe va en la carpeta del parche
else:
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERR = os.path.join(BASE, 'herramientas'); DATOS = os.path.join(BASE, 'datos')
sys.path.insert(0, HERR)
import armar, extraer, cambiar_estilo, kkk_revisar, estilos      # noqa: E402
from kkk_extraer import Dat                                       # noqa: E402
for m in (armar, extraer, cambiar_estilo, kkk_revisar):           # que usen las carpetas reales, no las del .exe
    m.HERE = HERR
    if hasattr(m, 'RAIZ'): m.RAIZ = BASE
armar.DATOS = DATOS

DISCORD = 'https://discord.gg/k3Zfp85jMr'
GITHUB = 'https://github.com/vicmaper/kkk_translationTool_spanish'
CONFIG = os.path.join(BASE, 'kkk_gui_config.json')
VERSION_TXT = ('Este parche es para: Kajiri Kamui Kagura, DVD de la caja «Dies irae & WORLD BOX ~Masada Premium~» '
               '(2017), malie.exe versión 1.1.\nCon otras ediciones no se probó y puede no funcionar: si tienes otra, '
               'escríbenos en el Discord (#otras-versiones) con el código de tu versión que aparece abajo.')
ESTILOS_TXT = {'BARRA': 'BARRA (recomendado): barra de lado a lado hecha para este parche. 92 letras x 6 renglones: cabe todo el texto.',
               'ABAJO': 'ABAJO: la imagen original del panel del juego, acostada como barra abajo. 92 x 5: cabe todo y tapa menos la imagen.',
               'ORIGINAL': 'ORIGINAL: el panel original de pie, a un lado (como el juego en japonés). 21 x 19: 5 mensajes muy largos se cortan.'}

def md5(b): return hashlib.md5(b).hexdigest()

class Salida(io.TextIOBase):
    def __init__(self, q): self.q = q
    def write(self, s): self.q.put(s); return len(s)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Kajiri Kamui Kagura — Traducción al español'); self.geometry('1000x720'); self.minsize(760, 560)
        self.q = queue.Queue(); self.ocupado = False
        self.cfg = self.leer_cfg()
        self.juego = tk.StringVar(value=self.cfg.get('juego', ''))
        self.estilo = tk.StringVar(value=self.cfg.get('estilo', 'BARRA'))
        self.alto = tk.IntVar(value=self.cfg.get('alto', estilos.ALTO_ABAJO))
        self.csv_path = None; self.filas = []; self.idx = {}
        nb = ttk.Notebook(self); nb.pack(fill='both', expand=True, padx=8, pady=(8, 0))
        self.tab_juego(nb); self.tab_traduccion(nb); self.tab_ayuda(nb)
        frm = ttk.LabelFrame(self, text='Mensajes'); frm.pack(fill='x', padx=8, pady=8)
        self.log = tk.Text(frm, height=9, wrap='word', state='disabled'); self.log.pack(fill='x', padx=4, pady=4)
        self.after(100, self.vaciar)
        if self.juego.get(): self.comprobar()

    # ---------- configuración ----------
    def leer_cfg(self):
        try: return json.load(open(CONFIG, encoding='utf-8'))
        except Exception: return {}
    def guardar_cfg(self):
        try: json.dump({'juego': self.juego.get(), 'estilo': self.estilo.get(), 'alto': self.alto.get()},
                       open(CONFIG, 'w', encoding='utf-8'))
        except Exception: pass

    # ---------- pestaña 1: juego ----------
    def tab_juego(self, nb):
        t = ttk.Frame(nb); nb.add(t, text='1. Mi juego')
        ttk.Label(t, text=VERSION_TXT, wraplength=1000, justify='left').pack(anchor='w', padx=10, pady=10)
        f = ttk.Frame(t); f.pack(fill='x', padx=10)
        ttk.Label(f, text='Carpeta del juego (la que tiene data1.dat y malie.exe):').pack(anchor='w')
        r = ttk.Frame(f); r.pack(fill='x', pady=4)
        ttk.Button(r, text='Comprobar', command=self.comprobar).pack(side='right')
        ttk.Button(r, text='Examinar…', command=self.examinar).pack(side='right', padx=4)
        ttk.Entry(r, textvariable=self.juego).pack(side='left', fill='x', expand=True)
        self.estado = ttk.Label(t, text='Elige la carpeta del juego.', justify='left', font=('Segoe UI', 10, 'bold'))
        self.estado.pack(anchor='w', padx=10, pady=6)
        e = ttk.LabelFrame(t, text='Cuadro de texto'); e.pack(fill='x', padx=10, pady=6)
        for k, txt in ESTILOS_TXT.items():
            ttk.Radiobutton(e, text=txt, value=k, variable=self.estilo).pack(anchor='w', padx=6)
        a = ttk.Frame(e); a.pack(anchor='w', padx=6, pady=4)
        ttk.Label(a, text='Alto de ABAJO (px, 120–220):').pack(side='left')
        ttk.Spinbox(a, from_=120, to=220, increment=10, textvariable=self.alto, width=6).pack(side='left', padx=4)
        b = ttk.Frame(t); b.pack(fill='x', padx=10, pady=10)
        ttk.Button(b, text='Instalar / actualizar el parche', command=self.instalar).pack(side='left')
        ttk.Button(b, text='Cambiar solo el cuadro de texto', command=self.cambiar).pack(side='left', padx=6)
        ttk.Button(b, text='Quitar el parche', command=self.quitar).pack(side='left')
        ttk.Label(t, text='Instalar tarda unos 10 minutos. Después juega con malie_es.exe (se crea en la carpeta del juego).\n'
                          'Los saltos de línea se acomodan solos al cuadro de texto que elijas: no tienes que hacer nada.\n'
                          'Cambiar el cuadro de texto conserva tu traducción y deja respaldo (data3_antes_estilo.dat).',
                  justify='left', wraplength=1000).pack(anchor='w', padx=10)

    def examinar(self):
        d = filedialog.askdirectory(title='Carpeta del juego')
        if d: self.juego.set(os.path.normpath(d)); self.guardar_cfg(); self.comprobar()

    def comprobar(self):
        j = self.juego.get().strip()
        d1 = os.path.join(j, 'data1.dat'); exe = os.path.join(j, 'malie.exe')
        if not os.path.exists(d1):
            self.estado.config(text='✗ No encontré data1.dat en esa carpeta.'); return False
        try:
            dat = Dat(d1); i = dat.find('data/system/exec.dat'); n, fl, a, size = dat.ents[i]
            m1 = md5(dat.read(dat.base + dat.offs[a] * 1024, size))
        except Exception as ex:
            self.estado.config(text='✗ No pude leer data1.dat: %s' % ex); return False
        m2 = md5(open(exe, 'rb').read()) if os.path.exists(exe) else '(no hay malie.exe)'
        ok = m1 == armar.EXEC_MD5
        txt = ('✓ Edición correcta.' if ok else '✗ Esta edición no es la probada: el parche no se instalará.')
        txt += '\nCódigo de tu versión → exec.dat: %s   malie.exe: %s' % (m1, m2)
        if os.path.exists(os.path.join(j, 'data3.dat')): txt += '\nYa hay un data3.dat (si es del parche, puedes cambiar el cuadro de texto).'
        self.estado.config(text=txt); self.guardar_cfg(); return ok

    def correr(self, fn, argv, al_final=None):
        if self.ocupado: messagebox.showinfo('Espera', 'Ya hay una tarea en curso.'); return
        self.ocupado = True; self.config(cursor='watch'); self.escribir('\n▶ %s\n' % ' '.join(argv[1:]))
        def trabajo():
            viejo = sys.argv; sys.argv = argv; ok = True
            try:
                with contextlib.redirect_stdout(Salida(self.q)), contextlib.redirect_stderr(Salida(self.q)):
                    fn()
            except SystemExit as e:
                if e.code not in (None, 0): self.q.put('\n%s\n' % e.code); ok = False
            except Exception:
                self.q.put(traceback.format_exc()); ok = False
            finally:
                sys.argv = viejo
            self.q.put(('fin', ok, al_final))
        threading.Thread(target=trabajo, daemon=True).start()

    def vaciar(self):
        try:
            while True:
                x = self.q.get_nowait()
                if isinstance(x, tuple):
                    self.ocupado = False; self.config(cursor='')
                    self.escribir('\n%s\n' % ('✓ Terminado.' if x[1] else '✗ Hubo un problema (lee los mensajes de arriba).'))
                    if x[2]: x[2](x[1])
                else: self.escribir(x)
        except queue.Empty: pass
        self.after(100, self.vaciar)

    def escribir(self, s):
        self.log.config(state='normal'); self.log.insert('end', s); self.log.see('end'); self.log.config(state='disabled')

    def args_estilo(self):
        self.guardar_cfg(); return ['--estilo', self.estilo.get(), '--alto', str(self.alto.get())]

    def instalar(self, tsv=None):
        if not self.comprobar(): messagebox.showerror('Edición', 'Revisa la carpeta del juego.'); return
        argv = ['armar.py', self.juego.get()] + (['--tsv', tsv] if tsv else []) + self.args_estilo()
        self.correr(armar.main, argv, lambda ok: ok and messagebox.showinfo('Listo', 'Listo. Juega con malie_es.exe.'))

    def cambiar(self):
        if not self.comprobar(): return
        if not os.path.exists(os.path.join(self.juego.get(), 'data3.dat')):
            messagebox.showerror('Sin parche', 'Primero instala el parche.'); return
        self.correr(cambiar_estilo.main, ['cambiar_estilo.py', self.juego.get(), self.estilo.get(), '--alto', str(self.alto.get())])

    def quitar(self):
        j = self.juego.get()
        if not messagebox.askyesno('Quitar el parche', 'Se borran data3.dat y malie_es.exe de la carpeta del juego.\n'
                                   'Si existe data3_antes_del_parche.dat, vuelve a ser data3.dat.\n¿Continuar?'): return
        for f in ('data3.dat', 'malie_es.exe'):
            p = os.path.join(j, f)
            if os.path.exists(p): os.remove(p)
        a = os.path.join(j, 'data3_antes_del_parche.dat')
        if os.path.exists(a): os.rename(a, os.path.join(j, 'data3.dat'))
        self.escribir('\nParche quitado. El juego vuelve a estar en japonés.\n')

    # ---------- pestaña 2: traducción ----------
    def tab_traduccion(self, nb):
        t = ttk.Frame(nb); nb.add(t, text='2. Editar la traducción')
        b = ttk.Frame(t); b.pack(fill='x', padx=6, pady=6)
        ttk.Button(b, text='Extraer de mi juego', command=self.extraer).pack(side='left')
        ttk.Button(b, text='Abrir CSV…', command=self.abrir).pack(side='left', padx=4)
        ttk.Button(b, text='Guardar', command=self.guardar).pack(side='left')
        ttk.Button(b, text='Revisar formato', command=self.revisar).pack(side='left', padx=4)
        ttk.Button(b, text='Integrar en el juego', command=self.integrar).pack(side='left')
        ttk.Label(b, text='   Buscar:').pack(side='left')
        self.buscar = tk.StringVar(); e = ttk.Entry(b, textvariable=self.buscar, width=28); e.pack(side='left')
        e.bind('<Return>', lambda ev: self.filtrar())
        ttk.Button(b, text='Buscar', command=self.filtrar).pack(side='left', padx=2)
        self.archivo = ttk.Label(t, text='Ningún archivo abierto.'); self.archivo.pack(anchor='w', padx=6)
        p = ttk.PanedWindow(t, orient='vertical'); p.pack(fill='both', expand=True, padx=6, pady=4)
        f1 = ttk.Frame(p); p.add(f1, weight=3)
        self.tv = ttk.Treeview(f1, columns=('id', 'jp', 'es'), show='headings', selectmode='browse')
        for c, w, h in (('id', 70, 'id'), ('jp', 420, 'Japonés'), ('es', 520, 'Español')):
            self.tv.heading(c, text=h); self.tv.column(c, width=w, stretch=(c != 'id'))
        sb = ttk.Scrollbar(f1, command=self.tv.yview); self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side='left', fill='both', expand=True); sb.pack(side='left', fill='y')
        self.tv.bind('<<TreeviewSelect>>', self.mostrar)
        f2 = ttk.Frame(p); p.add(f2, weight=2)
        self.jp = tk.Text(f2, height=4, wrap='word', state='disabled', background='#f2f2f2'); self.jp.pack(fill='x')
        self.es = tk.Text(f2, height=5, wrap='word', undo=True); self.es.pack(fill='both', expand=True, pady=4)
        r = ttk.Frame(f2); r.pack(fill='x')
        ttk.Button(r, text='Aplicar cambio a esta fila', command=self.aplicar).pack(side='left')
        self.aviso = ttk.Label(r, text='', foreground='#a33'); self.aviso.pack(side='left', padx=10)
        ttk.Label(f2, text='No borres ni muevas lo que va entre { }. {end} debe quedar igual que en el japonés; {n} = salto de línea.',
                  foreground='#555').pack(anchor='w')

    def extraer(self):
        if not self.comprobar(): return
        out = os.path.join(BASE, 'mi_traduccion.csv')
        self.correr(extraer.main, ['extraer.py', self.juego.get(), out], lambda ok: ok and self.cargar(out))

    def abrir(self):
        p = filedialog.askopenfilename(title='Abrir traducción', filetypes=[('CSV o TSV', '*.csv *.tsv'), ('Todos', '*.*')])
        if p: self.cargar(p)

    def cargar(self, p):
        try:
            if p.lower().endswith('.tsv'):
                filas = []
                for line in open(p, encoding='utf-8-sig'):
                    line = line.rstrip('\r\n')
                    if not line or line.startswith('id\t'): continue
                    k, _, v = line.partition('\t'); filas.append({'id': k, 'voice': '', 'japanese': '', 'spanish': v, 'status': 'draft'})
            else:
                filas = list(csv.DictReader(open(p, encoding='utf-8-sig', newline='')))
        except Exception as ex:
            messagebox.showerror('Error', 'No pude abrir el archivo:\n%s' % ex); return
        self.csv_path = p; self.filas = filas; self.idx = {r['id']: r for r in filas}
        self.archivo.config(text='Archivo: %s  (%d filas)' % (p, len(filas))); self.filtrar()

    def filtrar(self):
        self.tv.delete(*self.tv.get_children())
        q = self.buscar.get().strip().lower(); n = 0
        for r in self.filas:
            if q and q not in r.get('spanish', '').lower() and q not in r.get('japanese', '').lower() and q != r['id']: continue
            self.tv.insert('', 'end', iid=r['id'], values=(r['id'], r.get('japanese', '')[:120], r.get('spanish', '')[:150]))
            n += 1
            if n >= 3000 and q: break
        if q: self.escribir('\nBúsqueda «%s»: %d resultado(s)%s.\n' % (q, n, ' (se muestran los primeros 3000)' if n >= 3000 else ''))

    def mostrar(self, ev=None):
        s = self.tv.selection()
        if not s: return
        r = self.idx[s[0]]
        self.jp.config(state='normal'); self.jp.delete('1.0', 'end'); self.jp.insert('1.0', r.get('japanese', '')); self.jp.config(state='disabled')
        self.es.delete('1.0', 'end'); self.es.insert('1.0', r.get('spanish', '')); self.revisar_fila(r)

    def revisar_fila(self, r):
        es, jp = r.get('spanish', ''), r.get('japanese', ''); av = []
        if len(es) > 900: av.append('más de 900 caracteres')
        if jp and es and es.count('{end}') != jp.count('{end}'): av.append('{end}: %d (japonés %d)' % (es.count('{end}'), jp.count('{end}')))
        if '\n' in es: av.append('tiene Enter: usa {n}')
        self.aviso.config(text=' · '.join(av))

    def aplicar(self):
        s = self.tv.selection()
        if not s: return
        r = self.idx[s[0]]; r['spanish'] = self.es.get('1.0', 'end-1c').replace('\r', '')
        if r['spanish'].strip() and r.get('status', '') == 'untranslated': r['status'] = 'draft'
        self.tv.item(s[0], values=(r['id'], r.get('japanese', '')[:120], r['spanish'][:150])); self.revisar_fila(r)

    def guardar(self):
        if not self.csv_path: return
        p = self.csv_path if self.csv_path.lower().endswith('.csv') else os.path.splitext(self.csv_path)[0] + '.csv'
        with open(p, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['id', 'voice', 'japanese', 'spanish', 'status'], extrasaction='ignore')
            w.writeheader(); w.writerows(self.filas)
        self.csv_path = p; self.escribir('\nGuardado: %s\n' % p)

    def revisar(self, despues=None):
        if not self.csv_path: messagebox.showinfo('Sin archivo', 'Primero extrae o abre una traducción.'); return
        self.guardar()
        def fin(ok):
            corr = os.path.splitext(self.csv_path)[0] + '_CORREGIDO.csv'
            err = os.path.splitext(self.csv_path)[0] + '_FILAS_CON_ERROR.csv'
            hay_err = os.path.exists(err) and sum(1 for _ in open(err, encoding='utf-8-sig')) > 1
            if hay_err: messagebox.showwarning('Revisión', 'Hay errores. Mira:\n%s' % err)
            elif despues and os.path.exists(corr): despues(corr)
        self.correr(kkk_revisar.main, ['kkk_revisar.py', self.csv_path, '--sin-abrir'], fin)

    def integrar(self):
        if not self.comprobar(): return
        self.revisar(despues=lambda corr: self.instalar(tsv=corr))

    # ---------- pestaña 3: ayuda ----------
    def tab_ayuda(self, nb):
        t = ttk.Frame(nb); nb.add(t, text='3. Ayuda y contacto')
        txt = ('Kajiri Kamui Kagura — traducción al español (parche de fans, sin fines de lucro).\n\n'
               '• Este programa no incluye el juego: usa los archivos de TU copia original.\n'
               '• No compartas data3.dat, mi_traduccion.csv ni archivos del juego: llevan el texto original.\n'
               '• ¿Errores, dudas u otra edición del juego? Escríbenos en el Discord o abre un «Issue» en GitHub.\n\n'
               'Créditos: juego © light / Greenwood, guion de Masada Takashi. Dirección, revisión y pruebas: viper.\n'
               'Traducción, herramientas e interfaz hechas con asistencia de IA (Claude, Anthropic); revisadas y probadas por viper.')
        ttk.Label(t, text=txt, wraplength=1000, justify='left').pack(anchor='w', padx=12, pady=12)
        ttk.Button(t, text='Abrir el Discord', command=lambda: webbrowser.open(DISCORD)).pack(anchor='w', padx=12, pady=2)
        ttk.Button(t, text='Abrir GitHub (descargas e Issues)', command=lambda: webbrowser.open(GITHUB)).pack(anchor='w', padx=12, pady=2)
        g = os.path.join(os.path.dirname(BASE), 'glosario', 'glosario_kkk.html')
        g = g if os.path.exists(g) else os.path.join(BASE, 'glosario_kkk.html')
        ttk.Button(t, text='Abrir el glosario sin spoilers', command=lambda: webbrowser.open('file:///' + g.replace('\\', '/'))).pack(anchor='w', padx=12, pady=2)

if __name__ == '__main__':
    App().mainloop()
