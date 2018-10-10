#!/bin/bash
clear
echo "starting shell script"

mate-terminal \
--tab --title="LaunchControl"   -e "bash -c 'python ../../module/launchcontrol/launchcontrol.py     -i launchcontrol.ini';bash" \
--tab --title="Spectral"        -e "bash -c 'python ../../module/spectral/spectral.py     -i spectral.ini';bash" \
--tab --title="HistoryControl"  -e "bash -c 'python ../../module/historycontrol/historycontrol.py   -i historycontrol.ini'; bash" \
--tab --title="Postprocessing"  -e "bash -c 'python ../../module/postprocessing/postprocessing.py   -i postprocessing.ini'; bash" \
--tab --title="Endorphines"     -e "bash -c 'python ../../module/endorphines/endorphines.py         -i endorphines.ini';    bash" \
--tab --title="PlotControl"     -e "bash -c 'python ../../module/plotcontrol/plotcontrol.py         -i plotcontrol.ini';    bash" \
--tab --title="Plotspectral"    -e "bash -c 'python ../../module/plotspectral/plotspectral.py         -i plotspectral.ini';    bash" \
--tab --title="Plotsignal"      -e "bash -c 'python ../../module/plotsignal/plotsignal.py         -i plotsignal.ini';    bash" \
--tab --title="OSC"      -e "bash -c 'python ../../module/outputosc/outputosc.py         -i outputosc.ini';    bash" \
--tab --title="keyboard"      -e "bash -c 'python ../../module/keyboard/keyboard.py         -i keyboard.ini';    bash" \
--tab --title="synchronization"      -e "bash -c 'python ../../module/synchronization/synchronization.py         -i synchronization.ini';    bash"

# --tab --title="Playbacksignal"   -e "bash -c 'python ../../module/playbacksignal/playbacksignal.py     -i playbacksignal.ini';bash" \
