#!/bin/bash
clear
echo "starting shell script"

gnome-terminal \
--tab --title="Buffer"        -e "bash -c ' ./../../module/buffer/buffer.sh                -i buffer.ini';          bash" \
--tab --title="LSL2FT"        -e "bash -c 'python ../../module/lsl2ft/lsl2ft.py                -i lsl2ft.ini';          bash" \
--tab --title="Spectral"        -e "bash -c 'python ../../module/spectral_cbc/spectral_cbc.py                -i spectral_cbc.ini';          bash" \
--tab --title="Plotsignal"      -e "bash -c 'python ../../module/plotsignal/plotsignal.py            -i plotsignal.ini';        bash" \
--tab --title="Hurst"      -e "bash -c 'python ../../module/hurst/hurst.py            -i hurst.ini';        bash" \
--tab --title="OutputOSC"      -e "bash -c 'python ../../module/outputosc/outputosc.py            -i outputosc.ini';        bash" \
