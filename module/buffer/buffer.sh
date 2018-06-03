#!/bin/bash
#
# This will start the FieldTrip buffer (or multiple) according to the settings
# in the specified or the default inifile.
#
# Use as
#   buffer.sh [-i <inifile>] [-h] [-v]

# include library with helper functions
. "$(dirname "$0")/../../lib/EEGsynth.sh"

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`
BINDIR=$DIR/../../bin

# set the default
INIFILE=${DIR}/${NAME}.ini
VERBOSE=0

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
