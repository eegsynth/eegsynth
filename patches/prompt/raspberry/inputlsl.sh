#!/bin/bash

# activate the Python3 environment with the required packages
PATH=/home/pi/miniconda3/bin:$PATH
source activate eegsynth3

export RTMIDI_API=MACOSX_CORE
export DYLD_LIBRARY_PATH=/System/Library/Frameworks/ImageIO.framework/Versions/A/Resources
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib

MODULE=`basename $0 .sh`

EEGSYNTH=$HOME/eegsynth
INIDIR=`dirname $0`

cd $INIDIR

$EEGSYNTH/module/$MODULE/$MODULE.py -i $INIDIR/$MODULE.ini
