#!/bin/bash
#
# This will start the FieldTrip buffer (or multiple) according to the settings
# in the specified or the default inifile.
#
# Use as
#   buffer.sh [-h] [-v] [-i <inifile>]

# include library with helper functions
. "$(dirname "$0")/../../lib/EEGsynth.sh"

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`
BINDIR=$DIR/../../bin

# set the default
INIFILE=${DIR}/${NAME}.ini
VERBOSE=0

while getopts "hvi:" OPTION; do
  case ${OPTION} in
    h)
      echo "Use as: $0 [-h] [-v] [-i <inifile>]"
      exit 0
      ;;
    v)
      VERBOSE=1
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
PORT=$ini_fieldtrip_port

if [ ${VERBOSE} == 1 ] ; then
  echo INIFILE=$INIFILE
  echo PORT=$PORT
fi

if [[ ${PORT} == *","* ]] ; then
  ${BINDIR}/parallel ${BINDIR}/buffer ${PORT}
else
  ${BINDIR}/buffer ${PORT}
fi
