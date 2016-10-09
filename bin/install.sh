#!/usr/bin/env bash

DIR=`dirname "$0"`
OS=`uname -s`
MACHINE=`uname -m`

if [ $OS = Linux ] ; then
  if [ $MACHINE = i386 ] ; then
    ARCH=glnx86
  elif [ $MACHINE = x86_64 ] ; then
    ARCH=glnxa64
  elif [ $MACHINE = armv6l ] ; then
    ARCH=raspberrypi1
  elif [ $MACHINE = armv7l ] ; then
    ARCH=raspberrypi2
  elif [ $MACHINE = armv8l ] ; then
    ARCH=raspberrypi3
  fi
elif [ $OS = Darwin ] ; then
  if [ $MACHINE = i386 ] ; then
    ARCH=maci
  elif [ $MACHINE = x86_64 ] ; then
    ARCH=maci64
  fi
fi

if [ -z "$ARCH" ] ; then
  echo Error: cannot determine architecture for $OS on $MACHINE
  exit
else
  echo Downloading $ARCH binaries for $OS on $MACHINE
fi

for NAME in buffer openbci2ft jaga2ft ; do
  URL=https://github.com/fieldtrip/fieldtrip/raw/master/realtime/bin/$ARCH/$NAME
  echo ------------------------------------------------------------------------------
  echo Downloading binary from $URL
  echo See http://www.fieldtriptoolbox.org/development/realtime for details
  echo ------------------------------------------------------------------------------
  wget $URL -O $DIR/$NAME
  chmod +x $DIR/$NAME
done
