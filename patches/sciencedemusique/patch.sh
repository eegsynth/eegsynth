#!/bin/bash
clear
echo "starting shell script"

mate-terminal \
--tab --title="Preprocessing"   -e "bash -c 'python ../../module/preprocessing/preprocessing.py        -i preprocessing.ini';      bash" \
--tab --title="Inputcontrol"    -e "bash -c 'python ../../module/inputcontrol/inputcontrol.py        -i inputcontrol.ini';      bash" \
--tab --title="Spectral"        -e "bash -c 'python ../../module/spectral/spectral.py                -i spectral.ini';          bash" \
--tab --title="HistoryControl"  -e "bash -c 'python ../../module/historycontrol/historycontrol.py    -i historycontrol.ini';    bash" \
--tab --title="Postprocessing"  -e "bash -c 'python ../../module/postprocessing/postprocessing.py    -i postprocessing.ini';    bash" \
--tab --title="pControl"        -e "bash -c 'python ../../module/plotcontrol/plotcontrol.py          -i plotcontrol.ini';       bash" \
--tab --title="pSpectral"       -e "bash -c 'python ../../module/plotspectral/plotspectral.py        -i plotspectral.ini';      bash" \
--tab --title="pSignal"         -e "bash -c 'python ../../module/plotsignal/plotsignal.py            -i plotsignal.ini';        bash" \
--tab --title="ShuttleControl"  -e "bash -c 'python ../../module/endorphines/endorphines.py           -i endorphines.ini';        bash" \
--tab --title="SlewLimiter"     -e "bash -c 'python ../../module/slewlimiter/slewlimiter.py           -i slewlimiter.ini';        bash"
