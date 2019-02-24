#!/bin/bash

export RTMIDI_API=MACOSX_CORE
export DYLD_LIBRARY_PATH=/System/Library/Frameworks/ImageIO.framework/Versions/A/Resources
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib

MODULE=recordsignal

EEGSYNTH=$HOME/eegsynth
INIDIR=`dirname $0`

$EEGSYNTH/module/$MODULE/$MODULE.py -i $INIDIR/recordsignal_sound.ini
