"""estilos.py - los tres estilos de cuadro de texto del parche (data/screen/messageframe).
BARRA    = la barra de siempre (imagen barra_frame), 92 letras x 6 renglones.
ABAJO    = la imagen ORIGINAL del panel del juego, acostada como barra abajo (alto ajustable), 92 x 5.
ORIGINAL = el panel ORIGINAL de pie (estirado de 140 a 250 px), texto horizontal, 21 x 19.
Cada estilo cambia normal_l/c/r.svg y face_l/c/r.svg; no agrega imágenes nuevas."""
import re
ALTO_ABAJO = 150

BARRA_NORMAL = b'<svg width="1024px" height="600px" xmlns:a="http://www.adobe.com/svg10-extensions" xmlns:m="" xmlns:ui="">\r\n\t<defs>\r\n\t\t<filter id=\'Multiply\'>\r\n\t\t\t<feBlend mode=\'multiply\' in2=\'BackgroundImage\' in=\'SourceGraphic\'/>\r\n\t\t</filter>\r\n\t\t<filter id=\'Add\'>\r\n\t\t\t<feBlend mode=\'screen\' in2=\'BackgroundImage\' in=\'SourceGraphic\'/>\r\n\t\t</filter>\r\n\t</defs>\r\n\t<g id=\'hideframe\'>\r\n\t\t<image id=\'base\' x=\'13\' y=\'395\' width=\'998\' height=\'200\' xlink:href=\'./barra_frame.png\' opacity=\'1\'/>\r\n\t\t<ui:custom id=\'name\' x=\'40\' y=\'368\' width=\'400\' height=\'24\'/>\r\n\t\t<ui:custom id=\'message\' x=\'40\' y=\'410\' width=\'944\' height=\'170\'/>\r\n\t</g>\r\n</svg>\r\n'
BARRA_FACE = b'<svg width="1024px" height="600px" xmlns:a="http://www.adobe.com/svg10-extensions" xmlns:m="" xmlns:ui="">\r\n\t<defs>\r\n\t\t<filter id=\'Multiply\'>\r\n\t\t\t<feBlend mode=\'multiply\' in2=\'BackgroundImage\' in=\'SourceGraphic\'/>\r\n\t\t</filter>\r\n\t\t<filter id=\'Add\'>\r\n\t\t\t<feBlend mode=\'screen\' in2=\'BackgroundImage\' in=\'SourceGraphic\'/>\r\n\t\t</filter>\r\n\t</defs>\r\n\t<g id=\'hideframe\'>\r\n\t\t<image id=\'base\' x=\'13\' y=\'395\' width=\'998\' height=\'200\' xlink:href=\'./barra_frame.png\' opacity=\'1\'/>\r\n\t\t<image id=\'face_w\' transform=\'scale(0.5)\' x=\'50\' y=\'530\' width=\'256\' height=\'256\' xlink:href=\'./face_w.png\' opacity=\'1\'/>\r\n\t\t<ui:custom id=\'message\' x=\'40\' y=\'410\' width=\'944\' height=\'170\'/>\r\n\t\t<ui:custom id=\'name\' x=\'155\' y=\'368\' width=\'400\' height=\'24\'/>\r\n\t\t<ui:custom id=\'face\' x=\'25\' y=\'265\' width=\'120\' height=\'120\'/>\r\n\t</g>\r\n</svg>\r\n'

HEAD = """<svg width="1024px" height="600px" xmlns:a="http://www.adobe.com/svg10-extensions" xmlns:m="" xmlns:ui="">
\t<defs>
\t\t<filter id='Multiply'>
\t\t\t<feBlend mode='multiply' in2='BackgroundImage' in='SourceGraphic'/>
\t\t</filter>
\t\t<filter id='Add'>
\t\t\t<feBlend mode='screen' in2='BackgroundImage' in='SourceGraphic'/>
\t\t</filter>
\t</defs>
\t<g id='hideframe'>
%s
\t</g>
</svg>
"""

def _todos(normal, face):
    out = {}
    for p in 'lcr':
        out['normal_%s.svg' % p] = normal(p).encode('utf-8')
        out['face_%s.svg' % p] = face(p).encode('utf-8')
    return out

def barra(alto=None):
    out = {}
    for p in 'lcr':
        out['normal_%s.svg' % p] = BARRA_NORMAL; out['face_%s.svg' % p] = BARRA_FACE
    return dict(ancho=92, renglones=6, svgs=out)

def abajo(alto=ALTO_ABAJO):
    alto = max(120, min(220, int(alto))); top = 600 - alto
    img = ("\t\t<g transform='translate(0,600) rotate(-90)'>\n"
           "\t\t\t<image id='base' x='0' y='0' width='%d' height='1024' xlink:href='./normal_%%s_frame.png' opacity='1'/>\n"
           "\t\t</g>\n") % alto
    msg = "\t\t<ui:custom id='message' x='40' y='%d' width='944' height='%d'/>" % (top + 10, alto - 10)
    def normal(p):
        return HEAD % ((img % p) + "\t\t<ui:custom id='name' x='40' y='%d' width='400' height='24'/>\n" % (top - 26) + msg)
    def face(p):
        return HEAD % ((img % p) +
            "\t\t<image id='face_w' transform='scale(0.5)' x='50' y='%d' width='256' height='256' xlink:href='./face_w.png' opacity='1'/>\n" % (2 * (top - 130)) +
            msg + "\n\t\t<ui:custom id='name' x='155' y='%d' width='400' height='24'/>\n" % (top - 26) +
            "\t\t<ui:custom id='face' x='25' y='%d' width='120' height='120'/>" % (top - 130))
    renglones = max(3, (alto - 10) // 28)
    return dict(ancho=92, renglones=renglones, svgs=_todos(normal, face))

OX = {'l': 0, 'c': 387, 'r': 774}
def original(alto=None):
    def normal(p):
        x = OX[p]
        return HEAD % ("\t\t<image id='base' x='%d' y='0' width='250' height='600' xlink:href='./normal_%s_frame.png' opacity='1'/>\n"
                       "\t\t<ui:custom id='name' x='%d' y='24' width='222' height='24'/>\n"
                       "\t\t<ui:custom id='message' x='%d' y='56' width='222' height='534'/>" % (x, p, x + 14, x + 14))
    return dict(ancho=21, renglones=19, svgs=_todos(normal, normal))   # sin cara: no cabe en el panel

ESTILOS = {'BARRA': barra, 'ABAJO': abajo, 'ORIGINAL': original}

ANCHOS = {944: 92, 222: 21, 664: 64, 268: 26}      # ancho del área de texto -> letras por renglón
def detectar_ancho(svg):
    m = re.search(r"id='message'[^>]*width='(\d+)'", svg.decode('utf-8', 'replace'))
    return ANCHOS.get(int(m.group(1))) if m else None
