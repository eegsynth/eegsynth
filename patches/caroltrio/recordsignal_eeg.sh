#!/bin/bash

export RTMIDI_API=MACOSX_CORE
export DYLD_LIBRARY_PATH=/System/Library/Frameworks/ImageIO.framework/Versions/A/Resources
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib

MODULE=recordsignal

EEGSYNTH=$HOME/eegsynth
PATCH=`dirname $0`

$EEGSYNTH/src/module/$MODULE/$MODULE.py -i $PATCH/recordsignal_eeg.ini
