#!/bin/bash
clear
echo "starting shell script"
conemu64.exe /bash "python3 ../../module/playbacksignal/playbacksignal.py -i playbacksignal.ini" -new_console:t:playbacksignal
#ConEmu64.exe -run -new_console:t:"buffer":c {EEGsynth} ../../module/buffer/buffer.sh
#ConEmu64.exe -run -new_console:t:"playbacksignal":c {EEGsynth} python3 ../../module/playbacksignal/playbacksignal.py -i playbacksignal.ini
#ConEmu64.exe -run -new_console:t:"preprocessing":c {EEGsynth} python3 ../../module/preprocessing/preprocessing.py -i preprocessing.ini
#ConEmu64.exe -run -new_console:t:"inputcontrol":c {EEGsynth} python3 ../../module/inputcontrol/inputcontrol.py -i inputcontrol.ini
#ConEmu64.exe -run -new_console:t:"spectral":c {EEGsynth} python3 ../../module/spectral/spectral.py -i spectral.ini
#ConEmu64.exe -run -new_console:t:"historycontrol":c {EEGsynth} python3 ../../module/historycontrol/historycontrol.py -i historycontrol.ini
#ConEmu64.exe -run -new_console:t:"postprocessing":c {EEGsynth} python3 ../../module/postprocessing/postprocessing.py -i postprocessing.ini
#ConEmu64.exe -run -new_console:t:"plotcontrol":c {EEGsynth} python3 ../../module/plotcontrol/plotcontrol.py -i plotcontrol.ini
#ConEmu64.exe -run -new_console:t:"plotspectral":c {EEGsynth} python3 ../../module/plotspectral/plotspectral.py -i plotspectral.ini
#ConEmu64.exe -run -new_console:t:"plotsignal":c {EEGsynth} python3 ../../module/plotsignal/plotsignal.py -i plotsignal.ini
#ConEmu64.exe -run -new_console:t:"endorphines":c {EEGsynth} python3 ../../module/endorphines/endorphines.py -i endorphines.ini
#ConEmu64.exe -run -new_console:t:"slewlimiter":c {EEGsynth} python3 ../../module/slewlimiter/slewlimiter.py -i slewlimiter.ini
