#!/usr/bin/env bash

DIR=`dirname "$0"`
ARCH=`uname -m`

if [ $ARCH = armv7l ] ; then
  ARCH=raspberrypi
else
  ARCH=maci64
fi

for NAME in buffer openbci2ft ; do
  URL=https://github.com/fieldtrip/fieldtrip/raw/master/realtime/bin/$ARCH/$NAME
  echo ------------------------------------------------------------------------------
  echo Downloading binary from $URL
  echo See http://www.fieldtriptoolbox.org/development/realtime for details
  echo ------------------------------------------------------------------------------
  wget $URL -O $DIR/buffer
done

