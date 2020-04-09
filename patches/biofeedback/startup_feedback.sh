#!/bin/bash

cd $HOME/eegsynth/patches/biofeedback
for MODULE in redis buffer bitalino2ft preprocessing biofeedback_panel; do
lxterminal -e ./$MODULE.sh
sleep 5
done

