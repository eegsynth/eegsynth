REM this is a generic startup script for an EEGsynth module implemented in Python
REM it can be copied to any other file name

set rootdir=%userprofile%\Documents\GitHub\eegsynth
set module=%~n0
set inidir=%~dp0
CALL %userprofile%\Anaconda3\condabin\conda.bat activate eegsynth3
python %rootdir%\module\%module%\%module%.py -i %inidir%\%module%.ini

REM keep the command window open for debugging
pause
