#!/bin/bash
# RESPALDAR_ACTIVACION.sh - Kajiri Kamui Kagura en Steam Deck
# Úsalo UNA VEZ con el juego ya activado (que abra sin pedir disco). Guarda la activación
# junto a este archivo y en ~/kkk_respaldo. Cierra el juego antes de usarlo.

APPID_DEFECTO=2596824159
AQUI="$(cd "$(dirname "$0")" && pwd)"
COMPAT="$HOME/.local/share/Steam/steamapps/compatdata"
PT="flatpak run com.github.Matoking.protontricks"
aviso() { if command -v kdialog >/dev/null; then kdialog --title "KKK - Activación" --$1 "$2"; else echo "$2"; read -p "Enter para cerrar..."; fi; }

APPID="$APPID_DEFECTO"
if [ ! -d "$COMPAT/$APPID/pfx" ]; then
  APPID=$(grep -l -i "malie" "$COMPAT"/*/pfx/user.reg 2>/dev/null | head -1 | sed 's#.*/compatdata/\([0-9]*\)/.*#\1#')
fi
[ -z "$APPID" ] || [ ! -d "$COMPAT/$APPID/pfx" ] && { aviso error "No encontré la carpeta de Proton del juego."; exit 1; }
pgrep -f -i "malie" >/dev/null && { aviso error "Cierra el juego primero y vuelve a intentar."; exit 1; }

mkdir -p "$HOME/kkk_respaldo"; N=0
for par in 'light_deck_usuario.reg|HKCU\Software\light' 'light_deck_maquina.reg|HKLM\SOFTWARE\WOW6432Node\light'; do
  n="${par%%|*}"; k="${par#*|}"
  rm -f "$COMPAT/$APPID/pfx/drive_c/$n"
  $PT -c "wine reg export \"$k\" \"C:/$n\" /y" "$APPID" >/dev/null 2>&1
  if [ -s "$COMPAT/$APPID/pfx/drive_c/$n" ]; then
    cp "$COMPAT/$APPID/pfx/drive_c/$n" "$AQUI/$n"; cp "$COMPAT/$APPID/pfx/drive_c/$n" "$HOME/kkk_respaldo/$n"; N=$((N+1))
    rm -f "$COMPAT/$APPID/pfx/drive_c/$n"
  fi
done
if [ $N -gt 0 ]; then
  aviso msgbox "Listo: $N respaldo(s) guardado(s) aquí y en ~/kkk_respaldo.\nSi el juego vuelve a pedir el disco, usa RESTAURAR_ACTIVACION.sh.\n\nEstos archivos son tuyos: no los compartas."
else
  aviso error "No se pudo guardar el respaldo. ¿El juego ya está activado y Protontricks instalado?"
fi
