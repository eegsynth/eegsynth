REM this is a generic startup script for an EEGsynth module implemented in Python
REM it can be copied to any other file name

set rootdir=%userprofile%\eegsynth
set module=%~n0
set inidir=%~dp0
CALL conda activate EEGsynth
CALL %userprofile%\AppData\Local\Continuum\anaconda3\Scripts\activate EEGSynth
%rootdir%\bin\buffer.exe 1972 -new_console:t:"buffer1972"
%rootdir%\bin\buffer.exe 1973 -new_console:t:"buffer1972"

python %rootdir%\module\generatesignal\generatesignal.py -i %inidir%\generatesignal.ini -new_console:t:"generatesignal"
python %rootdir%\module\plotsignal\plotsignal.py -i %inidir%\plotsignal.ini -new_console:t:"plotsignal"


REM keep the command window open for debugging
pause
