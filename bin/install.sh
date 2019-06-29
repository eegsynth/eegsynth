#!/usr/bin/env bash
#
# This script can be used to download the required binary dependencies.
#

DIR=`dirname "$0"`
OS=`uname -s`
MACHINE=`uname -m`
EXT=

if [ $OS = Linux ] ; then
  if [ $MACHINE = i386 -o $MACHINE = i486 -o $MACHINE = i586 -o $MACHINE = i686 ] ; then
    ARCH=glnx86
  elif [ $MACHINE = x86_64 ] ; then
    ARCH=glnxa64
  elif [ $MACHINE = armv6l ] ; then
    ARCH=raspberrypi
  elif [ $MACHINE = armv7l ] ; then
    ARCH=raspberrypi
  fi
elif [ $OS = Darwin ] ; then
  if [ $MACHINE = i386 ] ; then
    ARCH=maci
  elif [ $MACHINE = x86_64 ] ; then
    ARCH=maci64
  fi
elif [ $OS = CYGWIN_NT-10.0 ] ; then
  EXT=.exe
  if [ $MACHINE = i386 ] ; then
    ARCH=win32
  elif [ $MACHINE = x86_64 ] ; then
    ARCH=win64
  fi
fi

if [ -z "$ARCH" ] ; then
  echo Error: cannot determine architecture for $OS on $MACHINE
  exit
else
  echo Downloading $ARCH binaries for $OS on $MACHINE
fi

for NAME in buffer openbci2ft jaga2ft ; do
  URL=https://github.com/fieldtrip/fieldtrip/raw/master/realtime/bin/$ARCH/$NAME$EXT
  echo ------------------------------------------------------------------------------
  echo Downloading binary from $URL
  echo See http://www.fieldtriptoolbox.org/development/realtime for details
  echo ------------------------------------------------------------------------------
  wget $URL -O $DIR/$NAME$EXT
  chmod +x $DIR/$NAME$EXT
done
