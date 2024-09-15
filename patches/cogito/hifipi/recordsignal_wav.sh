#!/bin/bash

PATCH=`dirname "$0"`
MODULE=`basename "$0" .sh`

if [ $PATCH == '.' ] ; then 
  PATCH=`pwd`
fi

cd $HOME/eegsynth/src/module/recordsignal
exec ./recordsignal.py -i $PATCH/$MODULE.ini

