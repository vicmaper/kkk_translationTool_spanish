#!/bin/bash
# RESTAURAR_ACTIVACION.sh - Kajiri Kamui Kagura en Steam Deck
# Úsalo cuando el juego vuelva a pedir el disco. Restaura la activación desde tu respaldo (.reg),
# sin disco y sin escribir comandos. Cierra el juego antes de usarlo.
# (Si es la primera vez y no tienes respaldo, usa antes RESPALDAR_ACTIVACION.sh con el juego ya activado.)

APPID_DEFECTO=2596824159
AQUI="$(cd "$(dirname "$0")" && pwd)"
COMPAT="$HOME/.local/share/Steam/steamapps/compatdata"
PT="flatpak run com.github.Matoking.protontricks"

aviso() {   # mensaje en ventana (o en la terminal si no hay kdialog)
  if command -v kdialog >/dev/null; then kdialog --title "KKK - Activación" --$1 "$2"; else echo "$2"; read -p "Enter para cerrar..."; fi
}

# 1) ¿dónde están los respaldos? junto a este archivo, o en ~/kkk_respaldo
REGS=()
for d in "$AQUI" "$HOME/kkk_respaldo"; do
  for f in "$d"/light_deck_usuario.reg "$d"/light_deck_maquina.reg; do [ -s "$f" ] && REGS+=("$f"); done
  [ ${#REGS[@]} -gt 0 ] && break
done
[ ${#REGS[@]} -eq 0 ] && { aviso error "No encontré el respaldo (light_deck_usuario.reg) junto a este archivo ni en ~/kkk_respaldo.\nActiva el juego con el disco y usa RESPALDAR_ACTIVACION.sh."; exit 1; }

# 2) ¿cuál es la carpeta (prefijo) del juego?
APPID="$APPID_DEFECTO"
if [ ! -d "$COMPAT/$APPID/pfx" ]; then
  APPID=$(grep -l -i "malie" "$COMPAT"/*/pfx/user.reg 2>/dev/null | head -1 | sed 's#.*/compatdata/\([0-9]*\)/.*#\1#')
fi
[ -z "$APPID" ] || [ ! -d "$COMPAT/$APPID/pfx" ] && { aviso error "No encontré la carpeta de Proton del juego.\nAbre el juego una vez desde Steam y vuelve a intentar."; exit 1; }

pgrep -f -i "malie" >/dev/null && { aviso error "Cierra el juego primero y vuelve a intentar."; exit 1; }

# 3) importar cada respaldo
OK=0
for f in "${REGS[@]}"; do
  n=$(basename "$f")
  cp "$f" "$COMPAT/$APPID/pfx/drive_c/$n" || continue
  $PT -c "wine reg import \"C:/$n\"" "$APPID" >/dev/null 2>&1 && OK=$((OK+1))
  rm -f "$COMPAT/$APPID/pfx/drive_c/$n"
done
if [ $OK -gt 0 ]; then
  aviso msgbox "Listo: activación restaurada ($OK archivo(s)).\nAbre Kajiri Kamui Kagura sin el disco.\n\nSi aún pide el disco, reactiva con el disco y usa RESPALDAR_ACTIVACION.sh."
else
  aviso error "No se pudo importar el respaldo.\n¿Está instalado Protontricks (Discover → Protontricks)?"
fi
