#!/bin/bash

PATCH=`dirname "$0"`
MODULE=`basename "$0" .sh`

if [ $PATCH == '.' ] ; then 
  PATCH=`pwd`
fi

cd $HOME/eegsynth/src/module/$MODULE
exec ./$MODULE.sh -i $PATCH/$MODULE.ini
