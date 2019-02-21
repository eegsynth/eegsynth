#!/bin/bash

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`
MODULE=playbacksignal

if [ $DIR == '.' ] ; then
  DIR=`pwd`
fi

cd $HOME/eegsynth/module/$MODULE
exec ./$MODULE.py -i $DIR/$NAME.ini
