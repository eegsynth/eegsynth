#!/bin/bash

MODULE=`basename $0 .sh`

EEGSYNTH=$HOME/eegsynth
PATCH=`dirname $0`

$EEGSYNTH/src/module/$MODULE/$MODULE.sh -i $PATCH/$MODULE.ini
