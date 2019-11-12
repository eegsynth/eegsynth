#!/bin/bash

cd $HOME/eegsynth/patches/biofeedback
for MODULE in redis buffer bitalino2ft plotsignal spectralfeedback; do
lxterminal -e ./$MODULE.sh
sleep 5
done

