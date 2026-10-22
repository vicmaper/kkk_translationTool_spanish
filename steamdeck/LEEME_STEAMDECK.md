# Kajiri Kamui Kagura en español en Steam Deck

Probado en una Steam Deck con Proton Experimental: texto, menús, videos, guardar/cargar y controles funcionan.

## 1. Preparar el juego (en la PC)
1. Instala el parche en tu PC con `INSTALAR.bat` (ver el README principal).
2. Copia la carpeta del juego completa (con `data3.dat` y `malie_es.exe`) a la Deck, por ejemplo a `/home/deck/Games/KKK` (USB, microSD o red).

## 2. Agregarlo a Steam (Modo Escritorio)
1. Steam → **Juegos → Agregar un juego que no es de Steam** → busca `malie_es.exe`.
2. Clic derecho en el juego → **Propiedades**:
   - Nombre: `Kajiri Kamui Kagura`
   - Opciones de lanzamiento: `LANG=ja_JP.UTF-8 %command%`
   - **Compatibilidad** → forzar **Proton Experimental**.

## 3. Activación
La activación de tu PC no pasa a la Deck. La primera vez:
1. Conecta un lector de DVD USB con el disco original.
2. Abre el juego: aparece la ventana **プロダクトID入力** (código de producto).
3. Escribe **tu** código (teclado en pantalla: **STEAM + X**) y pulsa **登録**.
4. Desde ahí funciona **sin disco**.

## 4. Controles (opcional)
Plantilla incluida: `controller_neptune_kkk.vdf`.
```
mkdir -p ~/.local/share/Steam/controller_base/templates && cp ~/Downloads/controller_neptune_kkk.vdf ~/.local/share/Steam/controller_base/templates/
```
Reinicia Steam → en el juego: botón del control → **Distribución → Plantillas → «Kajiri Kamui Kagura (ES)»**.
(Que Steam la cargue desde esa carpeta no está probado todavía. Si no aparece, configúrala a mano con esta tabla.)

| Botón | Acción |
|---|---|
| A / R4 | Avanzar (clic izquierdo) |
| B / Start / LT | Menú (clic derecho) |
| Y / L1 / Cruceta ↑ | Historial (rueda arriba) |
| R1 / Cruceta ↓ | Siguiente (rueda abajo) |
| RT (mantener) / L4 | Saltar texto (Ctrl) |
| Stick derecho / trackpad derecho | Cursor y clic |

## Actualizar la traducción
Copia solo el `data3.dat` nuevo encima del anterior. Tus partidas no se pierden.

## Si un día vuelve a pedir el disco (activación perdida)
Incluye dos archivos para no escribir comandos (Modo Escritorio, en la carpeta del juego):
- `RESPALDAR_ACTIVACION.sh`: úsalo **una vez** con el juego ya activado. Guarda tu activación en `~/kkk_respaldo`.
- `RESTAURAR_ACTIVACION.sh`: úsalo cuando vuelva a pedir el disco. Restaura la activación sin disco.

Antes del primer uso: clic derecho en cada uno → **Propiedades → Permisos → «Es ejecutable»**. Luego doble clic → **Ejecutar** (con el juego cerrado). Necesitan Protontricks (Discover → Protontricks).
No uses «Borrar datos de compatibilidad» en Steam: eso borra la activación. Tus archivos `.reg` son tuyos: no los compartas.
