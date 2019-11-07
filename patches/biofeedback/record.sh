#!/bin/bash

cd $HOME/eegsynth/patches/biofeedback
for MODULE in recordsignal recordtrigger; do
lxterminal -e ./$MODULE.sh
sleep 5
done

