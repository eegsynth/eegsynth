#!/bin/bash

MODULE=`basename $0 .sh`

EEGSYNTH=$HOME/eegsynth
INIDIR=`dirname $0`

$EEGSYNTH/module/$MODULE/$MODULE.py -i $INIDIR/$MODULE.ini
