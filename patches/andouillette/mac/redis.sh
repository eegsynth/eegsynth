#!/bin/bash
#
# This will start the REDIS server according to the settings
# in the specified or the default inifile.
#
# Use as
#   redis.sh [-i <inifile>] [-h] [-v]

# include library with helper functions
. "$(dirname "$0")/../../lib/EEGsynth.sh"

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`
BINDIR=$DIR/../../bin

# set the default
VERBOSE=notice

if [ -e "/usr/bin/redis-server" ]; then
  # on raspberry pi
  COMMAND="/usr/bin/redis-server"
  CONFIG=`echo $COMMAND | sed s/bin/etc/g | sed s/-server/\.conf/g`
else
  # on maci64
  COMMAND=`which redis-server`
  CONFIG=`echo $COMMAND | sed s/bin/etc/g | sed s/-server/\.conf/g`
fi

while getopts "hvd" option; do
  case "${option}" in
    d)
      VERBOSE=debug
      ;;
    v)
      VERBOSE=verbose
      ;;
    h)
      echo "Use as: $0 [-h] [-v]"
      ;;
    \?)
      echo "Invalid option: -${OPTARG}" >&2
      ;;
  esac
done

# debug (a lot of information, useful for development/testing)
# verbose (many rarely useful info, but not a mess like the debug level)
# notice (moderately verbose, what you want in production probably)
# warning (only very important / critical messages are logged)

echo COMMAND=$COMMAND
echo CONFIG=$CONFIG
echo VERBOSE=$VERBOSE

${COMMAND} ${CONFIG} --loglevel $VERBOSE --protected-mode no
