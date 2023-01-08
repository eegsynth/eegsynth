#!/bin/bash
#
# This will start the REDIS server according to the settings
# in the specified or the default inifile.
#
# Use as
#   redis.sh [-h] [-v] [-d] [-i <inifile>]

# include library with helper functions
. "$(dirname "$0")/../../lib/EEGsynth.sh"

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`
BINDIR=$DIR/../../bin

# set the default
INIFILE=${DIR}/${NAME}.ini
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

# debug (a lot of information, useful for development/testing)
# verbose (many rarely useful info, but not a mess like the debug level)
# notice (moderately verbose, what you want in production probably)
# warning (only very important / critical messages are logged)

while getopts "hvdi:" OPTION; do
  case ${OPTION} in
    h)
      echo "Use as: $0 [-h] [-v] [-d] [-i <inifile>]"
      exit 0
      ;;
    v)
      VERBOSE=verbose
      ;;
    d)
      VERBOSE=debug
      ;;
    i)
      INIFILE=${OPTARG}
      ;;
    \?)
      exit 0
      ;;
  esac
done

# this parses the ini file and creates local variables
shini_parse $INIFILE
PORT=$ini_redis_port

echo COMMAND=$COMMAND
echo CONFIG=$CONFIG
echo VERBOSE=$VERBOSE

${COMMAND} ${CONFIG} --port $PORT --loglevel $VERBOSE --protected-mode no
