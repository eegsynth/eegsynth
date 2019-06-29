#!/bin/bash

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`

if [ $DIR == '.' ] ; then 
  DIR=`pwd`
fi

cd $HOME/eegsynth/module/recordsignal
exec ./recordsignal.py -i $DIR/$NAME.ini
