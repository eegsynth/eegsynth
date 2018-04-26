#!/bin/bash
clear
echo "starting shell script"

mate-terminal \
--tab --title="LaunchControl"   -e "bash -c 'python ../module/launchcontrol/launchcontrol.py     -i launchcontrol.ini';bash" \
--tab --title="Spectral"        -e "bash -c 'python ../module/spectral/spectral.py     -i spectral.ini';bash" \
--tab --title="HistoryControl"  -e "bash -c 'python ../module/historycontrol/historycontrol.py   -i historycontrol.ini'; bash" \
--tab --title="Postprocessing"  -e "bash -c 'python ../module/postprocessing/postprocessing.py   -i postprocessing.ini'; bash" \
--tab --title="Endorphines"     -e "bash -c 'python ../module/endorphines/endorphines.py         -i endorphines.ini';    bash" \
--tab --title="PlotControl"     -e "bash -c 'python ../module/plotcontrol/plotcontrol.py         -i plotcontrol.ini';    bash" \
--tab --title="Plotfreq"        -e "bash -c 'python ../module/plotfreq/plotfreq.py         -i plotfreq.ini';    bash" \
--tab --title="Plotsignal"      -e "bash -c 'python ../module/plotsignal/plotsignal.py         -i plotsignal.ini';    bash"
--tab --title="Plotfreq"      -e "bash -c 'python ../module/plotfreq/plotfreq.py         -i plotfreq.ini';    bash"

