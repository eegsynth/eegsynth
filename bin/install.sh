#!/usr/bin/env bash

DIR=`dirname "$0"`
OS=`uname -s`
MACHINE=`uname -m`

if [ $OS = Linux ] ; then
  if [ $MACHINE = armv7l ] ; then
    # Rasperry Pi version 2 or 2+
    ARCH=raspberrypi
  elif [ $MACHINE = armv6l ] ; then
    # Rasperry Pi version 1
    ARCH=raspberrypi
  elif [ $MACHINE = x86_64 ] ; then
    ARCH=glnxa64
  elif [ $MACHINE = i386 ] ; then
    ARCH=glnx86
  fi
elif [ $OS = Darwin ] ; then
  if [ $MACHINE = x86_64 ] ; then
    ARCH=maci64
  elif [ $MACHINE = i386 ] ; then
    ARCH=maci
  fi
fi

if [ -z "$ARCH" ] ; then
  echo Error: cannot determine architecture for $OS on $MACHINE
  exit
else
  echo Downloading $ARCH binaries for $OS on $MACHINE
fi

for NAME in buffer openbci2ft ; do
  URL=https://github.com/fieldtrip/fieldtrip/raw/master/realtime/bin/$ARCH/$NAME
  echo ------------------------------------------------------------------------------
  echo Downloading binary from $URL
  echo See http://www.fieldtriptoolbox.org/development/realtime for details
  echo ------------------------------------------------------------------------------
  wget $URL -O $DIR/$NAME
  chmod +x $DIR/$NAME
done
