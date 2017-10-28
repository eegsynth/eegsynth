#!/bin/bash
#
# This will start the openbci2ft application with the specified inifile or
# with the default inifile from this directory.
#
# Use as
#   openbci2ft.sh [-i <inifile>] [-h] [-v]

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

if [ ${VERBOSE} == 1 ] ; then
  echo INIFILE=$INIFILE
fi

${BINDIR}/openbci2ft ${INIFILE}
