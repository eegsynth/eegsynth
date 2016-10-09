
# the following is needed for portmidi on OS X
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/opt/local/lib

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
