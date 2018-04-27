#!/bin/bash

export RTMIDI_API=MACOSX_CORE
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib

MODULE=`basename $0 .sh`

EEGSYNTH=$HOME/eegsynth
INIDIR=`dirname $0`

$EEGSYNTH/module/$MODULE/$MODULE.py -i $INIDIR/$MODULE.ini
