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
INIFILE=${DIR}/${NAME}.ini
VERBOSE=0

if [ -e "/usr/bin/redis-server" ]; then
  # on raspberry pi
  COMMAND="/usr/bin/redis-server"
  CONFIG=`echo $COMMAND | sed s/bin/etc/g | sed s/-server/\.conf/g`
else
  # on maci64
  COMMAND=`which redis-server`
  CONFIG=`echo $COMMAND | sed s/bin/etc/g | sed s/-server/\.conf/g`
fi

while getopts "hvi:" option; do
  case "${option}" in
    i)
      INIFILE=${OPTARG}
      ;;
    v)
      VERBOSE=1
      ;;
    h)
      echo "Use as: $0 [-i <inifile>] [-h] [-v]"
      ;;
    \?)
      echo "Invalid option: -${OPTARG}" >&2
      ;;
  esac
done

# this parses the ini file and creates local variables
shini_parse $INIFILE
PORT=$ini_redis_port

if [ ${VERBOSE} == 1 ] ; then
  echo INIFILE=$INIFILE
  echo PORT=$PORT
fi

${COMMAND} --port ${PORT}
