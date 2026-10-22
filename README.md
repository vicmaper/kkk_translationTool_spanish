# Kajiri Kamui Kagura — Traducción al español

Parche no oficial, hecho por fans y sin fines de lucro, que pone en español **神咒神威神楽 (Kajiri Kamui Kagura)**: todo el guion (27,864 mensajes), menús, configuración, fichas de personajes, cartas y extras.

> **Este parche NO incluye el juego.** Necesitas tu propia copia original. El instalador usa los archivos de TU juego y no reparte nada del original.

## ¿Qué versión necesito?
**Solo se probó con:** el DVD de Kajiri Kamui Kagura incluido en la caja **«Dies irae & WORLD BOX ~Masada Premium~» (2017)**, `malie.exe` versión 1.1.

El instalador revisa tu copia antes de tocar nada. Si es otra edición (2010, Akebono no Hikari 2013, etc.), te avisa y no cambia nada.
**¿Tienes otra edición?** Escríbenos en el [Discord](https://discord.gg/NV8TbQQ7B) (canal **#otras-versiones**) o abre un [Issue](../../issues/new/choose) con tu edición y el código que te muestra el instalador, e intentaremos adaptarlo.

## Descargar
Ve a **[Releases](../../releases)** y descarga el paquete completo `KKK_parche_es_vX.zip`. Trae el archivo grande `interfaz_es.dat`, que no está en el código de este repositorio.

## Instalar (Windows)
**Con la ventana (recomendado, no necesita Python):**
1. Descomprime el paquete y abre **`KKK_Traduccion.exe`**.
2. Pestaña **«Mi juego»** → **Examinar…** → elige la carpeta de tu juego (la que tiene `data1.dat` y `malie.exe`). Te dice si tu edición es la correcta.
3. Elige el **cuadro de texto** (ver abajo) → **Instalar / actualizar el parche**. Tarda unos 10 minutos.
4. Juega con **`malie_es.exe`**, que se crea dentro de la carpeta de tu juego.

**Con los .bat (necesita [Python](https://www.python.org/downloads/), marcando «Add python.exe to PATH»):**
arrastra la carpeta de tu juego encima de `INSTALAR.bat`, elige el cuadro de texto y espera a que diga **LISTO**.

**Quitar el parche:** en la ventana, **Quitar el parche**; o borra `data3.dat` y `malie_es.exe` de la carpeta del juego (si existe `data3_antes_del_parche.dat`, cámbiale el nombre a `data3.dat`). Tus archivos originales nunca se modifican.

**¿Descargaste el código en vez del Release?** Igual necesitas `interfaz_es.dat` del Release: cópialo a `parche/datos/`. Sin el `.exe`, abre la ventana con `ABRIR_GUI.bat` (requiere Python) o crea tu propio `.exe` con `CREAR_EXE.bat`.

## Cuadro de texto: 3 estilos
El juego original muestra el texto en vertical, en un panel angosto. El parche lo pone en **horizontal** y te deja elegir el cuadro:

| Estilo | Qué es | Letras × renglones | ¿Cabe todo? |
|---|---|---|---|
| **BARRA** (recomendado) | barra de lado a lado **hecha para este parche** | 92 × 6 | Sí |
| **ABAJO** | la **imagen original** del panel del juego, acostada como barra abajo; tapa menos la imagen | 92 × 5 | Sí |
| **ORIGINAL** | el **panel original de pie**, a un lado, como en japonés | 21 × 19 | 5 mensajes muy largos se cortan (ids 316, 4147, 4159, 4213 y 24262) |

Se puede cambiar cuando quieras sin reinstalar ni perder partidas: en la ventana (**Cambiar solo el cuadro de texto**) o arrastrando la carpeta del juego sobre `CAMBIAR_ESTILO.bat`. Con `GENERAR_ESTILOS.bat` puedes crear los tres a la vez y cambiar solo renombrando el archivo a `data3.dat`.

### Cómo se acomoda el texto (automático)
- **Los saltos de línea los pone el instalador solo**, según el estilo que elijas: corta entre palabras para que ningún renglón se pase. Tú no tienes que poner saltos.
- Si editas la traducción, el revisor (`REVISAR.bat` o el botón *Revisar formato*) corrige solo los detalles pequeños y te avisa de lo que debes arreglar a mano.
- **Los códigos entre `{ }` (tags)** son instrucciones para el juego. Esto es lo que pasa con cada uno:

| Código | Para qué sirve | ¿Automático? |
|---|---|---|
| `{n}` | salto de línea | **Sí**: el instalador los pone solo. Úsalo a mano solo si quieres un salto fijo (poemas). |
| `{v:…}` … `{/v}` | voz del personaje | **No los toques**: si faltan o cambian, el revisor marca error. |
| `{end}` | pausa / fin del mensaje | **No los toques**: debe haber los mismos que en el japonés; el revisor lo comprueba. |
| `{u0006}…` | letras antiguas (jindai) | El revisor **las vuelve a poner** si se pierden. |
| `{r:base\|lectura}` | furigana (lectura sobre el kanji) | El revisor traduce **solas** las conocidas; las nuevas te las marca. |

- El revisor también corrige solo: nombres sin macrón (Ryumei → Ryūmei), honoríficos (-sama → «señor»), puntos suspensivos, espacios y signos japoneses sueltos. Todo queda anotado en el `_INFORME.txt`.
- Límites del motor del juego que el revisor vigila:
  - **máximo 900 caracteres por mensaje** (con más, el juego se cierra);
  - el **mismo número de `{end}`** que el japonés (si no, el mensaje se corta);
  - no borrar ni mover lo que va entre `{ }` (voces, pausas, letras antiguas);
  - no usar Enter dentro de una celda: el salto manual es `{n}`.

## Steam Deck
Funciona con Proton. Guía, plantilla de controles y scripts para respaldar/restaurar la activación en [`steamdeck/`](steamdeck/).

## Glosario sin spoilers
Abre [`glosario/glosario_kkk.html`](glosario/glosario_kkk.html) en tu navegador: términos, personajes y música del juego, filtrados según el capítulo al que hayas llegado.

## Corregir o mejorar la traducción
Puedes editar cualquier texto:
- **En la ventana**, pestaña **«Editar la traducción»**: *Extraer de mi juego* → buscar y corregir → *Revisar formato* → *Integrar en el juego*.
- **Con los .bat:** `EXTRAER_CSV.bat` crea `mi_traduccion.csv`; edita solo la columna `spanish` (Excel o LibreOffice, CSV UTF-8); `INTEGRAR.bat` revisa y arma tu juego.

Las reglas de formato están en `LEEME_PRIMERO.txt`. **No compartas** tu `mi_traduccion.csv` ni `data3.dat`, porque llevan el texto japonés del juego. Si quieres compartir tus cambios, comparte solo la columna en español, o mejor, mándalos al Discord para incluirlos en la siguiente versión.

## Contenido del repositorio
| Carpeta | Qué es |
|---|---|
| `parche/` | Instalador, ventana (`herramientas/kkk_gui.py`, `ABRIR_GUI.bat`, `CREAR_EXE.bat`), cambio de estilo y herramientas (sin `interfaz_es.dat` ni el `.exe`, que van en Releases) |
| `parche/datos/traduccion_es.tsv` | La traducción (solo español) |
| `parche/datos/*_parche.json` | Diferencias que se aplican a TU `exec.dat` y `malie.exe` |
| `steamdeck/` | Guía, plantilla de controles y scripts para respaldar/restaurar la activación |
| `glosario/` | Glosario web sin spoilers |
| `desarrollo/` | Herramientas para quien quiera mantener el parche (integrar bloques, nombres «？？？», generar los 3 estilos a la vez) |

## Limitaciones conocidas
- **Solo se probó con la edición DVD 2017** (caja Dies irae & WORLD BOX, malie.exe 1.1). Con otras, el instalador no hace nada.
- **Estilo ORIGINAL:** 5 mensajes muy largos no caben completos en el panel angosto.
- **Letras antiguas (jindai moji):** se dejan como en el original, sin traducir, igual que en japonés.
- **Nombres:** la caja de nombre muestra «？？？» hasta que la historia revela al personaje, como en el original.
- Algunas escenas de Ryūsui muestran «…» a propósito: fue una decisión del equipo. La voz original se escucha igual.
- Los títulos de las canciones se dejan en japonés; su significado está en el glosario.
- **Videos desde Extras → Videos** pueden verse en negro: pasa igual sin el parche (es del juego). Dentro de la historia sí se ven.
- **Steam Deck:** la activación del juego no pasa de la PC a la Deck; hay que activarlo una vez con el disco (ver `steamdeck/`).

## Créditos
- **Juego original:** 神咒神威神楽 © light / Greenwood. Guion: Masada Takashi. Todos los derechos del juego son de sus dueños.
- **Dirección del proyecto, revisión y pruebas:** viper
- **Traducción, herramientas e interfaz:** hechas con asistencia de IA. Claude (Anthropic) hizo los borradores de la traducción, las herramientas de extracción y armado, y las imágenes de la interfaz. Todas las decisiones, la revisión y las pruebas en el juego las hizo viper. Se seguirá corrigiendo el estilo: reporta errores en el Discord.
- **Consultas y agradecimientos:** parche en inglés/chino de Akaruzi (kkk_r18_patch), consultado solo como referencia de sentido y de estructura del motor, sin copiar su redacción ni sus imágenes. VNDB y Nicopedia, para nombres y lecturas. GARbro.
- **Tipografías:** EB Garamond y Liberation Serif (SIL Open Font License).

## Contacto
- **Discord:** https://discord.gg/NV8TbQQ7B — ayuda, avisos de nuevas versiones y canal **#otras-versiones**.
- **GitHub Issues:** [reportar un error de traducción o pedir soporte para otra edición](../../issues/new/choose).
