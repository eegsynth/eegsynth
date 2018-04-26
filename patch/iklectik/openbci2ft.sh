#!/bin/bash

MODULE=`basename $0 .sh`

EEGSYNTH=../../
INIDIR=`dirname $0`

$EEGSYNTH/module/$MODULE/$MODULE.sh -i $INIDIR/$MODULE.ini

