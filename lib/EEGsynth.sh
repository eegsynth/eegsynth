
# determine the machine on which this is running
UNAME=`uname`
MACHINE=`uname -m`

if [ $MACHINE = Darwin ] ; then 
  #  OS X version 10.6  corresponds to Snow Leopard
  #  OS X version 10.7  corresponds to Lion
  #  OS X version 10.8  corresponds to Mountain Lion
  #  OS X version 10.9  corresponds to Mavericks
  #  OS X version 10.10 corresponds to Yosemite
  #  OS X version 10.11 corresponds to El Capitan
  # macOS version 10.12 corresponds to Sierra
  # macOS version 10.13 corresponds to High Sierra
  # the following may be needed for portmidi on OS X prior to El Captain
  MAJOR_MAC_VERSION=$(sw_vers -productVersion | awk -F '.' '{print $1 "." $2}')
  if [ -f /usr/local/lib/libportmidi.dylib ] ; then
    export DYLD_LIBRARY_PATH=/usr/local/lib/:$DYLD_LIBRARY_PATH
  elif [ -f /opt/local/lib/libportmidi.dylib ] ; then
    export DYLD_LIBRARY_PATH=/opt/local/lib/:$DYLD_LIBRARY_PATH
  fi
fi


# Include library to parse ini file
. "$(dirname "$0")/../../lib/shini.sh"

# Declare the required handler for parsed variables, this creates local variables
__shini_parsed()
{
export ini_$1_$2=$3
}

# shared functions for all startup scripts
function log_action_msg () {
  echo $* 1>&1
}

function log_action_err () {
  echo $* 1>&2
}

function check_running_process () {
  if [ ! -f "$PIDFILE" ]; then
    return 1
  else
    kill -0 `cat "$PIDFILE"` 2> /dev/null
    return $?
  fi
}

function ini_parser () {
  INIFILE="$1"
  SECTION="$2"
  ITEM="$3"
  cat "$INIFILE" | sed -n /^\[$SECTION\]/,/^\[.*\]/p | grep "^[[:space:]]*$ITEM[[:space:]]*=" | sed s/.*=[[:space:]]*// | tr -d \\r
}

function status_led () {
  if [ -f /usr/local/bin/status_led_$1 ] ; then
    sleep 0.2
    /usr/local/bin/status_led_$1
  fi
}
