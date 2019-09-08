#!/bin/bash
clear
echo "starting shell script"

gnome-terminal \
--tab --title="Buffer"        -e "bash -c ' ./../../module/buffer/buffer.sh                -i buffer.ini';          bash" \
--tab --title="LSL2FT"        -e "bash -c 'python ../../module/lsl2ft/lsl2ft.py                -i lsl2ft.ini';          bash" \
--tab --title="Plotsignal"      -e "bash -c 'python ../../module/plotsignal/plotsignal.py            -i plotsignal.ini';        bash" \
--tab --title="Record Signal"        -e "bash -c 'python ../../module/recordsignal/recordsignal.py                -i recordsignal.ini';          bash" \
