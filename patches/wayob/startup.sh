#!/bin/bash

# # this is needed to install the nvm application
# . $HOME/.nvm/nvm.sh
# nvm use v7.6.0
# 
# cd $HOME/eegsynth/interface
# /usr/local/bin/forever -w start index.js
#
# for MODULE in launchcontrol playbackctrl postprocessing outputartnet ; do
# $HOME/eegsynth/module/$MODULE/$MODULE.sh start
# sleep 3
# done

cd $HOME/eegsynth/patches/wayob
for MODULE in launchcontrol playbackcontrol postprocessing outputartnet ; do
./$MODULE.sh
sleep 3
done

